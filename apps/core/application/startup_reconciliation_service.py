"""Acquire required startup truth and evaluate reconciliation readiness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from apps.core.application.reconciliation_acquisition import (
    ReconciliationAcquisitionScope,
)
from apps.core.application.startup_reconciliation import (
    StartupReconciliationActivationGate,
    StartupReconciliationDecision,
    StartupReconciliationInput,
)


class StartupReconciliationAcquisitionPort(Protocol):
    """Read-only acquisition boundary required before startup reconciliation."""

    async def acquire(
        self,
        scope: ReconciliationAcquisitionScope,
    ) -> StartupReconciliationInput:
        """Acquire canonical local and venue truth for one scope."""

        ...


@dataclass(frozen=True, slots=True)
class StartupReconciliationService:
    """Acquire all required scopes before evaluating the startup gate."""

    acquisition: StartupReconciliationAcquisitionPort
    gate: StartupReconciliationActivationGate

    async def evaluate(
        self,
        scopes: tuple[ReconciliationAcquisitionScope, ...],
    ) -> StartupReconciliationDecision:
        """Acquire deterministic startup inputs and evaluate fail-closed gate."""

        if not isinstance(scopes, tuple):
            raise ValueError(
                "startup reconciliation scopes must be a tuple"
            )

        if not scopes:
            raise ValueError(
                "startup reconciliation requires at least one scope"
            )

        ordered = tuple(
            sorted(
                scopes,
                key=lambda scope: (
                    scope.user_id,
                    str(scope.account_id.venue_id),
                    scope.account_id.value,
                    str(scope.instrument_id.venue_id),
                    scope.instrument_id.native_symbol,
                    scope.instrument_id.instrument_type.value,
                    scope.instrument_id.asset_class.value,
                ),
            )
        )

        inputs: list[StartupReconciliationInput] = []

        for scope in ordered:
            inputs.append(
                await self.acquisition.acquire(scope)
            )

        return await self.gate.evaluate(tuple(inputs))
