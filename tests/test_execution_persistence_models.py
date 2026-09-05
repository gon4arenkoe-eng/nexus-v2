from sqlalchemy import (
    BigInteger,
    DateTime,
    Numeric,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from infra.persistence.base import PersistenceBase
from infra.persistence.models.execution import (
    ExecutionPlanLegModel,
    ExecutionPlanModel,
)


def test_execution_plan_tables_registered() -> None:
    tables = set(PersistenceBase.metadata.tables)

    assert {
        "execution_plans",
        "execution_plan_legs",
    }.issubset(tables)


def test_execution_plan_model_uses_canonical_plan_id() -> None:
    table = ExecutionPlanModel.__table__

    assert table.c.plan_id.nullable is False
    assert table.c.plan_id.unique is True
    assert isinstance(table.c.id.type, BigInteger)


def test_execution_plan_contains_rich_plan_evidence() -> None:
    table = ExecutionPlanModel.__table__

    expected = {
        "id",
        "plan_id",
        "intent_id",
        "user_id",
        "shape",
        "strategy",
        "strategy_version",
        "source",
        "created_at",
        "recorded_at",
        "schema_version",
        "metadata",
    }

    assert set(table.c.keys()) == expected
    assert isinstance(table.c.created_at.type, DateTime)
    assert table.c.created_at.type.timezone is True
    assert isinstance(table.c.recorded_at.type, DateTime)
    assert table.c.recorded_at.type.timezone is True


def test_execution_plan_leg_contains_canonical_identity_projection() -> None:
    table = ExecutionPlanLegModel.__table__

    expected = {
        "id",
        "plan_id",
        "leg_id",
        "order_id",
        "client_order_id",
        "venue_id",
        "account_value",
        "instrument_venue_id",
        "native_symbol",
        "instrument_type",
        "asset_class",
        "side",
        "quantity",
        "order_type",
        "limit_price",
        "reduce_only",
        "created_at",
    }

    assert set(table.c.keys()) == expected
    assert isinstance(table.c.account_value.type, BigInteger)


def test_execution_plan_leg_financial_precision_is_explicit() -> None:
    table = ExecutionPlanLegModel.__table__

    quantity_type = table.c.quantity.type
    limit_price_type = table.c.limit_price.type

    assert isinstance(quantity_type, Numeric)
    assert quantity_type.precision == 38
    assert quantity_type.scale == 18

    assert isinstance(limit_price_type, Numeric)
    assert limit_price_type.precision == 38
    assert limit_price_type.scale == 18


def test_execution_plan_leg_uniqueness_contracts_exist() -> None:
    table = ExecutionPlanLegModel.__table__

    unique_column_sets = {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert ("plan_id", "leg_id") in unique_column_sets
    assert ("order_id",) in unique_column_sets
    assert ("client_order_id",) in unique_column_sets


def test_execution_plan_leg_fk_targets_canonical_plan_id() -> None:
    fk = next(
        iter(
            ExecutionPlanLegModel.__table__
            .c.plan_id
            .foreign_keys
        )
    )

    assert fk.target_fullname == "execution_plans.plan_id"


def test_postgresql_plan_metadata_compiles_as_jsonb() -> None:
    sql = str(
        CreateTable(
            ExecutionPlanModel.__table__
        ).compile(
            dialect=postgresql.dialect()
        )
    )

    assert "metadata JSONB NOT NULL" in sql


def test_postgresql_schema_uses_timezone_timestamps() -> None:
    sql = str(
        CreateTable(
            ExecutionPlanModel.__table__
        ).compile(
            dialect=postgresql.dialect()
        )
    )

    assert "TIMESTAMP WITH TIME ZONE" in sql


def test_models_do_not_change_domain_dependency_direction() -> None:
    module = ExecutionPlanModel.__module__

    assert module.startswith("infra.persistence.models")
