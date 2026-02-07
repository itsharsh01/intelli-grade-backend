from fastapi import APIRouter
from .service import get_question_service

router = APIRouter(prefix="/questions", tags=["Question Engine"])

@router.get("/")
def get_questions():
    return get_question_service()
