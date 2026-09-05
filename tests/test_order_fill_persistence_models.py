from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from infra.persistence.base import PersistenceBase
from infra.persistence.models.execution_orders import (
    ExecutionFillModel,
    ExecutionOrderModel,
)


def _unique_column_sets(table) -> set[tuple[str, ...]]:
    return {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def _check_sql(table) -> set[str]:
    return {
        str(constraint.sqltext)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }


def test_order_fill_tables_registered() -> None:
    assert set(PersistenceBase.metadata.tables) == {
        "execution_plans",
        "execution_plan_legs",
        "position_groups",
        "position_legs",
        "execution_orders",
        "execution_fills",
    }


def test_execution_order_has_canonical_ownership_columns() -> None:
    table = ExecutionOrderModel.__table__

    required = {
        "id",
        "order_id",
        "plan_id",
        "group_id",
        "leg_id",
        "user_id",
        "venue_id",
        "account_value",
        "instrument_venue_id",
        "native_symbol",
        "instrument_type",
        "asset_class",
        "client_order_id",
        "venue_order_id",
        "side",
        "order_type",
        "reduce_only",
        "requested_quantity",
        "filled_quantity",
        "average_fill_price",
        "limit_price",
        "local_status",
        "last_venue_status",
        "last_venue_observed_at",
        "venue_observation_source",
        "rejection_reason",
        "submitted_at",
        "accepted_at",
        "filled_at",
        "cancelled_at",
        "created_at",
        "updated_at",
    }

    assert set(table.c.keys()) == required
    assert table.c.group_id.nullable is False
    assert table.c.leg_id.nullable is False
    assert table.c.order_id.nullable is False
    assert "state_version" not in table.c


def test_execution_order_preserves_plan_foreign_key() -> None:
    table = ExecutionOrderModel.__table__

    direct_plan_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        and tuple(constraint.columns.keys()) == ("plan_id",)
    ]

    assert len(direct_plan_constraints) == 1

    constraint = direct_plan_constraints[0]

    assert tuple(
        element.target_fullname
        for element in constraint.elements
    ) == ("execution_plans.plan_id",)

    assert constraint.ondelete == "RESTRICT"


def test_execution_order_preserves_position_group_plan_fk() -> None:
    table = ExecutionOrderModel.__table__

    constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        and constraint.name == "fk_execution_orders_position_group_plan"
    ]

    assert len(constraints) == 1

    constraint = constraints[0]

    assert tuple(constraint.columns.keys()) == (
        "group_id",
        "plan_id",
    )

    assert tuple(
        element.target_fullname
        for element in constraint.elements
    ) == (
        "position_groups.group_id",
        "position_groups.plan_id",
    )

    assert constraint.ondelete == "RESTRICT"


def test_execution_order_preserves_position_leg_composite_fk() -> None:
    table = ExecutionOrderModel.__table__

    constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        and constraint.name == "fk_execution_orders_position_leg"
    ]

    assert len(constraints) == 1

    constraint = constraints[0]

    assert tuple(constraint.columns.keys()) == (
        "group_id",
        "leg_id",
    )

    assert tuple(
        element.target_fullname
        for element in constraint.elements
    ) == (
        "position_legs.group_id",
        "position_legs.leg_id",
    )

    assert constraint.ondelete == "RESTRICT"


def test_execution_order_idempotency_uniqueness() -> None:
    unique_sets = _unique_column_sets(
        ExecutionOrderModel.__table__
    )

    assert ("order_id",) in unique_sets
    assert ("client_order_id",) in unique_sets


def test_execution_order_local_and_venue_state_are_separate() -> None:
    table = ExecutionOrderModel.__table__

    assert table.c.local_status.nullable is False
    assert table.c.last_venue_status.nullable is True
    assert table.c.last_venue_observed_at.nullable is True
    assert table.c.venue_observation_source.nullable is True

    assert "venue_state" not in table.c
    assert "status" not in table.c


