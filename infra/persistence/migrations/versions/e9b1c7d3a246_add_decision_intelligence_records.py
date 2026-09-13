"""Add immutable Decision Intelligence record journal."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "e9b1c7d3a246"
down_revision = "d8a0e6f5b125"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decision_intelligence_records",
        sa.Column("workspace_id", sa.String(length=160), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("record_type", sa.String(length=32), nullable=False),
        sa.Column("record_id", sa.String(length=160), nullable=False),
        sa.Column("parent_record_id", sa.String(length=160), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "workspace_id",
            "user_id",
            "record_type",
            "record_id",
            name="pk_decision_intelligence_records",
        ),
        sa.CheckConstraint(
            "user_id > 0",
            name="ck_decision_intelligence_records_user_positive",
        ),
    )
    op.create_index(
        "ix_decision_intelligence_records_owner_created",
        "decision_intelligence_records",
        ["workspace_id", "user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_decision_intelligence_records_parent",
        "decision_intelligence_records",
        ["workspace_id", "user_id", "record_type", "parent_record_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_decision_intelligence_records_parent",
        table_name="decision_intelligence_records",
    )
    op.drop_index(
        "ix_decision_intelligence_records_owner_created",
        table_name="decision_intelligence_records",
    )
    op.drop_table("decision_intelligence_records")
