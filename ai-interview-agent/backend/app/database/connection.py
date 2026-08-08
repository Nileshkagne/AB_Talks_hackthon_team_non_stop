import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env file from project root or current environment
_env_root = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if _env_root.exists():
    load_dotenv(dotenv_path=_env_root)
else:
    load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    """Returns a singleton Supabase Client instance."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables"
            )
        _client = create_client(url, key)
    return _client
