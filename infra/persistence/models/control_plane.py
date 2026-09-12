"""Phase 11 Control Plane workspace persistence models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


class UserWorkspaceModel(PersistenceBase):
    __tablename__ = "user_workspaces"

    tenant_workspace_id: Mapped[str] = mapped_column(
        String(160),
        primary_key=True,
    )
    user_workspace_id: Mapped[str] = mapped_column(
        String(160),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    theme: Mapped[str] = mapped_column(String(16), nullable=False)
    active_layout_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class WorkspaceLayoutVersionModel(PersistenceBase):
    __tablename__ = "workspace_layout_versions"

    tenant_workspace_id: Mapped[str] = mapped_column(
        String(160),
        primary_key=True,
    )
    user_workspace_id: Mapped[str] = mapped_column(
        String(160),
        primary_key=True,
    )
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )
    layout_json: Mapped[str] = mapped_column(Text, nullable=False)
    source_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class WorkspaceTemplateModel(PersistenceBase):
    __tablename__ = "workspace_templates"

    template_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    title_key: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_workspace_id: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
        index=True,
    )
    owner_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    shared: Mapped[bool] = mapped_column(Boolean, nullable=False)
    layout_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class UserPresentationPreferenceModel(PersistenceBase):
    __tablename__ = "user_presentation_preferences"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
    )
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    theme: Mapped[str] = mapped_column(String(16), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
