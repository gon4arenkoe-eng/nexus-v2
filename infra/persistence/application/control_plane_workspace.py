"""Canonical user-workspace layout persistence.

Presentation-only mutation boundary. This module has no trading,
venue, risk or execution authority.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import json
from typing import Any
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from apps.core.application.control_plane import (
    ControlPlaneError,
    WidgetRegistry,
    WorkspaceComposer,
)
from apps.core.application.control_plane_catalog import (
    INITIAL_WIDGET_DEFINITIONS,
)
from infra.persistence.repositories.control_plane import (
    ControlPlaneRepository,
)
from packages.contracts.control_plane import (
    SupportedLocale,
    ThemePreference,
    UserWorkspace,
    WidgetInstance,
    WorkspaceLayoutVersion,
)
from packages.contracts.workspace import (
    WidgetPlacement,
    WidgetSize,
)


class WorkspaceSaveError(RuntimeError):
    """Base presentation persistence failure."""


class WorkspaceSaveInvalid(WorkspaceSaveError):
    """Malformed or registry-invalid save request."""


class WorkspaceSaveNotFound(WorkspaceSaveError):
    """Workspace is unavailable inside trusted identity scope."""


class WorkspaceSaveConflict(WorkspaceSaveError):
    """The caller's base layout version is stale."""


class WorkspaceSaveStateError(WorkspaceSaveError):
    """Canonical persisted workspace state is incomplete."""


_COMPOSER = WorkspaceComposer(
    WidgetRegistry(INITIAL_WIDGET_DEFINITIONS)
)


def _required_text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkspaceSaveInvalid(
            f"{name} must be non-empty text"
        )
    return value.strip()


