from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from apps.core.application.reconciliation_acquisition import (
    ReconciliationAcquisitionScope,
    StartupReconciliationAcquisition,
)
from apps.core.domain.reconciliation import ReconciliationSourceState


@dataclass
class _Snapshot:
    orders: tuple = ()
    fills: tuple = ()
    positions: tuple = ()


class _Local:
    def __init__(self) -> None:
        self.calls = []

    async def load(self, *, user_id, account_id, instrument_id):
        self.calls.append((user_id, account_id, instrument_id))
        return _Snapshot()


class _Venue:
    def __init__(self) -> None:
        self.calls = []
        self.account = object()

    async def get_account_state(self, *, account_id):
        self.calls.append(("account", account_id))
        return self.account

    async def get_open_orders(self, *, account_id, instrument_id=None):
        self.calls.append(("orders", account_id, instrument_id))
        return ()

    async def get_positions(self, *, account_id):
        self.calls.append(("positions", account_id))
        return ()

    async def get_fills(
        self,
        *,
        account_id,
        instrument_id=None,
        since=None,
    ):
        self.calls.append(("fills", account_id, instrument_id))
        return ()

    async def submit_order(self, request):
        raise AssertionError("write attempted")

    async def cancel_order(
        self,
        *,
        account_id,
        instrument_id,
        venue_order_id,
    ):
        raise AssertionError("write attempted")


@pytest.mark.asyncio
async def test_acquisition_builds_current_startup_input():
    from packages.contracts.identities import (
        AccountId,
        AssetClass,
        InstrumentId,
        InstrumentType,
        VenueId,
    )

    venue_id = VenueId("BINGX")
    account_id = AccountId(venue_id=venue_id, value=1)
    instrument_id = InstrumentId(
        venue_id=venue_id,
        native_symbol="BTCUSDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )

    local = _Local()
    venue = _Venue()

    acquisition = StartupReconciliationAcquisition(
        local=local,
        venue=venue,
    )

    result = await acquisition.acquire(
        ReconciliationAcquisitionScope(
            user_id=1,
            account_id=account_id,
            instrument_id=instrument_id,
        )
    )

    assert result.user_id == 1
    assert result.account_id == account_id
    assert result.instrument_id == instrument_id
    assert result.source_state is ReconciliationSourceState.CURRENT
    assert result.local_orders == ()
    assert result.local_fills == ()
    assert result.local_positions == ()
    assert result.venue_orders == ()
    assert result.venue_fills == ()
    assert result.venue_positions == ()
    assert result.venue_account is venue.account

    assert local.calls == [(1, account_id, instrument_id)]
    assert [call[0] for call in venue.calls] == [
        "account",
        "orders",
        "positions",
        "fills",
    ]


@pytest.mark.asyncio
async def test_acquisition_fails_closed_on_venue_failure():
    from packages.contracts.identities import (
        AccountId,
        AssetClass,
        InstrumentId,
        InstrumentType,
        VenueId,
    )

    class FailingVenue(_Venue):
        async def get_open_orders(
            self,
            *,
            account_id,
            instrument_id=None,
        ):
            raise RuntimeError("venue unavailable")

    venue_id = VenueId("BINGX")
    account_id = AccountId(venue_id=venue_id, value=1)
    instrument_id = InstrumentId(
        venue_id=venue_id,
        native_symbol="BTCUSDT",
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )

    acquisition = StartupReconciliationAcquisition(
        local=_Local(),
        venue=FailingVenue(),
    )

    with pytest.raises(RuntimeError, match="venue unavailable"):
        await acquisition.acquire(
            ReconciliationAcquisitionScope(
                user_id=1,
                account_id=account_id,
                instrument_id=instrument_id,
            )
        )
