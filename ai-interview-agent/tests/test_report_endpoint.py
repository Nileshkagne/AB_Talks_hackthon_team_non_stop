"""Tests for GET /api/interview/{sessionId}/report endpoint."""

import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_COMPLETED_SESSION = {
    "session_id": "test-session-completed-123",
    "status": "completed",
    "candidate_id": "CAND-001",
    "candidate_name": "Alex Smith",
    "candidate_role": "AI Engineer",
}

MOCK_ACTIVE_SESSION = {
    "session_id": "test-session-active-456",
    "status": "active",
    "candidate_id": "CAND-002",
    "candidate_name": "Jordan Lee",
    "candidate_role": "ML Engineer",
}

MOCK_MESSAGES = [
    {
        "role": "interviewer",
        "content": "Explain async endpoints in FastAPI.",
        "question_number": 1,
        "topic": "FastAPI",
        "curriculum_day": 3,
    },
    {
        "role": "candidate",
        "content": "FastAPI uses async def for non-blocking I/O.",
        "question_number": 1,
    },
]

MOCK_EVALUATIONS = [
    {
        "question_number": 1,
        "topic": "FastAPI",
        "correctness": 9.0,
        "technical_depth": 8.0,
        "reasoning": 8.5,
        "practicality": 8.0,
        "communication": 9.0,
        "overall_score": 8.5,
        "missing_concepts": ["uvicorn concurrency limits"],
        "evaluation_summary": "Great explanation of async endpoints.",
    }
]

MOCK_FEEDBACK = {
    "summary": "Alex demonstrated strong backend knowledge.",
    "strengths": ["FastAPI async def knowledge"],
    "gaps": ["Concurrency tuning"],
    "next": ["Practice async benchmarks"],
    "closing_message": "Thanks Alex for your time!",
    "overall_percentage": 85,
    "category_breakdown": {
        "correctness": 90,
        "technical_depth": 80,
        "reasoning": 85,
        "practicality": 80,
        "communication": 90,
    },
    "fluency_score": 88,
    "fluency_notes": "Well structured responses with good clarity.",
}


def test_get_report_completed_session_success():
    """Verify GET /api/interview/{sessionId}/report returns full report for completed session."""
    session_id = "test-session-completed-123"

    def mock_get_session(s_id):
        if s_id == session_id:
            return MOCK_COMPLETED_SESSION
        return None

    with patch("app.database.repository.get_session", side_effect=mock_get_session), \
         patch("app.database.repository.get_messages", return_value=MOCK_MESSAGES), \
         patch("app.database.repository.get_evaluations", return_value=MOCK_EVALUATIONS), \
         patch("app.database.repository.get_feedback", return_value=MOCK_FEEDBACK):

        res = client.get(f"/api/interview/{session_id}/report")
        assert res.status_code == 200
        data = res.json()

        assert data["session_id"] == session_id
        assert "candidate" in data
        assert data["candidate"]["name"] == "Alex Smith"
        assert data["candidate"]["role"] == "AI Engineer"

        assert "transcript" in data
        assert isinstance(data["transcript"], list)
        assert len(data["transcript"]) == 2

        # Candidate turn should have evaluation attached
        cand_turn = [t for t in data["transcript"] if t["role"] == "candidate"][0]
        assert "evaluation" in cand_turn
        assert cand_turn["evaluation"]["overall_score"] == 8.5
        assert cand_turn["evaluation"]["correctness"] == 9.0
        # Check internal raw fields are omitted
        assert "missing_concepts" not in cand_turn["evaluation"]

        # Check feedback fields
        assert "feedback" in data
        fb = data["feedback"]
        assert fb["overall_percentage"] == 85
        assert fb["fluency_score"] == 88
        assert "category_breakdown" in fb


def test_get_report_incomplete_session_returns_404():
    """Verify GET /api/interview/{sessionId}/report returns 404 for an active/incomplete session."""
    session_id = "test-session-active-456"

    def mock_get_session(s_id):
        if s_id == session_id:
            return MOCK_ACTIVE_SESSION
        return None

    with patch("app.database.repository.get_session", side_effect=mock_get_session):
        res = client.get(f"/api/interview/{session_id}/report")
        assert res.status_code == 404
        data = res.json()
        assert data["error"] == "session_not_completed"


def test_get_report_unknown_session_returns_404():
    """Verify GET /api/interview/{sessionId}/report returns 404 for non-existent session."""
    with patch("app.database.repository.get_session", return_value=None):
        res = client.get("/api/interview/non-existent-session-id/report")
        assert res.status_code == 404
        data = res.json()
        assert data["error"] == "session_not_found"