def _positive_int(value: object, *, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise WorkspaceSaveInvalid(
            f"{name} must be a positive integer"
        )
    return value


def _non_negative_int(
    value: object,
    *,
    name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise WorkspaceSaveInvalid(
            f"{name} must be a non-negative integer"
        )
    return value


def _decode_widgets(
    value: object,
) -> tuple[WidgetInstance, ...]:
    if not isinstance(value, list):
        raise WorkspaceSaveInvalid(
            "widgets must be an array"
        )

    result: list[WidgetInstance] = []

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise WorkspaceSaveInvalid(
                f"widgets[{index}] must be an object"
            )

        settings_json = item.get("settingsJson")

        if not isinstance(settings_json, str):
            raise WorkspaceSaveInvalid(
                f"widgets[{index}].settingsJson must be text"
            )

        try:
            settings_value = json.loads(settings_json)
        except json.JSONDecodeError as exc:
            raise WorkspaceSaveInvalid(
                f"widgets[{index}].settingsJson is invalid JSON"
            ) from exc

        if not isinstance(settings_value, dict):
            raise WorkspaceSaveInvalid(
                f"widgets[{index}].settingsJson "
                "must encode an object"
            )

        context_group = item.get("contextGroup")

        if context_group is not None:
            context_group = _required_text(
                context_group,
                name=f"widgets[{index}].contextGroup",
            )

        try:
            result.append(
                WidgetInstance(
                    placement=WidgetPlacement(
                        instance_id=_required_text(
                            item.get("id"),
                            name=f"widgets[{index}].id",
                        ),
                        widget_key=_required_text(
                            item.get("key"),
                            name=f"widgets[{index}].key",
                        ),
                        widget_version=_positive_int(
                            item.get("widgetVersion"),
                            name=(
                                f"widgets[{index}]"
                                ".widgetVersion"
                            ),
                        ),
                        column=_non_negative_int(
                            item.get("column"),
                            name=f"widgets[{index}].column",
                        ),
                        row=_non_negative_int(
                            item.get("row"),
                            name=f"widgets[{index}].row",
                        ),
                        size=WidgetSize(
                            _positive_int(
                                item.get("width"),
                                name=f"widgets[{index}].width",
                            ),
                            _positive_int(
                                item.get("height"),
                                name=f"widgets[{index}].height",
                            ),
                        ),
                        context_group=context_group,
                    ),
                    settings_json=settings_json,
                )
            )
        except ValueError as exc:
            raise WorkspaceSaveInvalid(str(exc)) from exc

    return tuple(result)


async def save_existing_workspace(
    *,
    session_factory: Any,
    tenant_workspace_id: str,
    user_id: int,
    payload: object,
    created_at: datetime,
) -> tuple[UserWorkspace, WorkspaceLayoutVersion]:
    if not isinstance(payload, dict):
        raise WorkspaceSaveInvalid(
            "payload must be an object"
        )

    workspace_id = _required_text(
        payload.get("workspaceId"),
        name="workspaceId",
    )

    base_version = _positive_int(
        payload.get("baseVersion"),
        name="baseVersion",
    )

    widgets = _decode_widgets(
        payload.get("widgets")
    )

    async with session_factory() as session:
        repository = ControlPlaneRepository(session)

        workspace = await repository.get_user_workspace(
            tenant_workspace_id=tenant_workspace_id,
            user_id=user_id,
            user_workspace_id=workspace_id,
        )

        if workspace is None:
            raise WorkspaceSaveNotFound(
                "workspace unavailable"
            )

        if (
            workspace.active_layout_version
            != base_version
        ):
            raise WorkspaceSaveConflict(
                "workspace base version is stale"
            )

        previous = await repository.get_layout(
            tenant_workspace_id=tenant_workspace_id,
            user_id=user_id,
            user_workspace_id=workspace_id,
            version=base_version,
        )

        if previous is None:
            raise WorkspaceSaveStateError(
                "active workspace layout unavailable"
            )

        try:
            next_layout = _COMPOSER.next_version(
                previous=previous,
                widgets=widgets,
                created_at=created_at,
            )
        except (ControlPlaneError, ValueError) as exc:
            raise WorkspaceSaveInvalid(
                str(exc)
            ) from exc

        updated_workspace = replace(
            workspace,
            active_layout_version=next_layout.version,
            updated_at=created_at,
        )

        try:
            advanced = (
                await repository
                .compare_and_swap_active_layout_version(
                    tenant_workspace_id=tenant_workspace_id,
                    user_id=user_id,
                    user_workspace_id=workspace_id,
                    expected_version=base_version,
                    new_version=next_layout.version,
                    updated_at=created_at,
                )
            )

            if not advanced:
                raise WorkspaceSaveConflict(
                    "workspace base version is stale"
                )

            await repository.append_layout(
                next_layout
            )

            await session.commit()

        except WorkspaceSaveConflict:
            await session.rollback()
            raise

        except ValueError as exc:
            await session.rollback()
            raise WorkspaceSaveConflict(
                "workspace layout version conflict"
            ) from exc

        except Exception:
            await session.rollback()
            raise

        return updated_workspace, next_layout


class WorkspaceCreateError(RuntimeError):
    """Base blank-workspace creation failure."""


class WorkspaceCreateInvalid(WorkspaceCreateError):
    """Malformed workspace create request."""


class WorkspaceCreateConflict(WorkspaceCreateError):
    """Generated workspace identity already exists."""


def _create_text(
    value: object,
    *,
    name: str,
) -> str:
    if not isinstance(value, str):
        raise WorkspaceCreateInvalid(
            f"{name} must be text"
        )

    normalized = value.strip()

    if not normalized:
        raise WorkspaceCreateInvalid(
            f"{name} must be non-empty text"
        )

    return normalized


def _new_workspace_id() -> str:
    return f"ws-{uuid4().hex}"


async def create_blank_workspace(
    *,
    session_factory: Any,
    tenant_workspace_id: str,
    user_id: int,
    payload: object,
    created_at: datetime,
) -> tuple[
    UserWorkspace,
    WorkspaceLayoutVersion,
]:
    if not isinstance(payload, dict):
        raise WorkspaceCreateInvalid(
            "payload must be an object"
        )

    name = _create_text(
        payload.get("name"),
        name="name",
    )

    locale_value = _create_text(
        payload.get("locale"),
        name="locale",
    )

    theme_value = _create_text(
        payload.get("theme"),
        name="theme",
    )

    try:
        locale = SupportedLocale(
            locale_value
        )
    except ValueError as exc:
        raise WorkspaceCreateInvalid(
            "unsupported locale"
        ) from exc

    try:
        theme = ThemePreference(
            theme_value
        )
    except ValueError as exc:
        raise WorkspaceCreateInvalid(
            "unsupported theme"
        ) from exc

    workspace_id = _new_workspace_id()

    workspace = UserWorkspace(
        tenant_workspace_id=tenant_workspace_id,
        user_workspace_id=workspace_id,
        user_id=user_id,
        name=name,
        locale=locale,
        theme=theme,
        active_layout_version=1,
        created_at=created_at,
        updated_at=created_at,
    )

    layout = WorkspaceLayoutVersion(
        tenant_workspace_id=tenant_workspace_id,
        user_workspace_id=workspace_id,
        user_id=user_id,
        version=1,
        widgets=(),
        created_at=created_at,
    )

    _COMPOSER.validate_layout(layout)

    async with session_factory() as session:
        repository = ControlPlaneRepository(
            session
        )

        try:
            await repository.add_user_workspace(
                workspace
            )

            await repository.append_layout(
                layout
            )

            await session.commit()

        except (
            ValueError,
            IntegrityError,
        ) as exc:
            await session.rollback()

            raise WorkspaceCreateConflict(
                "workspace identity conflict"
            ) from exc

        except Exception:
            await session.rollback()
            raise

    return workspace, layout

class WorkspaceRestoreError(RuntimeError):
    """Base workspace layout restore failure."""


class WorkspaceRestoreInvalid(WorkspaceRestoreError):
    """Malformed restore request."""


class WorkspaceRestoreNotFound(WorkspaceRestoreError):
    """Workspace or target layout unavailable in scope."""


class WorkspaceRestoreConflict(WorkspaceRestoreError):
    """Current base layout changed concurrently."""


class WorkspaceRestoreStateError(WorkspaceRestoreError):
    """Canonical current layout is unavailable."""


async def restore_workspace_layout(
    *,
    session_factory: Any,
    tenant_workspace_id: str,
    user_id: int,
    payload: object,
    created_at: datetime,
) -> tuple[
    UserWorkspace,
    WorkspaceLayoutVersion,
]:
    if not isinstance(payload, dict):
        raise WorkspaceRestoreInvalid(
            "payload must be an object"
        )

    workspace_id = _required_text(
        payload.get("workspaceId"),
        name="workspaceId",
    )

    base_version = _positive_int(
        payload.get("baseVersion"),
        name="baseVersion",
    )

    target_version = _positive_int(
        payload.get("targetVersion"),
        name="targetVersion",
    )

    if target_version >= base_version:
        raise WorkspaceRestoreInvalid(
            "targetVersion must be older "
            "than baseVersion"
        )

    async with session_factory() as session:
        repository = ControlPlaneRepository(
            session
        )

        workspace = (
            await repository.get_user_workspace(
                tenant_workspace_id=(
                    tenant_workspace_id
                ),
                user_id=user_id,
                user_workspace_id=(
                    workspace_id
                ),
            )
        )

        if workspace is None:
            raise WorkspaceRestoreNotFound(
                "workspace unavailable"
            )

        if (
            workspace.active_layout_version
            != base_version
        ):
            raise WorkspaceRestoreConflict(
                "workspace base version is stale"
            )

        current = await repository.get_layout(
            tenant_workspace_id=(
                tenant_workspace_id
            ),
            user_id=user_id,
            user_workspace_id=workspace_id,
            version=base_version,
        )

        if current is None:
            raise WorkspaceRestoreStateError(
                "current layout unavailable"
            )

        target = await repository.get_layout(
            tenant_workspace_id=(
                tenant_workspace_id
            ),
            user_id=user_id,
            user_workspace_id=workspace_id,
            version=target_version,
        )

        if target is None:
            raise WorkspaceRestoreNotFound(
                "target layout unavailable"
            )

        try:
            restored = _COMPOSER.restore(
                current=current,
                target=target,
                created_at=created_at,
            )

        except (
            ControlPlaneError,
            ValueError,
        ) as exc:
            raise WorkspaceRestoreInvalid(
                str(exc)
            ) from exc

        updated_workspace = replace(
            workspace,
            active_layout_version=(
                restored.version
            ),
            updated_at=created_at,
        )

        try:
            advanced = (
                await repository
                .compare_and_swap_active_layout_version(
                    tenant_workspace_id=(
                        tenant_workspace_id
                    ),
                    user_id=user_id,
                    user_workspace_id=(
                        workspace_id
                    ),
                    expected_version=(
                        base_version
                    ),
                    new_version=(
                        restored.version
                    ),
                    updated_at=created_at,
                )
            )

            if not advanced:
                raise WorkspaceRestoreConflict(
                    "workspace base version is stale"
                )

            await repository.append_layout(
                restored
            )

            await session.commit()

        except WorkspaceRestoreConflict:
            await session.rollback()
            raise

        except ValueError as exc:
            await session.rollback()

            raise WorkspaceRestoreConflict(
                "workspace restore version conflict"
            ) from exc

        except Exception:
            await session.rollback()
            raise

        return (
            updated_workspace,
            restored,
        )
