from pathlib import Path
from typing import Any, Dict, Union
from app.llm import gemini
from app.services import curriculum_service

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "prompts"

DEFAULT_EVALUATION: Dict[str, Any] = {
    "correctness": 6.0,
    "technical_depth": 6.0,
    "reasoning": 6.0,
    "practicality": 6.0,
    "communication": 6.0,
    "overall_score": 6.0,
    "confidence": 0.5,
    "missing_concepts": [],
    "follow_up_needed": False,
    "evaluation_summary": "Evaluation unavailable, defaulting to pass-through.",
}


def _get_evaluator_system_prompt() -> str:
    path = _PROMPTS_DIR / "evaluator.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "You are a technical evaluator. Output JSON matching the required schema."


def evaluate_answer(
    question: str,
    answer: str,
    curriculum_day: Union[dict, int],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluates candidate's answer against curriculum day objectives using Gemini.
    Returns conservative default on failure.
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
    except Exception:
        return dict(DEFAULT_EVALUATION)
