from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from entities.database import get_db
from .service import get_scores_by_user, create_score, calculate_user_module_scores
from .schemas import ScoreResponse, ScoreCreate, ModuleScoreSummary
from typing import List

router = APIRouter(prefix="/scores", tags=["Score Engine"])

@router.get("/{user_id}", response_model=List[ScoreResponse])
def get_user_scores(user_id: int, db: Session = Depends(get_db)):
    return get_scores_by_user(db, user_id)

@router.get("/{user_id}/summary", response_model=List[ModuleScoreSummary])
def get_user_score_summary(user_id: int, db: Session = Depends(get_db)):
    return calculate_user_module_scores(db, user_id)
