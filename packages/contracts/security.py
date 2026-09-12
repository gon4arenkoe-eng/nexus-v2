"""Canonical multi-user, authorization, audit and secret contracts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from packages.contracts.primitives import normalize_utc_datetime


def _text(value: str, *, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must be non-empty")
    return value


def _user_id(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("user_id must be a positive integer")
    return value


class WorkspaceRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    TRADER = "TRADER"
    VIEWER = "VIEWER"


class Permission(StrEnum):
    WORKSPACE_READ = "workspace.read"
    MEMBERSHIP_MANAGE = "workspace.membership.manage"
    CREDENTIAL_MANAGE = "credential.manage"
    STRATEGY_ACTIVATE = "strategy.activate"
    GRID_MANAGE = "grid.manage"
    RISK_LIMIT_CHANGE = "risk.limit.change"
    EXCHANGE_ENVIRONMENT_CHANGE = "exchange.environment.change"
    LIVE_PERMISSION_CHANGE = "live.permission.change"
    AIEA_PROMOTION_APPROVE = "aiea.promotion.approve"
    MANUAL_RECOVERY = "execution.manual_recovery"
    SETTINGS_WRITE = "settings.write"
    AUDIT_READ = "audit.read"


_ROLE_PERMISSIONS: Mapping[WorkspaceRole, frozenset[Permission]] = MappingProxyType({  # noqa: E501
    WorkspaceRole.OWNER: frozenset(Permission),
    WorkspaceRole.ADMIN: frozenset({
        Permission.WORKSPACE_READ, Permission.MEMBERSHIP_MANAGE,
        Permission.CREDENTIAL_MANAGE, Permission.STRATEGY_ACTIVATE,
        Permission.GRID_MANAGE, Permission.RISK_LIMIT_CHANGE,
        Permission.EXCHANGE_ENVIRONMENT_CHANGE, Permission.MANUAL_RECOVERY,
        Permission.SETTINGS_WRITE, Permission.AUDIT_READ,
    }),
    WorkspaceRole.TRADER: frozenset({
        Permission.WORKSPACE_READ, Permission.STRATEGY_ACTIVATE,
        Permission.GRID_MANAGE, Permission.MANUAL_RECOVERY,
    }),
    WorkspaceRole.VIEWER: frozenset({Permission.WORKSPACE_READ}),
})


@dataclass(frozen=True, slots=True)
class Workspace:
    workspace_id: str
    name: str
    owner_user_id: int
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _text(self.workspace_id, name="workspace_id"))  # noqa: E501
        object.__setattr__(self, "name", _text(self.name, name="name"))
        _user_id(self.owner_user_id)
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class WorkspaceMembership:
    workspace_id: str
    user_id: int
    role: WorkspaceRole
    active: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _text(self.workspace_id, name="workspace_id"))  # noqa: E501
        _user_id(self.user_id)
        if not isinstance(self.role, WorkspaceRole):
            raise ValueError("role must be WorkspaceRole")
        if not isinstance(self.active, bool):
            raise ValueError("active must be bool")


@dataclass(frozen=True, slots=True)
class ResourceOwnership:
    workspace_id: str
    resource_type: str
    resource_id: str
    owner_user_id: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _text(self.workspace_id, name="workspace_id"))  # noqa: E501
        object.__setattr__(self, "resource_type", _text(self.resource_type, name="resource_type"))  # noqa: E501
        object.__setattr__(self, "resource_id", _text(self.resource_id, name="resource_id"))  # noqa: E501
        if self.owner_user_id is not None:
            _user_id(self.owner_user_id)


@dataclass(frozen=True, slots=True)
class AccessDecision:
    workspace_id: str
    user_id: int
    permission: Permission
    granted: bool
    reason: str


class SecretKind(StrEnum):
    EXCHANGE_API_KEY = "EXCHANGE_API_KEY"
    EXCHANGE_API_SECRET = "EXCHANGE_API_SECRET"
    EXCHANGE_PASSPHRASE = "EXCHANGE_PASSPHRASE"


class SecretConsumer(StrEnum):
    CORE_VENUE_ADAPTER = "CORE_VENUE_ADAPTER"
    CONTROL_PLANE_CREDENTIAL_ADMIN = "CONTROL_PLANE_CREDENTIAL_ADMIN"
    AIEA_WORKER = "AIEA_WORKER"


@dataclass(frozen=True, slots=True)
class EncryptedSecretEnvelope:
    workspace_id: str
    resource_id: str
    secret_kind: SecretKind
    ciphertext: str
    key_version: str
    rotated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _text(self.workspace_id, name="workspace_id"))  # noqa: E501
        object.__setattr__(self, "resource_id", _text(self.resource_id, name="resource_id"))  # noqa: E501
        object.__setattr__(self, "ciphertext", _text(self.ciphertext, name="ciphertext"))  # noqa: E501
        object.__setattr__(self, "key_version", _text(self.key_version, name="key_version"))  # noqa: E501
        if not isinstance(self.secret_kind, SecretKind):
            raise ValueError("secret_kind must be SecretKind")
        object.__setattr__(self, "rotated_at", normalize_utc_datetime(self.rotated_at, field_name="rotated_at"))  # noqa: E501

    def __repr__(self) -> str:
        return (
            "EncryptedSecretEnvelope(workspace_id={!r}, resource_id={!r}, "
            "secret_kind={!r}, ciphertext='<redacted>', key_version={!r}, "
            "rotated_at={!r})"
        ).format(self.workspace_id, self.resource_id, self.secret_kind, self.key_version, self.rotated_at)  # noqa: E501


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    workspace_id: str
    actor_user_id: int
    action: str
    resource_type: str
    resource_id: str
    old_value_json: str | None
    new_value_json: str | None
    reason: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        for field in ("event_id", "workspace_id", "action", "resource_type", "resource_id", "reason"):  # noqa: E501
            object.__setattr__(self, field, _text(getattr(self, field), name=field))  # noqa: E501
        _user_id(self.actor_user_id)
        object.__setattr__(self, "occurred_at", normalize_utc_datetime(self.occurred_at, field_name="occurred_at"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class BackgroundJobScope:
    workspace_id: str
    user_id: int
    job_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _text(self.workspace_id, name="workspace_id"))  # noqa: E501
        _user_id(self.user_id)
        object.__setattr__(self, "job_id", _text(self.job_id, name="job_id"))


@dataclass(frozen=True, slots=True)
class RealtimeEventScope:
    workspace_id: str
    user_id: int
    channel: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _text(self.workspace_id, name="workspace_id"))  # noqa: E501
        _user_id(self.user_id)
        object.__setattr__(self, "channel", _text(self.channel, name="channel"))  # noqa: E501


def permissions_for_role(role: WorkspaceRole) -> frozenset[Permission]:
    if not isinstance(role, WorkspaceRole):
        raise ValueError("role must be WorkspaceRole")
    return _ROLE_PERMISSIONS[role]
