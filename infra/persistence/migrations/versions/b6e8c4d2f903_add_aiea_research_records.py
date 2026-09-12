"""Add immutable AIEA research record journal."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "b6e8c4d2f903"
down_revision: str | None = "a5d7e9c3b102"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "aiea_research_records",
        sa.Column("workspace_id", sa.String(length=160), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("record_type", sa.String(length=48), nullable=False),
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
            name="pk_aiea_research_records",
        ),
        sa.CheckConstraint(
            "user_id > 0",
            name="ck_aiea_research_records_user_positive",
        ),
    )
    op.create_index(
        "ix_aiea_research_records_owner_created",
        "aiea_research_records",
        ["workspace_id", "user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_aiea_research_records_owner_created",
        table_name="aiea_research_records",
    )
    op.drop_table("aiea_research_records")
