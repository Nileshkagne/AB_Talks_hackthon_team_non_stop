from typing import Any, Callable, Dict, List, Literal, Set, Union

DIFFICULTY_LEVELS = ["foundation", "intermediate", "advanced", "expert"]

MIN_QUESTIONS = 8
MAX_QUESTIONS = 12
MIN_CURRICULUM_DAYS = 4
MAX_FOLLOWUPS_PER_TOPIC = 2


def bump_up(difficulty: str) -> str:
    """Bumps difficulty up one level, clamped at expert."""
    if difficulty in DIFFICULTY_LEVELS:
        idx = DIFFICULTY_LEVELS.index(difficulty)
        return DIFFICULTY_LEVELS[min(idx + 1, len(DIFFICULTY_LEVELS) - 1)]
    return "intermediate"


def bump_down(difficulty: str) -> str:
    """Bumps difficulty down one level, clamped at foundation."""
    if difficulty in DIFFICULTY_LEVELS:
        idx = DIFFICULTY_LEVELS.index(difficulty)
        return DIFFICULTY_LEVELS[max(idx - 1, 0)]
    return "intermediate"


def dedupe(items: List[str]) -> List[str]:
    """Deduplicates a list of strings while preserving insertion order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


ROLE_TOPIC_WEIGHTS: Dict[str, Dict[str, float]] = {
    "AI Engineer": {
        "Embeddings & Vector Search": 0.9,
        "LLM Core, Prompting & Fine-Tuning": 0.95,
        "Chatbot Application Build": 0.85,
        "Agentic AI & MCP": 1.0,
        "Production & Capstone": 0.9,
    },
    "Senior Data Engineer": {
        "Data Foundations": 0.95,
        "Embeddings & Vector Search": 0.9,
        "Evaluation, Security & Deployment": 0.85,
        "Production & Capstone": 0.8,
    },
    "Backend Software Engineer": {
        "Environment & Tooling": 0.8,
        "Chatbot Application Build": 0.9,
        "Evaluation, Security & Deployment": 0.85,
        "Production & Capstone": 0.85,
    },
    "DevOps Engineer": {
        "Environment & Tooling": 0.95,
        "Evaluation, Security & Deployment": 1.0,
        "Production & Capstone": 0.9,
    },
    "IT Support Specialist": {
        "Environment & Tooling": 0.9,
        "Evaluation, Security & Deployment": 0.8,
    },
    "Business Analyst": {
        "Data Foundations": 0.85,
        "Chatbot Application Build": 0.8,
    },
    "Software Engineer": {
        "Environment & Tooling": 0.8,
        "Chatbot Application Build": 0.85,
        "Production & Capstone": 0.85,
    },
    "Principal Architect": {
        "Agentic AI & MCP": 0.95,
        "Production & Capstone": 1.0,
        "Evaluation, Security & Deployment": 0.9,
    },
}


def score_day(
    day: dict,
    profile: dict,
    covered_days: Union[Set[int], List[int]],
    curriculum_module_lookup: Callable[[int], str],
) -> float:
    """
    Scores a curriculum day based on role relevance, candidate weak/skipped signals,
    coverage need, and an already-covered penalty.
    """
    covered_set = set(covered_days)
    module = curriculum_module_lookup(day["day"])
    role_relevance = ROLE_TOPIC_WEIGHTS.get(profile.get("role", ""), {}).get(module, 0.5)

    day_title = day.get("title", "")
    weak_topics = profile.get("weak_topics", [])
    skipped_topics = profile.get("skipped_topics", [])

    if day_title in weak_topics:
        weakness = 1.0
    elif day_title in skipped_topics:
        weakness = 0.6
    else:
        weakness = 0.2

    coverage_need = 1.0 if len(covered_set) < 4 else 0.4
    already_covered_penalty = 1.0 if day["day"] in covered_set else 0.0

    return (0.35 * role_relevance + 0.40 * weakness + 0.25 * coverage_need) - already_covered_penalty


def select_best_topic(
    profile: dict,
    curriculum_days: List[dict],
    covered_days: Union[Set[int], List[int]],
    curriculum_module_lookup: Callable[[int], str],
) -> dict:
    """
    Selects the highest-scoring uncovered curriculum day, breaking ties by lowest day number.
    """
    covered_set = set(covered_days)
    sorted_days = sorted(curriculum_days, key=lambda d: d["day"])

    best_day = None
    best_score = -999.0

    for day in sorted_days:
        s = score_day(day, profile, covered_set, curriculum_module_lookup)
        if s > best_score:
            best_score = s
            best_day = day

    return best_day if best_day else sorted_days[0]


def decide_next_action(state: Dict[str, Any]) -> Literal["follow_up", "new_topic", "finish"]:
    """
    Pure deterministic function deciding the next action in the interview workflow.
    """
    q_count = state.get("question_count", 0)
    covered_days = state.get("covered_days", [])
    last_eval = state.get("last_evaluation") or {}
    follow_up_needed = bool(last_eval.get("follow_up_needed", False))
    follow_up_count = state.get("follow_up_count", 0)

    if q_count >= MAX_QUESTIONS:
        return "finish"
    if q_count >= MIN_QUESTIONS and len(covered_days) >= MIN_CURRICULUM_DAYS:
        return "finish"
    if q_count >= MIN_QUESTIONS and len(covered_days) < MIN_CURRICULUM_DAYS:
        return "new_topic"
    if follow_up_needed and follow_up_count < MAX_FOLLOWUPS_PER_TOPIC:
        return "follow_up"
    return "new_topic"
