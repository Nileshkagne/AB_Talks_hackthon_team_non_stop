import logging
import time
from typing import Any, Dict, Tuple
from app.agent.graph import continue_graph, start_graph
from app.database import repository

from app.llm import gemini

logger = logging.getLogger(__name__)


def handle_turn(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    gemini.reset_fallback_flag()
    t_turn_start = time.monotonic()
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

            resp = {
                "reply": final_state.get("reply", "Welcome. Let's begin your interview."),
                "done": False,
            }
            if gemini.was_fallback_used():
                resp["warning"] = "ai_temporarily_unavailable"

            t_total = time.monotonic() - t_turn_start
            logger.info("[TIMING] Start turn total=%.2fs", t_total)
            return resp, 200

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

            t0 = time.monotonic()
            db_session = repository.get_session(session_id)
            t_get_session = time.monotonic() - t0

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

            # --- Restore last_question and last_evaluation from DB ---
            t0 = time.monotonic()
            recent_msgs = repository.get_recent_messages(session_id, limit=2)
            t_get_msgs = time.monotonic() - t0

            last_question = None
            for m in reversed(recent_msgs):
                if m.get("role") == "interviewer":
                    last_question = m.get("content")
                    break

            t0 = time.monotonic()
            last_evaluation = repository.get_latest_evaluation(session_id)
            t_get_eval = time.monotonic() - t0

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

            t0 = time.monotonic()
            final_state = continue_graph.invoke(current_state)
            t_graph = time.monotonic() - t0

            resp = {
                "reply": final_state.get("reply", "Interview completed."),
                "done": bool(final_state.get("done")),
            }
            if final_state.get("feedback"):
                resp["feedback"] = final_state.get("feedback")

            if gemini.was_fallback_used():
                resp["warning"] = "ai_temporarily_unavailable"

            t_total = time.monotonic() - t_turn_start
            logger.info(
                "[TIMING] Continue turn: get_session=%.2fs get_msgs=%.2fs get_eval=%.2fs "
                "graph=%.2fs TOTAL=%.2fs",
                t_get_session, t_get_msgs, t_get_eval, t_graph, t_total
            )
            return resp, 200

        return {"error": "bad_request", "message": "Invalid request payload"}, 422

    except gemini.GeminiError as ge:
        logger.error("Gemini API error in interview_service: %s", ge)
        err_str = str(ge).lower()
        if "429" in err_str or "resource_exhausted" in err_str or "limit" in err_str or "quota" in err_str:
            return {
                "error": "api_limit_exceeded",
                "message": "Gemini API key limit hit / quota exceeded. Please check your GEMINI_API_KEY in backend/.env or wait for quota reset.",
            }, 429
        return {
            "error": "gemini_api_error",
            "message": f"Gemini API Error: {ge}",
        }, 503

    except Exception as e:
        logger.exception("Unhandled server error in interview_service: %s", e)
        err_str = str(e).lower()
        if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
            return {
                "error": "api_limit_exceeded",
                "message": "Gemini API key limit hit / quota exceeded. Please check your GEMINI_API_KEY in backend/.env or wait for quota reset.",
            }, 429
        return {
            "error": "internal_error",
            "message": f"Server error: {e}",
        }, 500
