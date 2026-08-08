import os
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv("backend/.env")

api_key = os.getenv("GEMINI_API_KEY")
print("Loaded GEMINI_API_KEY ending in:", api_key[-4:] if api_key else "None")

client = genai.Client(api_key=api_key)

candidates = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-pro-latest",
]

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    temperature=0.4,
)

print("\nTesting available Gemini models for structured JSON output:")
for m in candidates:
    try:
        r = client.models.generate_content(model=m, contents='{"test": true}', config=config)
        print(f" [OK] {m} -> {r.text.strip()[:60]}")
    except Exception as e:
        print(f" [FAIL] {m} -> {str(e)[:120]}")
