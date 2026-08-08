import json
import os
import time
from typing import Any, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiError(Exception):
    """Custom exception raised when Gemini API call or parsing fails."""
    pass


_configured = False


def _ensure_configured():
    global _configured
    if not _configured:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise GeminiError("GEMINI_API_KEY environment variable is missing")
        genai.configure(api_key=api_key)
        _configured = True


def generate_structured(
    prompt: str,
    system_instruction: str,
    model_name: str = "gemini-1.5-flash",
    response_schema: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Calls Gemini API with structured JSON output requirements.
    Retries once on error, then raises GeminiError.
    """
    _ensure_configured()

    generation_config = genai.GenerationConfig(
        response_mime_type="application/json",
        temperature=0.7,
    )

    if response_schema:
        generation_config.response_schema = response_schema

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction,
    )

    last_exc = None
    for attempt in range(2):
        try:
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
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
