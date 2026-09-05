"""Stable product-access contracts outside of the trading domain."""

from __future__ import annotations

from dataclasses import dataclass
import re


_FEATURE_KEY_RE = re.compile(
    r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$"
)
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
    """A stable capability identifier, never a commercial-plan name."""

    value: str

    def __post_init__(self) -> None:
        normalized = _required_text(self.value, field_name="feature_key").lower()
        if not _FEATURE_KEY_RE.fullmatch(normalized):
            raise ValueError("feature_key must be dot-separated lowercase segments")
        if normalized.split(".", 1)[0] in _COMMERCIAL_KEY_PREFIXES:
            raise ValueError("feature_key must not encode commercial-plan state")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EntitlementDecision:
    """Tenant-scoped, backend-authoritative answer for one capability."""

    workspace_id: str
    feature_key: FeatureKey
    granted: bool
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "workspace_id",
            _required_text(self.workspace_id, field_name="workspace_id"),
        )
        if not isinstance(self.feature_key, FeatureKey):
            raise ValueError("feature_key must be a FeatureKey")
        if not isinstance(self.granted, bool):
            raise ValueError("granted must be bool")
        object.__setattr__(
            self,
            "reason",
            _required_text(self.reason, field_name="reason"),
        )


@dataclass(frozen=True, slots=True)
class QuotaResult:
    """An observed quota decision; mutation and usage counting live elsewhere."""

    workspace_id: str
    quota_key: FeatureKey
    permitted: bool
    limit: int | None
    usage: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "workspace_id",
            _required_text(self.workspace_id, field_name="workspace_id"),
        )
        if not isinstance(self.quota_key, FeatureKey):
            raise ValueError("quota_key must be a FeatureKey")
        if not isinstance(self.permitted, bool):
            raise ValueError("permitted must be bool")
        if isinstance(self.usage, bool) or not isinstance(self.usage, int):
            raise ValueError("usage must be an integer")
        if self.usage < 0:
            raise ValueError("usage must be non-negative")
        if self.limit is not None:
            if isinstance(self.limit, bool) or not isinstance(self.limit, int):
                raise ValueError("limit must be an integer or None")
            if self.limit < 0:
                raise ValueError("limit must be non-negative")
            if self.permitted != (self.usage < self.limit):
                raise ValueError("permitted must match the finite quota state")
        elif not self.permitted:
            raise ValueError("unlimited quota must be permitted")
