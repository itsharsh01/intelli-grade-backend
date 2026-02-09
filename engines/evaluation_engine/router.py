from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from entities.database import get_db
from .service import evaluate_answer
from .schemas import EvaluationRequest, EvaluationResponse

router = APIRouter(prefix="/evaluation", tags=["Evaluation Engine"])

@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate_submission(request: EvaluationRequest, db: Session = Depends(get_db)):
    try:
        return evaluate_answer(db, request)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
