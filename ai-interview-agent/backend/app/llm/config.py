"""
LLM Configuration and Fallback Chain.
"""

# Ordered fallback chain from most capable to least capable.
# All models in this list are verified available and support structured JSON outputs.
MODEL_FALLBACK_CHAIN = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-2.0-flash",
]
