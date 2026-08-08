from pathlib import Path
from typing import Any, Dict, List
from app.agent import fallback_questions, router
from app.agent.state import InterviewState
from app.database import repository
from app.llm import gemini
from app.services import curriculum_service, evaluation_service

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "prompts"


def _get_interviewer_system_prompt() -> str:
    path = _PROMPTS_DIR / "interviewer.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return (
        "You are a technical interviewer for an AI cohort. "
        "Output ONLY JSON matching {\"question\": str, \"type\": str}."
    )


def _get_feedback_system_prompt() -> str:
    path = _PROMPTS_DIR / "feedback.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return (
        "You are a senior technical mentor. "
        "Output ONLY JSON matching {\"summary\": str, \"strengths\": list, \"gaps\": list, \"next\": list}."
    )


def choose_target_question_type(
    difficulty: str, follow_up_count: int, question_count: int
) -> str:
    """Deterministically selects target question_type based on topic depth & candidate difficulty."""
    if follow_up_count == 0:
        return "conceptual" if question_count % 2 == 1 else "why_how"

    if difficulty in ["advanced", "expert"]:
        adv_types = ["architecture", "trade_off", "production"]
        return adv_types[question_count % len(adv_types)]

    cycle_types = ["comparison", "debugging", "scenario", "why_how"]
    return cycle_types[question_count % len(cycle_types)]


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

    if db_session.get("status") == "completed":
        stored_feedback = repository.get_feedback(session_id)
        return {
            "session_id": session_id,
            "done": True,
            "reply": "Interview completed.",
            "feedback": stored_feedback,
            "status": "completed",
        }

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
        "done": False,
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
        "follow_up_count": 0,
    }


