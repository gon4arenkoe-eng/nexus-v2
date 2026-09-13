"""BingX DEMO adapter for canonical NEXUS V2 venue contracts.

Raw BingX payload names are intentionally contained in this module.  Core
consumers receive only canonical VenueAdapter values.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Protocol, cast

from apps.core.domain.orders import OrderSide
from apps.core.ports.venue import (
    VenueAccountState,
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


BINGX_VENUE_ID = VenueId("BINGX")


class BingXTransport(Protocol):
    """Authenticated BingX transport boundary.

    The transport owns signing, HTTP authentication material,
    request dispatch, and retry timing. It returns the raw decoded
    BingX response so normalization stays venue-specific.
    """

    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, str],
    ) -> Mapping[str, object]: ...


@dataclass(frozen=True, slots=True)
class BingXDemoConfig:
    """Phase-13 BingX certification settings.

    REAL writes are deliberately unavailable in this slice.
    """

    environment: str = "DEMO"
    allow_demo_writes: bool = False

    def __post_init__(self) -> None:
        environment = self.environment.strip().upper()
        if environment != "DEMO":
            raise ValueError(
                "Phase 13 BingX adapter supports DEMO environment only"
            )
        object.__setattr__(self, "environment", environment)
        if not isinstance(self.allow_demo_writes, bool):
            raise ValueError("allow_demo_writes must be boolean")


class BingXApiError(RuntimeError):
    """Normalized BingX transport/API failure at the adapter boundary."""

    def __init__(
        self,
        *,
        code: int,
        message: str,
        retryable: bool,
    ) -> None:
        super().__init__(f"BingX error {code}: {message}")
        self.code = code
        self.retryable = retryable


_RETRYABLE_CODES = frozenset({100410, 100500, 109500, 110500})

_ORDER_STATES = {
    "NEW": VenueOrderState.ACCEPTED,
    "PENDING": VenueOrderState.PENDING,
    "PARTIALLY_FILLED": VenueOrderState.PARTIALLY_FILLED,
    "FILLED": VenueOrderState.FILLED,
    "CANCELED": VenueOrderState.CANCELLED,
    "CANCELLED": VenueOrderState.CANCELLED,
    "EXPIRED": VenueOrderState.CANCELLED,
    "REJECTED": VenueOrderState.REJECTED,
}


class BingXVenueAdapter(VenueAdapter):
    """Canonical BingX perpetual-swap adapter for DEMO certification."""

    def __init__(
        self,
        *,
        transport: BingXTransport,
        config: BingXDemoConfig | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = transport
        self._config = config if config is not None else BingXDemoConfig()
        self._clock = clock if clock is not None else _utc_now
        self._capabilities = VenueCapabilities(
            frozenset(
                {
                    VenueCapability.HEDGE_MODE,
                    VenueCapability.ORDER_QUERY,
                    VenueCapability.OPEN_ORDER_QUERY,
                    VenueCapability.POSITION_QUERY,
                    VenueCapability.ACCOUNT_QUERY,
                    VenueCapability.FILL_QUERY,
                }
            )
        )

    @property
    def capabilities(self) -> VenueCapabilities:
        return self._capabilities

    async def submit_order(
        self,
        request: VenueOrderRequest,
    ) -> VenueOrderResult:
        self._require_demo_write()
        _require_account(request.account_id)
        _require_instrument(request.instrument_id)

        params = {
            "symbol": _bingx_symbol(request.instrument_id),
            "side": request.side.value,
            "positionSide": _position_side_for_request(request),
            "type": request.order_type.value,
            "quantity": _decimal_text(request.quantity),
            "clientOrderId": request.client_order_id.value,
        }
        if request.limit_price is not None:
            params["price"] = _decimal_text(request.limit_price)
        if request.reduce_only:
            params["reduceOnly"] = "true"

        response = await self._transport.request(
            "POST",
            "/openApi/swap/v2/trade/order",
            params,
        )
        data = _response_data(response)
        order = _order_mapping(data)
        venue_order_id = _optional_venue_order_id(order.get("orderId"))

        return VenueOrderResult(
            client_order_id=request.client_order_id,
            venue_order_id=venue_order_id,
            state=VenueOrderState.ACCEPTED,
            requested_quantity=request.quantity,
            filled_quantity=Decimal("0"),
            average_fill_price=None,
            rejection_reason=None,
        )

    async def cancel_order(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult:
        self._require_demo_write()
        _require_account(account_id)
        _require_instrument(instrument_id)

        await self._transport.request(
            "DELETE",
            "/openApi/swap/v2/trade/order",
            {
                "symbol": _bingx_symbol(instrument_id),
                "orderId": venue_order_id.value,
            },
        )
        return await self.get_order(
            account_id=account_id,
            instrument_id=instrument_id,
            venue_order_id=venue_order_id,
        )

    async def get_order(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult:
        _require_account(account_id)
        _require_instrument(instrument_id)

        response = await self._transport.request(
            "GET",
            "/openApi/swap/v2/trade/order",
            {
                "symbol": _bingx_symbol(instrument_id),
                "orderId": venue_order_id.value,
            },
        )
        return _normalize_order(
            _order_mapping(_response_data(response)),
            fallback_venue_order_id=venue_order_id,
        )

    async def get_open_orders(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId | None = None,
    ) -> tuple[VenueOrderResult, ...]:
        _require_account(account_id)
        params: dict[str, str] = {}
        if instrument_id is not None:
            _require_instrument(instrument_id)
            params["symbol"] = _bingx_symbol(instrument_id)

        response = await self._transport.request(
            "GET",
            "/openApi/swap/v2/trade/openOrders",
            params,
        )
        rows = _list_payload(_response_data(response), keys=("orders",))
        return tuple(
            sorted(
                (_normalize_order(row) for row in rows),
                key=lambda item: (
                    item.venue_order_id.value
                    if item.venue_order_id is not None
                    else item.client_order_id.value
                ),
            )
        )

    async def get_positions(
        self,
        *,
        account_id: AccountId,
    ) -> tuple[VenuePosition, ...]:
        _require_account(account_id)
        response = await self._transport.request(
            "GET",
            "/openApi/swap/v2/user/positions",
            {},
        )
        rows = _list_payload(_response_data(response))
        observed_at = self._observed_at()
        positions: list[VenuePosition] = []

        for row in rows:
            quantity_signed = _decimal(
                row.get("positionAmt", "0"),
                field_name="positionAmt",
            )
            if quantity_signed == Decimal("0"):
                continue
            side = _normalize_position_side(
                row.get("positionSide"),
                quantity_signed,
            )
            quantity = abs(quantity_signed)
            entry_price = _first_positive_decimal(
                row,
                ("avgPrice", "entryPrice"),
            )
            positions.append(
                VenuePosition(
                    account_id=account_id,
                    instrument_id=_instrument_from_bingx_symbol(
                        row.get("symbol")
                    ),
                    side=side,
                    quantity=quantity,
                    entry_price=entry_price,
                    observed_at=observed_at,
                )
            )

        return tuple(
            sorted(
                positions,
                key=lambda item: (
                    item.instrument_id.native_symbol,
                    item.side.value,
                ),
            )
        )

    async def get_account_state(
        self,
        *,
        account_id: AccountId,
    ) -> VenueAccountState:
        _require_account(account_id)
        response = await self._transport.request(
            "GET",
            "/openApi/swap/v3/user/balance",
            {},
        )
        data = _response_data(response)
        balance_payload = (
            data.get("balance")
            if isinstance(data, Mapping)
            else None
        )
        rows = _balance_rows(balance_payload)
        balances = tuple(
            sorted(
                (_normalize_balance(row) for row in rows),
                key=lambda item: item.currency,
            )
        )
        return VenueAccountState(
            account_id=account_id,
            balances=balances,
            observed_at=self._observed_at(),
        )

    async def get_fills(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId | None = None,
        since: datetime | None = None,
    ) -> tuple[VenueFill, ...]:
        _require_account(account_id)
        if instrument_id is None:
            raise ValueError(
                "BingX fillHistory requires instrument_id"
            )
        _require_instrument(instrument_id)

        end_at = self._observed_at()
        start_at = since if since is not None else end_at - timedelta(days=1)
        if start_at.tzinfo is None or start_at.utcoffset() is None:
            raise ValueError("since must be timezone-aware")
        start_at = start_at.astimezone(UTC)
        if start_at > end_at:
            raise ValueError("since must not be after observation time")

        response = await self._transport.request(
            "GET",
            "/openApi/swap/v2/trade/fillHistory",
            {
                "symbol": _bingx_symbol(instrument_id),
                "startTs": str(_milliseconds(start_at)),
                "endTs": str(_milliseconds(end_at)),
                "pageIndex": "1",
                "pageSize": "1000",
            },
        )
        data = _response_data(response)
        rows = _list_payload(data, keys=("fill_orders", "fills", "orders"))
        fills = tuple(
            sorted(
                (
                    _normalize_fill(
                        row,
                        account_id=account_id,
                        fallback_instrument=instrument_id,
                        observed_at=end_at,
                    )
                    for row in rows
                ),
                key=lambda item: (
                    item.executed_at,
                    item.venue_fill_id.value
                    if item.venue_fill_id is not None
                    else "",
                ),
            )
        )
        return fills

    def _require_demo_write(self) -> None:
        if not self._config.allow_demo_writes:
            raise PermissionError(
                "BingX DEMO writes are disabled; explicit enablement required"
            )

    def _observed_at(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "adapter clock must return timezone-aware datetime"
            )
        return value.astimezone(UTC)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _require_account(account_id: AccountId) -> None:
    if not isinstance(account_id, AccountId):
        raise ValueError("account_id must be an AccountId")
    if account_id.venue_id != BINGX_VENUE_ID:
        raise ValueError("account_id must belong to BINGX")


def _require_instrument(instrument_id: InstrumentId) -> None:
    if not isinstance(instrument_id, InstrumentId):
        raise ValueError("instrument_id must be an InstrumentId")
    if instrument_id.venue_id != BINGX_VENUE_ID:
        raise ValueError("instrument_id must belong to BINGX")
    if instrument_id.instrument_type is not InstrumentType.PERPETUAL:
        raise ValueError("BingX adapter requires PERPETUAL instrument")
    if instrument_id.asset_class is not AssetClass.CRYPTO:
        raise ValueError("BingX adapter requires CRYPTO asset class")


def _bingx_symbol(instrument_id: InstrumentId) -> str:
    symbol = instrument_id.native_symbol.strip().upper()
    if "-" in symbol:
        return symbol
    for quote in ("USDT", "USDC"):
        if symbol.endswith(quote) and len(symbol) > len(quote):
            return f"{symbol[:-len(quote)]}-{quote}"
    raise ValueError("unsupported BingX perpetual symbol")


def _instrument_from_bingx_symbol(value: object) -> InstrumentId:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("BingX position symbol must be non-empty")
    return InstrumentId(
        venue_id=BINGX_VENUE_ID,
        native_symbol=value.replace("-", ""),
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )


def _position_side_for_request(request: VenueOrderRequest) -> str:
    if request.reduce_only:
        return "LONG" if request.side is OrderSide.SELL else "SHORT"
    return "LONG" if request.side is OrderSide.BUY else "SHORT"


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _decimal(value: object, *, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid BingX decimal field: {field_name}") from exc
    if not result.is_finite():
        raise ValueError(f"non-finite BingX decimal field: {field_name}")
    return result


def _positive_decimal_or_none(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    result = _decimal(value, field_name="positive_decimal")
    return result if result > Decimal("0") else None


def _first_positive_decimal(
    row: Mapping[str, object],
    keys: tuple[str, ...],
) -> Decimal | None:
    for key in keys:
        result = _positive_decimal_or_none(row.get(key))
        if result is not None:
            return result
    return None


def _response_data(response: Mapping[str, object]) -> object:
    code_raw = response.get("code", 0)
    try:
        code = int(str(code_raw))
    except ValueError as exc:
        raise ValueError("BingX response code must be an integer") from exc
    if code != 0:
        message = str(response.get("msg") or "unknown BingX error")
        raise BingXApiError(
            code=code,
            message=message,
            retryable=code in _RETRYABLE_CODES,
        )
    return response.get("data", {})


def _order_mapping(data: object) -> Mapping[str, object]:
    if not isinstance(data, Mapping):
        raise ValueError("BingX order data must be a mapping")
    inner = data.get("order")
    if isinstance(inner, Mapping):
        return cast(Mapping[str, object], inner)
    return cast(Mapping[str, object], data)


def _list_payload(
    data: object,
    *,
    keys: tuple[str, ...] = (),
) -> tuple[Mapping[str, object], ...]:
    raw = data
    if isinstance(data, Mapping):
        for key in keys:
            candidate = data.get(key)
            if candidate is not None:
                raw = candidate
                break
    if raw in (None, ""):
        return ()
    if isinstance(raw, Mapping):
        raw = [raw]
    if not isinstance(raw, list):
        raise ValueError("BingX list response must be a list")
    rows: list[Mapping[str, object]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("BingX list item must be a mapping")
        rows.append(cast(Mapping[str, object], item))
    return tuple(rows)


def _client_order_id(row: Mapping[str, object]) -> ClientOrderId:
    raw = row.get("clientOrderId") or row.get("clientOrderID")
    if raw is None or not str(raw).strip():
        order_id = row.get("orderId")
        if order_id is None or not str(order_id).strip():
            raise ValueError("BingX order requires clientOrderId or orderId")
        raw = f"venue:{order_id}"
    return ClientOrderId(str(raw))


def _optional_venue_order_id(value: object) -> VenueOrderId | None:
    if value is None or not str(value).strip():
        return None
    return VenueOrderId(str(value))


def _normalize_order(
    row: Mapping[str, object],
    *,
    fallback_venue_order_id: VenueOrderId | None = None,
) -> VenueOrderResult:
    requested_quantity = _decimal(
        row.get("origQty", row.get("quantity", "0")),
        field_name="origQty",
    )
    if requested_quantity <= Decimal("0"):
        raise ValueError("BingX order quantity must be positive")
    filled_quantity = _decimal(
        row.get("executedQty", "0"),
        field_name="executedQty",
    )
    state_raw = str(row.get("status") or "UNKNOWN").upper()
    state = _ORDER_STATES.get(state_raw, VenueOrderState.UNKNOWN)
    average_fill_price = _positive_decimal_or_none(row.get("avgPrice"))
    if filled_quantity > Decimal("0") and average_fill_price is None:
        raise ValueError("BingX filled quantity requires avgPrice")
    rejection_reason = None
    if state is VenueOrderState.REJECTED:
        rejection_reason = str(
            row.get("rejectReason") or row.get("msg") or "BingX rejected order"
        )
    venue_order_id = _optional_venue_order_id(row.get("orderId"))
    if venue_order_id is None:
        venue_order_id = fallback_venue_order_id
    return VenueOrderResult(
        client_order_id=_client_order_id(row),
        venue_order_id=venue_order_id,
        state=state,
        requested_quantity=requested_quantity,
        filled_quantity=filled_quantity,
        average_fill_price=average_fill_price,
        rejection_reason=rejection_reason,
    )


def _normalize_position_side(
    raw: object,
    quantity_signed: Decimal,
) -> VenuePositionSide:
    text = str(raw or "").upper()
    if text == "LONG":
        return VenuePositionSide.LONG
    if text == "SHORT":
        return VenuePositionSide.SHORT
    return (
        VenuePositionSide.LONG
        if quantity_signed > Decimal("0")
        else VenuePositionSide.SHORT
    )


def _balance_rows(value: object) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, Mapping):
        return (cast(Mapping[str, object], value),)
    if isinstance(value, list):
        rows: list[Mapping[str, object]] = []
        for item in value:
            if not isinstance(item, Mapping):
                raise ValueError("BingX balance row must be a mapping")
            rows.append(cast(Mapping[str, object], item))
        return tuple(rows)
    raise ValueError("BingX balance payload must be a mapping or list")


def _normalize_balance(row: Mapping[str, object]) -> VenueBalance:
    currency = str(row.get("asset") or row.get("currency") or "").upper()
    if not currency:
        raise ValueError("BingX balance requires asset")
    total = _decimal(
        row.get("balance", row.get("walletBalance", "0")),
        field_name="balance",
    )
    available = _decimal(
        row.get("availableMargin", row.get("available", "0")),
        field_name="availableMargin",
    )
    return VenueBalance(
        currency=currency,
        total=total,
        available=available,
    )


def _normalize_fill(
    row: Mapping[str, object],
    *,
    account_id: AccountId,
    fallback_instrument: InstrumentId,
    observed_at: datetime,
) -> VenueFill:
    symbol = row.get("symbol")
    instrument_id = (
        _instrument_from_bingx_symbol(symbol)
        if symbol is not None
        else fallback_instrument
    )
    side_raw = str(row.get("side") or "").upper()
    if side_raw not in {"BUY", "SELL"}:
        raise ValueError("BingX fill side must be BUY or SELL")
    quantity = _decimal(
        row.get("qty", row.get("quantity", row.get("executedQty", "0"))),
        field_name="fill quantity",
    )
    price = _decimal(row.get("price", "0"), field_name="fill price")
    fee = _decimal(
        row.get("commission", row.get("fee", "0")),
        field_name="fill fee",
    )
    fee_currency_raw = row.get("commissionAsset") or row.get("feeAsset")
    fee_currency = (
        str(fee_currency_raw).upper()
        if fee > Decimal("0") and fee_currency_raw is not None
        else None
    )
    executed_at = _timestamp_datetime(
        row.get("time", row.get("timestamp", row.get("fillTime")))
    )
    fill_id_raw = row.get("tradeId") or row.get("fillId")
    return VenueFill(
        account_id=account_id,
        instrument_id=instrument_id,
        venue_fill_id=(
            VenueFillId(str(fill_id_raw)) if fill_id_raw is not None else None
        ),
        venue_order_id=_optional_venue_order_id(row.get("orderId")),
        client_order_id=(
            ClientOrderId(str(row.get("clientOrderId")))
            if row.get("clientOrderId")
            else None
        ),
        side=OrderSide(side_raw),
        quantity=quantity,
        price=price,
        fee=fee,
        fee_currency=fee_currency,
        executed_at=executed_at,
        observed_at=observed_at,
    )


def _timestamp_datetime(value: object) -> datetime:
    if value is None:
        raise ValueError("BingX fill requires execution timestamp")
    try:
        milliseconds = int(str(value))
    except ValueError as exc:
        raise ValueError("invalid BingX execution timestamp") from exc
    return datetime.fromtimestamp(milliseconds / 1000, tz=UTC)


def _milliseconds(value: datetime) -> int:
    return int(value.timestamp() * 1000)
