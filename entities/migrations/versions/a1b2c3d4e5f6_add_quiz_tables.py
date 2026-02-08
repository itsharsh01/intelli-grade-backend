"""Add quiz and assessment tables

Revision ID: a1b2c3d4e5f6
Revises: 0f8b124367a2
Create Date: 2026-02-08

Question bank, quiz sessions, attempts, and evaluation results.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "0f8b124367a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_type", sa.String(32), nullable=False),
        sa.Column("difficulty", sa.String(16), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("correct_answer", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("evaluation_rubric", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("concept_tags", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questions_module_id"), "questions", ["module_id"], unique=False)

    op.create_table(
        "quiz_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_ids", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quiz_sessions_user_id"), "quiz_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_quiz_sessions_module_id"), "quiz_sessions", ["module_id"], unique=False)

    op.create_table(
        "question_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("quiz_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_answer", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("evaluated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["quiz_session_id"], ["quiz_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_attempts_quiz_session_id"), "question_attempts", ["quiz_session_id"], unique=False)
    op.create_index(op.f("ix_question_attempts_question_id"), "question_attempts", ["question_id"], unique=False)

    op.create_table(
        "evaluation_results",
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("correctness", sa.Numeric(4, 3), nullable=False),
        sa.Column("conceptual_depth", sa.Numeric(4, 3), nullable=True),
        sa.Column("reasoning_quality", sa.Numeric(4, 3), nullable=True),
        sa.Column("confidence_alignment", sa.Numeric(4, 3), nullable=True),
        sa.Column("misconceptions", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["question_attempts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("attempt_id"),
    )


def downgrade() -> None:
    op.drop_table("evaluation_results")
    op.drop_index(op.f("ix_question_attempts_question_id"), table_name="question_attempts")
    op.drop_index(op.f("ix_question_attempts_quiz_session_id"), table_name="question_attempts")
    op.drop_table("question_attempts")
    op.drop_index(op.f("ix_quiz_sessions_module_id"), table_name="quiz_sessions")
    op.drop_index(op.f("ix_quiz_sessions_user_id"), table_name="quiz_sessions")
    op.drop_table("quiz_sessions")
    op.drop_index(op.f("ix_questions_module_id"), table_name="questions")
    op.drop_table("questions")