def generate_question(state: InterviewState) -> Dict[str, Any]:
    session_id = state.get("session_id", "")
    new_count = state.get("question_count", 0) + 1
    c_day = state.get("current_day", 1)
    c_topic = state.get("current_topic", "Environment & Tooling")
    difficulty = state.get("difficulty", "intermediate")
    follow_up_count = state.get("follow_up_count", 0)
    profile = state.get("profile", {})
    last_answer = state.get("last_answer")
    last_eval = state.get("last_evaluation") or {}
    missing_concepts = last_eval.get("missing_concepts", [])
    missing_str = ", ".join(missing_concepts) if missing_concepts else "None"

    target_type = choose_target_question_type(difficulty, follow_up_count, new_count)

    day_details = curriculum_service.get_day(c_day) or {}
    objectives = day_details.get("objectives", [])
    tools = day_details.get("tools", [])

    recent_msgs = repository.get_recent_messages(session_id, limit=30) if session_id else []
    transcript_snippets = [
        f"[{m.get('role', 'user')}]: {m.get('content', '')}" for m in recent_msgs
    ]
    transcript_history = "\n".join(transcript_snippets) if transcript_snippets else "None"

    system_prompt = _get_interviewer_system_prompt()

    followup_context = ""
    if last_answer:
        eval_summary = last_eval.get("evaluation_summary", "")
        followup_context = f"""
*** CANDIDATE'S LATEST ANSWER & EVALUATION ***
Candidate's Previous Response: "{last_answer}"
Evaluation Assessment: "{eval_summary}"
Missing Concepts to Address: {missing_str}

CRITICAL DIRECTIVE FOR FOLLOW-UP/CONTINUATION:
Your next question MUST directly connect to and probe what the candidate just explained in their response ("{last_answer[:250]}..."). Ask them to clarify gaps, justify trade-offs, or handle specific edge cases related to their stated solution. Do NOT ask an unrelated or disconnected question!
"""

    user_prompt = f"""INTERVIEW CONTEXT:
- Candidate Role: {profile.get('role', 'AI Engineer')} ({profile.get('experience', 3)} years experience)
- Current Curriculum Day: Day {c_day} - {c_topic}
- Objectives: {', '.join(objectives)}
- Tools: {', '.join(tools)}
- Target Difficulty: {difficulty}
- Target Question Type: {target_type}
- Follow-up Count: {follow_up_count}
- Missing Concepts to Target: {missing_str}
{followup_context}

RECENT TRANSCRIPT HISTORY (Do NOT repeat any question below):
{transcript_history}

Task: Generate an intelligent, highly context-aware technical question of type "{target_type}" at "{difficulty}" difficulty matching the day's objectives and tools.
Respond ONLY with JSON: {{"question": "...", "type": "{target_type}"}}"""

    try:
        res = gemini.generate_structured(user_prompt, system_instruction=system_prompt)
        q_text = res.get("question")
        q_type = res.get("type", target_type)
        if not q_text:
            raise ValueError("Empty question returned from Gemini")
    except Exception:
        fallback = fallback_questions.generate_dynamic_fallback(
            last_answer=last_answer,
            current_topic=c_topic,
            current_day=c_day,
            difficulty=difficulty,
            target_type=target_type,
        )
        q_text = fallback["question"]
        q_type = fallback["type"]

    return {
        "question_count": new_count,
        "last_question": q_text,
        "last_question_type": q_type,
        "reply": q_text,
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
    last_q = state.get("last_question") or "Tell me about your technical experience."
    last_a = state.get("last_answer") or ""
    c_day = state.get("current_day", 1)
    topic = state.get("current_topic", "General Technical Concepts")
    profile = state.get("profile", {})

    evaluation = evaluation_service.evaluate_answer(
        question=last_q,
        answer=last_a,
        curriculum_day=c_day,
        profile=profile,
    )

    if session_id:
        repository.add_evaluation(
            session_id=session_id,
            question_number=q_num,
            question=last_q,
            answer=last_a,
            curriculum_day=c_day,
            topic=topic,
            overall_score=evaluation.get("overall_score", 6.0),
            evaluation_summary=evaluation.get("evaluation_summary", ""),
        )

    return {"last_evaluation": evaluation}


def update_state(state: InterviewState) -> Dict[str, Any]:
    covered = list(state.get("covered_days", []))
    strengths = list(state.get("strengths", []))
    weaknesses = list(state.get("weaknesses", []))
    difficulty = state.get("difficulty", "intermediate")
    c_day = state.get("current_day", 1)
    c_topic = state.get("current_topic", "")
    last_eval = state.get("last_evaluation", {})
    overall_score = float(last_eval.get("overall_score", 6.0))

    if c_day and c_day not in covered:
        covered.append(c_day)

    if overall_score >= 8.0:
        if c_topic and c_topic not in strengths:
            strengths.append(c_topic)
    elif overall_score < 6.0:
        if c_topic and c_topic not in weaknesses:
            weaknesses.append(c_topic)

    if overall_score >= 8.5:
        difficulty = router.bump_up(difficulty)
    elif overall_score < 6.0:
        difficulty = router.bump_down(difficulty)

    if last_eval.get("follow_up_needed", False):
        follow_up_count = state.get("follow_up_count", 0) + 1
    else:
        follow_up_count = 0

    return {
        "covered_days": covered,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "difficulty": difficulty,
        "follow_up_count": follow_up_count,
    }


def decide_next_action(state: InterviewState) -> str:
    return router.decide_next_action(state)


def generate_feedback(state: InterviewState) -> Dict[str, Any]:
    session_id = state.get("session_id", "")
    covered_days = state.get("covered_days", [])
    profile = state.get("profile", {})
    strengths = list(state.get("strengths", []))
    weaknesses = list(state.get("weaknesses", []))

    # Fetch COMPLETE transcript and ALL evaluations for this session
    messages = repository.get_messages(session_id) if session_id else []
    evaluations = repository.get_evaluations(session_id) if session_id else []

    # Build rich transcript with Q&A pairs
    transcript_lines = []
    for m in messages:
        role_label = "INTERVIEWER" if m.get("role") == "interviewer" else "CANDIDATE"
        topic_tag = f" [Day {m.get('curriculum_day')} - {m.get('topic')}]" if m.get('topic') else ""
        transcript_lines.append(f"[{role_label}]{topic_tag}: {m.get('content', '')}")
    transcript_text = "\n".join(transcript_lines) if transcript_lines else "No transcript available"

    # Build evaluation summary per question
    eval_lines = []
    for ev in evaluations:
        missing = ev.get("missing_concepts", [])
        missing_str = ", ".join(missing) if missing else "None"
        eval_lines.append(
            f"Q{ev.get('question_number', '?')} [{ev.get('topic', 'Unknown')}]: "
            f"Score={ev.get('overall_score', 'N/A')}/10, "
            f"Missing=[{missing_str}], "
            f"Summary: {ev.get('evaluation_summary', 'N/A')}"
        )
    evaluations_text = "\n".join(eval_lines) if eval_lines else "No evaluations available"

    system_prompt = _get_feedback_system_prompt()
    user_prompt = f"""INTERVIEW RECORD:
- Candidate Role: {profile.get('role', 'AI Engineer')} ({profile.get('experience', 3)} years experience)
- Covered Curriculum Days: {', '.join(map(str, covered_days))}
- Demonstrated Strengths (topics): {', '.join(strengths) if strengths else 'None recorded'}
- Demonstrated Weaknesses (topics): {', '.join(weaknesses) if weaknesses else 'None recorded'}

FULL INTERVIEW TRANSCRIPT (every question asked and every answer given):
{transcript_text}

PER-QUESTION EVALUATION SCORES AND GAPS:
{evaluations_text}

Task: Generate final candidate-facing technical interview feedback grounded in the SPECIFIC transcript and evaluations above.
Respond ONLY with JSON matching:
{{"summary": "...", "strengths": ["..."], "gaps": ["..."], "next": ["..."]}}"""

    try:
        res = gemini.generate_structured(user_prompt, system_instruction=system_prompt)
        summary = res.get("summary")
        strengths_res = list(res.get("strengths", []))
        gaps_res = list(res.get("gaps", []))
        next_res = list(res.get("next", []))

        if not summary or not strengths_res or not gaps_res or not next_res:
            raise ValueError("Incomplete feedback output from Gemini")

        feedback_data = {
            "summary": summary,
            "strengths": strengths_res,
            "gaps": gaps_res,
            "next": next_res,
        }
    except Exception:
        covered_str = ", ".join(map(str, covered_days)) if covered_days else "core topics"
        feedback_data = {
            "summary": f"The candidate completed an adaptive technical interview covering Days {covered_str}.",
            "strengths": strengths or ["Active technical participation", "Demonstrated foundational skills"],
            "gaps": weaknesses or ["Advanced system architecture and production deployment"],
            "next": ["Review core AI engineering patterns and production deployment."],
        }

    return {
        "feedback": feedback_data,
        "reply": "Interview completed.",
        "done": True,
    }


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
