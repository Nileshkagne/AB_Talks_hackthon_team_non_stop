import json
import logging
import os
import threading
import time
from typing import Any, Dict, Optional

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Custom exception raised when Gemini API call or parsing fails."""
    pass


from pathlib import Path

_client: Optional[genai.Client] = None
_current_api_key: Optional[str] = None

# ── STEP 4: In-process rate limiter ──────────────────────────────────
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
    """Check if the exception is a 429 rate-limit error."""
    code = getattr(exc, "code", getattr(exc, "status_code", None))
    if code == 429:
        return True
    error_str = str(exc).lower()
    return "429" in error_str or "resource_exhausted" in error_str


def _extract_retry_after(exc: Exception) -> Optional[float]:
    """Try to extract Retry-After seconds from a 429 error response."""
    try:
        error_str = str(exc)
        # Look for "retryDelay": "Ns" pattern in the error body
        if "retryDelay" in error_str:
            import re
            match = re.search(r'"retryDelay":\s*"(\d+)s?"', error_str)
            if match:
                return float(match.group(1))
        # Look for "Please retry in Xs" pattern
        if "retry in" in error_str.lower():
            import re
            match = re.search(r'retry in (\d+\.?\d*)', error_str, re.IGNORECASE)
            if match:
                return float(match.group(1))
    except Exception:
        pass
    return None


# Track whether any call in the current request used a fallback
_fallback_used = threading.local()


def mark_fallback_used():
    """Mark that a fallback was used during the current request processing."""
    _fallback_used.value = True


def was_fallback_used() -> bool:
    """Check if any fallback was used during the current request processing."""
    return getattr(_fallback_used, 'value', False)


def reset_fallback_flag():
    """Reset the fallback flag at the start of each request."""
    _fallback_used.value = False


def generate_structured(
    prompt: str,
    system_instruction: str,
    model_name: str = "gemini-flash-latest",
    response_schema: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Calls Gemini API with structured JSON output.

    Retry strategy:
    - 429 (rate limit): exponential backoff up to 3 attempts (1s, 2s, 4s),
      honoring Retry-After if present.
    - Other errors: single retry after 0.5s, then raise.
    """
    # STEP 4: Apply in-process rate limiting before each call
    _wait_for_rate_limit()

    client = _get_client()

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        temperature=0.4,
    )

    if response_schema:
        config.response_schema = response_schema

    max_attempts = 4  # 1 initial + 3 retries for 429s
    last_exc = None

    for attempt in range(max_attempts):
        try:
            logger.debug("[gemini] attempt=%d model=%s prompt_len=%d",
                         attempt + 1, model_name, len(prompt))

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            text = response.text.strip()

            # Strip markdown code fences if present
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()

            parsed = json.loads(text)
            if isinstance(parsed, dict):
                if attempt > 0:
                    logger.info("[gemini] succeeded on attempt %d after retries", attempt + 1)
                return parsed
            raise ValueError(f"Expected JSON object (dict), got {type(parsed)}")

        except Exception as e:
            last_exc = e

            if _is_rate_limit_error(e):
                # STEP 3: Exponential backoff specifically for 429s
                retry_after = _extract_retry_after(e)
                if retry_after and retry_after <= 60:
                    wait = min(retry_after, 15)  # Cap at 15s
                else:
                    wait = min(1.0 * (2 ** attempt), 8.0)  # 1s, 2s, 4s, 8s

                if attempt < max_attempts - 1:
                    logger.warning(
                        "[gemini] 429 rate-limited on attempt %d, retrying in %.1fs "
                        "(model=%s, retry_after=%s)",
                        attempt + 1, wait, model_name, retry_after
                    )
                    time.sleep(wait)
                    continue
                else:
                    logger.error(
                        "[gemini] 429 rate-limited on ALL %d attempts, giving up "
                        "(model=%s)", max_attempts, model_name
                    )
            else:
                # Non-429 error: single retry only
                if attempt == 0:
                    logger.warning("[gemini] non-429 error on attempt 1, retrying once: %s", e)
                    time.sleep(0.5)
                    continue
                else:
                    logger.error("[gemini] non-429 error on attempt %d, giving up: %s",
                                 attempt + 1, e)
                    break  # Don't retry non-429 errors more than once

    raise GeminiError(f"Gemini API call failed after {attempt + 1} attempts: {last_exc}") from last_exc
