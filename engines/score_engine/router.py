from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from entities.database import get_db
from .service import get_scores_by_user, create_score, calculate_user_course_scores
from .schemas import ScoreResponse, ScoreCreate, CourseScoreSummary
from typing import List

router = APIRouter(prefix="/scores", tags=["Score Engine"])

@router.get("/{user_id}", response_model=List[ScoreResponse])
def get_user_scores(user_id: int, db: Session = Depends(get_db)):
    return get_scores_by_user(db, user_id)

@router.get("/{user_id}/summary", response_model=List[CourseScoreSummary])
def get_user_score_summary(user_id: int, db: Session = Depends(get_db)):
    return calculate_user_course_scores(db, user_id)
