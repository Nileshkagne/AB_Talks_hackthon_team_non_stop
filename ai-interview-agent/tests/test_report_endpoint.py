"""Tests for GET /api/interview/{sessionId}/report endpoint."""

import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.agent.nodes import evaluate_answer

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

MOCK_DUPLICATE_MESSAGES = [
    {
        "role": "interviewer",
        "content": "Explain async endpoints in FastAPI.",
        "question_number": 1,
        "topic": "FastAPI",
        "curriculum_day": 3,
    },
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

        cand_turn = [t for t in data["transcript"] if t["role"] == "candidate"][0]
        assert "evaluation" in cand_turn
        assert cand_turn["evaluation"]["overall_score"] == 8.5
        assert cand_turn["evaluation"]["correctness"] == 9.0
        assert "missing_concepts" not in cand_turn["evaluation"]

        assert "feedback" in data
        fb = data["feedback"]
        assert fb["overall_percentage"] == 85
        assert fb["fluency_score"] == 88
        assert "category_breakdown" in fb


def test_get_report_deduplicates_duplicate_interviewer_messages():
    """Verify GET /api/interview/{sessionId}/report deduplicates interviewer messages with same question_number."""
    session_id = "test-session-completed-123"

    with patch("app.database.repository.get_session", return_value=MOCK_COMPLETED_SESSION), \
         patch("app.database.repository.get_messages", return_value=MOCK_DUPLICATE_MESSAGES), \
         patch("app.database.repository.get_evaluations", return_value=MOCK_EVALUATIONS), \
         patch("app.database.repository.get_feedback", return_value=MOCK_FEEDBACK):

        res = client.get(f"/api/interview/{session_id}/report")
        assert res.status_code == 200
        data = res.json()

        # Should only have 1 interviewer message and 1 candidate message (total 2)
        interviewer_messages = [t for t in data["transcript"] if t["role"] == "interviewer"]
        assert len(interviewer_messages) == 1
        assert len(data["transcript"]) == 2


def test_evaluate_answer_node_passes_varying_subscores_to_repository():
    """Verify evaluate_answer node in nodes.py passes real varying category subscores to repository.add_evaluation."""
    state = {
        "session_id": "test-eval-subscores-session",
        "question_count": 1,
        "last_question": "Explain RAG index chunking.",
        "last_answer": "I use 512-token chunks with 10% overlap and bge-large embeddings.",
        "current_day": 7,
        "current_topic": "Embeddings & RAG",
        "profile": {"role": "AI Engineer", "experience": 3},
    }

    mock_service_eval = {
        "correctness": 8.5,
        "technical_depth": 9.0,
        "reasoning": 7.5,
        "practicality": 8.0,
        "communication": 8.5,
        "overall_score": 8.35,
        "confidence": 0.9,
        "missing_concepts": [],
        "follow_up_needed": False,
        "evaluation_summary": "Strong technical response on chunking.",
        "model_used": "gemini-3.6-flash",
    }

    with patch("app.services.evaluation_service.evaluate_answer", return_value=mock_service_eval), \
         patch("app.database.repository.add_evaluation") as mock_add_eval:

        res = evaluate_answer(state)
        assert res["last_evaluation"] == mock_service_eval

        # Verify add_evaluation was called with the REAL varying subscores (NOT defaulting to 6.0)
        assert mock_add_eval.called
        kwargs = mock_add_eval.call_args.kwargs
        assert kwargs["correctness"] == 8.5
        assert kwargs["technical_depth"] == 9.0
        assert kwargs["reasoning"] == 7.5
        assert kwargs["practicality"] == 8.0
        assert kwargs["communication"] == 8.5
        assert kwargs["overall_score"] == 8.35


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
