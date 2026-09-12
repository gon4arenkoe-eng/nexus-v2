"""Add durable pair/basket execution checkpoints."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "f4b6c8d2e1a0"
down_revision: str | None = "e3c7a9d1f2b4"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "multi_leg_execution_states",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("plan_id", sa.String(length=160), nullable=False),
        sa.Column("group_id", sa.String(length=160), nullable=False),
        sa.Column("shape", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("recovery_policy", sa.String(length=40), nullable=False),
        sa.Column("legs_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "user_id",
            "plan_id",
            name="pk_multi_leg_execution_states",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["execution_plans.plan_id"],
            ondelete="RESTRICT",
            name="fk_multi_leg_execution_states_plan",
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["position_groups.group_id"],
            ondelete="RESTRICT",
            name="fk_multi_leg_execution_states_group",
        ),
        sa.CheckConstraint(
            "user_id > 0",
            name="ck_multi_leg_execution_states_user_positive",
        ),
    )
    op.create_index(
        "ix_multi_leg_execution_states_state",
        "multi_leg_execution_states",
        ["state"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_multi_leg_execution_states_state",
        table_name="multi_leg_execution_states",
    )
    op.drop_table("multi_leg_execution_states")
