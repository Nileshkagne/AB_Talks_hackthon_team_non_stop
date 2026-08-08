from app.agent.nodes import build_profile_from_candidate
from app.agent.router import bump_down, bump_up, dedupe, score_day, select_best_topic
from app.services.candidate_service import get_candidate
from app.services.curriculum_service import all_days, get_module_for_day


def test_build_profile_divergent_difficulty():
    days = all_days()

    # CAND-003: Emily Chen (AI Engineer, high first-try ratio) -> advanced
    cand_strong = get_candidate("CAND-003")
    assert cand_strong is not None
    prof_strong = build_profile_from_candidate(cand_strong, days)
    assert prof_strong["difficulty"] == "advanced"
    assert prof_strong["confidence_level"] >= 0.8

    # CAND-017: Tyler Brooks (Software Engineer, 0 first try, 0 commit days) -> foundation
    cand_weak = get_candidate("CAND-017")
    assert cand_weak is not None
    prof_weak = build_profile_from_candidate(cand_weak, days)

    # Assert build_profile gives them different initial difficulties
    assert prof_strong["difficulty"] != prof_weak["difficulty"]
    assert prof_strong["confidence_level"] > prof_weak["confidence_level"]


def test_score_day_ranks_weak_topic_higher_than_normal():
    days = all_days()
    cand = get_candidate("CAND-010")
    assert cand is not None
    prof = build_profile_from_candidate(cand, days)

    assert len(prof["weak_topics"]) > 0
    weak_topic_title = prof["weak_topics"][0]

    weak_day = next(d for d in days if d["title"] == weak_topic_title)
    normal_day = next(
        d
        for d in days
        if d["title"] not in prof["weak_topics"]
        and d["title"] not in prof["skipped_topics"]
    )

    weak_score = score_day(weak_day, prof, set(), get_module_for_day)
    normal_score = score_day(normal_day, prof, set(), get_module_for_day)

    assert weak_score > normal_score


def test_select_best_topic_picks_highest_scoring_uncovered_day():
    days = all_days()
    cand = get_candidate("CAND-010")
    assert cand is not None
    prof = build_profile_from_candidate(cand, days)

    selected = select_best_topic(prof, days, set(), get_module_for_day)
    assert selected is not None
    assert (
        selected["title"] in prof["weak_topics"]
        or selected["title"] in prof["skipped_topics"]
    )


def test_bump_up_and_bump_down():
    assert bump_up("foundation") == "intermediate"
    assert bump_up("intermediate") == "advanced"
    assert bump_up("advanced") == "expert"
    assert bump_up("expert") == "expert"

    assert bump_down("expert") == "advanced"
    assert bump_down("advanced") == "intermediate"
    assert bump_down("intermediate") == "foundation"
    assert bump_down("foundation") == "foundation"
