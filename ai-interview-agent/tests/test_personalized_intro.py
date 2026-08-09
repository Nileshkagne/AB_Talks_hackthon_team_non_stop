"""
Tests for personalized interview intro generation.

Verifies:
1. Two different candidates produce different opening messages referencing their
   specific name and role.
2. On Gemini failure, the static fallback still contains the candidate's real
   name and role (not a generic greeting).
"""

from unittest.mock import MagicMock, patch
import pytest

from app.agent.nodes import generate_question, _build_static_intro
from app.llm.gemini import GeminiError


# ── Fixtures ──────────────────────────────────────────────────────────

CANDIDATE_A = {
    "member": {
        "id": "CAND-A",
        "name": "Priya Sharma",
        "jobRole": "ML Engineer",
        "yearsExperience": 5,
    },
    "missions": [],
    "signals": {},
}

CANDIDATE_B = {
    "member": {
        "id": "CAND-B",
        "name": "Alex Rivera",
        "jobRole": "Backend Developer",
        "yearsExperience": 2,
    },
    "missions": [],
    "signals": {},
}

PROFILE_A = {
    "role": "ML Engineer",
    "experience": 5,
    "strength_topics": ["RAG Pipelines", "Transformer Fine-Tuning"],
    "weak_topics": [],
    "skipped_topics": [],
    "difficulty": "advanced",
}

PROFILE_B = {
    "role": "Backend Developer",
    "experience": 2,
    "strength_topics": [],
    "weak_topics": ["Vector Databases"],
    "skipped_topics": ["LLM Agents"],
    "difficulty": "foundation",
}


def _make_intro_state(candidate, profile, topic="Environment & Tooling"):
    """Build a state dict simulating the first turn (question_count == 0)."""
    return {
        "session_id": "test-session",
        "question_count": 0,
        "current_day": 1,
        "current_topic": topic,
        "difficulty": profile["difficulty"],
        "follow_up_count": 0,
        "profile": profile,
        "candidate": candidate,
        "last_answer": None,
        "last_evaluation": None,
    }


# ── Test 1: Gemini returns intro — two candidates get different openings ──

@patch("app.agent.nodes.repository")
@patch("app.agent.nodes.curriculum_service")
@patch("app.agent.nodes.gemini")
def test_intro_different_candidates_produce_different_messages(
    mock_gemini, mock_curriculum, mock_repo
):
    """
    Two different candidate fixtures (different name/role/profile) should
    produce two different opening messages that each reference that specific
    candidate's real name and role.
    """
    mock_curriculum.get_day.return_value = {
        "objectives": ["Understand dev env"],
        "tools": ["VS Code", "Docker"],
    }
    mock_repo.get_recent_messages.return_value = []

    # Gemini response for Candidate A
    mock_gemini.generate_structured.return_value = {
        "question": "How would you set up a containerized ML training pipeline?",
        "type": "why_how",
        "intro": "Hi Priya! With your 5 years as an ML Engineer and strong performance on RAG Pipelines, I'd love to dive into some advanced topics today.",
        "_model_used": "gemini-test",
    }

    result_a = generate_question(_make_intro_state(CANDIDATE_A, PROFILE_A))

    # Gemini response for Candidate B
    mock_gemini.generate_structured.return_value = {
        "question": "What tools do you typically use for local development?",
        "type": "why_how",
        "intro": "Hey Alex! As a Backend Developer with 2 years of experience, let's explore some foundational concepts together.",
        "_model_used": "gemini-test",
    }

    result_b = generate_question(_make_intro_state(CANDIDATE_B, PROFILE_B))

    # Both replies should be non-empty and different
    assert result_a["reply"] != result_b["reply"]

    # Candidate A's reply references their name and role
    assert "Priya" in result_a["reply"]
    assert "ML Engineer" in result_a["reply"] or "ML" in result_a["reply"]

    # Candidate B's reply references their name and role
    assert "Alex" in result_b["reply"]
    assert "Backend Developer" in result_b["reply"] or "Backend" in result_b["reply"]

    # The structured question field should remain clean (no intro text in it)
    assert "Hi Priya" not in result_a["last_question"]
    assert "Hey Alex" not in result_b["last_question"]


# ── Test 2: Gemini failure → static personalized fallback ──

@patch("app.agent.nodes.repository")
@patch("app.agent.nodes.curriculum_service")
@patch("app.agent.nodes.gemini")
def test_intro_gemini_failure_uses_personalized_static_fallback(
    mock_gemini, mock_curriculum, mock_repo
):
    """
    When Gemini fails for the intro call, the fallback message should still
    contain the candidate's actual name and role — not a fully generic greeting.
    """
    mock_curriculum.get_day.return_value = {
        "objectives": ["Understand dev env"],
        "tools": ["VS Code"],
    }
    mock_repo.get_recent_messages.return_value = []

    # Gemini raises an error
    mock_gemini.generate_structured.side_effect = Exception("API quota exhausted")
    mock_gemini.GeminiError = GeminiError

    result_a = generate_question(_make_intro_state(CANDIDATE_A, PROFILE_A))

    # Should NOT raise — should return a static fallback
    assert result_a["reply"] is not None
    assert "Priya" in result_a["reply"]
    assert "ML Engineer" in result_a["reply"]
    assert result_a["model_used"] is None  # No model was used
    assert result_a["done"] is False

    # Run for Candidate B too
    mock_gemini.generate_structured.side_effect = Exception("Connection reset")

    result_b = generate_question(_make_intro_state(CANDIDATE_B, PROFILE_B))

    assert "Alex" in result_b["reply"]
    assert "Backend Developer" in result_b["reply"]

    # The two fallback replies should be different
    assert result_a["reply"] != result_b["reply"]


# ── Test 3: Gemini returns question but no intro field → static intro + question ──

@patch("app.agent.nodes.repository")
@patch("app.agent.nodes.curriculum_service")
@patch("app.agent.nodes.gemini")
def test_intro_gemini_no_intro_field_uses_static_intro(
    mock_gemini, mock_curriculum, mock_repo
):
    """
    If Gemini returns a valid question but omits the 'intro' field,
    the system should prepend a static personalized intro.
    """
    mock_curriculum.get_day.return_value = {
        "objectives": ["Understand dev env"],
        "tools": ["Docker"],
    }
    mock_repo.get_recent_messages.return_value = []

    mock_gemini.generate_structured.return_value = {
        "question": "Explain the purpose of Docker in ML workflows.",
        "type": "why_how",
        # No "intro" field
        "_model_used": "gemini-test",
    }

    result = generate_question(_make_intro_state(CANDIDATE_A, PROFILE_A))

    # Reply should contain both the static intro (with name) and the question
    assert "Priya" in result["reply"]
    assert "Docker" in result["reply"]
    # The question field is just the question
    assert result["last_question"] == "Explain the purpose of Docker in ML workflows."


# ── Test 4: _build_static_intro unit test ──

def test_build_static_intro_uses_real_candidate_data():
    """_build_static_intro should produce different text for different candidates."""
    intro_a = _build_static_intro(CANDIDATE_A, PROFILE_A, "RAG Pipelines")
    intro_b = _build_static_intro(CANDIDATE_B, PROFILE_B, "Dev Environment")

    assert "Priya" in intro_a
    assert "ML Engineer" in intro_a
    assert "5 years" in intro_a
    assert "RAG Pipelines" in intro_a  # strength_topics[0] or c_topic

    assert "Alex" in intro_b
    assert "Backend Developer" in intro_b
    assert "2 years" in intro_b

    assert intro_a != intro_b
