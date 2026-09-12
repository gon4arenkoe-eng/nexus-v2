"""Structure tests for immutable execution Ledger persistence."""

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from infra.persistence.models import ExecutionLedgerEventModel


def test_ledger_model_uses_expected_table() -> None:
    assert ExecutionLedgerEventModel.__tablename__ == (
        "execution_ledger_events"
    )


def test_ledger_event_id_is_unique() -> None:
    constraints = ExecutionLedgerEventModel.__table__.constraints

    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_execution_ledger_events_event_id"
        and tuple(column.name for column in constraint.columns)
        == ("event_id",)
        for constraint in constraints
    )


def test_ledger_model_preserves_required_columns() -> None:
    columns = ExecutionLedgerEventModel.__table__.columns

    expected = {
        "id",
        "event_id",
        "event_type",
        "event_version",
        "user_id",
        "plan_id",
        "group_id",
        "leg_id",
        "order_id",
        "fill_id",
        "venue_id",
        "account_value",
        "instrument_venue_id",
        "native_symbol",
        "instrument_type",
        "asset_class",
        "source",
        "correlation_id",
        "causation_id",
        "occurred_at",
        "recorded_at",
        "sequence_no",
        "evidence_source",
        "evidence_quality",
        "schema_version",
        "payload",
    }

    assert set(columns.keys()) == expected


def test_ledger_payload_compiles_as_postgresql_jsonb() -> None:
    ddl = str(
        CreateTable(ExecutionLedgerEventModel.__table__).compile(
            dialect=postgresql.dialect()
        )
    )

    assert "payload JSONB" in ddl


def test_ledger_timestamps_compile_with_timezone() -> None:
    table = ExecutionLedgerEventModel.__table__

    assert table.c.occurred_at.type.timezone is True
    assert table.c.recorded_at.type.timezone is True


def test_ledger_business_lineage_foreign_keys() -> None:
    table = ExecutionLedgerEventModel.__table__

    targets = {
        fk.target_fullname
        for fk in table.foreign_keys
    }

    assert "execution_plans.plan_id" in targets
    assert "position_groups.group_id" in targets
    assert "position_legs.group_id" in targets
    assert "position_legs.leg_id" in targets
    assert "execution_orders.order_id" in targets
    assert "execution_fills.fill_id" in targets


def test_ledger_model_has_no_user_or_exchange_foreign_key() -> None:
    targets = {
        fk.target_fullname
        for fk in ExecutionLedgerEventModel.__table__.foreign_keys
    }

    assert not any(target.startswith("users.") for target in targets)
    assert not any(target.startswith("exchanges.") for target in targets)


def test_ledger_query_indexes_are_present() -> None:
    names = {
        index.name
        for index in ExecutionLedgerEventModel.__table__.indexes
    }

    expected = {
        "ix_execution_ledger_events_user_id",
        "ix_execution_ledger_events_plan_id",
        "ix_execution_ledger_events_group_id",
        "ix_execution_ledger_events_leg_id",
        "ix_execution_ledger_events_order_id",
        "ix_execution_ledger_events_fill_id",
        "ix_execution_ledger_events_venue_id",
        "ix_execution_ledger_events_event_type",
        "ix_execution_ledger_events_occurred_at",
        "ix_execution_ledger_events_correlation_id",
        "ix_execution_ledger_events_causation_id",
    }

    assert expected <= names


def test_ledger_payload_has_server_default() -> None:
    column = ExecutionLedgerEventModel.__table__.c.payload

    assert column.server_default is not None
