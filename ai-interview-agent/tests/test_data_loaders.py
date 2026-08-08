from app.services.curriculum_service import (
    all_days,
    get_day,
    get_module_for_day,
    load_curriculum,
)
from app.services.candidate_service import (
    all_candidates,
    get_candidate,
    load_candidates,
)


def test_curriculum_loader_31_days():
    curriculum = load_curriculum()
    assert "days" in curriculum
    days = all_days()
    assert len(days) == 31


def test_candidates_loader_20_candidates():
    candidates_data = load_candidates()
    assert "candidates" in candidates_data
    candidates = all_candidates()
    assert len(candidates) == 20


def test_get_candidate_cand_001():
    candidate = get_candidate("CAND-001")
    assert candidate is not None
    assert candidate["member"]["id"] == "CAND-001"


def test_get_module_for_day_1():
    module_title = get_module_for_day(1)
    assert module_title == "Environment & Tooling"


def test_get_module_for_day_31():
    module_title = get_module_for_day(31)
    assert module_title == "Production & Capstone"
