"""Tests for the reusable canonical VenueAdapter contract suite."""

from __future__ import annotations

import asyncio
import inspect
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.core.domain.orders import (
    OrderSide,
)
from apps.core.ports.venue import (
    VenueAccountState,
    VenueAccountObservationState,
    VenueAdapter,
    VenueBalance,
    VenueCapabilities,
    VenueCapability,
    VenueFill,
    VenueOrderRequest,
    VenueOrderResult,
    VenueOrderState,
    VenuePosition,
    VenuePositionSide,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    InstrumentId,
    InstrumentType,
    VenueFillId,
    VenueId,
    VenueOrderId,
)
from packages.testkit.venue_adapter_contracts import (
    VenueAdapterReadContractCase,
    verify_venue_adapter_read_contract,
)


VENUE_ID = VenueId("TEST")
ACCOUNT_ID = AccountId(
    venue_id=VENUE_ID,
    value=1,
)
INSTRUMENT_ID = InstrumentId(
    venue_id=VENUE_ID,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)
CLIENT_ORDER_ID = ClientOrderId("client-1")
VENUE_ORDER_ID = VenueOrderId("venue-order-1")
OBSERVED_AT = datetime(
    2026,
    9,
    12,
    12,
    0,
    tzinfo=UTC,
)


def _order() -> VenueOrderResult:
    return VenueOrderResult(
        client_order_id=CLIENT_ORDER_ID,
        venue_order_id=VENUE_ORDER_ID,
        state=VenueOrderState.ACCEPTED,
        requested_quantity=Decimal("1"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        rejection_reason=None,
    )


def _position() -> VenuePosition:
    return VenuePosition(
        account_id=ACCOUNT_ID,
        instrument_id=INSTRUMENT_ID,
        side=VenuePositionSide.LONG,
        quantity=Decimal("1"),
        entry_price=Decimal("60000"),
        observed_at=OBSERVED_AT,
    )


def _account_state() -> VenueAccountState:
    return VenueAccountState(
        account_id=ACCOUNT_ID,
        state=VenueAccountObservationState.CURRENT,
        balances=(
            VenueBalance(
                asset="USDT",
                total=Decimal("1000"),
                available=Decimal("800"),
            ),
        ),
        observed_at=OBSERVED_AT,
    )


def _fill() -> VenueFill:
    return VenueFill(
        account_id=ACCOUNT_ID,
        instrument_id=INSTRUMENT_ID,
        venue_fill_id=VenueFillId("fill-1"),
        venue_order_id=VENUE_ORDER_ID,
        client_order_id=CLIENT_ORDER_ID,
        side=OrderSide.BUY,
        quantity=Decimal("0.25"),
        price=Decimal("60000"),
        fee=Decimal("1"),
        fee_currency="USDT",
        executed_at=OBSERVED_AT,
        observed_at=OBSERVED_AT,
    )


class ContractVenueAdapter(VenueAdapter):
    """Deterministic adapter proving the reusable contract suite."""

    def __init__(
        self,
        *,
        capabilities: VenueCapabilities | None = None,
    ) -> None:
        self._capabilities = (
            capabilities
            if capabilities is not None
            else VenueCapabilities(
                frozenset(
                    {
                        VenueCapability.ORDER_QUERY,
                        VenueCapability.OPEN_ORDER_QUERY,
                        VenueCapability.POSITION_QUERY,
                        VenueCapability.ACCOUNT_QUERY,
                        VenueCapability.FILL_QUERY,
                    }
                )
            )
        )

        self.calls: list[
            tuple[str, object]
        ] = []

    @property
    def capabilities(self) -> VenueCapabilities:
        return self._capabilities

    async def submit_order(
        self,
        request: VenueOrderRequest,
    ) -> VenueOrderResult:
        raise AssertionError(
            "read contract must not submit orders"
        )

    async def cancel_order(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult:
        raise AssertionError(
            "read contract must not cancel orders"
        )

    async def get_order(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult:
        self.calls.append(
            (
                "get_order",
                (
                    account_id,
                    instrument_id,
                    venue_order_id,
                ),
            )
        )

        return _order()

    async def get_open_orders(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId | None = None,
    ) -> tuple[VenueOrderResult, ...]:
        self.calls.append(
            (
                "get_open_orders",
                (
                    account_id,
                    instrument_id,
                ),
            )
        )

        return (_order(),)

    async def get_positions(
        self,
        *,
        account_id: AccountId,
    ) -> tuple[VenuePosition, ...]:
        self.calls.append(
            (
                "get_positions",
                account_id,
            )
        )

        return (_position(),)

    async def get_account_state(
        self,
        *,
        account_id: AccountId,
    ) -> VenueAccountState:
        self.calls.append(
            (
                "get_account_state",
                account_id,
            )
        )

        return _account_state()

    async def get_fills(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId | None = None,
        since: datetime | None = None,
    ) -> tuple[VenueFill, ...]:
        self.calls.append(
            (
                "get_fills",
                (
                    account_id,
                    instrument_id,
                    since,
                ),
            )
        )

        return (_fill(),)


def _case() -> VenueAdapterReadContractCase:
    return VenueAdapterReadContractCase(
        account_id=ACCOUNT_ID,
        instrument_id=INSTRUMENT_ID,
        venue_order_id=VENUE_ORDER_ID,
        since=OBSERVED_AT,
        order=_order(),
        open_orders=(_order(),),
        positions=(_position(),),
        account_state=_account_state(),
        fills=(_fill(),),
    )


def test_venue_adapter_exposes_required_reconciliation_reads() -> None:
    abstract_methods = VenueAdapter.__abstractmethods__

    assert {
        "get_order",
        "get_open_orders",
        "get_positions",
        "get_account_state",
        "get_fills",
    } <= abstract_methods


def test_reconciliation_reads_are_async() -> None:
    for name in (
        "get_order",
        "get_open_orders",
        "get_positions",
        "get_account_state",
        "get_fills",
    ):
        assert inspect.iscoroutinefunction(
            getattr(VenueAdapter, name)
        )


def test_generic_read_contract_suite_passes() -> None:
    async def scenario() -> None:
        adapter = ContractVenueAdapter()

        await verify_venue_adapter_read_contract(
            adapter=adapter,
            case=_case(),
        )

        assert [
            call[0]
            for call in adapter.calls
        ] == [
            "get_order",
            "get_open_orders",
            "get_positions",
            "get_account_state",
            "get_fills",
        ]

    asyncio.run(scenario())


def test_contract_suite_fails_closed_on_missing_capability() -> None:
    async def scenario() -> None:
        adapter = ContractVenueAdapter(
            capabilities=VenueCapabilities(
                frozenset(
                    {
                        VenueCapability.ORDER_QUERY,
                        VenueCapability.OPEN_ORDER_QUERY,
                        VenueCapability.POSITION_QUERY,
                        VenueCapability.ACCOUNT_QUERY,
                    }
                )
            )
        )

        with pytest.raises(
            ValueError,
            match="unsupported venue capability: FILL_QUERY",
        ):
            await verify_venue_adapter_read_contract(
                adapter=adapter,
                case=_case(),
            )

        assert adapter.calls == []

    asyncio.run(scenario())


def test_read_contract_does_not_use_write_surface() -> None:
    source = inspect.getsource(
        verify_venue_adapter_read_contract
    )

    assert "submit_order" not in source
    assert "cancel_order" not in source


def test_fake_venue_remains_independent_testkit_helper() -> None:
    from packages.testkit.fake_venue import FakeVenue

    assert not issubclass(FakeVenue, VenueAdapter)
