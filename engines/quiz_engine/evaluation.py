"""
Evaluation: deterministic for MCQ/DOUBLE_MCQ; AI for SUBJECTIVE only.
Prefer under-scoring when in doubt. No teaching, hints, or answer revelation.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from entities.models import Question, QuestionAttempt, EvaluationResult
from .constants import (
    QUESTION_TYPE_MCQ,
    QUESTION_TYPE_DOUBLE_MCQ,
    QUESTION_TYPE_SUBJECTIVE,
    DEFAULT_CONCEPTUAL_DEPTH,
    DEFAULT_REASONING_QUALITY,
    DEFAULT_CONFIDENCE_ALIGNMENT,
    DOUBLE_MCQ_FULL_CREDIT_IF_EXACT,
    DOUBLE_MCQ_PARTIAL_CREDIT_RATE,
)


def _normalize_option(value: str | list) -> str | list:
    """Normalize for comparison: strip, lower for single string; sort for list."""
    if isinstance(value, list):
        return sorted(str(x).strip().lower() for x in value)
    return str(value).strip().lower() if value is not None else ""


def evaluate_mcq(user_answer: str, correct_answer: object) -> Decimal:
    """
    Single correct: 1 if match (normalized), else 0. Prefer under-scoring.
    """
    if correct_answer is None:
        return Decimal("0")
    correct = _normalize_option(correct_answer)
    user = _normalize_option(user_answer)
    return Decimal("1") if user == correct else Decimal("0")


def evaluate_double_mcq(user_answer: str, correct_answer: object) -> Decimal:
    """
    Multiple correct: partial credit. Correct answer is list of correct options.
    - Exact match (same set) → 1.0
    - Else: partial by correct selected / total correct, with penalty for wrong selected.
    Prefer under-scoring.
    """
    if correct_answer is None:
        return Decimal("0")
    if isinstance(correct_answer, list):
        correct_set = set(_normalize_option(x) for x in correct_answer)
    else:
        correct_set = {_normalize_option(correct_answer)}

    try:
        user_raw = json.loads(user_answer) if isinstance(user_answer, str) and user_answer.strip().startswith("[") else [user_answer]
    except (json.JSONDecodeError, TypeError):
        user_raw = [user_answer]
    user_set = set(_normalize_option(x) for x in user_raw)

    if not correct_set:
        return Decimal("0")

    correct_selected = len(user_set & correct_set)
    wrong_selected = len(user_set - correct_set)
    if DOUBLE_MCQ_FULL_CREDIT_IF_EXACT and user_set == correct_set:
        return Decimal("1")
    # Partial: credit for correct, penalty for wrong
    partial = (correct_selected / len(correct_set)) - 0.25 * (wrong_selected / max(len(correct_set), 1))
    return max(Decimal("0"), min(Decimal("1"), Decimal(str(round(partial, 3)))))


def evaluate_objective_attempt(
    db: Session,
    attempt: QuestionAttempt,
    question: Question,
) -> EvaluationResult:
    """
    Evaluate MCQ or DOUBLE_MCQ deterministically; create and return EvaluationResult.
    Objective questions get no conceptual_depth/reasoning_quality/confidence_alignment
    from this path (use defaults in aggregation).
    """
    user_answer = (attempt.user_answer or "").strip()
    correct = question.correct_answer
    qtype = question.question_type

    if qtype == QUESTION_TYPE_MCQ:
        correctness = evaluate_mcq(user_answer, correct)
    elif qtype == QUESTION_TYPE_DOUBLE_MCQ:
        correctness = evaluate_double_mcq(user_answer, correct)
    else:
        correctness = Decimal("0")

    result = EvaluationResult(
        attempt_id=attempt.id,
        correctness=correctness,
        conceptual_depth=DEFAULT_CONCEPTUAL_DEPTH,
        reasoning_quality=DEFAULT_REASONING_QUALITY,
        confidence_alignment=DEFAULT_CONFIDENCE_ALIGNMENT,
        misconceptions=None,
        feedback=None,
    )
    db.add(result)
    return result


def _parse_subjective_ai_response(text: str) -> dict | None:
    """
    Parse AI response into our strict schema. Expect JSON object with:
    correctness, conceptual_depth, reasoning_quality, confidence_alignment, misconceptions, feedback.
    Retry logic is in caller; here we return None if parse fails.
    """
    text = (text or "").strip()
    # Try to extract JSON object (in case wrapped in markdown or extra text)
    json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    try:
        correctness = float(data.get("correctness", 0))
        conceptual_depth = float(data.get("conceptual_depth", 0))
        reasoning_quality = float(data.get("reasoning_quality", 0))
        confidence_alignment = float(data.get("confidence_alignment", 0))
        misconceptions = data.get("misconceptions")
        if misconceptions is not None and not isinstance(misconceptions, list):
            misconceptions = []
        feedback = str(data.get("feedback", "")) if data.get("feedback") is not None else ""
    except (TypeError, ValueError):
        return None
    # Clamp 0–1
    correctness = max(0.0, min(1.0, correctness))
    conceptual_depth = max(0.0, min(1.0, conceptual_depth))
    reasoning_quality = max(0.0, min(1.0, reasoning_quality))
    confidence_alignment = max(0.0, min(1.0, confidence_alignment))
    return {
        "correctness": correctness,
        "conceptual_depth": conceptual_depth,
        "reasoning_quality": reasoning_quality,
        "confidence_alignment": confidence_alignment,
        "misconceptions": misconceptions or [],
        "feedback": feedback[:500],
    }


def build_subjective_prompt(question_text: str, rubric: object, user_answer: str, module_context: str | None) -> str:
    """
    Build prompt for AI: only module context + rubric, no teaching/hints/answer.
    Instruction to return JSON only in the exact format.
    """
    rubric_str = json.dumps(rubric, indent=2) if rubric else "{}"
    context = (module_context or "").strip()[:3000]
    return f"""You are an evaluator for a learning platform. Evaluate the following subjective answer strictly.

Module context (for reference only):
{context or "No additional context."}

Evaluation rubric (use this to score):
{rubric_str}

Question:
{question_text}

Student's answer:
{user_answer or "(No answer provided)"}

Rules:
- Do NOT teach, give hints, or reveal the correct answer.
- Score each dimension from 0.0 to 1.0. Prefer under-scoring when uncertain.
- Return ONLY a single JSON object, no other text, with exactly these keys: correctness, conceptual_depth, reasoning_quality, confidence_alignment, misconceptions (array of strings), feedback (short, neutral, non-revealing string).
- Example format: {{"correctness": 0.7, "conceptual_depth": 0.6, "reasoning_quality": 0.5, "confidence_alignment": 0.8, "misconceptions": [], "feedback": "Consider reviewing the definition of X."}}
"""


def create_subjective_evaluation_result(
    db: Session,
    attempt: QuestionAttempt,
    parsed: dict,
) -> EvaluationResult:
    """Create EvaluationResult from parsed AI output for a subjective attempt."""
    result = EvaluationResult(
        attempt_id=attempt.id,
        correctness=Decimal(str(parsed["correctness"])),
        conceptual_depth=Decimal(str(parsed["conceptual_depth"])),
        reasoning_quality=Decimal(str(parsed["reasoning_quality"])),
        confidence_alignment=Decimal(str(parsed["confidence_alignment"])),
        misconceptions=parsed.get("misconceptions") or [],
        feedback=parsed.get("feedback"),
    )
    db.add(result)
    return result
