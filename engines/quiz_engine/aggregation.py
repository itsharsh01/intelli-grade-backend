"""
Aggregated scoring and insights: composite score from four dimensions,
strengths and weak_areas from per-question results. Auditable, no magic numbers.
"""
from __future__ import annotations

from decimal import Decimal

from .constants import (
    SCORE_WEIGHT_CORRECTNESS,
    SCORE_WEIGHT_CONCEPTUAL_DEPTH,
    SCORE_WEIGHT_REASONING_QUALITY,
    SCORE_WEIGHT_CONFIDENCE_ALIGNMENT,
    QUESTION_TYPE_SUBJECTIVE,
)
from .schemas import PerQuestionResult, AggregatedScores


def _decimal_to_float(d: Decimal | None) -> float:
    if d is None:
        return 0.0
    return float(d)


def compute_composite(
    correctness: float,
    conceptual_depth: float,
    reasoning_quality: float,
    confidence_alignment: float,
) -> float:
    """Weighted composite 0–1. Weights must sum to 1.0."""
    return (
        SCORE_WEIGHT_CORRECTNESS * correctness
        + SCORE_WEIGHT_CONCEPTUAL_DEPTH * conceptual_depth
        + SCORE_WEIGHT_REASONING_QUALITY * reasoning_quality
        + SCORE_WEIGHT_CONFIDENCE_ALIGNMENT * confidence_alignment
    )


def aggregate_results(per_question: list[PerQuestionResult]) -> AggregatedScores:
    """Compute mean per dimension and composite. Uses 0 for missing dimensions (objective questions)."""
    if not per_question:
        return AggregatedScores(
            correctness=0.0,
            conceptual_depth=0.0,
            reasoning_quality=0.0,
            confidence_alignment=0.0,
            composite=0.0,
        )
    n = len(per_question)
    correctness = sum(p.correctness for p in per_question) / n
    conceptual_depth = sum((p.conceptual_depth or 0.0) for p in per_question) / n
    reasoning_quality = sum((p.reasoning_quality or 0.0) for p in per_question) / n
    confidence_alignment = sum((p.confidence_alignment or 0.0) for p in per_question) / n
    composite = compute_composite(
        correctness, conceptual_depth, reasoning_quality, confidence_alignment
    )
    return AggregatedScores(
        correctness=round(correctness, 4),
        conceptual_depth=round(conceptual_depth, 4),
        reasoning_quality=round(reasoning_quality, 4),
        confidence_alignment=round(confidence_alignment, 4),
        composite=round(composite, 4),
    )


def infer_strengths_weak_areas(
    per_question: list[PerQuestionResult],
    composite: float,
) -> tuple[list[str], list[str]]:
    """
    Simple rule-based: strength = dimension where score is above composite;
    weak = dimension below composite or questions with low correctness.
    No AI; auditable.
    """
    if not per_question:
        return [], []
    n = len(per_question)
    avg_correctness = sum(p.correctness for p in per_question) / n
    avg_depth = sum((p.conceptual_depth or 0) for p in per_question) / n
    avg_reasoning = sum((p.reasoning_quality or 0) for p in per_question) / n
    avg_conf_align = sum((p.confidence_alignment or 0) for p in per_question) / n

    strengths = []
    weak_areas = []
    if avg_correctness >= composite and avg_correctness >= 0.6:
        strengths.append("Correctness")
    elif avg_correctness < 0.5:
        weak_areas.append("Correctness")
    if avg_depth >= composite and avg_depth >= 0.5:
        strengths.append("Conceptual depth")
    elif avg_depth < 0.4 and any(p.conceptual_depth is not None for p in per_question):
        weak_areas.append("Conceptual depth")
    if avg_reasoning >= composite and avg_reasoning >= 0.5:
        strengths.append("Reasoning quality")
    elif avg_reasoning < 0.4 and any(p.reasoning_quality is not None for p in per_question):
        weak_areas.append("Reasoning quality")
    if avg_conf_align >= composite and avg_conf_align >= 0.5:
        strengths.append("Confidence alignment")
    elif avg_conf_align < 0.4 and any(p.confidence_alignment is not None for p in per_question):
        weak_areas.append("Confidence alignment")

    return strengths, weak_areas
