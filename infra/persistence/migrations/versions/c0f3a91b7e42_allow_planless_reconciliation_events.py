"""Allow planless reconciliation ledger evidence.

Revision ID: c0f3a91b7e42
Revises: 7da0d0b113ef
"""

from __future__ import annotations

from alembic import op


revision = "c0f3a91b7e42"
down_revision = "7da0d0b113ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "execution_ledger_events",
        "plan_id",
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "execution_ledger_events",
        "plan_id",
        nullable=False,
    )
