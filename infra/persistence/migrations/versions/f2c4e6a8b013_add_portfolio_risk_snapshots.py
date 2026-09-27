"""Add immutable Portfolio Risk snapshot history.

Revision ID: f2c4e6a8b013
Revises: e9b1c7d3a246
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "f2c4e6a8b013"
down_revision = "e9b1c7d3a246"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portfolio_risk_snapshots",
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("observation_state", sa.String(length=32), nullable=False),
        sa.Column("trading_state", sa.String(length=32), nullable=False),
        sa.Column("equity", sa.Numeric(38, 18), nullable=False),
        sa.Column("daily_start_equity", sa.Numeric(38, 18), nullable=False),
        sa.Column("rolling_peak_equity", sa.Numeric(38, 18), nullable=False),
        sa.Column("exposures_json", sa.Text(), nullable=False),
        sa.Column("limits_json", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=160), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("snapshot_id"),
        sa.CheckConstraint(
            "user_id > 0",
            name="ck_portfolio_risk_snapshots_user_positive",
        ),
        sa.CheckConstraint(
            "equity > 0",
            name="ck_portfolio_risk_snapshots_equity_positive",
        ),
        sa.CheckConstraint(
            "daily_start_equity > 0",
            name="ck_portfolio_risk_snapshots_daily_equity_positive",
        ),
        sa.CheckConstraint(
            "rolling_peak_equity > 0",
            name="ck_portfolio_risk_snapshots_peak_equity_positive",
        ),
    )
    op.create_index(
        "ix_portfolio_risk_snapshots_user_id",
        "portfolio_risk_snapshots",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_risk_snapshots_observed_at",
        "portfolio_risk_snapshots",
        ["observed_at"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_risk_snapshots_user_observed",
        "portfolio_risk_snapshots",
        ["user_id", "observed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_portfolio_risk_snapshots_user_observed",
        table_name="portfolio_risk_snapshots",
    )
    op.drop_index(
        "ix_portfolio_risk_snapshots_observed_at",
        table_name="portfolio_risk_snapshots",
    )
    op.drop_index(
        "ix_portfolio_risk_snapshots_user_id",
        table_name="portfolio_risk_snapshots",
    )
    op.drop_table("portfolio_risk_snapshots")
