"""question transition audit metadata

Revision ID: 20260410_000002
Revises: 20260410_000001
Create Date: 2026-04-10 00:00:02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260410_000002"
down_revision = "20260410_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("last_status_transition_actor_role", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("last_status_transition_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("last_status_transition_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("questions", "last_status_transition_at")
    op.drop_column("questions", "last_status_transition_reason")
    op.drop_column("questions", "last_status_transition_actor_role")
