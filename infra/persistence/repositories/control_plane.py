"""Tenant-scoped persistence for Control Plane workspaces and layouts."""

from __future__ import annotations

from datetime import UTC, datetime
import json

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.persistence.models.control_plane import (
    UserPresentationPreferenceModel,
    UserWorkspaceModel,
    WorkspaceLayoutVersionModel,
    WorkspaceTemplateModel,
)
from packages.contracts.control_plane import (
    SupportedLocale,
    ThemePreference,
    UserWorkspace,
    WidgetInstance,
    WorkspaceLayoutVersion,
    WorkspaceTemplate,
)
from packages.contracts.workspace import WidgetPlacement, WidgetSize


def _restore_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _widget_payload(item: WidgetInstance) -> dict[str, object]:
    placement = item.placement
    return {
        "instance_id": placement.instance_id,
        "widget_key": placement.widget_key,
        "widget_version": placement.widget_version,
        "column": placement.column,
        "row": placement.row,
        "columns": placement.size.columns,
        "rows": placement.size.rows,
        "context_group": placement.context_group,
        "settings_json": item.settings_json,
    }


def _encode_widgets(widgets: tuple[WidgetInstance, ...]) -> str:
    payload = [_widget_payload(item) for item in widgets]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _decode_widgets(payload: str) -> tuple[WidgetInstance, ...]:
    raw = json.loads(payload)
    if not isinstance(raw, list):
        raise ValueError("layout_json must contain a list")
    result: list[WidgetInstance] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("layout_json widget must be an object")
        result.append(
            WidgetInstance(
                placement=WidgetPlacement(
                    instance_id=str(item["instance_id"]),
                    widget_key=str(item["widget_key"]),
                    widget_version=int(item["widget_version"]),
                    column=int(item["column"]),
                    row=int(item["row"]),
                    size=WidgetSize(
                        columns=int(item["columns"]),
                        rows=int(item["rows"]),
                    ),
                    context_group=(
                        None
                        if item.get("context_group") is None
                        else str(item["context_group"])
                    ),
                ),
                settings_json=str(item["settings_json"]),
            )
        )
    return tuple(result)


