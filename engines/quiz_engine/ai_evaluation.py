"""
AI evaluation for SUBJECTIVE questions only. Uses module context + rubric; no teaching/hints.
Retry once on invalid response; then fail gracefully (under-score).
"""
from __future__ import annotations

from entities.models import Question, QuestionAttempt
from .evaluation import (
    build_subjective_prompt,
    _parse_subjective_ai_response,
    create_subjective_evaluation_result,
)
from .constants import QUESTION_TYPE_SUBJECTIVE


def get_module_context_for_evaluation(db, module_id):  # noqa: ANN001
    """
    Optional: load module content title/snippet for context. If no module_content row, return None.
    """
    try:
        from entities.models import ModuleContent
        row = db.query(ModuleContent).filter(ModuleContent.id == module_id).first()
        if row and getattr(row, "content", None):
            return (getattr(row, "title", "") or "") + "\n" + (row.content or "")[:2000]
        return None
    except Exception:
        return None


def _get_genai():
    """Lazy import so quiz works when GEMINI_API_KEY is not set."""
    try:
        from core.genai_service import genai_service
        return genai_service
    except Exception:
        return None


def evaluate_subjective_with_ai(
    db,
    attempt: QuestionAttempt,
    question: Question,
    module_context: str | None,
) -> bool:
    """
    Call AI, parse response, persist EvaluationResult. Prefer under-scoring on failure.
    Returns True if evaluation was successful and result stored; False on parse/API failure (caller may store default).
    """
    genai = _get_genai()
    if genai is None:
        return False
    prompt = build_subjective_prompt(
        question_text=question.question_text,
        rubric=question.evaluation_rubric,
        user_answer=attempt.user_answer or "",
        module_context=module_context,
    )
    text = None
    try:
        text = genai.generate_response(prompt)
    except Exception:
        pass
    parsed = _parse_subjective_ai_response(text) if text else None
    if parsed is None and text and genai:
        # Retry once (e.g. model added markdown)
        try:
            text2 = genai.generate_response(prompt)
            parsed = _parse_subjective_ai_response(text2)
        except Exception:
            pass
    if parsed is None:
        return False
    create_subjective_evaluation_result(db, attempt, parsed)
    return True