def test_execution_order_financial_precision() -> None:
    table = ExecutionOrderModel.__table__

    for column_name in (
        "requested_quantity",
        "filled_quantity",
        "average_fill_price",
        "limit_price",
    ):
        column_type = table.c[column_name].type

        assert isinstance(column_type, Numeric)
        assert column_type.precision == 38
        assert column_type.scale == 18


def test_execution_order_database_guards() -> None:
    checks = _check_sql(ExecutionOrderModel.__table__)

    assert "user_id > 0" in checks
    assert "account_value > 0" in checks
    assert "venue_id = instrument_venue_id" in checks
    assert "requested_quantity > 0" in checks
    assert "filled_quantity >= 0" in checks
    assert "filled_quantity <= requested_quantity" in checks


def test_execution_fill_has_rich_evidence_columns() -> None:
    table = ExecutionFillModel.__table__

    assert set(table.c.keys()) == {
        "id",
        "fill_id",
        "order_id",
        "user_id",
        "venue_id",
        "account_value",
        "venue_fill_id",
        "quantity",
        "price",
        "fee",
        "fee_currency",
        "executed_at",
        "received_at",
        "created_at",
        "source",
        "raw_evidence_hash",
    }


def test_execution_fill_owns_canonical_execution_order() -> None:
    foreign_keys = ExecutionFillModel.__table__.c.order_id.foreign_keys

    assert len(foreign_keys) == 1

    fk = next(iter(foreign_keys))

    assert fk.target_fullname == "execution_orders.order_id"
    assert fk.ondelete == "RESTRICT"


def test_execution_fill_uniqueness_and_venue_dedup_scope() -> None:
    unique_sets = _unique_column_sets(
        ExecutionFillModel.__table__
    )

    assert ("fill_id",) in unique_sets
    assert (
        "venue_id",
        "account_value",
        "venue_fill_id",
    ) in unique_sets

    assert ("venue_fill_id",) not in unique_sets


def test_execution_fill_financial_precision() -> None:
    table = ExecutionFillModel.__table__

    for column_name in (
        "quantity",
        "price",
        "fee",
    ):
        column_type = table.c[column_name].type

        assert isinstance(column_type, Numeric)
        assert column_type.precision == 38
        assert column_type.scale == 18


def test_execution_fill_database_guards() -> None:
    checks = _check_sql(ExecutionFillModel.__table__)

    assert "user_id > 0" in checks
    assert "account_value > 0" in checks
    assert "quantity > 0" in checks
    assert "price > 0" in checks
    assert "fee >= 0" in checks
    assert "fee = 0 OR fee_currency IS NOT NULL" in checks


def test_order_fill_timestamps_are_timezone_aware() -> None:
    order = ExecutionOrderModel.__table__
    fill = ExecutionFillModel.__table__

    for column_name in (
        "last_venue_observed_at",
        "submitted_at",
        "accepted_at",
        "filled_at",
        "cancelled_at",
        "created_at",
        "updated_at",
    ):
        assert order.c[column_name].type.timezone is True

    for column_name in (
        "executed_at",
        "received_at",
        "created_at",
    ):
        assert fill.c[column_name].type.timezone is True


def test_postgresql_order_fill_schema_compiles() -> None:
    order_sql = str(
        CreateTable(ExecutionOrderModel.__table__).compile(
            dialect=postgresql.dialect(),
        )
    )

    fill_sql = str(
        CreateTable(ExecutionFillModel.__table__).compile(
            dialect=postgresql.dialect(),
        )
    )

    assert "BIGSERIAL" in order_sql
    assert "NUMERIC(38, 18)" in order_sql
    assert "TIMESTAMP WITH TIME ZONE" in order_sql
    assert "FOREIGN KEY(group_id, leg_id)" in order_sql

    assert "BIGSERIAL" in fill_sql
    assert "NUMERIC(38, 18)" in fill_sql
    assert "TIMESTAMP WITH TIME ZONE" in fill_sql


def test_order_fill_models_remain_in_persistence_boundary() -> None:
    assert ExecutionOrderModel.__module__.startswith(
        "infra.persistence.models"
    )
    assert ExecutionFillModel.__module__.startswith(
        "infra.persistence.models"
    )
