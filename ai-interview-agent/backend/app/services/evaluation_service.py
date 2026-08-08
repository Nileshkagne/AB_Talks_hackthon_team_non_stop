from pathlib import Path
from typing import Any, Dict, Union
from app.llm import gemini
from app.llm.gemini import GeminiError
from app.services import curriculum_service

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "prompts"


def _get_evaluator_system_prompt() -> str:
    path = _PROMPTS_DIR / "evaluator.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "You are a technical evaluator. Output JSON matching the required schema."


def _build_dynamic_fallback_evaluation(
    answer: str, objectives: list, tools: list
) -> Dict[str, Any]:
    """
    Dynamically derives evaluation scores and missing concepts directly from
    the candidate's answer text and active topic curriculum requirements.
    """
    answer_text = (answer or "").strip()
    if not answer_text:
        return {
            "correctness": 2.0,
            "technical_depth": 1.0,
            "reasoning": 1.0,
            "practicality": 1.0,
            "communication": 1.0,
            "overall_score": 1.5,
            "confidence": 0.9,
            "missing_concepts": [str(obj) for obj in objectives[:2]] if objectives else ["core concepts"],
            "follow_up_needed": True,
            "evaluation_summary": "Candidate provided no response to the technical question.",
        }

    # Analyze answer content against expected tools and objectives
    answer_lower = answer_text.lower()
    matched_tools = [t for t in tools if t.lower() in answer_lower]
    missing_tools = [t for t in tools if t.lower() not in answer_lower]

    word_count = len(answer_text.split())
    depth_score = min(9.5, max(4.0, 4.0 + (word_count / 12.0) + (len(matched_tools) * 1.5)))
    correctness_score = min(9.5, max(4.0, 5.0 + (len(matched_tools) * 1.5)))

    overall = round(0.35 * correctness_score + 0.25 * depth_score + 0.20 * 6.5 + 0.10 * 6.0 + 0.10 * (7.0 if word_count > 10 else 4.0), 2)

    return {
        "correctness": round(correctness_score, 1),
        "technical_depth": round(depth_score, 1),
        "reasoning": 6.5,
        "practicality": 6.0,
        "communication": 7.0 if word_count > 10 else 4.0,
        "overall_score": overall,
        "confidence": 0.75,
        "missing_concepts": missing_tools[:2] if missing_tools else [],
        "follow_up_needed": overall < 6.5,
        "evaluation_summary": f"Candidate response ({word_count} words) evaluated against topic requirements.",
    }


def evaluate_answer(
    question: str,
    answer: str,
    curriculum_day: Union[dict, int],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluates candidate's answer strictly against curriculum day objectives using Gemini.
    Uses dynamic answer-derived fallback evaluation on LLM API failure.
    """
    if isinstance(curriculum_day, int):
        day_details = curriculum_service.get_day(curriculum_day) or {}
    else:
        day_details = curriculum_day or {}

    day_num = day_details.get("day", 1)
    day_title = day_details.get("title", "Core AI Concepts")
    objectives = day_details.get("objectives", [])
    tools = day_details.get("tools", [])

    user_prompt = f"""EVALUATION CONTEXT:
- Candidate Role: {profile.get('role', 'AI Engineer')} ({profile.get('experience', 3)} years experience)
- Curriculum Topic: Day {day_num} - {day_title}
- Learning Objectives: {', '.join(objectives)}
- Expected Tools: {', '.join(tools)}

INTERVIEW QUESTION ASKED:
{question}

CANDIDATE RESPONSE TO EVALUATE:
{answer or "(No response provided)"}

Task: Evaluate the candidate's response strictly against the curriculum objectives and tools above.
Calculate overall_score = (0.35 * correctness) + (0.25 * technical_depth) + (0.20 * reasoning) + (0.10 * practicality) + (0.10 * communication).
Respond ONLY with JSON matching the required schema."""

    system_prompt = _get_evaluator_system_prompt()

    try:
        res = gemini.generate_structured(user_prompt, system_instruction=system_prompt)

        c = float(res.get("correctness", 6.0))
        td = float(res.get("technical_depth", 6.0))
        r = float(res.get("reasoning", 6.0))
        p = float(res.get("practicality", 6.0))
        cm = float(res.get("communication", 6.0))

        calculated_score = round(0.35 * c + 0.25 * td + 0.20 * r + 0.10 * p + 0.10 * cm, 2)
        overall_score = float(res.get("overall_score", calculated_score))

        return {
            "correctness": c,
            "technical_depth": td,
            "reasoning": r,
            "practicality": p,
            "communication": cm,
            "overall_score": overall_score,
            "confidence": float(res.get("confidence", 0.9)),
            "missing_concepts": list(res.get("missing_concepts", [])),
            "follow_up_needed": bool(res.get("follow_up_needed", overall_score < 6.5)),
            "evaluation_summary": str(res.get("evaluation_summary", "Evaluation complete.")),
        }
    except Exception as exc:
        raise GeminiError(f"Gemini evaluation failed: {exc}") from exc
