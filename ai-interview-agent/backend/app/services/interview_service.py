import logging
from typing import Any, Dict, Tuple
from app.agent.graph import continue_graph, start_graph
from app.database import repository

logger = logging.getLogger(__name__)


def handle_turn(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    try:
        session_id = payload.get("sessionId")
        if (
            not session_id
            or not isinstance(session_id, str)
            or len(session_id.strip()) == 0
            or len(session_id) > 128
        ):
            return {
                "error": "invalid_session_id",
                "message": "sessionId must be a non-empty string under 128 characters.",
            }, 422

        session_id = session_id.strip()

        # Turn 1: Session Start Request
        if "candidate" in payload:
            candidate = payload.get("candidate", {})
            initial_state = {
                "session_id": session_id,
                "candidate": candidate,
                "difficulty": "intermediate",
                "question_count": 0,
                "follow_up_count": 0,
                "covered_days": [],
                "strengths": [],
                "weaknesses": [],
                "done": False,
            }
            final_state = start_graph.invoke(initial_state)

            return {
                "reply": final_state.get("reply", "Welcome. Let's begin your interview."),
                "done": False,
            }, 200

        # Turn 2+: Continuation Request
        if "message" in payload:
            message = payload.get("message", "")
            if not isinstance(message, str):
                return {
                    "error": "invalid_message",
                    "message": "message must be a string.",
                }, 422

            if len(message) > 4000:
                return {
                    "error": "message_too_long",
                    "message": "Message exceeds maximum allowed length of 4000 characters.",
                }, 422

            db_session = repository.get_session(session_id)

            if not db_session:
                return {
                    "error": "session_not_found",
                    "message": "No active interview found for this sessionId.",
                }, 404

            # Idempotency check: return stored feedback if session is already completed
            if db_session.get("status") == "completed":
                stored_feedback = repository.get_feedback(session_id)
                return {
                    "reply": "Interview completed.",
                    "done": True,
                    "feedback": stored_feedback,
                }, 200

            # --- FIX: Restore last_question and last_evaluation from DB ---
            # Fetch the most recent interviewer message to recover last_question
            recent_msgs = repository.get_recent_messages(session_id, limit=2)
            last_question = None
            for m in reversed(recent_msgs):
                if m.get("role") == "interviewer":
                    last_question = m.get("content")
                    break

            # Fetch the most recent evaluation to recover last_evaluation
            last_evaluation = repository.get_latest_evaluation(session_id)

            current_state = {
                "session_id": session_id,
                "difficulty": db_session.get("difficulty", "intermediate"),
                "question_count": db_session.get("question_count", 0),
                "follow_up_count": db_session.get("follow_up_count", 0),
                "current_day": db_session.get("current_day", 1),
                "current_topic": db_session.get("current_topic", "Environment & Tooling"),
                "covered_days": db_session.get("covered_days", []),
                "strengths": db_session.get("strengths", []),
                "weaknesses": db_session.get("weaknesses", []),
                "last_answer": message,
                "last_question": last_question,
                "last_evaluation": last_evaluation,
                "done": False,
            }

            final_state = continue_graph.invoke(current_state)

            if final_state.get("done"):
                return {
                    "reply": final_state.get("reply", "Interview completed."),
                    "done": True,
                    "feedback": final_state.get("feedback"),
                }, 200

            return {
                "reply": final_state.get("reply", ""),
                "done": False,
            }, 200

        return {"error": "bad_request", "message": "Invalid request payload"}, 422

    except Exception as e:
        logger.exception("Unhandled server error in interview_service: %s", e)
        return {
            "error": "internal_error",
            "message": "Something went wrong. Please try again.",
        }, 500
