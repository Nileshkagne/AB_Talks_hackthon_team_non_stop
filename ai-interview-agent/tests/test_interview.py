from unittest.mock import patch
from app.agent.router import (
    MAX_FOLLOWUPS_PER_TOPIC,
    MAX_QUESTIONS,
    MIN_CURRICULUM_DAYS,
    MIN_QUESTIONS,
    decide_next_action,
)
from app.services.interview_service import handle_turn


def test_never_finishes_before_min_questions():
    """Asserts interview flow never finishes before MIN_QUESTIONS (8)."""
    for q_count in range(0, MIN_QUESTIONS):
        state = {
            "question_count": q_count,
            "covered_days": [1, 2, 3, 4, 5],
            "last_evaluation": {"overall_score": 9.5, "follow_up_needed": False},
            "follow_up_count": 0,
        }
        action = decide_next_action(state)
        assert action != "finish", f"Interview finished prematurely at question_count={q_count}"


def test_never_finishes_with_fewer_than_min_covered_days():
    """Asserts interview never finishes with < 4 covered days before MAX_QUESTIONS."""
    for q_count in range(MIN_QUESTIONS, MAX_QUESTIONS):
        state = {
            "question_count": q_count,
            "covered_days": [1, 2],  # Fewer than MIN_CURRICULUM_DAYS (4)
            "last_evaluation": {"overall_score": 9.5, "follow_up_needed": False},
            "follow_up_count": 0,
        }
        action = decide_next_action(state)
        assert action != "finish", f"Should not finish at q_count={q_count} with 2 covered days"
        assert action == "new_topic"


def test_force_finishes_at_max_questions():
    """Asserts interview force-finishes at MAX_QUESTIONS (12) regardless of state."""
    state = {
        "question_count": MAX_QUESTIONS,
        "covered_days": [1],
        "last_evaluation": {"overall_score": 4.0, "follow_up_needed": True},
        "follow_up_count": 0,
    }
    action = decide_next_action(state)
    assert action == "finish"

    state["question_count"] = 13
    assert decide_next_action(state) == "finish"


def test_max_followups_per_topic_cap():
    """Asserts follow_up_count is capped at MAX_FOLLOWUPS_PER_TOPIC (2) before changing topic."""
    state = {
        "question_count": 4,
        "covered_days": [1],
        "last_evaluation": {"overall_score": 4.0, "follow_up_needed": True},
        "follow_up_count": 0,
    }
    assert decide_next_action(state) == "follow_up"

    state["follow_up_count"] = 1
    assert decide_next_action(state) == "follow_up"

    # Reached cap of 2 -> must force transition to new_topic
    state["follow_up_count"] = 2
    assert decide_next_action(state) == "new_topic"

    state["follow_up_count"] = 3
    assert decide_next_action(state) == "new_topic"


def test_full_interview_reaches_feedback():
    """Simulates a full interview end-to-end until completion and asserts feedback structure."""
    mock_question = {"question": "Describe vector similarity search.", "type": "conceptual"}
    mock_eval = {
        "correctness": 8.0,
        "technical_depth": 8.0,
        "reasoning": 8.0,
        "practicality": 8.0,
        "communication": 8.0,
        "overall_score": 8.0,
        "confidence": 0.9,
        "missing_concepts": [],
        "follow_up_needed": False,
        "evaluation_summary": "Solid response.",
    }
    mock_feedback = {
        "summary": "Candidate demonstrated strong understanding of AI concepts across 4 modules.",
        "strengths": ["Clear explanation of dense vectors", "Understands prompt engineering"],
        "gaps": ["Needs deeper knowledge of Kubernetes scaling"],
        "next": ["Review production deployment patterns and container orchestration"],
    }

    def mock_gemini_structured(prompt, system_instruction=None, **kwargs):
        sys_str = (system_instruction or "").lower()
        prompt_str = (prompt or "").lower()
        if "feedback" in sys_str or "feedback" in prompt_str:
            return mock_feedback
        if "evaluat" in sys_str or "evaluat" in prompt_str:
            return mock_eval
        return mock_question

    session_id = "test-session-full-feedback"

    with patch("app.llm.gemini.generate_structured", side_effect=mock_gemini_structured):
        # 1. Start Session
        start_payload = {
            "sessionId": session_id,
            "candidate": {
                "member": {
                    "id": "CAND-001",
                    "name": "Sarah Johnson",
                    "jobRole": "AI Engineer",
                    "yearsExperience": 4,
                },
                "missions": [],
                "signals": {"commitDays": 10, "missionsCompleted": 5, "missionsFirstTry": 4},
            },
        }
        res, code = handle_turn(start_payload)
        assert code == 200
        assert res["done"] is False
        assert "reply" in res

        # 2. Loop continuation turns until done (max 15 turns for safety)
        turn_count = 0
        final_res = res
        while not final_res.get("done") and turn_count < 15:
            turn_count += 1
            cont_payload = {
                "sessionId": session_id,
                "message": f"Response {turn_count}: I implemented dense vector search using FAISS and cosine similarity.",
            }
            final_res, code = handle_turn(cont_payload)
            assert code == 200

        # Assert interview finished successfully
        assert final_res["done"] is True
        assert "feedback" in final_res
        fb = final_res["feedback"]
        assert isinstance(fb["summary"], str) and len(fb["summary"]) > 0
        assert isinstance(fb["strengths"], list) and len(fb["strengths"]) > 0
        assert isinstance(fb["gaps"], list) and len(fb["gaps"]) > 0
        assert isinstance(fb["next"], list) and len(fb["next"]) > 0

        # Idempotency check: sending another turn for a completed session returns stored feedback
        idempotent_payload = {
            "sessionId": session_id,
            "message": "Hello again after completion",
        }
        idem_res, idem_code = handle_turn(idempotent_payload)
        assert idem_code == 200
        assert idem_res["done"] is True
        assert "feedback" in idem_res
