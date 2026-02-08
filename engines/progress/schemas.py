"""Schemas for progress/completion and module understanding."""
from uuid import UUID
from pydantic import BaseModel


class ModuleCompleteResponse(BaseModel):
    module_id: UUID
    completed_at: str  # ISO datetime


class ModuleStatusResponse(BaseModel):
    module_id: UUID
    completed: bool
    completed_at: str | None = None


class ModuleUnderstandingResponse(BaseModel):
    module_id: UUID
    quiz_session_id: UUID
    composite: float
    correctness: float
    conceptual_depth: float
    reasoning_quality: float
    confidence_alignment: float
    strengths: list[str]
    weak_areas: list[str]
