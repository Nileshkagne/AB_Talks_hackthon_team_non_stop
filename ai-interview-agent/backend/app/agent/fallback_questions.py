"""
Module for handling Gemini API errors without fallback questions.
Strict policy: No hardcoded questions or templates allowed.
"""
from typing import Dict, NoReturn
from app.llm.gemini import GeminiError


def generate_dynamic_fallback(*args, **kwargs) -> NoReturn:
    """Strict policy: Hardcoded question fallbacks are disabled."""
    raise GeminiError("Gemini API call failed. Hardcoded question fallback is disabled.")
