"""Run credential-safe read-only BingX VST certification evidence."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from adapters.bingx.http_transport import (
    BingXVstHttpConfig,
    BingXVstReadOnlyHttpTransport,
)
from adapters.bingx.venue import BINGX_VENUE_ID, BingXVenueAdapter
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
)


@dataclass(frozen=True, slots=True)
class BingXVstReadOnlyEvidence:
    environment: str
    symbol: str
    account_query: str
    open_orders_query: str
    positions_query: str
    fills_query: str
    balance_assets: tuple[str, ...]
    open_order_count: int
    position_count: int
    fill_count: int
    observed_at: str
    writes_attempted: bool
    real_environment_used: bool


async def _run() -> BingXVstReadOnlyEvidence:
    api_key = _required_env("BINGX_VST_API_KEY")
    secret_key = _required_env("BINGX_VST_SECRET_KEY")
    symbol = os.environ.get("BINGX_VST_SYMBOL", "BTCUSDT").strip().upper()

    transport = BingXVstReadOnlyHttpTransport(
        config=BingXVstHttpConfig(
            api_key=api_key,
            secret_key=secret_key,
        )
    )
    adapter = BingXVenueAdapter(transport=transport)
    account_id = AccountId(venue_id=BINGX_VENUE_ID, value=1)
    instrument_id = InstrumentId(
        venue_id=BINGX_VENUE_ID,
        native_symbol=symbol,
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )

    account = await adapter.get_account_state(account_id=account_id)
    open_orders = await adapter.get_open_orders(
        account_id=account_id,
        instrument_id=instrument_id,
    )
    positions = await adapter.get_positions(account_id=account_id)
    now = datetime.now(UTC)
    fills = await adapter.get_fills(
        account_id=account_id,
        instrument_id=instrument_id,
        since=now - timedelta(hours=24),
    )

    return BingXVstReadOnlyEvidence(
        environment="BINGX_VST",
        symbol=symbol,
        account_query="PASS",
        open_orders_query="PASS",
        positions_query="PASS",
        fills_query="PASS",
        balance_assets=tuple(item.currency for item in account.balances),
        open_order_count=len(open_orders),
        position_count=len(positions),
        fill_count=len(fills),
        observed_at=datetime.now(UTC).isoformat(),
        writes_attempted=False,
        real_environment_used=False,
    )


def _required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.strip():
        raise RuntimeError(f"required environment variable is missing: {name}")
    return value


def main() -> int:
    evidence = asyncio.run(_run())
    print(json.dumps(asdict(evidence), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
