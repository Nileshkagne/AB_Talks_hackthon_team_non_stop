import json
from pathlib import Path
from typing import Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_CANDIDATES_PATH = _DATA_DIR / "candidates.json"


def _load_and_validate_candidates() -> Dict:
    if not _CANDIDATES_PATH.exists():
        raise RuntimeError(f"Candidates file not found at: {_CANDIDATES_PATH}")

    with open(_CANDIDATES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    candidates = data.get("candidates", [])
    if len(candidates) < 1:
        raise ValueError("Expected at least 1 candidate in candidates.json")

    return data


# Cache candidates at import time
_CANDIDATES_CACHE: Dict = _load_and_validate_candidates()
_CANDIDATES_BY_ID: Dict[str, Dict] = {
    cand["member"]["id"]: cand
    for cand in _CANDIDATES_CACHE.get("candidates", [])
    if "member" in cand and "id" in cand["member"]
}


def load_candidates() -> Dict:
    """Returns the cached candidates data."""
    return _CANDIDATES_CACHE


def get_candidate(candidate_id: str) -> Optional[Dict]:
    """Searches for a candidate by member.id."""
    return _CANDIDATES_BY_ID.get(candidate_id)


def all_candidates() -> List[Dict]:
    """Returns all candidate dicts."""
    return _CANDIDATES_CACHE.get("candidates", [])
