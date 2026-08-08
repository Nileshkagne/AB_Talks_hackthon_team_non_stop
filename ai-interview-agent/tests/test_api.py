import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
