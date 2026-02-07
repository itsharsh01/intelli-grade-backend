from fastapi import APIRouter
from .service import get_evaluation_service

router = APIRouter(prefix="/evaluation", tags=["Evaluation Engine"])

@router.get("/")
def get_evaluation():
    return get_evaluation_service()
