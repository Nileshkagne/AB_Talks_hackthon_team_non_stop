import os
import socket
import uuid
from urllib.parse import urlparse
import pytest
from dotenv import load_dotenv

load_dotenv()


def is_supabase_ready() -> bool:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return False
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return False
        socket.gethostbyname(hostname)
        from app.database import connection
        client = connection.get_client()
        client.table("interview_sessions").select("session_id").limit(1).execute()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not is_supabase_ready(),
    reason="SUPABASE_URL unconfigured or schema.sql not yet executed in Supabase SQL editor",
)

from app.database import repository


def test_repository_lifecycle():
    test_session_id = f"test-sess-{uuid.uuid4().hex[:8]}"
    candidate_id = "CAND-001"

    # 1. Create session
    session = repository.create_session(
        test_session_id, candidate_id, difficulty="advanced"
    )
    assert session is not None
    assert session["session_id"] == test_session_id
    assert session["candidate_id"] == candidate_id
    assert session["difficulty"] == "advanced"
    assert session["status"] == "active"

    # 2. Get session
    retrieved = repository.get_session(test_session_id)
    assert retrieved is not None
    assert retrieved["session_id"] == test_session_id

    # 3. Update session
    updated = repository.update_session(
        test_session_id,
        question_count=1,
        current_day=7,
        current_topic="Embeddings Explained",
        covered_days=[7],
    )
    assert updated["question_count"] == 1
    assert updated["current_day"] == 7
    assert updated["current_topic"] == "Embeddings Explained"
    assert updated["covered_days"] == [7]

    # 4. Add message
    msg = repository.add_message(
        session_id=test_session_id,
        role="interviewer",
        content="What is an embedding vector?",
        question_number=1,
        curriculum_day=7,
        topic="Embeddings Explained",
        question_type="conceptual",
    )
    assert msg["id"] is not None
    assert msg["content"] == "What is an embedding vector?"

    # 5. Read recent messages
    recent_msgs = repository.get_recent_messages(test_session_id, limit=6)
    assert len(recent_msgs) >= 1
    assert recent_msgs[-1]["content"] == "What is an embedding vector?"

    # 6. Add evaluation
    eval_rec = repository.add_evaluation(
        session_id=test_session_id,
        question_number=1,
        question="What is an embedding vector?",
        answer="It is a dense numerical vector representing semantic meaning.",
        curriculum_day=7,
        topic="Embeddings Explained",
        correctness=9.0,
        technical_depth=8.5,
        overall_score=8.75,
        confidence=0.95,
        missing_concepts=["dimension trade-offs"],
        follow_up_needed=True,
        evaluation_summary="Strong baseline understanding.",
    )
    assert eval_rec["id"] is not None
    assert float(eval_rec["overall_score"]) == 8.75

    # 7. Save feedback
    feedback = repository.save_feedback(
        session_id=test_session_id,
        summary="Great performance on embeddings.",
        strengths=["Dense representation", "Semantic search"],
        gaps=["Dimensionality reduction"],
        next_steps=["Review Day 8 vector DBs"],
        overall_score=8.75,
    )
    assert feedback["session_id"] == test_session_id
    assert feedback["summary"] == "Great performance on embeddings."
