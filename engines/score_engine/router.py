from fastapi import APIRouter
from .service import get_score_service

router = APIRouter(prefix="/scores", tags=["Score Engine"])

@router.get("/")
def get_scores():
    return get_score_service()
