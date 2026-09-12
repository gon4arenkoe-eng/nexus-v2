"""Stable product-access contracts outside of the trading domain."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import re
from typing import Protocol

from packages.contracts.primitives import normalize_utc_datetime

_FEATURE_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_COMMERCIAL_KEY_PREFIXES = frozenset({"plan", "pricing", "subscription"})


def _required_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


@dataclass(frozen=True, slots=True)
class FeatureKey:
    value: str

    def __post_init__(self) -> None:
        normalized = _required_text(self.value, field_name="feature_key").lower()  # noqa: E501
        if not _FEATURE_KEY_RE.fullmatch(normalized):
            raise ValueError("feature_key must be dot-separated lowercase segments")  # noqa: E501
        if normalized.split(".", 1)[0] in _COMMERCIAL_KEY_PREFIXES:
            raise ValueError("feature_key must not encode commercial-plan state")  # noqa: E501
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EntitlementDecision:
    workspace_id: str
    feature_key: FeatureKey
    granted: bool
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _required_text(self.workspace_id, field_name="workspace_id"))  # noqa: E501
        if not isinstance(self.feature_key, FeatureKey):
            raise ValueError("feature_key must be a FeatureKey")
        if not isinstance(self.granted, bool):
            raise ValueError("granted must be bool")
        object.__setattr__(self, "reason", _required_text(self.reason, field_name="reason"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class QuotaResult:
    workspace_id: str
    quota_key: FeatureKey
    permitted: bool
    limit: int | None
    usage: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _required_text(self.workspace_id, field_name="workspace_id"))  # noqa: E501
        if not isinstance(self.quota_key, FeatureKey):
            raise ValueError("quota_key must be a FeatureKey")
        if not isinstance(self.permitted, bool):
            raise ValueError("permitted must be bool")
        if isinstance(self.usage, bool) or not isinstance(self.usage, int) or self.usage < 0:  # noqa: E501
            raise ValueError("usage must be a non-negative integer")
        if self.limit is not None:
            if isinstance(self.limit, bool) or not isinstance(self.limit, int) or self.limit < 0:  # noqa: E501
                raise ValueError("limit must be a non-negative integer or None")  # noqa: E501
            if self.permitted != (self.usage < self.limit):
                raise ValueError("permitted must match the finite quota state")
        elif not self.permitted:
            raise ValueError("unlimited quota must be permitted")


@dataclass(frozen=True, slots=True)
class ProductPlan:
    plan_id: str
    display_name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", _required_text(self.plan_id, field_name="plan_id"))  # noqa: E501
        object.__setattr__(self, "display_name", _required_text(self.display_name, field_name="display_name"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class PlanVersion:
    plan_id: str
    version: int
    entitlements: frozenset[FeatureKey]
    quotas: tuple["QuotaDefinition", ...]
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", _required_text(self.plan_id, field_name="plan_id"))  # noqa: E501
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version <= 0:  # noqa: E501
            raise ValueError("version must be positive")
        if not isinstance(self.entitlements, frozenset) or not all(isinstance(item, FeatureKey) for item in self.entitlements):  # noqa: E501
            raise ValueError("entitlements must be frozenset[FeatureKey]")
        if not isinstance(self.quotas, tuple) or not all(isinstance(item, QuotaDefinition) for item in self.quotas):  # noqa: E501
            raise ValueError("quotas must be tuple[QuotaDefinition, ...]")
        keys = [item.quota_key for item in self.quotas]
        if len(keys) != len(set(keys)):
            raise ValueError("quota definitions must be unique")
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class PlanEntitlement:
    plan_id: str
    plan_version: int
    feature_key: FeatureKey


@dataclass(frozen=True, slots=True)
class QuotaDefinition:
    quota_key: FeatureKey
    limit: int | None

    def __post_init__(self) -> None:
        if not isinstance(self.quota_key, FeatureKey):
            raise ValueError("quota_key must be FeatureKey")
        if self.limit is not None and (isinstance(self.limit, bool) or not isinstance(self.limit, int) or self.limit < 0):  # noqa: E501
            raise ValueError("limit must be non-negative integer or None")


@dataclass(frozen=True, slots=True)
class QuotaSnapshot:
    workspace_id: str
    quota_key: FeatureKey
    usage: int
    limit: int | None
    period_key: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _required_text(self.workspace_id, field_name="workspace_id"))  # noqa: E501
        object.__setattr__(self, "period_key", _required_text(self.period_key, field_name="period_key"))  # noqa: E501
        if not isinstance(self.quota_key, FeatureKey):
            raise ValueError("quota_key must be FeatureKey")
        if isinstance(self.usage, bool) or not isinstance(self.usage, int) or self.usage < 0:  # noqa: E501
            raise ValueError("usage must be non-negative")
        if self.limit is not None and (isinstance(self.limit, bool) or not isinstance(self.limit, int) or self.limit < 0):  # noqa: E501
            raise ValueError("limit must be non-negative integer or None")


class SubscriptionState(StrEnum):
    TRIALING = "TRIALING"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class Subscription:
    subscription_id: str
    workspace_id: str
    plan_id: str
    plan_version: int
    state: SubscriptionState
    updated_at: datetime

    def __post_init__(self) -> None:
        for name in ("subscription_id", "workspace_id", "plan_id"):
            object.__setattr__(self, name, _required_text(getattr(self, name), field_name=name))  # noqa: E501
        if isinstance(self.plan_version, bool) or not isinstance(self.plan_version, int) or self.plan_version <= 0:  # noqa: E501
            raise ValueError("plan_version must be positive")
        if not isinstance(self.state, SubscriptionState):
            raise ValueError("state must be SubscriptionState")
        object.__setattr__(self, "updated_at", normalize_utc_datetime(self.updated_at, field_name="updated_at"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class EntitlementOverride:
    override_id: str
    workspace_id: str
    feature_key: FeatureKey
    granted: bool
    actor_user_id: int
    reason: str
    created_at: datetime
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        for name in ("override_id", "workspace_id", "reason"):
            object.__setattr__(self, name, _required_text(getattr(self, name), field_name=name))  # noqa: E501
        if not isinstance(self.feature_key, FeatureKey):
            raise ValueError("feature_key must be FeatureKey")
        if not isinstance(self.granted, bool):
            raise ValueError("granted must be bool")
        if isinstance(self.actor_user_id, bool) or not isinstance(self.actor_user_id, int) or self.actor_user_id <= 0:  # noqa: E501
            raise ValueError("actor_user_id must be positive")
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))  # noqa: E501
        if self.expires_at is not None:
            object.__setattr__(self, "expires_at", normalize_utc_datetime(self.expires_at, field_name="expires_at"))  # noqa: E501
            if self.expires_at <= self.created_at:
                raise ValueError("expires_at must be after created_at")


@dataclass(frozen=True, slots=True)
class BillingEvent:
    provider: str
    event_id: str
    workspace_id: str
    event_type: str
    payload_hash: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        for name in ("provider", "event_id", "workspace_id", "event_type", "payload_hash"):  # noqa: E501
            object.__setattr__(self, name, _required_text(getattr(self, name), field_name=name))  # noqa: E501
        object.__setattr__(self, "occurred_at", normalize_utc_datetime(self.occurred_at, field_name="occurred_at"))  # noqa: E501


class BillingProviderPort(Protocol):
    async def acknowledge(self, event: BillingEvent) -> None: ...
