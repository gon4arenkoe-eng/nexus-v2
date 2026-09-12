"""Typed hierarchical settings contracts for NEXUS V2."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum
import json

from packages.contracts.primitives import normalize_utc_datetime


class SettingDomain(StrEnum):
    TRADING = "TRADING"
    PORTFOLIO_RISK = "PORTFOLIO_RISK"
    STRATEGY = "STRATEGY"
    VENUE_ACCOUNT = "VENUE_ACCOUNT"
    MARKET_DATA = "MARKET_DATA"
    AIEA_RESEARCH = "AIEA_RESEARCH"
    PROMOTION = "PROMOTION"
    NOTIFICATIONS = "NOTIFICATIONS"
    UI = "UI"
    FEATURE_FLAGS = "FEATURE_FLAGS"


class SettingScope(IntEnum):
    SYSTEM_DEFAULT = 0
    WORKSPACE = 10
    EXCHANGE_ACCOUNT = 20
    RISK_PROFILE = 30
    STRATEGY_INSTANCE = 40
    SESSION_OVERRIDE = 50


@dataclass(frozen=True, slots=True)
class SettingValue:
    workspace_id: str
    key: str
    domain: SettingDomain
    scope: SettingScope
    scope_id: str
    value_json: str
    version: int
    safety_critical: bool
    actor_user_id: int
    created_at: datetime

    def __post_init__(self) -> None:
        for name in ("workspace_id", "key", "scope_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
            object.__setattr__(self, name, value.strip())
        if not isinstance(self.domain, SettingDomain):
            raise ValueError("domain must be SettingDomain")
        if not isinstance(self.scope, SettingScope):
            raise ValueError("scope must be SettingScope")
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version <= 0:  # noqa: E501
            raise ValueError("version must be positive")
        if isinstance(self.actor_user_id, bool) or self.actor_user_id <= 0:
            raise ValueError("actor_user_id must be positive")
        if not isinstance(self.safety_critical, bool):
            raise ValueError("safety_critical must be bool")
        try:
            json.loads(self.value_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("value_json must be valid JSON") from exc
        object.__setattr__(self, "created_at", normalize_utc_datetime(self.created_at, field_name="created_at"))  # noqa: E501


@dataclass(frozen=True, slots=True)
class ResolvedSetting:
    key: str
    value_json: str
    source_scope: SettingScope
    source_scope_id: str
    source_version: int
