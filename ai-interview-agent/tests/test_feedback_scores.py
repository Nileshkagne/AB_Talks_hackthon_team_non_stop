"""Tests for overall_percentage, category_breakdown, and fluency analysis in generate_feedback."""

import uuid
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import candidate_service

client = TestClient(app)


# ── Mock per-turn evaluations (simulating DB rows from answer_evaluations) ──
MOCK_EVALUATIONS = [
    {
        "question_number": 1,
        "topic": "FastAPI",
        "overall_score": 8.0,
        "correctness": 9.0,
        "technical_depth": 7.0,
        "reasoning": 8.0,
        "practicality": 7.0,
        "communication": 9.0,
        "missing_concepts": [],
        "evaluation_summary": "Strong understanding of async endpoints.",
    },
    {
        "question_number": 2,
        "topic": "RAG Pipelines",
        "overall_score": 6.0,
        "correctness": 7.0,
        "technical_depth": 5.0,
        "reasoning": 6.0,
        "practicality": 5.0,
        "communication": 7.0,
        "missing_concepts": ["HNSW"],
        "evaluation_summary": "Partial understanding of vector search.",
    },
    {
        "question_number": 3,
        "topic": "LangGraph",
        "overall_score": 9.0,
        "correctness": 9.0,
        "technical_depth": 9.0,
        "reasoning": 8.0,
        "practicality": 9.0,
        "communication": 8.0,
        "missing_concepts": [],
        "evaluation_summary": "Excellent grasp of agent orchestration.",
    },
]

MOCK_MESSAGES = [
    {"role": "interviewer", "content": "Explain async endpoints in FastAPI.", "question_number": 1},
    {"role": "candidate", "content": "FastAPI uses async def for non-blocking I/O endpoints with uvicorn."},
    {"role": "interviewer", "content": "How does RAG work with vector stores?", "question_number": 2},
    {"role": "candidate", "content": "RAG retrieves relevant chunks using cosine similarity from a vector database."},
    {"role": "interviewer", "content": "Describe agent orchestration with LangGraph.", "question_number": 3},
    {"role": "candidate", "content": "LangGraph uses a state machine approach with nodes and edges for multi-agent workflows."},
]


# Expected overall_percentage: mean([8.0, 6.0, 9.0]) * 10 = 76.67 -> rounded to 77
# Expected category breakdown:
#   correctness:     mean([9, 7, 9]) * 10 = 83
#   technical_depth: mean([7, 5, 9]) * 10 = 70
#   reasoning:       mean([8, 6, 8]) * 10 = 73
#   practicality:    mean([7, 5, 9]) * 10 = 70
#   communication:   mean([9, 7, 8]) * 10 = 80

EXPECTED_OVERALL_PCT = 77
EXPECTED_BREAKDOWN = {
    "correctness": 83,
    "technical_depth": 70,
    "reasoning": 73,
    "practicality": 70,
    "communication": 80,
}

mock_feedback_response = {
    "closing_message": "Thank you Alex for your thoughtful responses today! That wraps up our session.",
    "summary": "Alex showed solid understanding across FastAPI, RAG, and LangGraph topics.",
    "strengths": ["Correctly explained async FastAPI endpoints with uvicorn."],
    "gaps": ["Did not mention HNSW for production vector search."],
    "next": ["Implement FAISS with IVF for hands-on vector indexing experience."],
    "fluency_score": 82,
    "fluency_notes": "Clear and well-structured responses with strong technical vocabulary; a few run-on sentences under time pressure.",
}


def mock_gemini_for_feedback(prompt, system_instruction=None, **kwargs):
    return mock_feedback_response


def test_overall_percentage_calculation():
    """Verify overall_percentage is correctly averaged from per-turn overall_score values."""
    session_id = f"test-pct-{uuid.uuid4().hex[:8]}"
    candidate = {
        "id": "CAND-PCT-001",
        "member": {"name": "Alex", "track": "AI Engineering", "jobRole": "AI Engineer"},
    }

    with patch("app.llm.gemini.generate_structured", side_effect=mock_gemini_for_feedback), \
         patch("app.database.repository.get_evaluations", return_value=MOCK_EVALUATIONS), \
         patch("app.database.repository.get_messages", return_value=MOCK_MESSAGES):

        from app.agent.nodes import generate_feedback

        state = {
            "session_id": session_id,
            "candidate": candidate,
            "profile": candidate.get("member", {}),
            "covered_days": [1, 2, 3],
            "strengths": ["FastAPI"],
            "weaknesses": ["RAG"],
            "question_count": 3,
        }

        result = generate_feedback(state)
        fb = result["feedback"]

        # overall_percentage should be a number 0-100
        assert "overall_percentage" in fb
        assert isinstance(fb["overall_percentage"], int)
        assert 0 <= fb["overall_percentage"] <= 100
        assert fb["overall_percentage"] == EXPECTED_OVERALL_PCT, (
            f"Expected overall_percentage={EXPECTED_OVERALL_PCT}, got {fb['overall_percentage']}"
        )


