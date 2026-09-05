from sqlalchemy import (
    BigInteger,
    DateTime,
    Numeric,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from infra.persistence.base import PersistenceBase
from infra.persistence.models import (
    ExecutionPlanLegModel,
    ExecutionPlanModel,
    PositionGroupModel,
    PositionLegModel,
)


def test_position_tables_registered_with_existing_execution_tables() -> None:
    assert set(PersistenceBase.metadata.tables) == {
        "execution_plans",
        "execution_plan_legs",
        "position_groups",
        "position_legs",
    }

    assert ExecutionPlanModel.__tablename__ == "execution_plans"
    assert ExecutionPlanLegModel.__tablename__ == "execution_plan_legs"


def test_position_group_contains_canonical_projection_fields() -> None:
    table = PositionGroupModel.__table__

    expected = {
        "id",
        "group_id",
        "plan_id",
        "user_id",
        "shape",
        "strategy",
        "strategy_version",
        "trade_source",
        "status",
        "opened_at",
        "closed_at",
        "created_at",
        "updated_at",
    }

    assert set(table.c.keys()) == expected
    assert table.c.group_id.nullable is False
    assert table.c.group_id.unique is True
    assert isinstance(table.c.id.type, BigInteger)


def test_position_group_has_no_unowned_state_version() -> None:
    assert "state_version" not in PositionGroupModel.__table__.c


def test_position_group_fk_uses_canonical_plan_identity() -> None:
    fk = next(
        iter(
            PositionGroupModel.__table__
            .c.plan_id
            .foreign_keys
        )
    )

    assert fk.target_fullname == "execution_plans.plan_id"


def test_position_group_timestamps_are_timezone_aware() -> None:
    table = PositionGroupModel.__table__

    for column_name in (
        "opened_at",
        "closed_at",
        "created_at",
        "updated_at",
    ):
        column_type = table.c[column_name].type

        assert isinstance(column_type, DateTime)
        assert column_type.timezone is True


def test_position_leg_contains_canonical_projection_fields() -> None:
    table = PositionLegModel.__table__

    expected = {
        "id",
        "group_id",
        "leg_id",
        "venue_id",
        "account_value",
        "instrument_venue_id",
        "native_symbol",
        "instrument_type",
        "asset_class",
        "side",
        "target_quantity",
        "filled_quantity",
        "current_quantity",
        "average_entry_price",
        "average_exit_price",
        "status",
        "opened_at",
        "closed_at",
        "created_at",
        "updated_at",
    }

    assert set(table.c.keys()) == expected
    assert isinstance(table.c.id.type, BigInteger)
    assert isinstance(table.c.account_value.type, BigInteger)


def test_position_leg_has_no_unowned_state_version() -> None:
    assert "state_version" not in PositionLegModel.__table__.c


def test_position_leg_fk_uses_canonical_group_identity() -> None:
    fk = next(
        iter(
            PositionLegModel.__table__
            .c.group_id
            .foreign_keys
        )
    )

    assert fk.target_fullname == "position_groups.group_id"


def test_position_leg_uniqueness_is_group_and_leg() -> None:
    table = PositionLegModel.__table__

    unique_column_sets = {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert ("group_id", "leg_id") in unique_column_sets


def test_position_leg_financial_precision_is_explicit() -> None:
    table = PositionLegModel.__table__

    for column_name in (
        "target_quantity",
        "filled_quantity",
        "current_quantity",
        "average_entry_price",
        "average_exit_price",
    ):
        column_type = table.c[column_name].type

        assert isinstance(column_type, Numeric)
        assert column_type.precision == 38
        assert column_type.scale == 18


def test_position_leg_timestamps_are_timezone_aware() -> None:
    table = PositionLegModel.__table__

    for column_name in (
        "opened_at",
        "closed_at",
        "created_at",
        "updated_at",
    ):
        column_type = table.c[column_name].type

        assert isinstance(column_type, DateTime)
        assert column_type.timezone is True


def test_position_models_compile_for_postgresql() -> None:
    group_sql = str(
        CreateTable(
            PositionGroupModel.__table__
        ).compile(
            dialect=postgresql.dialect()
        )
    )

    leg_sql = str(
        CreateTable(
            PositionLegModel.__table__
        ).compile(
            dialect=postgresql.dialect()
        )
    )

    assert "BIGSERIAL" in group_sql
    assert "TIMESTAMP WITH TIME ZONE" in group_sql

    assert "NUMERIC(38, 18)" in leg_sql
    assert "TIMESTAMP WITH TIME ZONE" in leg_sql


def test_position_leg_database_guards_match_domain_basics() -> None:
    table = PositionLegModel.__table__

    check_sql = {
        str(constraint.sqltext)
        for constraint in table.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }

    assert "account_value > 0" in check_sql
    assert "venue_id = instrument_venue_id" in check_sql
    assert "target_quantity > 0" in check_sql
    assert "filled_quantity >= 0" in check_sql
    assert "current_quantity >= 0" in check_sql


def test_position_models_remain_in_infrastructure_boundary() -> None:
    assert PositionGroupModel.__module__.startswith(
        "infra.persistence.models"
    )
    assert PositionLegModel.__module__.startswith(
        "infra.persistence.models"
    )
