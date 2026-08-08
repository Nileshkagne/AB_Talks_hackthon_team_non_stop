import json
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from dotenv import load_dotenv

from app.llm.config import MODEL_FALLBACK_CHAIN

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Custom exception raised when Gemini API call or parsing fails."""
    pass


_client: Optional[genai.Client] = None
_current_api_key: Optional[str] = None

# ── In-process rate limiter ──────────────────────────────────────────
# Ensures at least MIN_INTERVAL_SECONDS between consecutive Gemini calls
# from this backend process to avoid self-inflicted rate-limit bursts.
_MIN_INTERVAL_SECONDS = 2.5
_last_call_time = 0.0
_rate_lock = threading.Lock()


def _wait_for_rate_limit():
    """Block until at least _MIN_INTERVAL_SECONDS since the last call."""
    global _last_call_time
    with _rate_lock:
        now = time.monotonic()
        elapsed = now - _last_call_time
        if elapsed < _MIN_INTERVAL_SECONDS:
            wait = _MIN_INTERVAL_SECONDS - elapsed
            logger.debug("[gemini] rate-limiter: waiting %.1fs before next call", wait)
            time.sleep(wait)
        _last_call_time = time.monotonic()


def _get_client() -> genai.Client:
    global _client, _current_api_key

    # Resolve .env locations relative to this file
    backend_dir = Path(__file__).resolve().parent.parent.parent
    possible_envs = [
        backend_dir / ".env",
        backend_dir.parent / ".env",
    ]
    for env_path in possible_envs:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            break

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("GEMINI_API_KEY environment variable is missing in .env")

    # Re-create client if key changed or client not initialized
    if _client is None or _current_api_key != api_key:
        _current_api_key = api_key
        _client = genai.Client(api_key=api_key)
        logger.info("[gemini] Initialized Gemini client with API key ending in ...%s", api_key[-4:] if len(api_key) >= 4 else "****")

    return _client


def _is_rate_limit_error(exc: Exception) -> bool:
    """Check if the exception is any 429 rate-limit or quota error."""
    code = getattr(exc, "code", getattr(exc, "status_code", None))
    if code == 429:
        return True
    error_str = str(exc).lower()
    return "429" in error_str or "resource_exhausted" in error_str


def is_daily_quota_error(exc: Exception) -> bool:
    """
    Returns True if the error indicates a DAILY quota ceiling (RPD/PerDay).
    A daily quota failure means retrying the same model is useless and we
    must immediately skip to the next model in the fallback chain.
    """
    if not _is_rate_limit_error(exc):
        return False
    error_str = str(exc).lower()
    if "perday" in error_str or "per_day" in error_str or "daily" in error_str or "requests per day" in error_str:
        return True
    if "perminute" not in error_str and "rpm" not in error_str:
        return True
    return False


def is_per_minute_rate_limit_error(exc: Exception) -> bool:
    """
    Returns True if the error indicates a temporary per-minute burst limit (RPM).
    Per-minute limits should be retried with exponential backoff on the SAME model.
    """
    if not _is_rate_limit_error(exc):
        return False
    error_str = str(exc).lower()
    return "perminute" in error_str or "rpm" in error_str or "requests per minute" in error_str


def _extract_retry_after(exc: Exception) -> Optional[float]:
    """Try to extract Retry-After seconds from a 429 error response."""
    try:
        error_str = str(exc)
        if "retryDelay" in error_str:
            match = re.search(r'"retryDelay":\s*"(\d+)s?"', error_str)
            if match:
                return float(match.group(1))
        if "retry in" in error_str.lower():
            match = re.search(r'retry in (\d+\.?\d*)', error_str, re.IGNORECASE)
            if match:
                return float(match.group(1))
    except Exception:
        pass
    return None


# Thread-local storage for request-level fallback tracking
_fallback_used = threading.local()


def mark_fallback_used():
    """Mark that the entire model chain was exhausted and static fallback was used."""
    _fallback_used.value = True


def was_fallback_used() -> bool:
    """Check if static fallback was used during the current request processing."""
    return getattr(_fallback_used, 'value', False)


def reset_fallback_flag():
    """Reset the fallback flag at the start of each request."""
    _fallback_used.value = False


def _clean_and_parse_json(text: str) -> Dict[str, Any]:
    """Cleans code fences and parses JSON robustly, extracting JSON object if extra text exists."""
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Extract JSON object substring if model returned extra trailing commentary
    match = re.search(r'(\{.*\})', raw, re.DOTALL)
    if match:
        extracted = match.group(1).strip()
        parsed = json.loads(extracted)
        if isinstance(parsed, dict):
            return parsed

    raise ValueError(f"Could not parse valid JSON dict from model response: {text[:200]}")


def generate_structured(
    prompt: str,
    system_instruction: str,
    model_name: Optional[str] = None,
    response_schema: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Calls Gemini API with structured JSON output using a model fallback chain.

    Fallback Logic:
    1. Iterates through MODEL_FALLBACK_CHAIN (or model_name if specified).
    2. On DAILY quota error (RPD / PerDay): immediately skips to next model in chain.
    3. On PER-MINUTE rate limit (RPM): retries up to 3 times on SAME model with backoff,
       then advances to next model if retries fail.
    4. On JSON parsing error: logs warning and tries next model in fallback chain.
    5. On Non-quota API errors (auth, 404, 5xx): raises GeminiError immediately.
    6. Returns parsed dict with '_model_used' metadata attached.
    """
    chain = [model_name] if model_name else MODEL_FALLBACK_CHAIN
    last_exc = None

    for model_index, current_model in enumerate(chain):
        _wait_for_rate_limit()
        client = _get_client()

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.4,
        )

        if response_schema:
            config.response_schema = response_schema

        max_same_model_attempts = 3
        for attempt in range(max_same_model_attempts):
            try:
                logger.debug("[gemini] model=%s (chain %d/%d) attempt=%d prompt_len=%d",
                             current_model, model_index + 1, len(chain), attempt + 1, len(prompt))

                response = client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=config,
                )

                parsed = _clean_and_parse_json(response.text)
                parsed["_model_used"] = current_model
                if model_index > 0:
                    logger.info("[gemini] Successfully served request using fallback model: %s (chain position %d)",
                                current_model, model_index + 1)
                return parsed

            except (json.JSONDecodeError, ValueError) as parse_err:
                last_exc = parse_err
                logger.warning(
                    "[gemini] JSON output parse error on model=%s (chain position %d/%d): %s. Trying next model...",
                    current_model, model_index + 1, len(chain), parse_err
                )
                break  # Try next model in chain

            except Exception as e:
                last_exc = e

                if is_daily_quota_error(e):
                    logger.warning(
                        "[gemini] DAILY quota exhausted on model=%s (chain position %d/%d). Immediately skipping to next model in chain. Error: %s",
                        current_model, model_index + 1, len(chain), str(e)[:150]
                    )
                    break  # Skip to next model in chain immediately

                elif is_per_minute_rate_limit_error(e):
                    retry_after = _extract_retry_after(e)
                    wait = retry_after if (retry_after and retry_after <= 15) else min(1.0 * (2 ** attempt), 6.0)
                    if attempt < max_same_model_attempts - 1:
                        logger.warning(
                            "[gemini] PER-MINUTE rate limit on model=%s, retrying in %.1fs (attempt %d/%d)",
                            current_model, wait, attempt + 1, max_same_model_attempts
                        )
                        time.sleep(wait)
                        continue
                    else:
                        logger.warning(
                            "[gemini] PER-MINUTE retries exhausted on model=%s, advancing to next model in chain",
                            current_model
                        )
                        break
                else:
                    # Non-quota API error (auth, 404, 5xx) -> do NOT switch models
                    logger.error("[gemini] Non-quota error on model=%s: %s", current_model, e)
                    raise GeminiError(f"Gemini API call failed on {current_model}: {e}") from e

    # Entire chain exhausted
    logger.error("[gemini] Entire model fallback chain exhausted (%d models tried). Last error: %s",
                 len(chain), last_exc)
    raise GeminiError(f"All models in Gemini fallback chain exhausted: {last_exc}") from last_exc
