"""Progress service: module completion and module understanding score."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from entities.models import UserModuleCompletion, QuizSession

from engines.quiz_engine.service import get_quiz_result
from engines.quiz_engine.schemas import QuizResultResponse

from .schemas import ModuleCompleteResponse, ModuleStatusResponse, ModuleUnderstandingResponse

def mark_module_complete(db: Session, user_id: int, module_id: UUID) -> ModuleCompleteResponse:
    """Mark a module as complete for the user (upsert). Unlocks quiz."""
    now = datetime.now(timezone.utc)
    row = db.query(UserModuleCompletion).filter(
        UserModuleCompletion.user_id == user_id,
        UserModuleCompletion.module_id == module_id,
    ).first()
    if row:
        row.completed_at = now
    else:
        row = UserModuleCompletion(user_id=user_id, module_id=module_id, completed_at=now)
        db.add(row)
    db.commit()
    db.refresh(row)
    return ModuleCompleteResponse(
        module_id=row.module_id,
        completed_at=row.completed_at.isoformat(),
        user_id=row.user_id
    )


def get_module_status(db: Session, user_id: int, module_id: UUID) -> ModuleStatusResponse:
    """Return whether the user has marked this module as complete."""
    row = db.query(UserModuleCompletion).filter(
        UserModuleCompletion.user_id == user_id,
        UserModuleCompletion.module_id == module_id,
    ).first()
    if not row:
        return ModuleStatusResponse(module_id=module_id, completed=False, completed_at=None, user_id=user_id)
    return ModuleStatusResponse(
        module_id=module_id,
        completed=True,
        completed_at=row.completed_at.isoformat() if row.completed_at else None,
        user_id=user_id
    )


def get_module_understanding(db: Session, user_id: int, module_id: UUID) -> ModuleUnderstandingResponse | None:
    """
    Return the latest quiz result for this user+module (module understanding score).
    Uses the most recent quiz session that has completed_at set (quiz was finished).
    """
    session = (
        db.query(QuizSession)
        .filter(
            QuizSession.user_id == user_id,
            QuizSession.module_id == module_id,
            QuizSession.completed_at.isnot(None),
        )
        .order_by(QuizSession.completed_at.desc())
        .first()
    )
    if not session:
        return None
    result: QuizResultResponse = get_quiz_result(db, user_id=user_id, quiz_session_id=session.id)
    agg = result.aggregated_scores
    return ModuleUnderstandingResponse(
        module_id=module_id,
        quiz_session_id=session.id,
        composite=agg.composite,
        correctness=agg.correctness,
        conceptual_depth=agg.conceptual_depth,
        reasoning_quality=agg.reasoning_quality,
        confidence_alignment=agg.confidence_alignment,
        strengths=result.strengths,
        weak_areas=result.weak_areas,
    )
