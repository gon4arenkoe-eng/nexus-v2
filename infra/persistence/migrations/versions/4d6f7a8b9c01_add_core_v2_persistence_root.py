"""Add canonical Core V2 persistence root schema.

Revision ID: 4d6f7a8b9c01
Revises:
Create Date: 2026-09-05

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "4d6f7a8b9c01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the canonical Core V2 execution persistence schema."""

    op.create_table(
        "execution_plans",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("plan_id", sa.String(length=160), nullable=False),
        sa.Column("intent_id", sa.String(length=160), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("shape", sa.String(length=32), nullable=False),
        sa.Column("strategy", sa.String(length=160), nullable=False),
        sa.Column(
            "strategy_version",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column("source", sa.String(length=160), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "user_id > 0",
            name="ck_execution_plans_user_id_positive",
        ),
        sa.CheckConstraint(
            "schema_version > 0",
            name="ck_execution_plans_schema_version_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_id"),
    )

    op.create_index(
        "ix_execution_plans_user_id",
        "execution_plans",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "execution_plan_legs",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("plan_id", sa.String(length=160), nullable=False),
        sa.Column("leg_id", sa.String(length=160), nullable=False),
        sa.Column("order_id", sa.String(length=160), nullable=False),
        sa.Column(
            "client_order_id",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column("venue_id", sa.String(length=80), nullable=False),
        sa.Column("account_value", sa.BigInteger(), nullable=False),
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
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column(
            "quantity",
            sa.Numeric(precision=38, scale=18),
            nullable=False,
        ),
        sa.Column(
            "order_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "limit_price",
            sa.Numeric(precision=38, scale=18),
            nullable=True,
        ),
        sa.Column("reduce_only", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "account_value > 0",
            name="ck_execution_plan_legs_account_value_positive",
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_execution_plan_legs_quantity_positive",
        ),
        sa.CheckConstraint(
            "limit_price IS NULL OR limit_price > 0",
            name="ck_execution_plan_legs_limit_price_positive",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["execution_plans.plan_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "plan_id",
            "leg_id",
            name="uq_execution_plan_legs_plan_leg",
        ),
        sa.UniqueConstraint(
            "order_id",
            name="uq_execution_plan_legs_order_id",
        ),
        sa.UniqueConstraint(
            "client_order_id",
            name="uq_execution_plan_legs_client_order_id",
        ),
    )

    op.create_index(
        "ix_execution_plan_legs_plan_id",
        "execution_plan_legs",
        ["plan_id"],
        unique=False,
    )

    op.create_table(
        "position_groups",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("group_id", sa.String(length=160), nullable=False),
        sa.Column("plan_id", sa.String(length=160), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("shape", sa.String(length=32), nullable=False),
        sa.Column("strategy", sa.String(length=160), nullable=False),
        sa.Column(
            "strategy_version",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column(
            "trade_source",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "closed_at",
            sa.DateTime(timezone=True),
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
        sa.CheckConstraint(
            "user_id > 0",
            name="ck_position_groups_user_id_positive",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["execution_plans.plan_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id"),
        sa.UniqueConstraint(
            "group_id",
            "plan_id",
            name="uq_position_groups_group_plan",
        ),
    )

    op.create_index(
        "ix_position_groups_plan_id",
        "position_groups",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        "ix_position_groups_status",
        "position_groups",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_position_groups_user_id",
        "position_groups",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "position_legs",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("group_id", sa.String(length=160), nullable=False),
        sa.Column("leg_id", sa.String(length=160), nullable=False),
        sa.Column("venue_id", sa.String(length=80), nullable=False),
        sa.Column("account_value", sa.BigInteger(), nullable=False),
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
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column(
            "target_quantity",
            sa.Numeric(precision=38, scale=18),
            nullable=False,
        ),
        sa.Column(
            "filled_quantity",
            sa.Numeric(precision=38, scale=18),
            nullable=False,
        ),
        sa.Column(
            "current_quantity",
            sa.Numeric(precision=38, scale=18),
            nullable=False,
        ),
        sa.Column(
            "average_entry_price",
            sa.Numeric(precision=38, scale=18),
            nullable=True,
        ),
        sa.Column(
            "average_exit_price",
            sa.Numeric(precision=38, scale=18),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "closed_at",
            sa.DateTime(timezone=True),
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
        sa.CheckConstraint(
            "account_value > 0",
            name="ck_position_legs_account_value_positive",
        ),
        sa.CheckConstraint(
            "venue_id = instrument_venue_id",
            name="ck_position_legs_matching_venue",
        ),
        sa.CheckConstraint(
            "target_quantity > 0",
            name="ck_position_legs_target_quantity_positive",
        ),
        sa.CheckConstraint(
            "filled_quantity >= 0",
            name="ck_position_legs_filled_quantity_non_negative",
        ),
        sa.CheckConstraint(
            "current_quantity >= 0",
            name="ck_position_legs_current_quantity_non_negative",
        ),
        sa.CheckConstraint(
            "average_entry_price IS NULL OR "
            "average_entry_price > 0",
            name="ck_position_legs_average_entry_price_positive",
        ),
        sa.CheckConstraint(
            "average_exit_price IS NULL OR "
            "average_exit_price > 0",
            name="ck_position_legs_average_exit_price_positive",
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["position_groups.group_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "group_id",
            "leg_id",
            name="uq_position_legs_group_leg",
        ),
    )

    op.create_index(
        "ix_position_legs_group_id",
        "position_legs",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        "ix_position_legs_status",
        "position_legs",
        ["status"],
        unique=False,
    )

    op.create_table(
        "execution_orders",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("order_id", sa.String(length=160), nullable=False),
        sa.Column("plan_id", sa.String(length=160), nullable=False),
        sa.Column("group_id", sa.String(length=160), nullable=False),
        sa.Column("leg_id", sa.String(length=160), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("venue_id", sa.String(length=80), nullable=False),
        sa.Column("account_value", sa.BigInteger(), nullable=False),
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
            "client_order_id",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column(
            "venue_order_id",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column(
            "order_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column("reduce_only", sa.Boolean(), nullable=False),
        sa.Column(
            "requested_quantity",
            sa.Numeric(precision=38, scale=18),
            nullable=False,
        ),
        sa.Column(
            "filled_quantity",
            sa.Numeric(precision=38, scale=18),
            nullable=False,
        ),
        sa.Column(
            "average_fill_price",
            sa.Numeric(precision=38, scale=18),
            nullable=True,
        ),
        sa.Column(
            "limit_price",
            sa.Numeric(precision=38, scale=18),
            nullable=True,
        ),
        sa.Column(
            "local_status",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "last_venue_status",
            sa.String(length=80),
            nullable=True,
        ),
        sa.Column(
            "last_venue_observed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "venue_observation_source",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column(
            "rejection_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "filled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
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
        sa.CheckConstraint(
            "user_id > 0",
            name="ck_execution_orders_user_id_positive",
        ),
        sa.CheckConstraint(
            "account_value > 0",
            name="ck_execution_orders_account_value_positive",
        ),
        sa.CheckConstraint(
            "venue_id = instrument_venue_id",
            name="ck_execution_orders_matching_venue",
        ),
        sa.CheckConstraint(
            "requested_quantity > 0",
            name="ck_execution_orders_requested_quantity_positive",
        ),
        sa.CheckConstraint(
            "filled_quantity >= 0",
            name="ck_execution_orders_filled_quantity_non_negative",
        ),
        sa.CheckConstraint(
            "filled_quantity <= requested_quantity",
            name="ck_execution_orders_filled_not_above_requested",
        ),
        sa.CheckConstraint(
            "average_fill_price IS NULL OR average_fill_price > 0",
            name="ck_execution_orders_average_fill_price_positive",
        ),
        sa.CheckConstraint(
            "limit_price IS NULL OR limit_price > 0",
            name="ck_execution_orders_limit_price_positive",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["execution_plans.plan_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["group_id", "plan_id"],
            ["position_groups.group_id", "position_groups.plan_id"],
            name="fk_execution_orders_position_group_plan",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["group_id", "leg_id"],
            ["position_legs.group_id", "position_legs.leg_id"],
            name="fk_execution_orders_position_leg",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_id",
            name="uq_execution_orders_order_id",
        ),
        sa.UniqueConstraint(
            "client_order_id",
            name="uq_execution_orders_client_order_id",
        ),
    )

    op.create_index(
        "ix_execution_orders_group_id",
        "execution_orders",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_orders_local_status",
        "execution_orders",
        ["local_status"],
        unique=False,
    )
    op.create_index(
        "ix_execution_orders_plan_id",
        "execution_orders",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_orders_user_id",
        "execution_orders",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "execution_fills",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("fill_id", sa.String(length=160), nullable=False),
        sa.Column("order_id", sa.String(length=160), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("venue_id", sa.String(length=80), nullable=False),
        sa.Column("account_value", sa.BigInteger(), nullable=False),
        sa.Column(
            "venue_fill_id",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column(
            "quantity",
            sa.Numeric(precision=38, scale=18),
            nullable=False,
        ),
        sa.Column(
            "price",
            sa.Numeric(precision=38, scale=18),
            nullable=False,
        ),
        sa.Column(
            "fee",
            sa.Numeric(precision=38, scale=18),
            nullable=False,
        ),
        sa.Column(
            "fee_currency",
            sa.String(length=40),
            nullable=True,
        ),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=160), nullable=False),
        sa.Column(
            "raw_evidence_hash",
            sa.String(length=160),
            nullable=True,
        ),
        sa.CheckConstraint(
            "user_id > 0",
            name="ck_execution_fills_user_id_positive",
        ),
        sa.CheckConstraint(
            "account_value > 0",
            name="ck_execution_fills_account_value_positive",
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_execution_fills_quantity_positive",
        ),
        sa.CheckConstraint(
            "price > 0",
            name="ck_execution_fills_price_positive",
        ),
        sa.CheckConstraint(
            "fee >= 0",
            name="ck_execution_fills_fee_non_negative",
        ),
        sa.CheckConstraint(
            "fee = 0 OR fee_currency IS NOT NULL",
            name="ck_execution_fills_positive_fee_currency",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["execution_orders.order_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "fill_id",
            name="uq_execution_fills_fill_id",
        ),
        sa.UniqueConstraint(
            "venue_id",
            "account_value",
            "venue_fill_id",
            name="uq_execution_fills_venue_account_fill",
        ),
    )

    op.create_index(
        "ix_execution_fills_order_id",
        "execution_fills",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_fills_user_id",
        "execution_fills",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove only the canonical Core V2 root schema."""

    op.drop_index(
        "ix_execution_fills_user_id",
        table_name="execution_fills",
    )
    op.drop_index(
        "ix_execution_fills_order_id",
        table_name="execution_fills",
    )
    op.drop_table("execution_fills")

    op.drop_index(
        "ix_execution_orders_user_id",
        table_name="execution_orders",
    )
    op.drop_index(
        "ix_execution_orders_plan_id",
        table_name="execution_orders",
    )
    op.drop_index(
        "ix_execution_orders_local_status",
        table_name="execution_orders",
    )
    op.drop_index(
        "ix_execution_orders_group_id",
        table_name="execution_orders",
    )
    op.drop_table("execution_orders")

    op.drop_index(
        "ix_position_legs_status",
        table_name="position_legs",
    )
    op.drop_index(
        "ix_position_legs_group_id",
        table_name="position_legs",
    )
    op.drop_table("position_legs")

    op.drop_index(
        "ix_position_groups_user_id",
        table_name="position_groups",
    )
    op.drop_index(
        "ix_position_groups_status",
        table_name="position_groups",
    )
    op.drop_index(
        "ix_position_groups_plan_id",
        table_name="position_groups",
    )
    op.drop_table("position_groups")

    op.drop_index(
        "ix_execution_plan_legs_plan_id",
        table_name="execution_plan_legs",
    )
    op.drop_table("execution_plan_legs")

    op.drop_index(
        "ix_execution_plans_user_id",
        table_name="execution_plans",
    )
    op.drop_table("execution_plans")
