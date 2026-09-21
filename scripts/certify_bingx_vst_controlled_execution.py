"""Controlled BingX VST order lifecycle certification.

Supported certification modes:

LIMIT
    LIMIT submit -> observe -> cancel.

PROTECTION
    MARKET LONG open -> position confirmation ->
    STOP_MARKET active -> TAKE_PROFIT_MARKET active ->
    cancel protections -> MARKET LONG close -> flat confirmation.

Safety:
- BingX VST hosts only;
- explicit certification enablement required;
- canonical BingXVenueAdapter boundary;
- no database access;
- no production host support.
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
from apps.core.ports.venue import (
    VenueAdapter,
    VenueOrderRequest,
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
    VenueOrderId,
)


_POLL_ATTEMPTS = 30
_POLL_SECONDS = 0.5


@dataclass(frozen=True, slots=True)
class BingXVstControlledExecutionEvidence:
    environment: str
    mode: str
    symbol: str
    quantity: str
    writes_attempted: bool
    production_environment_used: bool
    client_order_id: str | None = None
    submitted_state: str | None = None
    observed_state: str | None = None
    cancelled_state: str | None = None
    venue_order_id: str | None = None
    limit_price: str | None = None
    open_order_id: str | None = None
    open_state: str | None = None
    entry_price: str | None = None
    stop_order_id: str | None = None
    stop_active: bool | None = None
    take_profit_order_id: str | None = None
    take_profit_active: bool | None = None
    protections_cancelled: bool | None = None
    close_order_id: str | None = None
    close_state: str | None = None
    flat_confirmed: bool | None = None


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} must be set")
    return value


def _require_certification_enablement() -> None:
    if (
        os.environ.get(
            "NEXUS_BINGX_VST_CONTROLLED_WRITE",
            "",
        )
        != "I_UNDERSTAND_VST_ONLY"
    ):
        raise RuntimeError(
            "controlled BingX VST write requires "
            "explicit certification enablement"
        )


def _certification_mode() -> str:
    mode = os.environ.get(
        "NEXUS_BINGX_VST_CERT_MODE",
        "LIMIT",
    ).strip().upper()

    if mode not in {"LIMIT", "PROTECTION"}:
        raise RuntimeError(
            "NEXUS_BINGX_VST_CERT_MODE must be "
            "LIMIT or PROTECTION"
        )

    return mode


def _client_order_id(prefix: str = "nexus-cert") -> ClientOrderId:
    return ClientOrderId(
        f"{prefix}-{secrets.token_hex(8)}"
    )


def _build_adapter(
    api_key: str,
    secret_key: str,
) -> BingXVenueAdapter:
    transport = BingXVstControlledWriteHttpTransport(
        config=BingXVstHttpConfig(
            api_key=api_key,
            secret_key=secret_key,
        )
    )

    return BingXVenueAdapter(
        transport=transport,
        config=BingXDemoConfig(
            environment="DEMO",
            allow_demo_writes=True,
        ),
    )


def _identities(
    symbol: str,
) -> tuple[AccountId, InstrumentId]:
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

    return account_id, instrument_id


async def _wait_for_long_position(
    adapter: VenueAdapter,
    *,
    account_id: AccountId,
    minimum_quantity: Decimal,
) -> VenuePosition:
    for _ in range(_POLL_ATTEMPTS):
        positions = await adapter.get_positions(
            account_id=account_id,
        )

        for position in positions:
            if (
                position.side is VenuePositionSide.LONG
                and position.quantity >= minimum_quantity
            ):
                return position

        await asyncio.sleep(_POLL_SECONDS)

    raise RuntimeError(
        "BingX VST long position was not confirmed"
    )


async def _wait_for_flat_long(
    adapter: VenueAdapter,
    *,
    account_id: AccountId,
) -> None:
    for _ in range(_POLL_ATTEMPTS):
        positions = await adapter.get_positions(
            account_id=account_id,
        )

        long_open = any(
            position.side is VenuePositionSide.LONG
            and position.quantity > Decimal("0")
            for position in positions
        )

        if not long_open:
            return

        await asyncio.sleep(_POLL_SECONDS)

    raise RuntimeError(
        "BingX VST long position did not become flat"
    )


async def _wait_for_open_order(
    adapter: VenueAdapter,
    *,
    account_id: AccountId,
    instrument_id: InstrumentId,
    venue_order_id: VenueOrderId,
) -> None:
    for _ in range(_POLL_ATTEMPTS):
        orders = await adapter.get_open_orders(
            account_id=account_id,
            instrument_id=instrument_id,
        )

        if any(
            order.venue_order_id == venue_order_id
            for order in orders
        ):
            return

        await asyncio.sleep(_POLL_SECONDS)

    raise RuntimeError(
        "BingX VST protective order was not observed active"
    )


async def _cancel_best_effort(
    adapter: VenueAdapter,
    *,
    account_id: AccountId,
    instrument_id: InstrumentId,
    venue_order_id: VenueOrderId | None,
) -> bool:
    if venue_order_id is None:
        return True

    try:
        await adapter.cancel_order(
            account_id=account_id,
            instrument_id=instrument_id,
            venue_order_id=venue_order_id,
        )
    except Exception:
        return False

    return True


async def _close_long_best_effort(
    adapter: VenueAdapter,
    *,
    account_id: AccountId,
    instrument_id: InstrumentId,
) -> VenueOrderId | None:
    positions = await adapter.get_positions(
        account_id=account_id,
    )

    long_position = next(
        (
            position
            for position in positions
            if (
                position.side is VenuePositionSide.LONG
                and position.quantity > Decimal("0")
            )
        ),
        None,
    )

    if long_position is None:
        return None

    close_request = VenueOrderRequest(
        client_order_id=_client_order_id(
            "nexus-cert-close"
        ),
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.SELL,
        quantity=long_position.quantity,
        order_type=OrderType.MARKET,
        position_side=VenuePositionSide.LONG,
        reduce_only=False,
    )

    result = await adapter.submit_order(close_request)
    return result.venue_order_id


async def _run_limit(
    adapter: BingXVenueAdapter,
    *,
    account_id: AccountId,
    instrument_id: InstrumentId,
    symbol: str,
    quantity: Decimal,
) -> BingXVstControlledExecutionEvidence:
    limit_price = Decimal(
        _required_env("BINGX_VST_CERT_LIMIT_PRICE")
    )

    if limit_price <= Decimal("0"):
        raise RuntimeError(
            "certification limit price must be positive"
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
            "BingX certification submit returned "
            "no venue_order_id"
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
        mode="LIMIT",
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


async def _run_protection(
    adapter: BingXVenueAdapter,
    *,
    account_id: AccountId,
    instrument_id: InstrumentId,
    symbol: str,
    quantity: Decimal,
) -> BingXVstControlledExecutionEvidence:
    stop_price = Decimal(
        _required_env("BINGX_VST_CERT_STOP_PRICE")
    )
    take_profit_price = Decimal(
        _required_env("BINGX_VST_CERT_TAKE_PROFIT_PRICE")
    )

    if stop_price <= Decimal("0"):
        raise RuntimeError(
            "certification stop price must be positive"
        )

    if take_profit_price <= Decimal("0"):
        raise RuntimeError(
            "certification take-profit price must be positive"
        )

    stop_order_id: VenueOrderId | None = None
    take_profit_order_id: VenueOrderId | None = None
    close_order_id: VenueOrderId | None = None
    protections_cancelled = False
    flat_confirmed = False

    open_request = VenueOrderRequest(
        client_order_id=_client_order_id(
            "nexus-cert-open"
        ),
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=quantity,
        order_type=OrderType.MARKET,
        position_side=VenuePositionSide.LONG,
        reduce_only=False,
    )

    opened = await adapter.submit_order(open_request)

    if opened.venue_order_id is None:
        raise RuntimeError(
            "BingX VST open returned no venue_order_id"
        )

    try:
        position = await _wait_for_long_position(
            adapter,
            account_id=account_id,
            minimum_quantity=quantity,
        )

        if position.entry_price is None:
            raise RuntimeError(
                "BingX VST long position has no entry price"
            )

        if not (
            stop_price
            < position.entry_price
            < take_profit_price
        ):
            raise RuntimeError(
                "protection prices must satisfy "
                "stop < entry < take_profit"
            )

        stop_request = VenueOrderRequest(
            client_order_id=_client_order_id(
                "nexus-cert-sl"
            ),
            account_id=account_id,
            instrument_id=instrument_id,
            side=OrderSide.SELL,
            quantity=position.quantity,
            order_type=OrderType.STOP_MARKET,
            trigger_price=stop_price,
            position_side=VenuePositionSide.LONG,
            reduce_only=False,
        )

        stop_result = await adapter.submit_order(
            stop_request
        )

        if stop_result.venue_order_id is None:
            raise RuntimeError(
                "BingX VST stop returned no venue_order_id"
            )

        stop_order_id = stop_result.venue_order_id

        await _wait_for_open_order(
            adapter,
            account_id=account_id,
            instrument_id=instrument_id,
            venue_order_id=stop_order_id,
        )

        take_profit_request = VenueOrderRequest(
            client_order_id=_client_order_id(
                "nexus-cert-tp"
            ),
            account_id=account_id,
            instrument_id=instrument_id,
            side=OrderSide.SELL,
            quantity=position.quantity,
            order_type=OrderType.TAKE_PROFIT_MARKET,
            trigger_price=take_profit_price,
            position_side=VenuePositionSide.LONG,
            reduce_only=False,
        )

        take_profit_result = await adapter.submit_order(
            take_profit_request
        )

        if take_profit_result.venue_order_id is None:
            raise RuntimeError(
                "BingX VST take-profit returned "
                "no venue_order_id"
            )

        take_profit_order_id = (
            take_profit_result.venue_order_id
        )

        await _wait_for_open_order(
            adapter,
            account_id=account_id,
            instrument_id=instrument_id,
            venue_order_id=take_profit_order_id,
        )

        stop_cancelled = await _cancel_best_effort(
            adapter,
            account_id=account_id,
            instrument_id=instrument_id,
            venue_order_id=stop_order_id,
        )
        take_profit_cancelled = await _cancel_best_effort(
            adapter,
            account_id=account_id,
            instrument_id=instrument_id,
            venue_order_id=take_profit_order_id,
        )

        protections_cancelled = (
            stop_cancelled
            and take_profit_cancelled
        )

        if not protections_cancelled:
            raise RuntimeError(
                "BingX VST protective order cleanup failed"
            )

        close_order_id = await _close_long_best_effort(
            adapter,
            account_id=account_id,
            instrument_id=instrument_id,
        )

        await _wait_for_flat_long(
            adapter,
            account_id=account_id,
        )
        flat_confirmed = True

        return BingXVstControlledExecutionEvidence(
            environment="BINGX_VST",
            mode="PROTECTION",
            symbol=symbol,
            quantity=str(quantity),
            writes_attempted=True,
            production_environment_used=False,
            open_order_id=opened.venue_order_id.value,
            open_state=opened.state.value,
            entry_price=str(position.entry_price),
            stop_order_id=stop_order_id.value,
            stop_active=True,
            take_profit_order_id=(
                take_profit_order_id.value
            ),
            take_profit_active=True,
            protections_cancelled=True,
            close_order_id=(
                close_order_id.value
                if close_order_id is not None
                else None
            ),
            close_state=(
                VenueOrderState.ACCEPTED.value
                if close_order_id is not None
                else None
            ),
            flat_confirmed=True,
        )

    finally:
        if not protections_cancelled:
            await _cancel_best_effort(
                adapter,
                account_id=account_id,
                instrument_id=instrument_id,
                venue_order_id=stop_order_id,
            )
            await _cancel_best_effort(
                adapter,
                account_id=account_id,
                instrument_id=instrument_id,
                venue_order_id=take_profit_order_id,
            )

        if not flat_confirmed:
            try:
                await _close_long_best_effort(
                    adapter,
                    account_id=account_id,
                    instrument_id=instrument_id,
                )
                await _wait_for_flat_long(
                    adapter,
                    account_id=account_id,
                )
            except Exception:
                pass


async def _run() -> BingXVstControlledExecutionEvidence:
    _require_certification_enablement()

    api_key = _required_env("BINGX_VST_API_KEY")
    secret_key = _required_env("BINGX_VST_SECRET_KEY")

    symbol = os.environ.get(
        "BINGX_VST_SYMBOL",
        "BTCUSDT",
    ).strip().upper()

    quantity = Decimal(
        os.environ.get(
            "BINGX_VST_CERT_QUANTITY",
            "0.0001",
        )
    )

    if quantity <= Decimal("0"):
        raise RuntimeError(
            "certification quantity must be positive"
        )

    adapter = _build_adapter(
        api_key,
        secret_key,
    )
    account_id, instrument_id = _identities(symbol)

    mode = _certification_mode()

    if mode == "LIMIT":
        return await _run_limit(
            adapter,
            account_id=account_id,
            instrument_id=instrument_id,
            symbol=symbol,
            quantity=quantity,
        )

    return await _run_protection(
        adapter,
        account_id=account_id,
        instrument_id=instrument_id,
        symbol=symbol,
        quantity=quantity,
    )


def main() -> None:
    evidence = asyncio.run(_run())
    print(
        json.dumps(
            asdict(evidence),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
