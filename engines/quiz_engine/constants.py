"""
Quiz and assessment constants. No magic numbers in selection or scoring.
"""

# Question type identifiers (must match DB and frontend)
QUESTION_TYPE_MCQ = "MCQ"
QUESTION_TYPE_DOUBLE_MCQ = "DOUBLE_MCQ"
QUESTION_TYPE_SUBJECTIVE = "SUBJECTIVE"

QUESTION_TYPES_OBJECTIVE = (QUESTION_TYPE_MCQ, QUESTION_TYPE_DOUBLE_MCQ)
QUESTION_TYPES_ALL = (QUESTION_TYPE_MCQ, QUESTION_TYPE_DOUBLE_MCQ, QUESTION_TYPE_SUBJECTIVE)

# Module size → question count range (inclusive). Used when generating quiz.
MODULE_SIZE_SMALL = "small"
MODULE_SIZE_MEDIUM = "medium"
MODULE_SIZE_LARGE = "large"

QUESTION_COUNT_BY_SIZE = {
    MODULE_SIZE_SMALL: (3, 5),
    MODULE_SIZE_MEDIUM: (6, 10),
    MODULE_SIZE_LARGE: (10, 15),
}

# Default size when module has no size metadata (prefer under-selecting)
DEFAULT_MODULE_SIZE = MODULE_SIZE_SMALL

# Desired distribution: MCQ 40%, DOUBLE_MCQ 30%, SUBJECTIVE 30%
DISTRIBUTION = {
    QUESTION_TYPE_MCQ: 0.40,
    QUESTION_TYPE_DOUBLE_MCQ: 0.30,
    QUESTION_TYPE_SUBJECTIVE: 0.30,
}

# Aggregated quiz score weights (must sum to 1.0)
SCORE_WEIGHT_CORRECTNESS = 0.40
SCORE_WEIGHT_CONCEPTUAL_DEPTH = 0.30
SCORE_WEIGHT_REASONING_QUALITY = 0.20
SCORE_WEIGHT_CONFIDENCE_ALIGNMENT = 0.10

# For objective questions we only have correctness; others default for aggregation
DEFAULT_CONCEPTUAL_DEPTH = 0.0
DEFAULT_REASONING_QUALITY = 0.0
DEFAULT_CONFIDENCE_ALIGNMENT = 0.0

# DOUBLE_MCQ partial credit: per correct option, no penalty for wrong
# Score = (correct_selected / total_correct) * (1 - 0.5 * (wrong_selected / total_options))
# Simpler: full credit only if exactly correct; else partial by overlap.
DOUBLE_MCQ_FULL_CREDIT_IF_EXACT = True  # If exact match, 1.0; else partial
DOUBLE_MCQ_PARTIAL_CREDIT_RATE = 0.5  # For partial: (correct_selected / total_correct) * 0.5 + 0.5 * (no wrong)

# Confidence alignment: how well user's confidence matched correctness (for subjective)
# Stored 0–1; we use as-is in aggregation.

# Minimum questions per type when distributing (avoid zero if we have at least one)
MIN_QUESTIONS_PER_TYPE = 0
