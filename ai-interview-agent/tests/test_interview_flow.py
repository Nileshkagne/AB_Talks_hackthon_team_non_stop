import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import candidate_service
from app.database import repository

client = TestClient(app)

mock_question = {"question": "Describe environment setup and virtual environment tools.", "type": "conceptual"}
mock_eval = {
    "correctness": 8.5,
    "technical_depth": 8.0,
    "reasoning": 8.0,
    "practicality": 8.0,
    "communication": 8.0,
    "overall_score": 8.2,
    "confidence": 0.9,
    "missing_concepts": [],
    "follow_up_needed": False,
    "evaluation_summary": "Good setup explanation.",
}


def mock_gemini_flow(prompt, system_instruction=None, **kwargs):
    p_str = (prompt or "").lower()
    if "evaluation context:" in p_str or "candidate response to evaluate" in p_str:
        return mock_eval
    return mock_question


def test_sequential_interview_turns():
    session_id = f"test-flow-{uuid.uuid4().hex[:8]}"
    candidate = candidate_service.get_candidate("CAND-001")
    assert candidate is not None

    with patch("app.llm.gemini.generate_structured", side_effect=mock_gemini_flow):
        # 1. Start turn (POST /api/interview with candidate)
        start_payload = {
            "sessionId": session_id,
            "candidate": candidate
        }
        res1 = client.post("/api/interview", json=start_payload)
        assert res1.status_code == 200
        data1 = res1.json()
        assert "reply" in data1
        assert data1["done"] is False

        # Check question_count after turn 1
        session_after_turn1 = repository.get_session(session_id)
        assert session_after_turn1 is not None
        count1 = session_after_turn1["question_count"]
        assert count1 == 1

        # 2. Continuation turn (POST /api/interview with message)
        turn_payload = {
            "sessionId": session_id,
            "message": "I installed VS Code and created a virtual environment."
        }
        res2 = client.post("/api/interview", json=turn_payload)
        assert res2.status_code == 200
        data2 = res2.json()
        assert "reply" in data2
        assert data2["done"] is False

        # Check question_count after turn 2
        session_after_turn2 = repository.get_session(session_id)
        assert session_after_turn2 is not None
        count2 = session_after_turn2["question_count"]
        assert count2 == 2

    # 3. Test unknown session returns HTTP 404
    unknown_payload = {
        "sessionId": "unknown-nonexistent-session-id",
        "message": "Hello?"
    }
    res3 = client.post("/api/interview", json=unknown_payload)
    assert res3.status_code == 404
    assert res3.json()["error"] == "session_not_found"