def test_category_breakdown_present_and_correct():
    """Verify category_breakdown contains all 5 categories with correct averaged values."""
    session_id = f"test-cat-{uuid.uuid4().hex[:8]}"
    candidate = {
        "id": "CAND-CAT-001",
        "member": {"name": "Alex", "track": "AI Engineering"},
    }

    with patch("app.llm.gemini.generate_structured", side_effect=mock_gemini_for_feedback), \
         patch("app.database.repository.get_evaluations", return_value=MOCK_EVALUATIONS), \
         patch("app.database.repository.get_messages", return_value=MOCK_MESSAGES):

        from app.agent.nodes import generate_feedback

        state = {
            "session_id": session_id,
            "candidate": candidate,
            "profile": candidate.get("member", {}),
            "covered_days": [1, 2, 3],
            "strengths": [],
            "weaknesses": [],
            "question_count": 3,
        }

        result = generate_feedback(state)
        fb = result["feedback"]

        assert "category_breakdown" in fb
        breakdown = fb["category_breakdown"]
        assert isinstance(breakdown, dict)

        expected_keys = {"correctness", "technical_depth", "reasoning", "practicality", "communication"}
        assert set(breakdown.keys()) == expected_keys, (
            f"Expected keys {expected_keys}, got {set(breakdown.keys())}"
        )

        for cat, expected_val in EXPECTED_BREAKDOWN.items():
            assert breakdown[cat] == expected_val, (
                f"Expected {cat}={expected_val}, got {breakdown[cat]}"
            )


def test_fluency_score_and_notes_present_and_separate():
    """Verify fluency_score/fluency_notes are present in feedback and separate from overall_percentage."""
    session_id = f"test-flu-{uuid.uuid4().hex[:8]}"
    candidate = {
        "id": "CAND-FLU-001",
        "member": {"name": "Alex", "track": "AI Engineering"},
    }

    with patch("app.llm.gemini.generate_structured", side_effect=mock_gemini_for_feedback), \
         patch("app.database.repository.get_evaluations", return_value=MOCK_EVALUATIONS), \
         patch("app.database.repository.get_messages", return_value=MOCK_MESSAGES):

        from app.agent.nodes import generate_feedback

        state = {
            "session_id": session_id,
            "candidate": candidate,
            "profile": candidate.get("member", {}),
            "covered_days": [1, 2, 3],
            "strengths": [],
            "weaknesses": [],
            "question_count": 3,
        }

        result = generate_feedback(state)
        fb = result["feedback"]

        # fluency_score must be present, integer, 0-100
        assert "fluency_score" in fb
        assert isinstance(fb["fluency_score"], int)
        assert 0 <= fb["fluency_score"] <= 100

        # fluency_notes must be present and a string
        assert "fluency_notes" in fb
        assert isinstance(fb["fluency_notes"], str)
        assert len(fb["fluency_notes"]) > 0

        # fluency_score must be SEPARATE from overall_percentage (different values possible)
        assert "overall_percentage" in fb
        # They are independent metrics — fluency comes from Gemini, overall_percentage is computed
        assert fb["fluency_score"] == 82  # from mock
        assert fb["overall_percentage"] == EXPECTED_OVERALL_PCT  # computed from eval scores


def test_required_schema_fields_unchanged():
    """Verify the original required fields (summary, strengths, gaps, next) are still present."""
    session_id = f"test-schema-{uuid.uuid4().hex[:8]}"
    candidate = {
        "id": "CAND-SCH-001",
        "member": {"name": "Alex", "track": "AI Engineering"},
    }

    with patch("app.llm.gemini.generate_structured", side_effect=mock_gemini_for_feedback), \
         patch("app.database.repository.get_evaluations", return_value=MOCK_EVALUATIONS), \
         patch("app.database.repository.get_messages", return_value=MOCK_MESSAGES):

        from app.agent.nodes import generate_feedback

        state = {
            "session_id": session_id,
            "candidate": candidate,
            "profile": candidate.get("member", {}),
            "covered_days": [1, 2, 3],
            "strengths": [],
            "weaknesses": [],
            "question_count": 3,
        }

        result = generate_feedback(state)
        fb = result["feedback"]

        # Original required fields
        assert "summary" in fb and isinstance(fb["summary"], str) and len(fb["summary"]) > 0
        assert "strengths" in fb and isinstance(fb["strengths"], list)
        assert "gaps" in fb and isinstance(fb["gaps"], list)
        assert "next" in fb and isinstance(fb["next"], list)
        assert "closing_message" in fb

        # done and reply still present at top level
        assert result["done"] is True
        assert isinstance(result["reply"], str)
