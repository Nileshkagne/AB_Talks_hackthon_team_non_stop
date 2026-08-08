from typing import Any, Dict, List, Optional
from app.database.connection import get_client


def create_session(
    session_id: str, candidate_id: str, difficulty: str = "intermediate"
) -> Dict[str, Any]:
    """Creates a new interview session record in Supabase."""
    client = get_client()
    data = {
        "session_id": session_id,
        "candidate_id": candidate_id,
        "difficulty": difficulty,
        "status": "active",
        "question_count": 0,
        "follow_up_count": 0,
        "covered_days": [],
        "strengths": [],
        "weaknesses": [],
    }
    response = client.table("interview_sessions").insert(data).execute()
    return response.data[0] if response.data else {}


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an interview session record by session_id."""
    client = get_client()
    response = (
        client.table("interview_sessions")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    return response.data[0] if response.data else None


def update_session(session_id: str, **fields) -> Dict[str, Any]:
    """Updates an existing interview session record."""
    client = get_client()
    response = (
        client.table("interview_sessions")
        .update(fields)
        .eq("session_id", session_id)
        .execute()
    )
    return response.data[0] if response.data else {}


def add_message(
    session_id: str,
    role: str,
    content: str,
    question_number: Optional[int] = None,
    curriculum_day: Optional[int] = None,
    topic: Optional[str] = None,
    question_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Appends a new message to the interview transcript."""
    client = get_client()
    data = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "question_number": question_number,
        "curriculum_day": curriculum_day,
        "topic": topic,
        "question_type": question_type,
    }
    response = client.table("interview_messages").insert(data).execute()
    return response.data[0] if response.data else {}


def add_evaluation(
    session_id: str,
    question_number: int,
    question: str,
    answer: str,
    curriculum_day: Optional[int] = None,
    topic: Optional[str] = None,
    correctness: float = 0.0,
    technical_depth: float = 0.0,
    reasoning: float = 0.0,
    practicality: float = 0.0,
    communication: float = 0.0,
    overall_score: float = 0.0,
    confidence: float = 1.0,
    missing_concepts: Optional[List[str]] = None,
    follow_up_needed: bool = False,
    evaluation_summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Appends an evaluation record for a candidate's answer."""
    client = get_client()
    data = {
        "session_id": session_id,
        "question_number": question_number,
        "question": question,
        "answer": answer,
        "curriculum_day": curriculum_day,
        "topic": topic,
        "correctness": correctness,
        "technical_depth": technical_depth,
        "reasoning": reasoning,
        "practicality": practicality,
        "communication": communication,
        "overall_score": overall_score,
        "confidence": confidence,
        "missing_concepts": missing_concepts if missing_concepts is not None else [],
        "follow_up_needed": follow_up_needed,
        "evaluation_summary": evaluation_summary,
    }
    response = client.table("answer_evaluations").insert(data).execute()
    return response.data[0] if response.data else {}


def save_feedback(
    session_id: str,
    summary: str,
    strengths: List[str],
    gaps: List[str],
    next_steps: List[str],
    overall_score: Optional[float] = None,
) -> Dict[str, Any]:
    """Saves final interview feedback record."""
    client = get_client()
    data = {
        "session_id": session_id,
        "summary": summary,
        "strengths": strengths,
        "gaps": gaps,
        "next_steps": next_steps,
        "overall_score": overall_score,
    }
    response = client.table("interview_feedback").upsert(data).execute()
    return response.data[0] if response.data else {}


def get_recent_messages(session_id: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Retrieves recent transcript messages in chronological order."""
    client = get_client()
    response = (
        client.table("interview_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("id", desc=True)
        .limit(limit)
        .execute()
    )
    messages = response.data or []
    messages.reverse()
    return messages
