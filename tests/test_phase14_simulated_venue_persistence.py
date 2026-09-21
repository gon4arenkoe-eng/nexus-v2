from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.core.ports.venue import (
    VenueOrderResult,
    VenueOrderState,
)
from infra.persistence.models.execution_orders import (
    ExecutionOrderModel,
)
from infra.persistence.repositories.phase14_simulated_venue import (
    PHASE14_SIMULATED_SOURCE,
    Phase14SimulatedVenueObservationRepository,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    InstrumentId,
    InstrumentType,
    VenueId,
    VenueOrderId,
)


NOW = datetime(2026, 9, 21, 18, 0, tzinfo=UTC)
VENUE = VenueId("SIM")
ACCOUNT = AccountId(VENUE, 1)
INSTRUMENT = InstrumentId(
    VENUE,
    "BTCUSDT",
    InstrumentType.PERPETUAL,
    AssetClass.CRYPTO,
)


class FakeScalarResult:
    def __init__(self, one=None, many=()):
        self._one = one
        self._many = tuple(many)

    def scalar_one_or_none(self):
        return self._one

    def scalars(self):
        return self

    def all(self):
        return list(self._many)


class FakeSession:
    def __init__(self, results):
        self.results = list(results)
        self.statements = []
        self.flushes = 0

    async def execute(self, statement):
        self.statements.append(statement)
        return self.results.pop(0)

    async def flush(self):
        self.flushes += 1


def make_model() -> ExecutionOrderModel:
    return ExecutionOrderModel(
        order_id="order-1",
        plan_id="plan-1",
        group_id="group-1",
        leg_id="leg-1",
        user_id=1,
        venue_id="SIM",
        account_value=1,
        instrument_venue_id="SIM",
        native_symbol="BTCUSDT",
        instrument_type="PERPETUAL",
        asset_class="CRYPTO",
        client_order_id="client-1",
        venue_order_id=None,
        side="BUY",
        order_type="LIMIT",
        reduce_only=False,
        requested_quantity=Decimal("0.001"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        limit_price=Decimal("100"),
        local_status="PENDING",
        last_venue_status=None,
        last_venue_observed_at=None,
        venue_observation_source=None,
        rejection_reason=None,
        submitted_at=None,
        accepted_at=None,
        filled_at=None,
        cancelled_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


def accepted_result() -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=ClientOrderId("client-1"),
        venue_order_id=VenueOrderId("sim-order-1"),
        state=VenueOrderState.ACCEPTED,
        requested_quantity=Decimal("0.001"),
        filled_quantity=Decimal("0"),
    )


def test_record_accepted_updates_existing_canonical_order() -> None:
    model = make_model()
    session = FakeSession([FakeScalarResult(one=model)])
    repo = Phase14SimulatedVenueObservationRepository(session)

    asyncio.run(
        repo.record_accepted(
            user_id=1,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            result=accepted_result(),
            observed_at=NOW,
        )
    )

    assert model.venue_order_id == "sim-order-1"
    assert model.last_venue_status == "ACCEPTED"
    assert model.last_venue_observed_at == NOW
    assert (
        model.venue_observation_source
        == PHASE14_SIMULATED_SOURCE
    )
    assert session.flushes == 1


def test_record_unknown_canonical_order_fails_closed() -> None:
    session = FakeSession([FakeScalarResult(one=None)])
    repo = Phase14SimulatedVenueObservationRepository(session)

    with pytest.raises(
        LookupError,
        match="canonical execution order not found",
    ):
        asyncio.run(
            repo.record_accepted(
                user_id=1,
                account_id=ACCOUNT,
                instrument_id=INSTRUMENT,
                result=accepted_result(),
                observed_at=NOW,
            )
        )

    assert session.flushes == 0


def test_non_accepted_result_is_rejected() -> None:
    session = FakeSession([])
    repo = Phase14SimulatedVenueObservationRepository(session)

    result = VenueOrderResult(
        client_order_id=ClientOrderId("client-1"),
        venue_order_id=VenueOrderId("sim-order-1"),
        state=VenueOrderState.UNKNOWN,
        requested_quantity=Decimal("0.001"),
        filled_quantity=Decimal("0"),
    )

    with pytest.raises(
        ValueError,
        match="only ACCEPTED",
    ):
        asyncio.run(
            repo.record_accepted(
                user_id=1,
                account_id=ACCOUNT,
                instrument_id=INSTRUMENT,
                result=result,
                observed_at=NOW,
            )
        )


def test_load_by_venue_order_id_round_trips_accepted_result() -> None:
    model = make_model()
    model.venue_order_id = "sim-order-1"
    model.last_venue_status = "ACCEPTED"
    model.last_venue_observed_at = NOW
    model.venue_observation_source = PHASE14_SIMULATED_SOURCE

    session = FakeSession([FakeScalarResult(one=model)])
    repo = Phase14SimulatedVenueObservationRepository(session)

    restored = asyncio.run(
        repo.load_by_venue_order_id(
            user_id=1,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            venue_order_id=VenueOrderId("sim-order-1"),
        )
    )

    assert restored == accepted_result()


def test_load_open_orders_is_scoped_by_user_account_instrument() -> None:
    model = make_model()
    model.venue_order_id = "sim-order-1"
    model.last_venue_status = "ACCEPTED"
    model.venue_observation_source = PHASE14_SIMULATED_SOURCE

    session = FakeSession([
        FakeScalarResult(many=(model,))
    ])
    repo = Phase14SimulatedVenueObservationRepository(session)

    restored = asyncio.run(
        repo.load_open_orders(
            user_id=1,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
        )
    )

    assert restored == (accepted_result(),)

    sql = str(session.statements[0])

    for required in (
        "execution_orders.user_id",
        "execution_orders.venue_id",
        "execution_orders.account_value",
        "execution_orders.instrument_venue_id",
        "execution_orders.native_symbol",
        "execution_orders.instrument_type",
        "execution_orders.asset_class",
    ):
        assert required in sql
