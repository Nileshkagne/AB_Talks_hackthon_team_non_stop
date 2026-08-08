import os
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
    return response.data[0] if response.data else data


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an existing interview session by session_id."""
    client = get_client()
    response = (
        client.table("interview_sessions")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    return response.data[0] if response.data else None


def update_session(
    session_id: str,
    question_count: Optional[int] = None,
    follow_up_count: Optional[int] = None,
    current_day: Optional[int] = None,
    current_topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    covered_days: Optional[List[int]] = None,
    strengths: Optional[List[str]] = None,
    weaknesses: Optional[List[str]] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Updates session fields in Supabase."""
    client = get_client()
    data: Dict[str, Any] = {}
    if question_count is not None:
        data["question_count"] = question_count
    if follow_up_count is not None:
        data["follow_up_count"] = follow_up_count
    if current_day is not None:
        data["current_day"] = current_day
    if current_topic is not None:
        data["current_topic"] = current_topic
    if difficulty is not None:
        data["difficulty"] = difficulty
    if covered_days is not None:
        data["covered_days"] = covered_days
    if strengths is not None:
        data["strengths"] = strengths
    if weaknesses is not None:
        data["weaknesses"] = weaknesses
    if status is not None:
        data["status"] = status

    if not data:
        return {}

    response = (
        client.table("interview_sessions")
        .update(data)
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
    """Appends a message (interviewer question or candidate response) to interview_messages."""
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
    curriculum_day: int,
    topic: str,
    correctness: float = 6.0,
    technical_depth: float = 6.0,
    reasoning: float = 6.0,
    practicality: float = 6.0,
    communication: float = 6.0,
    overall_score: float = 6.0,
    confidence: float = 0.9,
    missing_concepts: Optional[List[str]] = None,
    follow_up_needed: bool = False,
    evaluation_summary: str = "",
) -> Dict[str, Any]:
    """Inserts an evaluation record into answer_evaluations."""
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
    try:
        response = client.table("answer_evaluations").insert(data).execute()
        return response.data[0] if response.data else {}
    except Exception:
        return {}


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
    try:
        response = client.table("interview_feedback").upsert(data).execute()
        return response.data[0] if response.data else {}
    except Exception:
        return {}


def get_recent_messages(session_id: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Retrieves recent transcript messages in chronological order."""
    client = get_client()
    if not client:
        return []
    try:
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
    except Exception:
        return []


def get_latest_evaluation(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the most recent evaluation for a session."""
    client = get_client()
    if not client:
        return None
    try:
        response = (
            client.table("answer_evaluations")
            .select("*")
            .eq("session_id", session_id)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            row = response.data[0]
            return {
                "correctness": row.get("correctness", 6.0),
                "technical_depth": row.get("technical_depth", 6.0),
                "reasoning": row.get("reasoning", 6.0),
                "practicality": row.get("practicality", 6.0),
                "communication": row.get("communication", 6.0),
                "overall_score": row.get("overall_score", 6.0),
                "confidence": row.get("confidence", 0.9),
                "missing_concepts": row.get("missing_concepts", []),
                "follow_up_needed": row.get("follow_up_needed", False),
                "evaluation_summary": row.get("evaluation_summary", ""),
            }
        return None
    except Exception:
        return None


def get_evaluations(session_id: str) -> List[Dict[str, Any]]:
    """Retrieves ALL evaluations for a session in chronological order."""
    client = get_client()
    if not client:
        return []
    try:
        response = (
            client.table("answer_evaluations")
            .select("*")
            .eq("session_id", session_id)
            .order("id", desc=False)
            .execute()
        )
        return response.data or []
    except Exception:
        return []


def get_messages(session_id: str) -> List[Dict[str, Any]]:
    """Retrieves all transcript messages for a session in chronological order."""
    client = get_client()
    if not client:
        return []
    try:
        response = (
            client.table("interview_messages")
            .select("*")
            .eq("session_id", session_id)
            .order("id", desc=False)
            .execute()
        )
        return response.data or []
    except Exception:
        return []


def get_feedback(session_id: str) -> Dict[str, Any]:
    """Retrieves stored interview feedback for a completed session."""
    client = get_client()
    if not client:
        return {}
    try:
        response = (
            client.table("interview_feedback")
            .select("*")
            .eq("session_id", session_id)
            .execute()
        )
        if response.data:
            row = response.data[0]
            return {
                "summary": row.get("summary", ""),
                "strengths": row.get("strengths", []),
                "gaps": row.get("gaps", []),
                "next": row.get("next_steps", []),
            }
        return {}
    except Exception:
        return {}
