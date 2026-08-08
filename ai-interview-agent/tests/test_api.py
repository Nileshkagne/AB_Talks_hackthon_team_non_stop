import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_start_turn_returns_valid_reply_and_done_false():
    """Start turn (candidate present) returns valid {reply, done:false}."""
    session_id = f"test-api-start-{uuid.uuid4()}"
    mock_question = {"question": "What is dense vector retrieval?", "type": "conceptual"}

    with patch("app.llm.gemini.generate_structured", return_value=mock_question):
        payload = {
            "sessionId": session_id,
            "candidate": {
                "member": {
                    "id": "CAND-001",
                    "name": "Sarah Johnson",
                    "jobRole": "Senior Data Engineer",
                    "yearsExperience": 9,
                    "education": "MS Computer Science",
                },
                "missions": [],
                "signals": {"commitDays": 28, "missionsCompleted": 30, "missionsFirstTry": 20},
            },
        }
        response = client.post("/api/interview", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["done"] is False
        assert "reply" in data
        assert len(data["reply"]) > 0


def test_continuation_turn_with_valid_session():
    """Continuation turn with valid active session works properly."""
    session_id = f"test-api-cont-{uuid.uuid4()}"
    mock_question = {"question": "Describe chunk size trade-offs.", "type": "trade_off"}
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
        "evaluation_summary": "Solid explanation.",
    }

    def mock_gemini(prompt, system_instruction=None, **kwargs):
        if "evaluat" in (system_instruction or "").lower():
            return mock_eval
        return mock_question

    with patch("app.llm.gemini.generate_structured", side_effect=mock_gemini):
        # 1. Start Session
        start_payload = {
            "sessionId": session_id,
            "candidate": {
                "member": {"id": "CAND-001", "name": "Sarah", "jobRole": "Engineer", "yearsExperience": 5},
                "missions": [],
                "signals": {"commitDays": 10, "missionsCompleted": 5, "missionsFirstTry": 4},
            },
        }
        start_res = client.post("/api/interview", json=start_payload)
        assert start_res.status_code == 200

        # 2. Continuation turn
        cont_payload = {
            "sessionId": session_id,
            "message": "Chunking text improves context retrieval accuracy.",
        }
        cont_res = client.post("/api/interview", json=cont_payload)
        assert cont_res.status_code == 200
        data = cont_res.json()
        assert "reply" in data
        assert isinstance(data["done"], bool)


def test_continuation_unknown_session_returns_404():
    unknown_id = f"unknown-session-{uuid.uuid4()}"
    response = client.post(
        "/api/interview",
        json={"sessionId": unknown_id, "message": "Hello, I am ready for the interview."},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "session_not_found"
    assert "No active interview found" in data["message"]


def test_malformed_body_returns_422():
    # Missing candidate and message
    res_malformed = client.post(
        "/api/interview",
        json={"sessionId": "test-session-123"},
    )
    assert res_malformed.status_code == 422
    assert res_malformed.json()["error"] == "bad_request"


def test_message_exceeds_4000_chars_returns_422():
    long_message = "A" * 4001
    response = client.post(
        "/api/interview",
        json={"sessionId": "test-session-valid", "message": long_message},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "message_too_long"
    assert "4000" in data["message"]


def test_invalid_session_id_format_returns_422():
    # Empty string sessionId
    res_empty = client.post(
        "/api/interview",
        json={"sessionId": "", "message": "Hello"},
    )
    assert res_empty.status_code == 422
    assert res_empty.json()["error"] == "invalid_session_id"

    # Excessively long sessionId (> 128 chars)
    long_session_id = "X" * 129
    res_long = client.post(
        "/api/interview",
        json={"sessionId": long_session_id, "message": "Hello"},
    )
    assert res_long.status_code == 422
    assert res_long.json()["error"] == "invalid_session_id"
