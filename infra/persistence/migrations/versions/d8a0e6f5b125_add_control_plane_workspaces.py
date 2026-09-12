"""add control plane workspace persistence

Revision ID: d8a0e6f5b125
Revises: c7f9d5e4a014
"""

from alembic import op
import sqlalchemy as sa

revision = "d8a0e6f5b125"
down_revision = "c7f9d5e4a014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_workspaces",
        sa.Column("tenant_workspace_id", sa.String(160), primary_key=True),
        sa.Column("user_workspace_id", sa.String(160), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("theme", sa.String(16), nullable=False),
        sa.Column("active_layout_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "workspace_layout_versions",
        sa.Column("tenant_workspace_id", sa.String(160), primary_key=True),
        sa.Column("user_workspace_id", sa.String(160), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("layout_json", sa.Text(), nullable=False),
        sa.Column("source_version", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "workspace_templates",
        sa.Column("template_key", sa.String(160), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True),
        sa.Column("title_key", sa.String(200), nullable=False),
        sa.Column(
            "owner_workspace_id",
            sa.String(160),
            nullable=True,
            index=True,
        ),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
        sa.Column("shared", sa.Boolean(), nullable=False),
        sa.Column("layout_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "user_presentation_preferences",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=False,
        ),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("theme", sa.String(16), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in (
        "user_presentation_preferences",
        "workspace_templates",
        "workspace_layout_versions",
        "user_workspaces",
    ):
        op.drop_table(table)
