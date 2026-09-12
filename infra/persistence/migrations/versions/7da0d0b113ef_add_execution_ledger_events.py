"""Add immutable execution Ledger event persistence.

Revision ID: 7da0d0b113ef
Revises: 4d6f7a8b9c01
Create Date: 2026-09-10

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "7da0d0b113ef"
down_revision: Union[str, Sequence[str], None] = "4d6f7a8b9c01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create immutable canonical execution Ledger evidence."""

    op.create_table(
        "execution_ledger_events",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("event_id", sa.String(length=160), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("plan_id", sa.String(length=160), nullable=False),
        sa.Column("group_id", sa.String(length=160), nullable=True),
        sa.Column("leg_id", sa.String(length=160), nullable=True),
        sa.Column("order_id", sa.String(length=160), nullable=True),
        sa.Column("fill_id", sa.String(length=160), nullable=True),
        sa.Column("venue_id", sa.String(length=80), nullable=True),
        sa.Column("account_value", sa.BigInteger(), nullable=True),
        sa.Column(
            "instrument_venue_id",
            sa.String(length=80),
            nullable=True,
        ),
        sa.Column(
            "native_symbol",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column(
            "instrument_type",
            sa.String(length=40),
            nullable=True,
        ),
        sa.Column(
            "asset_class",
            sa.String(length=40),
            nullable=True,
        ),
        sa.Column("source", sa.String(length=160), nullable=False),
        sa.Column(
            "correlation_id",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column(
            "causation_id",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("sequence_no", sa.BigInteger(), nullable=True),
        sa.Column(
            "evidence_source",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column(
            "evidence_quality",
            sa.String(length=80),
            nullable=True,
        ),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_version > 0",
            name="ck_execution_ledger_events_event_version_positive",
        ),
        sa.CheckConstraint(
            "user_id > 0",
            name="ck_execution_ledger_events_user_id_positive",
        ),
        sa.CheckConstraint(
            "account_value IS NULL OR account_value > 0",
            name="ck_execution_ledger_events_account_value_positive",
        ),
        sa.CheckConstraint(
            "schema_version > 0",
            name="ck_execution_ledger_events_schema_version_positive",
        ),
        sa.CheckConstraint(
            "account_value IS NULL OR venue_id IS NOT NULL",
            name="ck_execution_ledger_events_account_requires_venue",
        ),
        sa.CheckConstraint(
            "instrument_venue_id IS NULL OR "
            "venue_id IS NULL OR instrument_venue_id = venue_id",
            name="ck_execution_ledger_events_matching_venue",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["execution_plans.plan_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["position_groups.group_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["group_id", "leg_id"],
            ["position_legs.group_id", "position_legs.leg_id"],
            name="fk_execution_ledger_events_position_leg",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["execution_orders.order_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["fill_id"],
            ["execution_fills.fill_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            name="uq_execution_ledger_events_event_id",
        ),
    )

    for column in (
        "user_id",
        "plan_id",
        "group_id",
        "leg_id",
        "order_id",
        "fill_id",
        "venue_id",
        "event_type",
        "occurred_at",
        "correlation_id",
        "causation_id",
    ):
        op.create_index(
            f"ix_execution_ledger_events_{column}",
            "execution_ledger_events",
            [column],
            unique=False,
        )


def downgrade() -> None:
    """Remove only immutable execution Ledger evidence storage."""

    for column in reversed(
        (
            "user_id",
            "plan_id",
            "group_id",
            "leg_id",
            "order_id",
            "fill_id",
            "venue_id",
            "event_type",
            "occurred_at",
            "correlation_id",
            "causation_id",
        )
    ):
        op.drop_index(
            f"ix_execution_ledger_events_{column}",
            table_name="execution_ledger_events",
        )

    op.drop_table("execution_ledger_events")
