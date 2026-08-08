from typing import Any, Dict
from app.agent.state import InterviewState
from app.database import repository


def load_or_create_session(state: InterviewState) -> Dict[str, Any]:
    session_id = state.get("session_id", "")
    candidate = state.get("candidate", {})
    member = candidate.get("member", {})
    candidate_id = member.get("id", "CAND-001")
    difficulty = state.get("difficulty", "intermediate")

    db_session = repository.get_session(session_id)
    if not db_session:
        db_session = repository.create_session(session_id, candidate_id, difficulty)

    return {
        "session_id": session_id,
        "candidate": candidate,
        "difficulty": db_session.get("difficulty", difficulty),
        "question_count": db_session.get("question_count", 0),
        "follow_up_count": db_session.get("follow_up_count", 0),
        "covered_days": db_session.get("covered_days", []),
        "strengths": db_session.get("strengths", []),
        "weaknesses": db_session.get("weaknesses", []),
        "status": db_session.get("status", "active"),
        "done": False,
    }


def load_session(state: InterviewState) -> Dict[str, Any]:
    session_id = state.get("session_id", "")
    db_session = repository.get_session(session_id)
    if not db_session:
        return {"done": True, "reply": "Session not found."}

    return {
        "session_id": session_id,
        "difficulty": db_session.get("difficulty", "intermediate"),
        "question_count": db_session.get("question_count", 0),
        "follow_up_count": db_session.get("follow_up_count", 0),
        "current_day": db_session.get("current_day"),
        "current_topic": db_session.get("current_topic"),
        "covered_days": db_session.get("covered_days", []),
        "strengths": db_session.get("strengths", []),
        "weaknesses": db_session.get("weaknesses", []),
        "done": db_session.get("status") == "completed",
    }


def build_profile(state: InterviewState) -> Dict[str, Any]:
    candidate = state.get("candidate", {})
    member = candidate.get("member", {})
    profile = {
        "candidate_id": member.get("id", "CAND-001"),
        "name": member.get("name", "Candidate"),
        "role": member.get("jobRole", "AI Engineer"),
        "years_experience": member.get("yearsExperience", 3),
    }
    return {"profile": profile}


def select_topic(state: InterviewState) -> Dict[str, Any]:
    current_day = state.get("current_day") or 1
    current_topic = state.get("current_topic") or "Environment & Tooling"
    return {"current_day": current_day, "current_topic": current_topic}


def generate_question(state: InterviewState) -> Dict[str, Any]:
    new_count = state.get("question_count", 0) + 1
    day = state.get("current_day", 1)
    topic = state.get("current_topic", "Environment & Tooling")
    question_text = f"Welcome. Question {new_count}: Tell me about your experience with Day {day} - {topic}."

    return {
        "question_count": new_count,
        "last_question": question_text,
        "last_question_type": "conceptual",
        "reply": question_text,
        "done": False,
    }


def save_candidate_answer(state: InterviewState) -> Dict[str, Any]:
    session_id = state.get("session_id", "")
    last_answer = state.get("last_answer", "")
    if session_id and last_answer:
        repository.add_message(
            session_id=session_id,
            role="candidate",
            content=last_answer,
            question_number=state.get("question_count"),
            curriculum_day=state.get("current_day"),
            topic=state.get("current_topic"),
        )
    return {}


def evaluate_answer(state: InterviewState) -> Dict[str, Any]:
    session_id = state.get("session_id", "")
    q_num = state.get("question_count", 1)
    last_q = state.get("last_question", "Question")
    last_a = state.get("last_answer", "")
    c_day = state.get("current_day", 1)
    topic = state.get("current_topic", "Topic")

    evaluation = {
        "correctness": 8.0,
        "technical_depth": 7.5,
        "overall_score": 7.75,
        "missing_concepts": [],
        "follow_up_needed": False,
        "summary": "Solid response.",
    }

    if session_id:
        repository.add_evaluation(
            session_id=session_id,
            question_number=q_num,
            question=last_q or "Question",
            answer=last_a or "",
            curriculum_day=c_day,
            topic=topic,
            overall_score=7.75,
            evaluation_summary="Solid response.",
        )

    return {"last_evaluation": evaluation}


def update_state(state: InterviewState) -> Dict[str, Any]:
    covered = list(state.get("covered_days", []))
    c_day = state.get("current_day", 1)
    if c_day not in covered:
        covered.append(c_day)
    return {"covered_days": covered}


def decide_next_action(state: InterviewState) -> str:
    q_count = state.get("question_count", 0)
    covered = state.get("covered_days", [])
    eval_rec = state.get("last_evaluation", {})

    if q_count >= 12 or (q_count >= 8 and len(covered) >= 4):
        return "finish"
    if eval_rec.get("follow_up_needed", False) and state.get("follow_up_count", 0) < 2:
        return "follow_up"
    return "new_topic"


def generate_feedback(state: InterviewState) -> Dict[str, Any]:
    feedback = {
        "summary": "Completed technical interview covering core curriculum topics.",
        "strengths": ["Clear communication", "Good foundational concepts"],
        "gaps": ["Deep architectural details"],
        "next": ["Review advanced deployment patterns"],
    }
    return {"feedback": feedback, "reply": "Interview completed.", "done": True}


def persist_state(state: InterviewState) -> Dict[str, Any]:
    session_id = state.get("session_id", "")
    if session_id:
        repository.update_session(
            session_id=session_id,
            question_count=state.get("question_count", 0),
            follow_up_count=state.get("follow_up_count", 0),
            current_day=state.get("current_day"),
            current_topic=state.get("current_topic"),
            difficulty=state.get("difficulty", "intermediate"),
            covered_days=state.get("covered_days", []),
            status="completed" if state.get("done") else "active",
        )
        if state.get("reply"):
            repository.add_message(
                session_id=session_id,
                role="interviewer",
                content=state["reply"],
                question_number=state.get("question_count"),
                curriculum_day=state.get("current_day"),
                topic=state.get("current_topic"),
                question_type=state.get("last_question_type"),
            )
    return {}


def persist_feedback(state: InterviewState) -> Dict[str, Any]:
    session_id = state.get("session_id", "")
    feedback = state.get("feedback")
    if session_id and feedback:
        repository.save_feedback(
            session_id=session_id,
            summary=feedback.get("summary", ""),
            strengths=feedback.get("strengths", []),
            gaps=feedback.get("gaps", []),
            next_steps=feedback.get("next", []),
        )
        repository.update_session(session_id=session_id, status="completed")
    return {}
