from typing import Any, Dict, List
from app.agent import router
from app.agent.state import InterviewState
from app.database import repository
from app.services import curriculum_service


def build_profile_from_candidate(candidate: dict, curriculum_days: List[dict]) -> dict:
    """Builds a candidate profile based on mission records and learning signals."""
    member = candidate["member"]
    missions = candidate.get("missions", [])
    signals = candidate.get("signals", {})

    strength_topics, weak_topics, skipped_topics = [], [], []
    for m in missions:
        day_title = m["title"]
        if m.get("skipped"):
            skipped_topics.append(day_title)
        elif m.get("passed") and m.get("attempts") == 1:
            strength_topics.append(day_title)
        elif not m.get("passed"):
            weak_topics.append(day_title)

    total_missions = candidate.get("totalMissions", 31)
    missions_completed = signals.get("missionsCompleted", 0)
    missions_first_try = signals.get("missionsFirstTry", 0)
    commit_days = signals.get("commitDays", 0)
    cohort_days = candidate.get("cohortDays", 31)

    completion_rate = missions_completed / max(total_missions, 1)
    first_try_rate = missions_first_try / max(missions_completed, 1)
    consistency = commit_days / max(cohort_days, 1)

    confidence_score = 0.4 * completion_rate + 0.4 * first_try_rate + 0.2 * consistency

    difficulty = (
        "advanced"
        if confidence_score >= 0.8
        else "intermediate"
        if confidence_score >= 0.5
        else "foundation"
    )

    years = member.get("yearsExperience", 0)
    if years >= 5 and difficulty != "advanced":
        difficulty = router.bump_up(difficulty)
    if years <= 1 and difficulty != "foundation":
        difficulty = router.bump_down(difficulty)

    return {
        "candidate_id": member.get("id", ""),
        "role": member.get("jobRole", ""),
        "experience": years,
        "strength_topics": router.dedupe(strength_topics),
        "weak_topics": router.dedupe(weak_topics),
        "skipped_topics": router.dedupe(skipped_topics),
        "confidence_level": round(confidence_score, 3),
        "difficulty": difficulty,
        "covered_mission_days": [m["day"] for m in missions],
    }


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
    if not candidate or "member" not in candidate:
        return {"profile": {}, "difficulty": "intermediate"}

    days = curriculum_service.all_days()
    profile = build_profile_from_candidate(candidate, days)
    return {"profile": profile, "difficulty": profile["difficulty"]}


def select_topic(state: InterviewState) -> Dict[str, Any]:
    profile = state.get("profile", {})
    if not profile and state.get("candidate"):
        days = curriculum_service.all_days()
        profile = build_profile_from_candidate(state["candidate"], days)

    curriculum_days = curriculum_service.all_days()
    covered_days = state.get("covered_days", [])

    selected_day = router.select_best_topic(
        profile=profile,
        curriculum_days=curriculum_days,
        covered_days=covered_days,
        curriculum_module_lookup=curriculum_service.get_module_for_day,
    )

    return {
        "current_day": selected_day["day"],
        "current_topic": selected_day["title"],
    }


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
