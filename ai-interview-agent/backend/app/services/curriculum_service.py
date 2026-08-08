import json
from pathlib import Path
from typing import Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_CURRICULUM_PATH = _DATA_DIR / "curriculum.json"


def _load_and_validate_curriculum() -> Dict:
    if not _CURRICULUM_PATH.exists():
        raise RuntimeError(f"Curriculum file not found at: {_CURRICULUM_PATH}")

    with open(_CURRICULUM_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    days = data.get("days", [])
    if len(days) != 31:
        raise ValueError(f"Expected exactly 31 curriculum days, but found {len(days)}")

    return data


# Cache curriculum at import time
_CURRICULUM_CACHE: Dict = _load_and_validate_curriculum()
_DAYS_BY_NUMBER: Dict[int, Dict] = {
    day["day"]: day for day in _CURRICULUM_CACHE.get("days", [])
}


def load_curriculum() -> Dict:
    """Returns the cached curriculum data."""
    return _CURRICULUM_CACHE


def get_day(day_number: int) -> Optional[Dict]:
    """Returns day details for the given day number, or None if not found."""
    return _DAYS_BY_NUMBER.get(day_number)


def all_days() -> List[Dict]:
    """Returns all 31 curriculum days."""
    return _CURRICULUM_CACHE.get("days", [])


def get_module_for_day(day_number: int) -> str:
    """Looks up which module's [start, end] range contains day_number and returns its title."""
    modules = _CURRICULUM_CACHE.get("modules", [])
    for module in modules:
        days_range = module.get("days", [])
        if len(days_range) == 2:
            start_day, end_day = days_range[0], days_range[1]
            if start_day <= day_number <= end_day:
                return module.get("title", "")
    return ""
