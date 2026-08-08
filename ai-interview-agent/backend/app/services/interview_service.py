from typing import Any, Dict, Tuple
from app.agent.graph import continue_graph, start_graph
from app.database import repository


def handle_turn(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    session_id = payload.get("sessionId", "")

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
        db_session = repository.get_session(session_id)

        if not db_session:
            return {
                "error": "session_not_found",
                "message": f"Session '{session_id}' not found.",
            }, 404

        current_state = {
            "session_id": session_id,
            "difficulty": db_session.get("difficulty", "intermediate"),
            "question_count": db_session.get("question_count", 0),
            "follow_up_count": db_session.get("follow_up_count", 0),
            "current_day": db_session.get("current_day", 1),
            "current_topic": db_session.get("current_topic", "Environment & Tooling"),
            "covered_days": db_session.get("covered_days", []),
            "last_answer": message,
            "done": db_session.get("status") == "completed",
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

    return {"error": "bad_request", "message": "Invalid request payload"}, 400
