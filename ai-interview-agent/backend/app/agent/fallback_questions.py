from typing import Dict, Optional


def generate_dynamic_fallback(
    last_answer: Optional[str],
    current_topic: str,
    current_day: int,
    difficulty: str = "intermediate",
    target_type: str = "conceptual",
) -> Dict[str, str]:
    """
    Generates a dynamic fallback question derived directly from the candidate's
    latest answer and current curriculum topic.
    """
    answer_text = (last_answer or "").strip()

    if answer_text:
        # Extract meaningful terms from candidate's actual answer
        words = [w.strip(".,!?:;\"'()") for w in answer_text.split() if len(w) > 3]
        candidate_phrase = f"'{' '.join(words[:4])}'" if words else "your response"

        question = (
            f"Reflecting on your point about {candidate_phrase} for {current_topic} (Day {current_day}), "
            f"how would you handle edge cases or performance bottlenecks with that approach?"
        )
    else:
        question = (
            f"In your work on Day {current_day} ({current_topic}), what specific architecture "
            f"or implementation trade-offs did you encounter?"
        )

    return {
        "question": question,
        "type": target_type,
    }
