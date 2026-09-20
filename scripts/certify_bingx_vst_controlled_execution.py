"""Controlled BingX VST order lifecycle certification.

This runner is intentionally narrow:
- BingX VST hosts only;
- explicit certification enablement required;
- canonical BingXVenueAdapter write/read boundary;
- unique certification client-order identity;
- LIMIT submit -> observe -> cancel -> observe;
- no database access;
- no production host support;
- no position-closing or protection operations.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
from dataclasses import asdict, dataclass
from decimal import Decimal

from adapters.bingx.http_transport import (
    BingXVstControlledWriteHttpTransport,
    BingXVstHttpConfig,
)
from adapters.bingx.venue import (
    BINGX_VENUE_ID,
    BingXDemoConfig,
    BingXVenueAdapter,
)
from apps.core.domain.orders import OrderSide, OrderType
from apps.core.ports.venue import VenueOrderRequest
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    ClientOrderId,
    InstrumentId,
    InstrumentType,
)


@dataclass(frozen=True, slots=True)
class BingXVstControlledExecutionEvidence:
    environment: str
    symbol: str
    client_order_id: str
    submitted_state: str
    observed_state: str
    cancelled_state: str
    venue_order_id: str
    quantity: str
    limit_price: str
    writes_attempted: bool
    production_environment_used: bool


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} must be set")
    return value


def _require_certification_enablement() -> None:
    if os.environ.get("NEXUS_BINGX_VST_CONTROLLED_WRITE", "") != "I_UNDERSTAND_VST_ONLY":
        raise RuntimeError(
            "controlled BingX VST write requires explicit certification enablement"
        )


def _client_order_id() -> ClientOrderId:
    return ClientOrderId(
        "nexus-cert-" + secrets.token_hex(8)
    )


async def _run() -> BingXVstControlledExecutionEvidence:
    _require_certification_enablement()

    api_key = _required_env("BINGX_VST_API_KEY")
    secret_key = _required_env("BINGX_VST_SECRET_KEY")

    symbol = os.environ.get(
        "BINGX_VST_SYMBOL",
        "BTCUSDT",
    ).strip().upper()

    quantity = Decimal(
        os.environ.get("BINGX_VST_CERT_QUANTITY", "0.0001")
    )
    limit_price = Decimal(
        _required_env("BINGX_VST_CERT_LIMIT_PRICE")
    )

    if quantity <= Decimal("0"):
        raise RuntimeError("certification quantity must be positive")

    if limit_price <= Decimal("0"):
        raise RuntimeError("certification limit price must be positive")

    transport = BingXVstControlledWriteHttpTransport(
        config=BingXVstHttpConfig(
            api_key=api_key,
            secret_key=secret_key,
        )
    )

    adapter = BingXVenueAdapter(
        transport=transport,
        config=BingXDemoConfig(
            environment="DEMO",
            allow_demo_writes=True,
        ),
    )

    account_id = AccountId(
        venue_id=BINGX_VENUE_ID,
        value=1,
    )

    instrument_id = InstrumentId(
        venue_id=BINGX_VENUE_ID,
        native_symbol=symbol,
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )

    client_order_id = _client_order_id()

    request = VenueOrderRequest(
        client_order_id=client_order_id,
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=quantity,
        order_type=OrderType.LIMIT,
        limit_price=limit_price,
        reduce_only=False,
    )

    submitted = await adapter.submit_order(request)

    if submitted.venue_order_id is None:
        raise RuntimeError(
            "BingX certification submit returned no venue_order_id"
        )

    observed = await adapter.get_order(
        account_id=account_id,
        instrument_id=instrument_id,
        venue_order_id=submitted.venue_order_id,
    )

    cancelled = await adapter.cancel_order(
        account_id=account_id,
        instrument_id=instrument_id,
        venue_order_id=submitted.venue_order_id,
    )

    return BingXVstControlledExecutionEvidence(
        environment="BINGX_VST",
        symbol=symbol,
        client_order_id=client_order_id.value,
        submitted_state=submitted.state.value,
        observed_state=observed.state.value,
        cancelled_state=cancelled.state.value,
        venue_order_id=submitted.venue_order_id.value,
        quantity=str(quantity),
        limit_price=str(limit_price),
        writes_attempted=True,
        production_environment_used=False,
    )


def main() -> None:
    evidence = asyncio.run(_run())
    print(json.dumps(asdict(evidence), sort_keys=True))


if __name__ == "__main__":
    main()
