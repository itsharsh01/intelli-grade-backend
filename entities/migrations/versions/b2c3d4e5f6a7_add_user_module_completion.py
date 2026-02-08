"""Add user_module_completion table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-08

Tracks when user marks a module as complete (unlocks quiz).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_module_completion",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "module_id"),
    )
    op.create_index(op.f("ix_user_module_completion_module_id"), "user_module_completion", ["module_id"], unique=False)
    op.create_index(op.f("ix_user_module_completion_user_id"), "user_module_completion", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_module_completion_user_id"), table_name="user_module_completion")
    op.drop_index(op.f("ix_user_module_completion_module_id"), table_name="user_module_completion")
    op.drop_table("user_module_completion")
