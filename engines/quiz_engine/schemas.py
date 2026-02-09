"""
Pydantic schemas for quiz API. No auth or course delivery; only quiz lifecycle and scoring.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field


# ----- Start quiz -----


class StartQuizRequest(BaseModel):
    module_id: UUID
    user_id: int  # Added to bypass auth dependency for testing


class QuizQuestionOut(BaseModel):
    """One question in the quiz (no correct answer or rubric exposed)."""
    id: UUID
    type: str  # MCQ | DOUBLE_MCQ | SUBJECTIVE
    question_text: str
    options: list | None = None  # Only for MCQ types

    class Config:
        from_attributes = True


class StartQuizResponse(BaseModel):
    quiz_session_id: UUID
    questions: list[QuizQuestionOut]


# ----- Submit answer -----


class SubmitAnswerRequest(BaseModel):
    quiz_session_id: UUID
    question_id: UUID
    user_answer: str  # For MCQ can be "A" or JSON array for DOUBLE_MCQ
    confidence: float = Field(ge=0.0, le=10.0)
    user_id: int  # Added for consistency


class SubmitAnswerResponse(BaseModel):
    """After evaluation (sync for objective, async possible for subjective)."""
    attempt_id: UUID
    evaluated: bool  # True when result is ready (always true for objective)
    message: str = "Answer recorded."


# ----- Result -----


class PerQuestionResult(BaseModel):
    question_id: UUID
    question_type: str
    correctness: float
    conceptual_depth: float | None = None
    reasoning_quality: float | None = None
    confidence_alignment: float | None = None
    misconceptions: list[str] | None = None
    feedback: str | None = None


class AggregatedScores(BaseModel):
    correctness: float
    conceptual_depth: float
    reasoning_quality: float
    confidence_alignment: float
    composite: float  # Weighted composite 0–1


class QuizResultResponse(BaseModel):
    total_questions: int
    total_attempted: int
    is_complete: bool
    questions_needed: int = 0
    correctness_percentage: float | None = None
    per_question: list[PerQuestionResult] | None = None
    aggregated_scores: AggregatedScores | None = None
    strengths: list[str] | None = None
    weak_areas: list[str] | None = None


# ----- Create question (question bank) -----


class CreateQuestionRequest(BaseModel):
    """Add a question to the question bank. Requires auth."""
    module_id: UUID
    question_type: str  # MCQ | DOUBLE_MCQ | SUBJECTIVE
    difficulty: str = "medium"  # easy | medium | hard
    question_text: str
    options: list | None = None  # For MCQ types: list of option strings
    correct_answer: str | list | None = None  # Single value for MCQ, list for DOUBLE_MCQ
    evaluation_rubric: dict | None = None  # For SUBJECTIVE only
    concept_tags: list[str] | None = None
    weight: float = 1.0


class CreateQuestionResponse(BaseModel):
    question_id: UUID
    message: str = "Question added to question bank."


# ----- Internal / AI evaluation -----


class SubjectiveEvaluationOutput(BaseModel):
    """Strict AI output schema; must match exactly for parsing."""
    correctness: float = Field(ge=0.0, le=1.0)
    conceptual_depth: float = Field(ge=0.0, le=1.0)
    reasoning_quality: float = Field(ge=0.0, le=1.0)
    confidence_alignment: float = Field(ge=0.0, le=1.0)
    misconceptions: list[str] = Field(default_factory=list)
    feedback: str = ""
