from typing import Any, Dict
from fastapi import APIRouter, Response
from app.services import interview_service

router = APIRouter()


@router.post("/interview")
def interview_turn(payload: Dict[str, Any], response: Response):
    result, status_code = interview_service.handle_turn(payload)
    response.status_code = status_code
    return result
