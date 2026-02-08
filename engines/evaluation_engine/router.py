from fastapi import APIRouter, HTTPException
from .service import evaluate_answer
from .schemas import EvaluationRequest, EvaluationResponse

router = APIRouter(prefix="/evaluation", tags=["Evaluation Engine"])

@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate_submission(request: EvaluationRequest):
    try:
        return evaluate_answer(request)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
