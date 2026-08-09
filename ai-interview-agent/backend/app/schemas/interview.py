from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class InterviewStartRequest(BaseModel):
    sessionId: str
    candidate: Dict[str, Any]


class InterviewTurnRequest(BaseModel):
    sessionId: str
    message: str


class FeedbackSchema(BaseModel):
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]
    closing_message: Optional[str] = None


class InterviewResponse(BaseModel):
    reply: str
    done: bool = False
    feedback: Optional[FeedbackSchema] = None
