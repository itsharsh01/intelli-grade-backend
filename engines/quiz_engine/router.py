"""
Quiz API: start session, submit answer, get result. Auth via Bearer token (user id).
"""
from uuid import UUID

from fastapi import APIRouter, Depends

from entities.database import get_db
from core.security import get_current_user_id
from sqlalchemy.orm import Session

from .schemas import (
    StartQuizRequest,
    StartQuizResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    QuizResultResponse,
    CreateQuestionRequest,
    CreateQuestionResponse,
)
from .service import start_quiz, submit_answer, get_quiz_result, create_question

router = APIRouter(prefix="/quiz", tags=["Quiz & Assessment"])


@router.post("/start", response_model=StartQuizResponse)
def start(
    body: StartQuizRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Start a new quiz for the given module. Questions are selected by the backend
    (module size and 40/30/30 distribution). Questions are fixed for this session.
    """
    return start_quiz(db, user_id=user_id, module_id=body.module_id)


@router.post("/submit", response_model=SubmitAnswerResponse)
def submit(
    body: SubmitAnswerRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Submit an answer for one question in a quiz session. MCQ/DOUBLE_MCQ are
    evaluated immediately; SUBJECTIVE is evaluated via AI (with fallback).
    """
    return submit_answer(
        db,
        user_id=user_id,
        quiz_session_id=body.quiz_session_id,
        question_id=body.question_id,
        user_answer=body.user_answer,
        confidence=body.confidence,
    )


@router.get("/result/{quiz_session_id}", response_model=QuizResultResponse)
def result(
    quiz_session_id: UUID,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get full result for a quiz session: per-question scores, aggregated
    multi-dimensional scores, strengths and weak areas.
    """
    return get_quiz_result(db, user_id=user_id, quiz_session_id=quiz_session_id)


@router.post("/questions", response_model=CreateQuestionResponse)
def create_question_endpoint(
    body: CreateQuestionRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Add a question to the question bank for a module. Requires auth.
    Use module_id from your course outline (e.g. Singly Linked List).
    """
    return create_question(db, body)
