import logging
import time
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)
from app.agent import fallback_questions, router
from app.agent.state import InterviewState
from app.database import repository
from app.llm import gemini
from app.llm.gemini import GeminiError
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
        stored_feedback = repository.get_feedback(session_id) or {}
        closing_msg = (
            stored_feedback.get("closing_message")
            or "Thank you for completing your technical interview session!"
        )
        return {
            "session_id": session_id,
            "done": True,
            "reply": closing_msg,
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


def _build_static_intro(candidate: dict, profile: dict, c_topic: str) -> str:
    """Build a locally-constructed personalized intro when Gemini fails.
    Uses real candidate data so the fallback isn't fully generic."""
    member = candidate.get("member", {})
    name = member.get("name", "").split()[0] if member.get("name") else "there"
    role = member.get("jobRole", profile.get("role", "engineer"))
    years = member.get("yearsExperience", profile.get("experience", ""))

    # Pick a real signal from the profile if available
    signal = ""
    strengths = profile.get("strength_topics", [])
    weak_topics = profile.get("weak_topics", [])
    if strengths:
        signal = f" I can see you've done well on topics like {strengths[0]}, so we'll build on that foundation."
    elif weak_topics:
        signal = f" We'll cover a few areas to get a well-rounded picture of your skills."

    years_str = f" with {years} years of experience" if years else ""
    return (
        f"Hi {name}, thanks for joining today! "
        f"Given your background as a {role}{years_str}, I'm looking forward to our conversation.{signal} "
        f"Let's start with {c_topic} —"
    )


def generate_question(state: InterviewState) -> Dict[str, Any]:
    t_node_start = time.monotonic()
    session_id = state.get("session_id", "")
    new_count = state.get("question_count", 0) + 1
    c_day = state.get("current_day", 1)
    c_topic = state.get("current_topic", "Environment & Tooling")
    difficulty = state.get("difficulty", "intermediate")
    follow_up_count = state.get("follow_up_count", 0)
    profile = state.get("profile", {})
    candidate = state.get("candidate", {})
    last_answer = state.get("last_answer")
    last_eval = state.get("last_evaluation") or {}
    missing_concepts = last_eval.get("missing_concepts", [])
    missing_str = ", ".join(missing_concepts) if missing_concepts else "None"

    is_intro = (new_count == 1 and not last_answer)

    target_type = choose_target_question_type(difficulty, follow_up_count, new_count)

    day_details = curriculum_service.get_day(c_day) or {}
    objectives = day_details.get("objectives", [])
    tools = day_details.get("tools", [])

    # Reduced from 30 to 10 — keeps prompt short, model responds faster
    t0 = time.monotonic()
    recent_msgs = repository.get_recent_messages(session_id, limit=10) if session_id else []
    t_db = time.monotonic() - t0
    transcript_snippets = [
        f"[{m.get('role', 'user')}]: {m.get('content', '')[:200]}" for m in recent_msgs
    ]
    transcript_history = "\n".join(transcript_snippets) if transcript_snippets else "None"

    system_prompt = _get_interviewer_system_prompt()

    # ── INTRO MODE: personalized opening on the very first turn ──
    intro_block = ""
    if is_intro:
        member = candidate.get("member", {})
        cand_name = member.get("name", "Candidate")
        cand_role = member.get("jobRole", profile.get("role", "AI Engineer"))
        cand_years = member.get("yearsExperience", profile.get("experience", ""))
        strength_topics = profile.get("strength_topics", [])
        weak_topics = profile.get("weak_topics", [])
        skipped_topics = profile.get("skipped_topics", [])

        intro_block = f"""
MODE: INTRO
This is the FIRST turn of the interview. Generate a personalized opening.

CANDIDATE PROFILE FOR INTRO:
- Name: {cand_name}
- Role: {cand_role}
- Years of Experience: {cand_years or 'not specified'}
- Strong Topics: {', '.join(strength_topics) if strength_topics else 'None recorded'}
- Weak Topics: {', '.join(weak_topics) if weak_topics else 'None recorded'}
- Skipped Topics: {', '.join(skipped_topics) if skipped_topics else 'None'}

Include an "intro" field in your JSON: a warm 2-3 sentence personalized opening referencing something specific about this candidate. Do NOT mention difficulty levels or scores.
"""

    followup_context = ""
    if last_answer:
        eval_summary = last_eval.get("evaluation_summary", "")
        followup_context = f"""
*** CANDIDATE'S LATEST ANSWER & EVALUATION ***
Candidate's Previous Response: "{last_answer[:300]}"
Evaluation: "{eval_summary}"
Missing Concepts: {missing_str}

Your next question MUST directly build upon the candidate's response above. Probe gaps, trade-offs, or edge cases in their stated approach.
"""

    user_prompt = f"""INTERVIEW CONTEXT:
- Candidate: {profile.get('role', 'AI Engineer')} ({profile.get('experience', 3)}y exp)
- Day {c_day}: {c_topic}
- Objectives: {', '.join(objectives)}
- Tools: {', '.join(tools)}
- Difficulty: {difficulty} | Type: {target_type} | Follow-ups: {follow_up_count}
- Missing Concepts: {missing_str}
{intro_block}{followup_context}

RECENT TRANSCRIPT (Do NOT repeat any question):
{transcript_history}

Generate a context-aware "{target_type}" question at "{difficulty}" difficulty.
Respond ONLY with JSON: {{"question": "...", "type": "{target_type}"{', "intro": "..."' if is_intro else ''}}}"""

    try:
        t0 = time.monotonic()
        res = gemini.generate_structured(user_prompt, system_instruction=system_prompt)
        t_gemini = time.monotonic() - t0
        q_text = res.get("question")
        q_type = res.get("type", target_type)
        model_used = res.get("_model_used")
        if not q_text:
            raise ValueError("Empty question returned from Gemini")

        # Build the combined reply for intro turns
        if is_intro:
            intro_text = res.get("intro", "")
            if intro_text:
                reply_text = f"{intro_text}\n\n{q_text}"
            else:
                # Gemini returned a question but no intro — use static fallback intro
                static_intro = _build_static_intro(candidate, profile, c_topic)
                reply_text = f"{static_intro} {q_text}"
        else:
            reply_text = q_text

        t0 = time.monotonic()
        if session_id and q_text:
            repository.add_message(
                session_id=session_id,
                role="interviewer",
                content=reply_text,
                question_number=new_count,
                curriculum_day=c_day,
                topic=c_topic,
                question_type=q_type,
                model_used=model_used,
            )
        t_db_write = time.monotonic() - t0

        logger.info(
            "[TIMING] generate_question: db_read=%.2fs gemini=%.2fs db_write=%.2fs total=%.2fs model=%s intro=%s",
            t_db, t_gemini, t_db_write, time.monotonic() - t_node_start, model_used, is_intro
        )
    except Exception as exc:
        logger.error("[generate_question] Gemini API error for session=%s: %s", session_id, exc)
        # On intro failure, use static personalized fallback instead of raising
        if is_intro:
            logger.warning("[generate_question] Using static personalized fallback for intro")
            static_intro = _build_static_intro(candidate, profile, c_topic)
            reply_text = f"{static_intro} To start, could you walk me through your understanding of the key concepts in {c_topic}?"
            q_text = f"Could you walk me through your understanding of the key concepts in {c_topic}?"
            q_type = target_type
            model_used = None
            if session_id:
                try:
                    repository.add_message(
                        session_id=session_id,
                        role="interviewer",
                        content=reply_text,
                        question_number=new_count,
                        curriculum_day=c_day,
                        topic=c_topic,
                        question_type=q_type,
                    )
                except Exception:
                    logger.warning("[generate_question] Failed to persist fallback intro message")
            return {
                "question_count": new_count,
                "last_question": q_text,
                "last_question_type": q_type,
                "reply": reply_text,
                "done": False,
                "model_used": model_used,
            }
        raise GeminiError(f"Gemini API call failed during question generation: {exc}") from exc

    return {
        "question_count": new_count,
        "last_question": q_text,
        "last_question_type": q_type,
        "reply": reply_text,
        "done": False,
        "model_used": model_used,
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
    t_node_start = time.monotonic()
    session_id = state.get("session_id", "")
    q_num = state.get("question_count", 1)
    last_q = state.get("last_question") or "Tell me about your technical experience."
    last_a = state.get("last_answer") or ""
    c_day = state.get("current_day", 1)
    topic = state.get("current_topic", "General Technical Concepts")
    profile = state.get("profile", {})

    t0 = time.monotonic()
    evaluation = evaluation_service.evaluate_answer(
        question=last_q,
        answer=last_a,
        curriculum_day=c_day,
        profile=profile,
    )
    t_gemini = time.monotonic() - t0

    model_used = evaluation.get("model_used")

    t0 = time.monotonic()
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
            model_used=model_used,
        )
    t_db = time.monotonic() - t0

    logger.info(
        "[TIMING] evaluate_answer: gemini=%.2fs db_write=%.2fs total=%.2fs model=%s",
        t_gemini, t_db, time.monotonic() - t_node_start, model_used
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


def _truncate(text: str, max_chars: int = 400) -> str:
    """Truncate text to max_chars, appending '...' if truncated."""
    if not text or len(text) <= max_chars:
        return text or ""
    return text[:max_chars].rstrip() + "..."


def generate_feedback(state: InterviewState) -> Dict[str, Any]:
    session_id = state.get("session_id", "")
    covered_days = state.get("covered_days", [])
    profile = state.get("profile", {})
    strengths = list(state.get("strengths", []))
    weaknesses = list(state.get("weaknesses", []))

    # Fetch COMPLETE transcript and ALL evaluations for this session
    messages = repository.get_messages(session_id) if session_id else []
    evaluations = repository.get_evaluations(session_id) if session_id else []

    # Build an index of evaluations by question number for merging
    eval_by_qnum: Dict[int, Dict] = {}
    for ev in evaluations:
        qn = ev.get("question_number")
        if qn is not None:
            eval_by_qnum[int(qn)] = ev

    # Build CONDENSED transcript — full questions, TRUNCATED answers, + per-turn eval summary
    # This prevents payload-size failures on long multi-paragraph answers.
    condensed_turns = []
    current_question = None
    current_qnum = None
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        topic_tag = f" [Day {m.get('curriculum_day')} - {m.get('topic')}]" if m.get("topic") else ""

        if role == "interviewer":
            current_question = content
            current_qnum = m.get("question_number")
            condensed_turns.append(f"QUESTION{topic_tag}: {content}")
        elif role == "candidate":
            # Truncate long answers — the evaluation_summary already captures the key findings
            condensed_turns.append(f"ANSWER (excerpt): {_truncate(content, 400)}")
            # Append the evaluation for this turn inline
            ev = eval_by_qnum.get(int(current_qnum)) if current_qnum else None
            if ev:
                missing = ev.get("missing_concepts", [])
                missing_str = ", ".join(missing) if missing else "None"
                condensed_turns.append(
                    f"  → EVAL: Score={ev.get('overall_score', 'N/A')}/10, "
                    f"Missing=[{missing_str}], "
                    f"{ev.get('evaluation_summary', '')}"
                )
    condensed_text = "\n".join(condensed_turns) if condensed_turns else "No transcript available"

    # Build standalone evaluation summary table (for redundancy)
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

    # ── STEP 1: Compute overall_percentage & category_breakdown from per-turn evaluations ──
    CATEGORY_KEYS = ["correctness", "technical_depth", "reasoning", "practicality", "communication"]
    category_sums: Dict[str, float] = {k: 0.0 for k in CATEGORY_KEYS}
    category_counts: Dict[str, int] = {k: 0 for k in CATEGORY_KEYS}
    overall_scores: list = []

    for ev in evaluations:
        os_val = ev.get("overall_score")
        if os_val is not None:
            try:
                overall_scores.append(float(os_val))
            except (ValueError, TypeError):
                pass
        for cat in CATEGORY_KEYS:
            cat_val = ev.get(cat)
            if cat_val is not None:
                try:
                    category_sums[cat] += float(cat_val)
                    category_counts[cat] += 1
                except (ValueError, TypeError):
                    pass

    if overall_scores:
        overall_percentage = round(sum(overall_scores) / len(overall_scores) * 10)
    else:
        overall_percentage = 0

    category_breakdown = {}
    for cat in CATEGORY_KEYS:
        if category_counts[cat] > 0:
            category_breakdown[cat] = round(category_sums[cat] / category_counts[cat] * 10)
        else:
            category_breakdown[cat] = 0

    # ── Candidate name extraction ──
    cand_name = (
        profile.get("name")
        or profile.get("member", {}).get("name")
        or "Candidate"
    )

    # ── Collect all candidate answer texts for fluency context ──
    candidate_answers = []
    for m in messages:
        if m.get("role") == "candidate":
            candidate_answers.append(m.get("content", ""))
    answers_sample = "\n---\n".join([_truncate(a, 300) for a in candidate_answers]) if candidate_answers else "No candidate answers available"

    system_prompt = _get_feedback_system_prompt()
    user_prompt = f"""INTERVIEW RECORD:
- Candidate Name: {cand_name}
- Candidate Role: {profile.get('role', 'AI Engineer')} ({profile.get('experience', 3)} years experience)
- Covered Curriculum Days: {', '.join(map(str, covered_days))}
- Demonstrated Strengths (topics): {', '.join(strengths) if strengths else 'None recorded'}
- Demonstrated Weaknesses (topics): {', '.join(weaknesses) if weaknesses else 'None recorded'}

CONDENSED INTERVIEW TRANSCRIPT (questions in full, answers excerpted, with per-turn evaluation):
{condensed_text}

PER-QUESTION EVALUATION SCORES AND GAPS:
{evaluations_text}

CANDIDATE ANSWER SAMPLES (for fluency/grammar analysis):
{answers_sample}

Task: Generate final candidate-facing technical interview feedback.
Produce a short (2-3 sentence), warm, natural closing remark from the interviewer's voice referencing {cand_name} by name, thanking them for participating, and noting the interview is complete.
For each strength, cite a SPECIFIC technical detail the candidate actually said (a term, a design choice, a trade-off they named).
For each gap, describe what was specifically MISSING or WRONG in their actual answer — not just the topic name.
ALSO: Analyze the candidate's written answers collectively for grammatical correctness, sentence structure, and clarity of written expression (distinct from technical correctness). Produce a fluency_score (0-100) and fluency_notes (1-2 constructive sentences). Be fair — never penalize non-native English phrasing harshly.
Respond ONLY with JSON matching:
{{"closing_message": "...", "summary": "...", "strengths": ["..."], "gaps": ["..."], "next": ["..."], "fluency_score": 85, "fluency_notes": "..."}}"""

    logger.info("[generate_feedback] session=%s, transcript_chars=%d, eval_count=%d, overall_pct=%d",
                session_id, len(condensed_text), len(evaluations), overall_percentage)

    try:
        res = gemini.generate_structured(user_prompt, system_instruction=system_prompt)
        summary = res.get("summary")
        strengths_res = list(res.get("strengths", []))
        gaps_res = list(res.get("gaps", []))
        next_res = list(res.get("next", []))
        closing_msg = res.get("closing_message")

        if not summary or not strengths_res or not gaps_res or not next_res:
            raise ValueError("Incomplete feedback output from Gemini")

        if not closing_msg:
            closing_msg = f"Thank you so much for your time and thoughtful responses today, {cand_name}! That concludes our technical interview session."

        # Extract fluency analysis from the same Gemini response (folded into one call)
        fluency_score = res.get("fluency_score")
        fluency_notes = res.get("fluency_notes")
        if fluency_score is not None:
            try:
                fluency_score = max(0, min(100, int(round(float(fluency_score)))))
            except (ValueError, TypeError):
                fluency_score = None
        if not fluency_notes or not isinstance(fluency_notes, str):
            fluency_notes = None

        feedback_data = {
            "summary": summary,
            "strengths": strengths_res,
            "gaps": gaps_res,
            "next": next_res,
            "closing_message": closing_msg,
            "overall_percentage": overall_percentage,
            "category_breakdown": category_breakdown,
        }
        if fluency_score is not None:
            feedback_data["fluency_score"] = fluency_score
        if fluency_notes:
            feedback_data["fluency_notes"] = fluency_notes

        logger.info("[generate_feedback] SUCCESS — Gemini returned grounded feedback for session=%s", session_id)
    except Exception as exc:
        logger.error("[generate_feedback] Gemini API error for session=%s: %s", session_id, exc)
        raise GeminiError(f"Gemini API call failed during feedback generation: {exc}") from exc

    return {
        "feedback": feedback_data,
        "reply": closing_msg,
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
                model_used=state.get("model_used"),
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
            closing_message=feedback.get("closing_message"),
            overall_score=feedback.get("overall_percentage"),
        )
        repository.update_session(session_id=session_id, status="completed")
    return {}
