"""
Quiz question selection: module size → count, distribution by type, random draw.
Questions are fixed for the session once selected; no magic numbers (use constants).
"""
import random
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from entities.models import Question
from .constants import (
    QUESTION_TYPE_MCQ,
    QUESTION_TYPE_DOUBLE_MCQ,
    QUESTION_TYPE_SUBJECTIVE,
    QUESTION_COUNT_BY_SIZE,
    MODULE_SIZE_SMALL,
    MODULE_SIZE_MEDIUM,
    MODULE_SIZE_LARGE,
    DEFAULT_MODULE_SIZE,
    DISTRIBUTION,
    MIN_QUESTIONS_PER_TYPE,
)


def _module_size_from_question_count(count: int) -> str:
    """
    Derive module size from number of questions in the bank so we don't over-promise.
    Prefer under-selecting when in doubt.
    """
    if count < 10:
        return MODULE_SIZE_SMALL
    if count <= 25:
        return MODULE_SIZE_MEDIUM
    return MODULE_SIZE_LARGE


def _total_count_for_size(size: str) -> int:
    """Use midpoint of range for target total; caller can cap by availability."""
    lo, hi = QUESTION_COUNT_BY_SIZE.get(size, QUESTION_COUNT_BY_SIZE[DEFAULT_MODULE_SIZE])
    return (lo + hi) // 2


def _counts_by_type(total: int) -> dict[str, int]:
    """Desired counts per type from distribution; at least MIN_QUESTIONS_PER_TYPE per type if total allows."""
    counts = {
        QUESTION_TYPE_MCQ: max(MIN_QUESTIONS_PER_TYPE, round(total * DISTRIBUTION[QUESTION_TYPE_MCQ])),
        QUESTION_TYPE_DOUBLE_MCQ: max(MIN_QUESTIONS_PER_TYPE, round(total * DISTRIBUTION[QUESTION_TYPE_DOUBLE_MCQ])),
        QUESTION_TYPE_SUBJECTIVE: max(MIN_QUESTIONS_PER_TYPE, round(total * DISTRIBUTION[QUESTION_TYPE_SUBJECTIVE])),
    }
    # Normalize so sum <= total (may be 1 off due to rounding)
    while sum(counts.values()) > total and (counts[QUESTION_TYPE_MCQ] or counts[QUESTION_TYPE_DOUBLE_MCQ] or counts[QUESTION_TYPE_SUBJECTIVE]):
        if counts[QUESTION_TYPE_MCQ] > (MIN_QUESTIONS_PER_TYPE or 1):
            counts[QUESTION_TYPE_MCQ] -= 1
        elif counts[QUESTION_TYPE_DOUBLE_MCQ] > (MIN_QUESTIONS_PER_TYPE or 1):
            counts[QUESTION_TYPE_DOUBLE_MCQ] -= 1
        elif counts[QUESTION_TYPE_SUBJECTIVE] > (MIN_QUESTIONS_PER_TYPE or 1):
            counts[QUESTION_TYPE_SUBJECTIVE] -= 1
        else:
            break
    return counts


def select_questions_for_session(db: Session, module_id: UUID) -> list[UUID]:
    """
    Randomly select questions for a new quiz session:
    - Module size derived from question bank size for this module.
    - Total count from size; distribution 40% MCQ, 30% DOUBLE_MCQ, 30% SUBJECTIVE.
    - If insufficient questions for a type, reduce that type and never exceed available.
    - Shuffle final list so order is random.
    Returns list of question IDs (UUIDs) in the order to present.
    """
    # Count by type for this module
    type_counts = (
        db.query(Question.question_type, func.count(Question.id))
        .filter(Question.module_id == module_id)
        .group_by(Question.question_type)
        .all()
    )
    available = {row[0]: row[1] for row in type_counts}
    for qtype in (QUESTION_TYPE_MCQ, QUESTION_TYPE_DOUBLE_MCQ, QUESTION_TYPE_SUBJECTIVE):
        available.setdefault(qtype, 0)

    total_available = sum(available.values())
    if total_available == 0:
        return []

    size = _module_size_from_question_count(total_available)
    total_target = _total_count_for_size(size)
    total_target = min(total_target, total_available)

    desired = _counts_by_type(total_target)
    # Cap each type by availability (prefer under-selecting)
    take = {
        t: min(desired[t], available[t]) for t in desired
    }
    # If we reduced some type, we may have room to add more of others; keep total <= total_available
    current_total = sum(take.values())
    if current_total < total_available and current_total < total_target:
        for t in (QUESTION_TYPE_MCQ, QUESTION_TYPE_DOUBLE_MCQ, QUESTION_TYPE_SUBJECTIVE):
            if take[t] < available[t] and current_total < total_target:
                add = min(available[t] - take[t], total_target - current_total)
                take[t] += add
                current_total += add

    selected_ids: list[UUID] = []
    for qtype, count in take.items():
        if count <= 0:
            continue
        rows = (
            db.query(Question.id)
            .filter(Question.module_id == module_id, Question.question_type == qtype)
            .order_by(func.random())
            .limit(count)
            .all()
        )
        selected_ids.extend([r[0] for r in rows])

    random.shuffle(selected_ids)
    return selected_ids