class ControlPlaneRepository:
    def __init__(self, session: AsyncSession) -> None:
        if not isinstance(session, AsyncSession):
            raise ValueError("session must be AsyncSession")
        self._session = session

    async def put_user_workspace(self, value: UserWorkspace) -> None:
        model = await self._session.get(
            UserWorkspaceModel,
            (value.tenant_workspace_id, value.user_workspace_id),
        )
        if model is None:
            self._session.add(
                UserWorkspaceModel(
                    tenant_workspace_id=value.tenant_workspace_id,
                    user_workspace_id=value.user_workspace_id,
                    user_id=value.user_id,
                    name=value.name,
                    locale=value.locale.value,
                    theme=value.theme.value,
                    active_layout_version=value.active_layout_version,
                    created_at=value.created_at,
                    updated_at=value.updated_at,
                )
            )
            return
        if model.user_id != value.user_id:
            raise ValueError("user workspace ownership conflict")
        model.name = value.name
        model.locale = value.locale.value
        model.theme = value.theme.value
        model.active_layout_version = value.active_layout_version
        model.updated_at = value.updated_at

    async def get_user_workspace(
        self,
        *,
        tenant_workspace_id: str,
        user_id: int,
        user_workspace_id: str,
    ) -> UserWorkspace | None:
        model = await self._session.get(
            UserWorkspaceModel,
            (tenant_workspace_id, user_workspace_id),
        )
        if model is None or model.user_id != user_id:
            return None
        return UserWorkspace(
            tenant_workspace_id=model.tenant_workspace_id,
            user_workspace_id=model.user_workspace_id,
            user_id=model.user_id,
            name=model.name,
            locale=SupportedLocale(model.locale),
            theme=ThemePreference(model.theme),
            active_layout_version=model.active_layout_version,
            created_at=_restore_utc(model.created_at),
            updated_at=_restore_utc(model.updated_at),
        )

    async def list_user_workspaces(
        self,
        *,
        tenant_workspace_id: str,
        user_id: int,
    ) -> tuple[UserWorkspace, ...]:
        result = await self._session.execute(
            select(UserWorkspaceModel)
            .where(
                UserWorkspaceModel.tenant_workspace_id == tenant_workspace_id,
                UserWorkspaceModel.user_id == user_id,
            )
            .order_by(UserWorkspaceModel.user_workspace_id)
        )
        return tuple(
            UserWorkspace(
                tenant_workspace_id=model.tenant_workspace_id,
                user_workspace_id=model.user_workspace_id,
                user_id=model.user_id,
                name=model.name,
                locale=SupportedLocale(model.locale),
                theme=ThemePreference(model.theme),
                active_layout_version=model.active_layout_version,
                created_at=_restore_utc(model.created_at),
                updated_at=_restore_utc(model.updated_at),
            )
            for model in result.scalars().all()
        )

    async def append_layout(self, value: WorkspaceLayoutVersion) -> None:
        key = (
            value.tenant_workspace_id,
            value.user_workspace_id,
            value.version,
        )
        payload = _encode_widgets(value.widgets)
        existing = await self._session.get(WorkspaceLayoutVersionModel, key)
        if existing is not None:
            if (
                existing.user_id == value.user_id
                and existing.layout_json == payload
            ):
                return
            raise ValueError("immutable layout version conflict")
        self._session.add(
            WorkspaceLayoutVersionModel(
                tenant_workspace_id=value.tenant_workspace_id,
                user_workspace_id=value.user_workspace_id,
                user_id=value.user_id,
                version=value.version,
                layout_json=payload,
                source_version=value.source_version,
                created_at=value.created_at,
            )
        )

    async def get_layout(
        self,
        *,
        tenant_workspace_id: str,
        user_id: int,
        user_workspace_id: str,
        version: int,
    ) -> WorkspaceLayoutVersion | None:
        model = await self._session.get(
            WorkspaceLayoutVersionModel,
            (tenant_workspace_id, user_workspace_id, version),
        )
        if model is None or model.user_id != user_id:
            return None
        return WorkspaceLayoutVersion(
            tenant_workspace_id=model.tenant_workspace_id,
            user_workspace_id=model.user_workspace_id,
            user_id=model.user_id,
            version=model.version,
            widgets=_decode_widgets(model.layout_json),
            source_version=model.source_version,
            created_at=_restore_utc(model.created_at),
        )

    async def append_template(self, value: WorkspaceTemplate) -> None:
        payload = _encode_widgets(value.widgets)
        existing = await self._session.get(
            WorkspaceTemplateModel,
            (value.template_key, value.version),
        )
        if existing is not None:
            if (
                existing.layout_json == payload
                and existing.owner_workspace_id == value.owner_workspace_id
                and existing.owner_user_id == value.owner_user_id
            ):
                return
            raise ValueError("immutable workspace template conflict")
        self._session.add(
            WorkspaceTemplateModel(
                template_key=value.template_key,
                version=value.version,
                title_key=value.title_key,
                owner_workspace_id=value.owner_workspace_id,
                owner_user_id=value.owner_user_id,
                shared=value.shared,
                layout_json=payload,
                created_at=value.created_at,
            )
        )

    async def list_templates(
        self,
        *,
        tenant_workspace_id: str,
        user_id: int,
    ) -> tuple[WorkspaceTemplate, ...]:
        result = await self._session.execute(
            select(WorkspaceTemplateModel)
            .where(
                or_(
                    WorkspaceTemplateModel.owner_workspace_id.is_(None),
                    WorkspaceTemplateModel.owner_workspace_id
                    == tenant_workspace_id,
                )
            )
            .order_by(
                WorkspaceTemplateModel.template_key,
                WorkspaceTemplateModel.version,
            )
        )
        visible: list[WorkspaceTemplate] = []
        for model in result.scalars().all():
            if (
                model.owner_workspace_id is not None
                and not model.shared
                and model.owner_user_id != user_id
            ):
                continue
            visible.append(
                WorkspaceTemplate(
                    template_key=model.template_key,
                    version=model.version,
                    title_key=model.title_key,
                    owner_workspace_id=model.owner_workspace_id,
                    owner_user_id=model.owner_user_id,
                    shared=model.shared,
                    widgets=_decode_widgets(model.layout_json),
                    created_at=_restore_utc(model.created_at),
                )
            )
        return tuple(visible)

    async def put_user_preferences(
        self,
        *,
        user_id: int,
        locale: SupportedLocale,
        theme: ThemePreference,
        updated_at: datetime,
    ) -> None:
        model = await self._session.get(
            UserPresentationPreferenceModel,
            user_id,
        )
        if model is None:
            self._session.add(
                UserPresentationPreferenceModel(
                    user_id=user_id,
                    locale=locale.value,
                    theme=theme.value,
                    updated_at=updated_at,
                )
            )
            return
        model.locale = locale.value
        model.theme = theme.value
        model.updated_at = updated_at

    async def get_user_preferences(
        self,
        *,
        user_id: int,
    ) -> tuple[SupportedLocale, ThemePreference, datetime] | None:
        model = await self._session.get(
            UserPresentationPreferenceModel,
            user_id,
        )
        if model is None:
            return None
        return (
            SupportedLocale(model.locale),
            ThemePreference(model.theme),
            _restore_utc(model.updated_at),
        )
