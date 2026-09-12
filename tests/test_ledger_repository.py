"""Contract tests for immutable execution Ledger repository."""

from __future__ import annotations

import inspect

from sqlalchemy.ext.asyncio import AsyncSession

from infra.persistence.repositories import ExecutionLedgerRepository


def test_repository_is_constructed_with_async_session() -> None:
    signature = inspect.signature(ExecutionLedgerRepository.__init__)

    assert "session" in signature.parameters


def test_repository_exposes_required_append_read_surface() -> None:
    required = {
        "add",
        "get_by_event_id",
        "list_for_plan",
        "list_for_group",
        "list_for_leg",
        "list_for_order",
        "list_for_fill",
    }

    assert required <= set(dir(ExecutionLedgerRepository))


def test_repository_has_no_ledger_mutation_surface() -> None:
    forbidden = {
        "update",
        "delete",
        "remove",
        "update_ledger_event",
        "delete_ledger_event",
        "remove_ledger_event",
    }

    assert forbidden.isdisjoint(dir(ExecutionLedgerRepository))


def test_repository_source_has_no_transaction_ownership() -> None:
    source = inspect.getsource(ExecutionLedgerRepository)

    assert ".commit(" not in source
    assert ".rollback(" not in source


def test_repository_source_has_no_runtime_execution_dependency() -> None:
    source = inspect.getsource(ExecutionLedgerRepository)

    forbidden = (
        "VenueAdapter",
        "ExecutionCoordinator",
        "ExecutionBoundary",
        "place_order",
        "reconcile",
    )

    assert not any(value in source for value in forbidden)


def test_repository_reads_require_user_scope() -> None:
    methods = (
        ExecutionLedgerRepository.get_by_event_id,
        ExecutionLedgerRepository.list_for_plan,
        ExecutionLedgerRepository.list_for_group,
        ExecutionLedgerRepository.list_for_leg,
        ExecutionLedgerRepository.list_for_order,
        ExecutionLedgerRepository.list_for_fill,
    )

    for method in methods:
        signature = inspect.signature(method)
        assert "user_id" in signature.parameters


def test_session_type_is_async_session() -> None:
    annotation = inspect.signature(
        ExecutionLedgerRepository.__init__
    ).parameters["session"].annotation

    assert annotation in {AsyncSession, "AsyncSession"}
