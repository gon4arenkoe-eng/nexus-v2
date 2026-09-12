"""Ports used by Portfolio Risk V2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from apps.core.domain.portfolio_risk import (
    PortfolioRiskSnapshot,
    RiskLegCandidate,
)


@dataclass(frozen=True, slots=True)
class SingleLegRiskDecision:
    approved: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.approved, bool):
            raise ValueError("approved must be boolean")
        if self.approved and self.reason is not None:
            raise ValueError(
                "approved single-leg decision cannot contain reason"
            )
        if not self.approved:
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError(
                    "rejected single-leg decision requires reason"
                )


class SingleLegRiskPolicy(Protocol):
    """Existing deterministic single-leg policy boundary."""

    def evaluate(
        self,
        *,
        candidate: RiskLegCandidate,
        portfolio: PortfolioRiskSnapshot,
    ) -> SingleLegRiskDecision:
        """Evaluate one allocated leg without portfolio authority."""
        ...
