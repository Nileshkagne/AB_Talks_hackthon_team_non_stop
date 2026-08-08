from typing import Any, Dict, List, Optional, TypedDict


class InterviewState(TypedDict, total=False):
    session_id: str
    candidate: Dict[str, Any]
    profile: Dict[str, Any]
    question_count: int
    follow_up_count: int
    covered_days: List[int]
    current_day: Optional[int]
    current_topic: Optional[str]
    difficulty: str
    last_question: Optional[str]
    last_question_type: Optional[str]
    last_answer: Optional[str]
    last_evaluation: Optional[Dict[str, Any]]
    strengths: List[str]
    weaknesses: List[str]
    done: bool
    reply: Optional[str]
    feedback: Optional[Dict[str, Any]]
