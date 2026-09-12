"""Add durable execution coordinator state checkpoints."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "e3c7a9d1f2b4"
down_revision: str | None = "c0f3a91b7e42"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "execution_coordinator_states",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column(
            "client_order_id",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column(
            "venue_id",
            sa.String(length=80),
            nullable=False,
        ),
        sa.Column(
            "account_value",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "instrument_venue_id",
            sa.String(length=80),
            nullable=False,
        ),
        sa.Column(
            "native_symbol",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column(
            "instrument_type",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "asset_class",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "state",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "attempt",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "venue_order_id",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
            "order_id",
            name="pk_execution_coordinator_states",
        ),
        sa.CheckConstraint(
            "user_id > 0",
            name="ck_execution_coordinator_states_user_id_positive",
        ),
        sa.CheckConstraint(
            "account_value > 0",
            name="ck_execution_coordinator_states_account_value_positive",
        ),
        sa.CheckConstraint(
            "attempt >= 0",
            name="ck_execution_coordinator_states_attempt_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["execution_orders.order_id"],
            ondelete="RESTRICT",
            name="fk_execution_coordinator_states_order",
        ),
    )

    op.create_index(
        "ix_execution_coordinator_states_state",
        "execution_coordinator_states",
        ["state"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_execution_coordinator_states_state",
        table_name="execution_coordinator_states",
    )
    op.drop_table("execution_coordinator_states")
