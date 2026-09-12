"""add phase10 platform security

Revision ID: c7f9d5e4a014
Revises: b6e8c4d2f903
"""
from alembic import op
import sqlalchemy as sa

revision = "c7f9d5e4a014"
down_revision = "b6e8c4d2f903"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("workspace_id", sa.String(160), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "workspace_memberships",
        sa.Column("workspace_id", sa.String(160), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "resource_ownership",
        sa.Column("workspace_id", sa.String(160), primary_key=True),
        sa.Column("resource_type", sa.String(80), primary_key=True),
        sa.Column("resource_id", sa.String(200), primary_key=True),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
    )
    op.create_table(
        "setting_versions",
        sa.Column("workspace_id", sa.String(160), primary_key=True),
        sa.Column("key", sa.String(200), primary_key=True),
        sa.Column("scope", sa.Integer(), primary_key=True),
        sa.Column("scope_id", sa.String(200), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True),
        sa.Column("domain", sa.String(64), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("safety_critical", sa.Boolean(), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "audit_events",
        sa.Column("workspace_id", sa.String(160), primary_key=True),
        sa.Column("event_id", sa.String(160), primary_key=True),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("resource_type", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.String(200), nullable=False),
        sa.Column("old_value_json", sa.Text(), nullable=True),
        sa.Column("new_value_json", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "product_plans",
        sa.Column("plan_id", sa.String(120), primary_key=True),
        sa.Column("display_name", sa.String(160), nullable=False),
    )
    op.create_table(
        "product_plan_versions",
        sa.Column("plan_id", sa.String(120), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True),
        sa.Column("entitlements_json", sa.Text(), nullable=False),
        sa.Column("quotas_json", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "quota_usage",
        sa.Column("workspace_id", sa.String(160), primary_key=True),
        sa.Column("quota_key", sa.String(200), primary_key=True),
        sa.Column("period_key", sa.String(120), primary_key=True),
        sa.Column("usage", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "workspace_subscriptions",
        sa.Column("workspace_id", sa.String(160), primary_key=True),
        sa.Column("subscription_id", sa.String(160), nullable=False, unique=True),  # noqa: E501
        sa.Column("plan_id", sa.String(120), nullable=False),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "entitlement_overrides",
        sa.Column("workspace_id", sa.String(160), primary_key=True),
        sa.Column("override_id", sa.String(160), primary_key=True),
        sa.Column("feature_key", sa.String(200), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "billing_events",
        sa.Column("provider", sa.String(80), primary_key=True),
        sa.Column("event_id", sa.String(200), primary_key=True),
        sa.Column("workspace_id", sa.String(160), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("payload_hash", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "encrypted_secrets",
        sa.Column("workspace_id", sa.String(160), primary_key=True),
        sa.Column("resource_id", sa.String(200), primary_key=True),
        sa.Column("secret_kind", sa.String(64), primary_key=True),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("key_version", sa.String(80), nullable=False),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in (
        "encrypted_secrets", "billing_events", "entitlement_overrides",
        "workspace_subscriptions", "quota_usage", "product_plan_versions",
        "product_plans", "audit_events", "setting_versions",
        "resource_ownership", "workspace_memberships", "workspaces",
    ):
        op.drop_table(table)
