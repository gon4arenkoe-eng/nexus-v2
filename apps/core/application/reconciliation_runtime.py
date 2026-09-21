"""Transactional reconciliation runtime composition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.application.reconciliation_acquisition import (
    ReconciliationAcquisitionScope,
    StartupReconciliationAcquisition,
)
from apps.core.application.reconciliation_orchestrator import (
    ReconciliationEvidencePort,
    ReconciliationPassOrchestrator,
)
from apps.core.application.startup_reconciliation import (
    StartupReconciliationActivationGate,
)
from apps.core.application.startup_reconciliation_service import (
    StartupReconciliationService,
)
from apps.core.ports.reconciliation_snapshot import (
    LocalReconciliationSnapshotProvider,
)
from apps.core.ports.venue import VenueAdapter


class AsyncSessionContext(Protocol):
    async def __aenter__(self) -> AsyncSession: ...

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> bool | None: ...


class SessionFactory(Protocol):
    def __call__(self) -> AsyncSessionContext: ...


class EvidenceFactory(Protocol):
    def __call__(self, session: AsyncSession) -> ReconciliationEvidencePort: ...


@dataclass(frozen=True, slots=True)
class ReconciliationRuntimeResult:
    reconciliation_gate_passed: bool
    strategy_execution_allowed: bool
    production_authority: bool
    writes_attempted: bool


class ReconciliationRuntime:
    """Acquire truth, reconcile, commit evidence, then publish readiness."""

    def __init__(
        self,
        *,
        session_factory: SessionFactory,
        local: LocalReconciliationSnapshotProvider,
        evidence_factory: EvidenceFactory,
        venue: VenueAdapter,
    ) -> None:
        self._session_factory = session_factory
        self._local = local
        self._evidence_factory = evidence_factory
        self._venue = venue

    async def run_once(
        self,
        scope: ReconciliationAcquisitionScope,
    ) -> ReconciliationRuntimeResult:
        # Acquisition happens before the evidence transaction. The concrete
        # SQLAlchemy snapshot provider owns its read session.
        acquisition = StartupReconciliationAcquisition(
            local=self._local,
            venue=self._venue,
        )
        startup_input = await acquisition.acquire(scope)

        # Evidence persistence owns one explicit transaction. Readiness is
        # never published until this transaction has committed successfully.
        async with self._session_factory() as session:
            async with session.begin():
                evidence = self._evidence_factory(session)

                orchestrator = ReconciliationPassOrchestrator(
                    evidence=evidence,
                )

                gate = StartupReconciliationActivationGate(
                    orchestrator
                )

                decision = await gate.evaluate(
                    (startup_input,)
                )

        return ReconciliationRuntimeResult(
            reconciliation_gate_passed=(
                decision.strategy_execution_allowed
            ),
            # Phase 3 verification must not grant trading authority.
            strategy_execution_allowed=False,
            production_authority=False,
            writes_attempted=False,
        )
