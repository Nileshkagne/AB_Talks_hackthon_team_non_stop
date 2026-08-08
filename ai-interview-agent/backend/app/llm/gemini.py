import json
import os
import time
from typing import Any, Dict, Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


class GeminiError(Exception):
    """Custom exception raised when Gemini API call or parsing fails."""
    pass


_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise GeminiError("GEMINI_API_KEY environment variable is missing")
        _client = genai.Client(api_key=api_key)
    return _client


def generate_structured(
    prompt: str,
    system_instruction: str,
    model_name: str = "gemini-flash-latest",
    response_schema: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Calls Gemini API with structured JSON output requirements.
    Uses the current google-genai SDK (not the deprecated google-generativeai).
    Retries once on error, then raises GeminiError.
    """
    client = _get_client()

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        temperature=0.4,
    )

    if response_schema:
        config.response_schema = response_schema

    last_exc = None
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            text = response.text.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()

            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
            raise ValueError(f"Expected JSON object (dict), got {type(parsed)}")

        except Exception as e:
            last_exc = e
            if attempt == 0:
                time.sleep(0.5)

    raise GeminiError(f"Gemini API call failed after retries: {last_exc}") from last_exc
