"""Reconciliation Ledger lineage correction tests."""

from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
from pathlib import Path

import pytest

from apps.core.domain.ledger import (
    ExecutionLedgerEvent,
    ExecutionLedgerEventType,
    ledger_event_requires_execution_plan,
)
from infra.persistence.models.ledger import (
    ExecutionLedgerEventModel,
)
from packages.contracts.identities import (
    AccountId,
    VenueId,
)


NOW = datetime(
    2026,
    9,
    12,
    12,
    0,
    tzinfo=UTC,
)

VENUE_ID = VenueId("BINANCE")

ACCOUNT_ID = AccountId(
    venue_id=VENUE_ID,
    value=7,
)


def _planless_event(
    event_type: ExecutionLedgerEventType,
) -> ExecutionLedgerEvent:
    return ExecutionLedgerEvent(
        event_id="reconciliation:test:event",
        event_type=event_type,
        event_version=1,
        user_id=11,
        execution_plan_id=None,
        position_group_id=None,
        position_leg_id=None,
        execution_order_id=None,
        execution_fill_id=None,
        account_id=ACCOUNT_ID,
        venue_id=VENUE_ID,
        occurred_at=NOW,
        recorded_at=NOW,
        source="reconciliation",
        correlation_id=None,
        causation_id=None,
        payload={
            "kind": "VENUE_ORDER_UNKNOWN_LOCALLY",
        },
    )


def test_only_reconciliation_event_families_may_be_planless() -> None:
    planless = {
        ExecutionLedgerEventType.RECONCILIATION_STARTED,
        ExecutionLedgerEventType.RECONCILIATION_DISCREPANCY,
        ExecutionLedgerEventType.RECONCILIATION_RESOLVED,
        ExecutionLedgerEventType.RECONCILIATION_COMPLETED,
        ExecutionLedgerEventType.RECONCILIATION_DEGRADED,
    }

    for event_type in ExecutionLedgerEventType:
        assert (
            ledger_event_requires_execution_plan(event_type)
            is (event_type not in planless)
        )


@pytest.mark.parametrize(
    "event_type",
    (
        ExecutionLedgerEventType.RECONCILIATION_DISCREPANCY,
        ExecutionLedgerEventType.RECONCILIATION_RESOLVED,
    ),
)
def test_planless_reconciliation_event_is_valid(
    event_type: ExecutionLedgerEventType,
) -> None:
    event = _planless_event(event_type)

    assert event.execution_plan_id is None
    assert event.account_id == ACCOUNT_ID
    assert event.venue_id == VENUE_ID


def test_planless_reconciliation_requires_account_and_venue() -> None:
    with pytest.raises(
        ValueError,
        match="requires account_id and venue_id",
    ):
        ExecutionLedgerEvent(
            event_id="reconciliation:no-owner",
            event_type=(
                ExecutionLedgerEventType
                .RECONCILIATION_DISCREPANCY
            ),
            event_version=1,
            user_id=11,
            execution_plan_id=None,
            position_group_id=None,
            position_leg_id=None,
            execution_order_id=None,
            execution_fill_id=None,
            account_id=None,
            venue_id=None,
            occurred_at=NOW,
            recorded_at=NOW,
            source="reconciliation",
            correlation_id=None,
            causation_id=None,
            payload={"kind": "SOURCE_UNAVAILABLE"},
        )


def test_planless_reconciliation_cannot_claim_plan_owned_lineage() -> None:
    with pytest.raises(
        ValueError,
        match="plan-owned aggregate lineage",
    ):
        ExecutionLedgerEvent(
            event_id="reconciliation:false-lineage",
            event_type=(
                ExecutionLedgerEventType
                .RECONCILIATION_DISCREPANCY
            ),
            event_version=1,
            user_id=11,
            execution_plan_id=None,
            position_group_id="group-1",
            position_leg_id=None,
            execution_order_id=None,
            execution_fill_id=None,
            account_id=ACCOUNT_ID,
            venue_id=VENUE_ID,
            occurred_at=NOW,
            recorded_at=NOW,
            source="reconciliation",
            correlation_id=None,
            causation_id=None,
            payload={"kind": "SOURCE_STALE"},
        )


def test_non_reconciliation_event_still_requires_plan() -> None:
    event_type = next(
        event_type
        for event_type in ExecutionLedgerEventType
        if ledger_event_requires_execution_plan(
            event_type
        )
    )

    with pytest.raises(
        ValueError,
        match="execution_plan_id is required",
    ):
        ExecutionLedgerEvent(
            event_id="execution:no-plan",
            event_type=event_type,
            event_version=1,
            user_id=11,
            execution_plan_id=None,
            position_group_id=None,
            position_leg_id=None,
            execution_order_id=None,
            execution_fill_id=None,
            account_id=ACCOUNT_ID,
            venue_id=VENUE_ID,
            occurred_at=NOW,
            recorded_at=NOW,
            source="test",
            correlation_id=None,
            causation_id=None,
            payload={},
        )


def test_orm_plan_id_nullable_with_fk_retained() -> None:
    column = (
        ExecutionLedgerEventModel
        .__table__
        .c
        .plan_id
    )

    assert column.nullable is True
    assert len(column.foreign_keys) == 1

    foreign_key = next(iter(column.foreign_keys))

    assert (
        foreign_key.target_fullname
        == "execution_plans.plan_id"
    )


def _load_migration():
    path = Path(
        "infra/persistence/migrations/versions/"
        "c0f3a91b7e42_allow_planless_reconciliation_events.py"
    )

    spec = importlib.util.spec_from_file_location(
        "reconciliation_lineage_migration",
        path,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def test_migration_lineage() -> None:
    migration = _load_migration()

    assert migration.revision == "c0f3a91b7e42"
    assert migration.down_revision == "7da0d0b113ef"


def test_migration_upgrade_makes_plan_id_nullable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migration = _load_migration()
    calls = []

    monkeypatch.setattr(
        migration.op,
        "alter_column",
        lambda *args, **kwargs: calls.append(
            (args, kwargs)
        ),
    )

    migration.upgrade()

    assert calls == [
        (
            (
                "execution_ledger_events",
                "plan_id",
            ),
            {"nullable": True},
        )
    ]


def test_migration_downgrade_restores_plan_id_not_null(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migration = _load_migration()
    calls = []

    monkeypatch.setattr(
        migration.op,
        "alter_column",
        lambda *args, **kwargs: calls.append(
            (args, kwargs)
        ),
    )

    migration.downgrade()

    assert calls == [
        (
            (
                "execution_ledger_events",
                "plan_id",
            ),
            {"nullable": False},
        )
    ]
