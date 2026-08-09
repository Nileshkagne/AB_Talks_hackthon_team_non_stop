from typing import Any, Dict
from fastapi import APIRouter, Response
from app.services import interview_service
from app.database import repository

router = APIRouter()


@router.post("/interview")
def interview_turn(payload: Dict[str, Any], response: Response):
    result, status_code = interview_service.handle_turn(payload)
    response.status_code = status_code
    return result


@router.get("/interview/{session_id}/report")
def get_interview_report(session_id: str, response: Response):
    """Returns the full interview report for a completed session.

    Includes candidate info, ordered transcript with per-question evaluation
    scores, and the final feedback object (with overall_percentage,
    category_breakdown, fluency data).
    Returns 404 for unknown or non-completed sessions.
    """
    # 1. Verify session exists and is completed
    session = repository.get_session(session_id)
    if not session:
        response.status_code = 404
        return {
            "error": "session_not_found",
            "message": "No interview session found for this sessionId.",
        }

    if session.get("status") != "completed":
        response.status_code = 404
        return {
            "error": "session_not_completed",
            "message": "Interview report is only available for completed sessions.",
        }

    # 2. Fetch transcript messages and evaluations
    messages = repository.get_messages(session_id)
    evaluations = repository.get_evaluations(session_id)

    # Build eval lookup by question_number
    eval_by_qnum: Dict[int, Dict] = {}
    for ev in evaluations:
        qn = ev.get("question_number")
        if qn is not None:
            eval_by_qnum[int(qn)] = ev

    # 3. Build ordered transcript with paired evaluations
    CANDIDATE_EVAL_FIELDS = [
        "correctness", "technical_depth", "reasoning",
        "practicality", "communication", "overall_score",
        "evaluation_summary",
    ]

    seen_qnums = set()
    transcript = []
    current_question = None
    current_qnum = None

    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        qn = m.get("question_number")

        if role == "interviewer":
            if qn is not None and int(qn) in seen_qnums:
                continue
            if qn is not None:
                seen_qnums.add(int(qn))
            current_question = content
            current_qnum = qn
            transcript.append({
                "role": "interviewer",
                "content": content,
                "question_number": current_qnum,
                "topic": m.get("topic"),
                "curriculum_day": m.get("curriculum_day"),
            })
        elif role == "candidate":
            entry = {
                "role": "candidate",
                "content": content,
                "question_number": current_qnum,
            }
            # Attach per-turn evaluation (candidate-safe fields only)
            ev = eval_by_qnum.get(int(current_qnum)) if current_qnum else None
            if ev:
                entry["evaluation"] = {
                    k: ev.get(k) for k in CANDIDATE_EVAL_FIELDS if ev.get(k) is not None
                }
            transcript.append(entry)

    # 4. Fetch final feedback
    feedback = repository.get_feedback(session_id)

    # 5. Candidate info from session metadata
    candidate_info = {
        "name": session.get("candidate_name") or "Candidate",
        "role": session.get("candidate_role") or "AI Engineer",
        "candidate_id": session.get("candidate_id"),
    }

    return {
        "session_id": session_id,
        "candidate": candidate_info,
        "transcript": transcript,
        "feedback": feedback,
    }

