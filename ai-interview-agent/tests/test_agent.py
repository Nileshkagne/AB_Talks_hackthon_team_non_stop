import time
import pytest
from unittest.mock import patch
from app.agent.nodes import (
    build_profile_from_candidate,
    evaluate_answer,
    generate_question,
    update_state,
)
from app.agent.router import bump_down, bump_up, dedupe, score_day, select_best_topic
from app.database import repository
from app.llm.gemini import GeminiError
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


def test_two_different_candidates_produce_different_sequences():
    """Asserts two different candidate profiles (strong vs weak/skipped) produce distinct topic/difficulty sequences."""
    days = all_days()

    # Candidate 1: Strong AI Engineer (CAND-003)
    cand_strong = get_candidate("CAND-003")
    prof_strong = build_profile_from_candidate(cand_strong, days)

    # Candidate 2: IT Support with failed/skipped missions (CAND-010)
    cand_weak = get_candidate("CAND-010")
    prof_weak = build_profile_from_candidate(cand_weak, days)

    # Assert initial starting difficulty differs
    assert prof_strong["difficulty"] != prof_weak["difficulty"]

    # Select initial best topics for both
    topic_strong = select_best_topic(prof_strong, days, set(), get_module_for_day)
    topic_weak = select_best_topic(prof_weak, days, set(), get_module_for_day)

    # Assert topic selections target their specific weak/skipped areas resulting in different initial topics
    assert topic_strong["day"] != topic_weak["day"] or topic_strong["title"] != topic_weak["title"]


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


def test_generate_question_gemini_success():
    mock_response = {
        "question": "What are the primary performance trade-offs when tuning chunk size in a RAG pipeline?",
        "type": "trade_off",
    }
    state = {
        "session_id": "test-mock-gemini-1",
        "question_count": 0,
        "current_day": 7,
        "current_topic": "Embeddings Explained",
        "difficulty": "advanced",
        "follow_up_count": 0,
        "profile": {"role": "AI Engineer", "experience": 5},
    }

    with patch("app.llm.gemini.generate_structured", return_value=mock_response):
        result = generate_question(state)
        assert result["question_count"] == 1
        assert result["last_question"] == mock_response["question"]
        assert result["last_question_type"] == "trade_off"
        assert mock_response["question"] in result["reply"]
        assert result["done"] is False


def test_generate_question_gemini_error_raises_gemini_error():
    state = {
        "session_id": "test-mock-gemini-2",
        "question_count": 0,
        "current_day": 7,
        "current_topic": "Embeddings Explained",
        "difficulty": "advanced",
        "follow_up_count": 0,
        "last_answer": "I used cosine similarity to index high dimensional vectors with FAISS.",
        "profile": {"role": "AI Engineer", "experience": 5},
    }

    with patch("app.llm.gemini.generate_structured", side_effect=GeminiError("API rate limit exceeded")):
        with pytest.raises(GeminiError):
            generate_question(state)


def test_evaluation_and_update_state_strong_answer_bumps_difficulty_up():
    session_id = f"test-eval-strong-{int(time.time())}"
    if repository.get_client():
        repository.create_session(session_id, "CAND-001", "intermediate")

    mock_eval = {
        "correctness": 9.5,
        "technical_depth": 9.0,
        "reasoning": 9.0,
        "practicality": 9.0,
        "communication": 9.5,
        "overall_score": 9.2,
        "confidence": 0.95,
        "missing_concepts": [],
        "follow_up_needed": False,
        "evaluation_summary": "Exceptional technical response.",
    }
    state = {
        "session_id": session_id,
        "question_count": 1,
        "last_question": "Explain vector embeddings.",
        "last_answer": "Vector embeddings represent tokens in dense high-dimensional space where distance maps to semantic similarity.",
        "current_day": 7,
        "current_topic": "Embeddings Explained",
        "difficulty": "intermediate",
        "covered_days": [],
        "strengths": [],
        "weaknesses": [],
        "profile": {"role": "AI Engineer", "experience": 3},
    }

    with patch("app.llm.gemini.generate_structured", return_value=mock_eval):
        eval_res = evaluate_answer(state)
        state["last_evaluation"] = eval_res["last_evaluation"]
        updated = update_state(state)

        assert updated["difficulty"] == "advanced"
        assert "Embeddings Explained" in updated["strengths"]
        assert 7 in updated["covered_days"]


def test_evaluation_and_update_state_weak_answer_bumps_difficulty_down():
    session_id = f"test-eval-weak-{int(time.time())}"
    if repository.get_client():
        repository.create_session(session_id, "CAND-001", "advanced")

    mock_eval = {
        "correctness": 4.0,
        "technical_depth": 4.0,
        "reasoning": 4.5,
        "practicality": 5.0,
        "communication": 5.0,
        "overall_score": 4.35,
        "confidence": 0.85,
        "missing_concepts": ["cosine similarity", "dense vectors"],
        "follow_up_needed": True,
        "evaluation_summary": "Lacked technical depth and missed core concepts.",
    }
    state = {
        "session_id": session_id,
        "question_count": 1,
        "last_question": "Explain vector embeddings.",
        "last_answer": "I don't really know, maybe something with math.",
        "current_day": 7,
        "current_topic": "Embeddings Explained",
        "difficulty": "advanced",
        "covered_days": [],
        "strengths": [],
        "weaknesses": [],
        "profile": {"role": "AI Engineer", "experience": 3},
    }

    with patch("app.llm.gemini.generate_structured", return_value=mock_eval):
        eval_res = evaluate_answer(state)
        state["last_evaluation"] = eval_res["last_evaluation"]
        updated = update_state(state)

        assert updated["difficulty"] == "intermediate"
        assert "Embeddings Explained" in updated["weaknesses"]
        assert updated["follow_up_count"] == 1
