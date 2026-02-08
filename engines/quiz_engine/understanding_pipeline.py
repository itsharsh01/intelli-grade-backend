"""
Understanding evaluation pipeline: single entry point that takes the four inputs
(module context, question text + rubric, user answer), sends them to Gemini, and
returns/stores understanding dimensions (correctness, conceptual_depth, reasoning_quality, etc.).

Pipeline steps:
1. Load module context (from DB by module_id).
2. Question text + rubric and user answer (from passed attempt and question).
3. Build prompt from these four.
4. Call Gemini with the prompt.
5. Parse model response into structured scores.
6. Persist to evaluation_results.
7. Return success or failure (caller handles fallback).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from entities.models import Question, QuestionAttempt

from .ai_evaluation import get_module_context_for_evaluation, _get_genai
from .evaluation import (
    build_subjective_prompt,
    _parse_subjective_ai_response,
    create_subjective_evaluation_result,
)


def run_understanding_evaluation_pipeline(
    db: Session,
    attempt: QuestionAttempt,
    question: Question,
) -> bool:
    """
    Run the full understanding evaluation pipeline:

    1. Load module context from DB (by question.module_id).
    2. Use question text, rubric, and attempt user_answer.
    3. Build prompt from context + question + rubric + user answer.
    4. Call Gemini.
    5. Parse response (retry once on parse failure).
    6. Persist EvaluationResult and return True; on failure return False.

    Caller is responsible for fallback (e.g. default under-score) when this returns False.
    """
    # Step 1: Load module context from DB
    module_context = get_module_context_for_evaluation(db, question.module_id)

    # Step 2 & 3: Build prompt from the four inputs
    prompt = build_subjective_prompt(
        question_text=question.question_text,
        rubric=question.evaluation_rubric,
        user_answer=attempt.user_answer or "",
        module_context=module_context,
    )

    genai = _get_genai()
    if genai is None:
        return False

    # Step 4: Call Gemini
    text = None
    try:
        text = genai.generate_response(prompt)
    except Exception:
        pass

    # Step 5: Parse response (retry once on parse failure)
    parsed = _parse_subjective_ai_response(text) if text else None
    if parsed is None and text and genai:
        try:
            text2 = genai.generate_response(prompt)
            parsed = _parse_subjective_ai_response(text2)
        except Exception:
            pass

    if parsed is None:
        return False

    # Step 6: Persist and return success
    create_subjective_evaluation_result(db, attempt, parsed)
    return True
