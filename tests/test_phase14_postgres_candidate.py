from __future__ import annotations

import asyncio
import ast
from decimal import Decimal
from pathlib import Path

from apps.core.ports.venue import VenueOrderRequest
from packages.contracts.identities import VenueOrderId
from scripts.phase14_postgres_candidate import (
    ACCOUNT,
    INSTRUMENT,
    Phase14PersistentSimulatedVenue,
    _graph,
)


class FakeObservationStore:
    def __init__(self) -> None:
        self.result = None
        self.records = 0

    async def record_accepted(
        self,
        *,
        user_id,
        account_id,
        instrument_id,
        result,
        observed_at,
    ) -> None:
        self.records += 1
        self.result = result

    async def load_by_venue_order_id(
        self,
        *,
        user_id,
        account_id,
        instrument_id,
        venue_order_id,
    ):
        if (
            self.result is not None
            and self.result.venue_order_id == venue_order_id
        ):
            return self.result
        return None

    async def load_open_orders(
        self,
        *,
        user_id,
        account_id,
        instrument_id,
    ):
        return () if self.result is None else (self.result,)


def test_graph_has_consistent_canonical_ownership() -> None:
    plan, group, legs, order = _graph("test-run")

    assert group.plan_id == plan.plan_id
    assert group.user_id == plan.user_id
    assert len(plan.legs) == len(legs) == 1
    assert plan.legs[0].leg_id == legs[0].leg_id
    assert order.plan_id == plan.plan_id
    assert order.group_id == group.group_id
    assert order.leg_id == legs[0].leg_id
    assert order.order_id == plan.legs[0].order_id
    assert (
        order.client_order_id
        == plan.legs[0].client_order_id
    )


def test_persistent_simulated_venue_round_trip() -> None:
    async def scenario():
        store = FakeObservationStore()
        venue = Phase14PersistentSimulatedVenue(
            store=store,
            user_id=1,
        )
        _, _, _, order = _graph("roundtrip")

        request = VenueOrderRequest(
            client_order_id=order.client_order_id,
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            side=order.side,
            quantity=order.requested_quantity,
            order_type=order.order_type,
            limit_price=order.limit_price,
            reduce_only=order.reduce_only,
        )

        submitted = await venue.submit_order(request)

        loaded = await venue.get_order(
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
            venue_order_id=submitted.venue_order_id,
        )

        open_orders = await venue.get_open_orders(
            account_id=ACCOUNT,
            instrument_id=INSTRUMENT,
        )

        return store, venue, submitted, loaded, open_orders

    store, venue, submitted, loaded, open_orders = asyncio.run(
        scenario()
    )

    assert store.records == 1
    assert len(venue.submitted) == 1
    assert submitted == loaded
    assert open_orders == (submitted,)
    assert submitted.filled_quantity == Decimal("0")
    assert submitted.venue_order_id == VenueOrderId(
        f"sim-{submitted.client_order_id}"
    )


def test_phase14_postgres_candidate_has_no_real_venue_import() -> None:
    path = Path("scripts/phase14_postgres_candidate.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    from_imports = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    combined = imports | from_imports

    forbidden = (
        "infra.venues",
        "bingx",
        "binance",
        "bybit",
        "okx",
    )

    assert not any(
        marker in item.lower()
        for item in combined
        for marker in forbidden
    )


def test_candidate_declares_all_eight_shadow_evidence_dimensions() -> None:
    source = Path("scripts/phase14_postgres_candidate.py").read_text(encoding="utf-8")
    for name in (
        "signals_intents",
        "risk_decisions",
        "order_intent",
        "positions",
        "fills_reconciliation",
        "pnl_attribution",
        "execution_quality",
        "failures_stale_states",
    ):
        assert f'"{name}"' in source

    assert '"shadow_evidence": shadow_evidence' in source
    assert '"real_exchange_writes": 0' in source
