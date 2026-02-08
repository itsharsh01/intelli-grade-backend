"""Progress API: module completion and module understanding."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from entities.database import get_db
from core.security import get_current_user_id
from sqlalchemy.orm import Session

from .service import mark_module_complete, get_module_status, get_module_understanding
from .schemas import ModuleCompleteResponse, ModuleStatusResponse, ModuleUnderstandingResponse

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.post("/module/{module_id}/complete", response_model=ModuleCompleteResponse)
def complete_module(
    module_id: UUID,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark this module as complete for the current user. Unlocks the quiz for this module."""
    return mark_module_complete(db, user_id=user_id, module_id=module_id)


@router.get("/module/{module_id}/status", response_model=ModuleStatusResponse)
def module_status(
    module_id: UUID,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get whether the user has marked this module as complete."""
    return get_module_status(db, user_id=user_id, module_id=module_id)


@router.get("/module/{module_id}/understanding", response_model=ModuleUnderstandingResponse)
def module_understanding(
    module_id: UUID,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get the user's understanding score for this module (from latest completed quiz)."""
    result = get_module_understanding(db, user_id=user_id, module_id=module_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed quiz found for this module.",
        )
    return result
