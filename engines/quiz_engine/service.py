"""
Quiz lifecycle: start (select questions, create session), submit (record attempt, evaluate),
result (aggregate, strengths/weak areas). Uses selection, evaluation, and aggregation modules.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from entities.models import Question, QuizSession, QuestionAttempt, EvaluationResult
from .constants import (
    QUESTION_TYPE_MCQ,
    QUESTION_TYPE_DOUBLE_MCQ,
    QUESTION_TYPE_SUBJECTIVE,
    DEFAULT_CONCEPTUAL_DEPTH,
    DEFAULT_REASONING_QUALITY,
    DEFAULT_CONFIDENCE_ALIGNMENT,
)
from .selection import select_questions_for_session
from .evaluation import evaluate_objective_attempt
from .understanding_pipeline import run_understanding_evaluation_pipeline
from .aggregation import aggregate_results, infer_strengths_weak_areas
from .schemas import (
    StartQuizResponse,
    QuizQuestionOut,
    SubmitAnswerResponse,
    QuizResultResponse,
    PerQuestionResult,
    AggregatedScores,
    CreateQuestionRequest,
    CreateQuestionResponse,
)
from .ai_evaluation import get_module_context_for_evaluation

# Integration with Evaluation Engine
from engines.evaluation_engine.service import evaluate_answer
from engines.evaluation_engine.schemas import EvaluationRequest


def start_quiz(db: Session, user_id: int, module_id: UUID) -> StartQuizResponse:
    """
    Start or resume a quiz session:
    - If an incomplete session exists for this user+module, resume it
    - Otherwise, create a new session with selected questions
    - Only returns questions that haven't been attempted yet in the session
    """
    # Check for existing incomplete session (completed_at is NULL)
    existing_session = db.query(QuizSession).filter(
        QuizSession.user_id == user_id,
        QuizSession.module_id == module_id,
        QuizSession.completed_at.is_(None)
    ).order_by(QuizSession.started_at.desc()).first()
    
    if existing_session:
        # Resume existing session
        session = existing_session
        question_ids = [UUID(x) if isinstance(x, str) else x for x in (session.question_ids or [])]
    else:
        # Create new session
        question_ids = select_questions_for_session(db, module_id)
        if not question_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No questions found for this module.",
            )
        session = QuizSession(
            user_id=user_id,
            module_id=module_id,
            question_ids=[str(q) for q in question_ids],
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Get already attempted question IDs for this session
    attempted_question_ids = set(
        row[0] for row in db.query(QuestionAttempt.question_id)
        .filter(QuestionAttempt.quiz_session_id == session.id)
        .all()
    )

    # Filter out attempted questions
    unattempted_question_ids = [qid for qid in question_ids if qid not in attempted_question_ids]

    questions = (
        db.query(Question)
        .filter(Question.id.in_(unattempted_question_ids))
        .all()
    )
    # Preserve order of question_ids
    by_id = {q.id: q for q in questions}
    ordered = [by_id[qid] for qid in unattempted_question_ids if qid in by_id]
    question_outs = [
        QuizQuestionOut(
            id=q.id,
            type=q.question_type,
            question_text=q.question_text,
            options=q.options if q.question_type in (QUESTION_TYPE_MCQ, QUESTION_TYPE_DOUBLE_MCQ) else None,
        )
        for q in ordered
    ]
    return StartQuizResponse(
        quiz_session_id=session.id,
        questions=question_outs,
    )


def submit_answer(
    db: Session,
    user_id: int,
    quiz_session_id: UUID,
    question_id: UUID,
    user_answer: str,
    confidence: float,
) -> SubmitAnswerResponse:
    """
    Record attempt; evaluate MCQ/DOUBLE_MCQ immediately; SUBJECTIVE via AI (with fallback).
    """
    session = db.query(QuizSession).filter(
        QuizSession.id == quiz_session_id,
        QuizSession.user_id == user_id,
    ).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz session not found or access denied.",
        )
    qids = [UUID(x) if isinstance(x, str) else x for x in (session.question_ids or [])]
    if question_id not in qids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question not part of this quiz session.",
        )
    # One attempt per question per session
    existing = db.query(QuestionAttempt).filter(
        QuestionAttempt.quiz_session_id == quiz_session_id,
        QuestionAttempt.question_id == question_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answer already submitted for this question.",
        )

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    attempt = QuestionAttempt(
        quiz_session_id=quiz_session_id,
        question_id=question_id,
        user_answer=user_answer,
        confidence=Decimal(str(confidence)),
    )
    db.add(attempt)
    db.flush()

    evaluated = False
    if question.question_type in (QUESTION_TYPE_MCQ, QUESTION_TYPE_DOUBLE_MCQ):
        evaluate_objective_attempt(db, attempt, question)
        attempt.evaluated_at = datetime.now(timezone.utc)
        evaluated = True
    elif question.question_type == QUESTION_TYPE_SUBJECTIVE:
        if run_understanding_evaluation_pipeline(db, attempt, question):
            attempt.evaluated_at = datetime.now(timezone.utc)
            evaluated = True
        else:
            # Fail gracefully: store under-score default so result endpoint still works
            attempt.correctness_score = Decimal("0")
            default = EvaluationResult(
                attempt_id=attempt.id,
                correctness=Decimal("0"),
                conceptual_depth=Decimal(str(DEFAULT_CONCEPTUAL_DEPTH)),
                reasoning_quality=Decimal(str(DEFAULT_REASONING_QUALITY)),
                confidence_alignment=Decimal(str(DEFAULT_CONFIDENCE_ALIGNMENT)),
                misconceptions=[],
                feedback="Evaluation could not be completed.",
            )
            db.add(default)
            attempt.evaluated_at = datetime.now(timezone.utc)
            evaluated = True
    
    # Mark quiz session complete when all questions have been answered
    attempt_count = db.query(QuestionAttempt).filter(QuestionAttempt.quiz_session_id == quiz_session_id).count()
    if attempt_count >= len(qids):
        session.completed_at = datetime.now(timezone.utc)
    
    db.commit()

    # Centralized Scoring: Send result to Evaluation Engine for cross-engine score aggregation
    # Fetch context to provide to the evaluation engine
    module_context_str = get_module_context_for_evaluation(db, question.module_id)
    
    eval_req = EvaluationRequest(
        user_id=user_id,
        module_content_id=question.module_id,
        module_context={"content": module_context_str} if module_context_str else None,
        question_context={
            "question_text": question.question_text,
            "question_type": question.question_type,
            "options": question.options
        },
        user_answer=user_answer
    )
    
    try:
        # This will re-evaluate with Gemini (as requested) and save the score centrally in Score Engine
        evaluate_answer(db, eval_req)
    except Exception:
        # We don't want the quiz submission to fail if the central scoring fails
        pass

    return SubmitAnswerResponse(
        attempt_id=attempt.id,
        evaluated=evaluated,
        message="Answer recorded and score synced.",
    )


def get_quiz_result(db: Session, user_id: int, quiz_session_id: UUID) -> QuizResultResponse:
    """Build per-question results, aggregated scores, strengths and weak areas."""
    session = db.query(QuizSession).filter(
        QuizSession.id == quiz_session_id,
        QuizSession.user_id == user_id,
    ).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz session not found or access denied.",
        )

    attempts = (
        db.query(QuestionAttempt, Question, EvaluationResult)
        .join(Question, QuestionAttempt.question_id == Question.id)
        .outerjoin(EvaluationResult, EvaluationResult.attempt_id == QuestionAttempt.id)
        .filter(QuestionAttempt.quiz_session_id == quiz_session_id)
        .all()
    )

    total_q = len(session.question_ids or [])
    total_a = len(attempts)
    is_complete = total_a >= total_q

    if not is_complete:
        return QuizResultResponse(
            total_questions=total_q,
            total_attempted=total_a,
            is_complete=False,
            questions_needed=total_q - total_a,
        )

    per_question: list[PerQuestionResult] = []
    total_correctness = 0.0
    for attempt, question, result in attempts:
        if not result:
            per_question.append(
                PerQuestionResult(
                    question_id=question.id,
                    question_type=question.question_type,
                    correctness=0.0,
                    conceptual_depth=None,
                    reasoning_quality=None,
                    confidence_alignment=None,
                    misconceptions=None,
                    feedback=None,
                )
            )
            continue
        
        c_val = float(result.correctness)
        total_correctness += c_val
        per_question.append(
            PerQuestionResult(
                question_id=question.id,
                question_type=question.question_type,
                correctness=c_val,
                conceptual_depth=float(result.conceptual_depth) if result.conceptual_depth is not None else None,
                reasoning_quality=float(result.reasoning_quality) if result.reasoning_quality is not None else None,
                confidence_alignment=float(result.confidence_alignment) if result.confidence_alignment is not None else None,
                misconceptions=result.misconceptions,
                feedback=result.feedback,
            )
        )

    aggregated = aggregate_results(per_question)
    strengths, weak_areas = infer_strengths_weak_areas(per_question, aggregated.composite)
    
    # Calculate percentage
    avg_correctness = total_correctness / total_q if total_q > 0 else 0.0
    percentage = round(avg_correctness * 100, 2)

    return QuizResultResponse(
        total_questions=total_q,
        total_attempted=total_a,
        is_complete=True,
        correctness_percentage=percentage,
        per_question=per_question,
        aggregated_scores=aggregated,
        strengths=strengths,
        weak_areas=weak_areas,
    )


def create_question(db: Session, body: CreateQuestionRequest) -> CreateQuestionResponse:
    """Add a question to the question bank. Validates question_type and required fields."""
    allowed_types = (QUESTION_TYPE_MCQ, QUESTION_TYPE_DOUBLE_MCQ, QUESTION_TYPE_SUBJECTIVE)
    if body.question_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"question_type must be one of: {', '.join(allowed_types)}",
        )
    if body.question_type in (QUESTION_TYPE_MCQ, QUESTION_TYPE_DOUBLE_MCQ) and not body.options:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="options are required for MCQ and DOUBLE_MCQ",
        )
    correct_answer = None if body.question_type == QUESTION_TYPE_SUBJECTIVE else body.correct_answer

    q = Question(
        module_id=body.module_id,
        question_type=body.question_type,
        difficulty=body.difficulty,
        question_text=body.question_text,
        options=body.options,
        correct_answer=correct_answer,
        evaluation_rubric=body.evaluation_rubric,
        concept_tags=body.concept_tags,
        weight=Decimal(str(body.weight)),
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return CreateQuestionResponse(question_id=q.id, message="Question added to question bank.")
