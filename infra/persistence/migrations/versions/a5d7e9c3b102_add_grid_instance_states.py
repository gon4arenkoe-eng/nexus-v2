"""Add durable Grid Trading Desk checkpoints."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "a5d7e9c3b102"
down_revision: str | None = "f4b6c8d2e1a0"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "grid_instance_states",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("instance_id", sa.String(length=160), nullable=False),
        sa.Column("program_id", sa.String(length=160), nullable=False),
        sa.Column("account_venue_id", sa.String(length=80), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("instrument_venue_id", sa.String(length=80), nullable=False),
        sa.Column("instrument_symbol", sa.String(length=160), nullable=False),
        sa.Column("instrument_type", sa.String(length=32), nullable=False),
        sa.Column("asset_class", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "instance_id", name="pk_grid_instance_states"),  # noqa: E501
        sa.CheckConstraint("user_id > 0", name="ck_grid_instance_states_user_positive"),  # noqa: E501
    )
    op.create_index("ix_grid_instance_states_program_id", "grid_instance_states", ["program_id"], unique=False)  # noqa: E501
    op.create_index("ix_grid_instance_states_state", "grid_instance_states", ["state"], unique=False)  # noqa: E501


def downgrade() -> None:
    op.drop_index("ix_grid_instance_states_state", table_name="grid_instance_states")  # noqa: E501
    op.drop_index("ix_grid_instance_states_program_id", table_name="grid_instance_states")  # noqa: E501
    op.drop_table("grid_instance_states")
