import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import candidate_service

client = TestClient(app)

mock_closing_feedback = {
    "closing_message": "Thank you for your time today, Alex! You demonstrated strong technical depth in FastAPI and RAG architecture. That completes our interview session.",
    "summary": "Alex demonstrated exceptional knowledge of backend engineering and LLM application design, specifically highlighting async endpoints and vector store indexing.",
    "strengths": ["Correctly explained chunk overlap in RAG pipelines.", "Demonstrated clear understanding of FastAPI background tasks."],
    "gaps": ["Did not mention HNSW indexing trade-offs."],
    "next": ["Practice implementing FAISS with IVF indexing."]
}

mock_question = {
    "question": "What is chunk overlap in RAG pipelines?",
    "type": "conceptual"
}

mock_eval = {
    "correctness": 9.0,
    "technical_depth": 8.5,
    "reasoning": 8.5,
    "practicality": 8.5,
    "communication": 9.0,
    "overall_score": 8.7,
    "confidence": 0.9,
    "missing_concepts": [],
    "follow_up_needed": False,
    "evaluation_summary": "Great answer on chunk overlap."
}


def mock_gemini_flow(prompt, system_instruction=None, **kwargs):
    p_str = (prompt or "").lower()
    if "final candidate-facing technical interview feedback" in p_str or "closing_message" in p_str or "feedback" in p_str:
        return mock_closing_feedback
    if "evaluation context:" in p_str or "candidate response to evaluate" in p_str:
        return mock_eval
    return mock_question


def test_interview_completion_returns_closing_message():
    session_id = f"test-closing-{uuid.uuid4().hex[:8]}"
    candidate = candidate_service.get_candidate("CAND-001") or {
        "id": "CAND-001",
        "member": {"name": "Alex", "track": "AI Engineering"}
    }

    with patch("app.llm.gemini.generate_structured", side_effect=mock_gemini_flow):
        # 1. Start interview turn
        start_res = client.post("/api/interview", json={"sessionId": session_id, "candidate": candidate})
        assert start_res.status_code == 200

        # 2. Directly call generate_feedback node
        from app.agent.nodes import generate_feedback
        from app.database import repository

        # Prepare a state ready for feedback generation
        state = {
            "session_id": session_id,
            "candidate": candidate,
            "profile": candidate.get("member", {}),
            "covered_days": [1, 2, 3],
            "strengths": ["FastAPI"],
            "weaknesses": ["Vectors"],
            "question_count": 5,
        }

        feedback_node_output = generate_feedback(state)

        assert feedback_node_output["done"] is True
        assert feedback_node_output["reply"] == mock_closing_feedback["closing_message"]
        assert feedback_node_output["feedback"]["closing_message"] == mock_closing_feedback["closing_message"]
        assert "Alex" in feedback_node_output["reply"]

        # 3. Verify turn endpoint when done: true returned from graph
        with patch("app.agent.graph.continue_graph.invoke") as mock_graph:
            mock_graph.return_value = {
                "session_id": session_id,
                "reply": mock_closing_feedback["closing_message"],
                "done": True,
                "feedback": mock_closing_feedback,
            }
            turn_res = client.post("/api/interview", json={"sessionId": session_id, "message": "Thank you."})
            assert turn_res.status_code == 200
            data = turn_res.json()
            assert data["done"] is True
            assert data["reply"] == mock_closing_feedback["closing_message"]
            assert data["feedback"]["closing_message"] == mock_closing_feedback["closing_message"]
