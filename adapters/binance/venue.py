"""Binance USD-M adapter foundation for canonical NEXUS V2 venue contracts.

This slice intentionally contains raw Binance field names only inside the
adapter package.  It uses an injected transport so signing, credentials,
network retries, and the real testnet runtime remain a separate certification
slice.  Production/live transport is not introduced here.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Protocol, cast

from adapters.common.normalization import (
    FillNormalizationContext,
    NormalizationEntity,
    OrderNormalizationContext,
    PositionNormalizationContext,
    VenueNormalizationProfile,
)
from apps.core.domain.orders import OrderSide, OrderType
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


BINANCE_USDM_VENUE_ID = VenueId("BINANCE")


class BinanceUsdMTransport(Protocol):
    """Signed/authenticated transport boundary owned outside canonical Core."""

    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, str],
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class BinanceUsdMTestnetConfig:
    """Phase-13 Binance USD-M foundation settings.

    Only TESTNET is permitted in this slice.  Writes are opt-in and remain
    fake/injected until the dedicated HTTP/signing certification slice.
    """

    environment: str = "TESTNET"
    allow_testnet_writes: bool = False
    position_mode: str = "ONEWAY"

    def __post_init__(self) -> None:
        environment = self.environment.strip().upper()
        if environment != "TESTNET":
            raise ValueError("Binance USD-M foundation supports TESTNET only")
        object.__setattr__(self, "environment", environment)
        if not isinstance(self.allow_testnet_writes, bool):
            raise ValueError("allow_testnet_writes must be boolean")
        position_mode = self.position_mode.strip().upper()
        if position_mode != "ONEWAY":
            raise ValueError(
                "Binance USD-M foundation is fail-closed to ONEWAY mode; "
                "HEDGE mode requires a separate canonical position-mode slice"
            )
        object.__setattr__(self, "position_mode", position_mode)


class BinanceUsdMApiError(RuntimeError):
    """Normalized Binance API failure at the adapter boundary."""

    def __init__(self, *, code: int, message: str, retryable: bool) -> None:
        super().__init__(f"Binance USD-M error {code}: {message}")
        self.code = code
        self.retryable = retryable


_RETRYABLE_CODES = frozenset({-1001, -1003, -1006, -1007, -1008, -1021})
_ORDER_STATES = {
    "NEW": VenueOrderState.ACCEPTED,
    "PARTIALLY_FILLED": VenueOrderState.PARTIALLY_FILLED,
    "FILLED": VenueOrderState.FILLED,
    "CANCELED": VenueOrderState.CANCELLED,
    "CANCELLED": VenueOrderState.CANCELLED,
    "EXPIRED": VenueOrderState.CANCELLED,
    "EXPIRED_IN_MATCH": VenueOrderState.CANCELLED,
    "REJECTED": VenueOrderState.REJECTED,
    "PENDING_CANCEL": VenueOrderState.PENDING,
}


class BinanceUsdMNormalizer:
    """Venue-specific raw-payload mapper into canonical NEXUS values."""

    venue_id = BINANCE_USDM_VENUE_ID

    @property
    def profile(self) -> VenueNormalizationProfile:
        return VenueNormalizationProfile(
            venue_id=self.venue_id,
            supported=frozenset(
                {
                    NormalizationEntity.INSTRUMENT,
                    NormalizationEntity.ORDER,
                    NormalizationEntity.POSITION,
                    NormalizationEntity.BALANCE,
                    NormalizationEntity.FILL,
                }
            ),
        )

    def normalize_instrument(self, raw: Mapping[str, object]) -> InstrumentId:
        symbol = raw.get("symbol")
        return _instrument_from_symbol(symbol)

    def normalize_order(
        self,
        raw: Mapping[str, object],
        *,
        context: OrderNormalizationContext = OrderNormalizationContext(),
    ) -> VenueOrderResult:
        requested_quantity = _decimal(raw.get("origQty", "0"), field_name="origQty")
        if requested_quantity <= Decimal("0"):
            raise ValueError("Binance order quantity must be positive")
        filled_quantity = _decimal(
            raw.get("executedQty", raw.get("cumQty", "0")),
            field_name="executedQty",
        )
        state = _ORDER_STATES.get(
            str(raw.get("status") or "UNKNOWN").upper(),
            VenueOrderState.UNKNOWN,
        )
        average_fill_price = _positive_decimal_or_none(raw.get("avgPrice"))
        if filled_quantity > Decimal("0") and average_fill_price is None:
            quote = _positive_decimal_or_none(raw.get("cumQuote"))
            if quote is not None:
                average_fill_price = quote / filled_quantity
        if filled_quantity > Decimal("0") and average_fill_price is None:
            raise ValueError("Binance filled quantity requires average fill price")
        rejection_reason = None
        if state is VenueOrderState.REJECTED:
            rejection_reason = str(
                raw.get("rejectReason") or raw.get("msg") or "Binance rejected order"
            )
        venue_order_id = _optional_venue_order_id(raw.get("orderId"))
        if venue_order_id is None:
            venue_order_id = context.fallback_venue_order_id
        return VenueOrderResult(
            client_order_id=_client_order_id(raw),
            venue_order_id=venue_order_id,
            state=state,
            requested_quantity=requested_quantity,
            filled_quantity=filled_quantity,
            average_fill_price=average_fill_price,
            rejection_reason=rejection_reason,
        )

    def normalize_position(
        self,
        raw: Mapping[str, object],
        *,
        context: PositionNormalizationContext,
    ) -> VenuePosition | None:
        instrument_id = _instrument_from_symbol(raw.get("symbol"))
        quantity_signed = _decimal(raw.get("positionAmt", "0"), field_name="positionAmt")
        if quantity_signed == Decimal("0"):
            return None
        side = _normalize_position_side(raw.get("positionSide"), quantity_signed)
        entry_price = _positive_decimal_or_none(raw.get("entryPrice"))
        if entry_price is None:
            raise ValueError("Binance open position requires entryPrice")
        return VenuePosition(
            account_id=context.account_id,
            instrument_id=instrument_id,
            side=side,
            quantity=abs(quantity_signed),
            entry_price=entry_price,
            observed_at=context.observed_at,
        )

    def normalize_balance(self, raw: Mapping[str, object]) -> VenueBalance:
        currency = str(raw.get("asset") or "").strip().upper()
        if not currency:
            raise ValueError("Binance balance requires asset")
        return VenueBalance(
            currency=currency,
            total=_decimal(raw.get("balance", "0"), field_name="balance"),
            available=_decimal(
                raw.get("availableBalance", raw.get("withdrawAvailable", "0")),
                field_name="availableBalance",
            ),
        )

    def normalize_fill(
        self,
        raw: Mapping[str, object],
        *,
        context: FillNormalizationContext,
    ) -> VenueFill:
        instrument = (
            _instrument_from_symbol(raw.get("symbol"))
            if raw.get("symbol") is not None
            else context.fallback_instrument
        )
        side_raw = str(raw.get("side") or "").upper()
        if side_raw not in {"BUY", "SELL"}:
            buyer = raw.get("buyer")
            if isinstance(buyer, bool):
                side_raw = "BUY" if buyer else "SELL"
            else:
                raise ValueError("Binance fill side must be BUY or SELL")
        fee = _decimal(raw.get("commission", "0"), field_name="commission")
        fee_asset = raw.get("commissionAsset")
        return VenueFill(
            account_id=context.account_id,
            instrument_id=instrument,
            venue_fill_id=(
                VenueFillId(str(raw.get("id"))) if raw.get("id") is not None else None
            ),
            venue_order_id=_optional_venue_order_id(raw.get("orderId")),
            client_order_id=(
                ClientOrderId(str(raw.get("clientOrderId")))
                if raw.get("clientOrderId")
                else None
            ),
            side=OrderSide(side_raw),
            quantity=_decimal(raw.get("qty", "0"), field_name="qty"),
            price=_decimal(raw.get("price", "0"), field_name="price"),
            fee=fee,
            fee_currency=(
                str(fee_asset).upper()
                if fee > Decimal("0") and fee_asset is not None
                else None
            ),
            executed_at=_timestamp_datetime(raw.get("time")),
            observed_at=context.observed_at,
        )


class BinanceUsdMVenueAdapter(VenueAdapter):
    """Canonical Binance USD-M perpetual adapter foundation for TESTNET."""

    def __init__(
        self,
        *,
        transport: BinanceUsdMTransport,
        config: BinanceUsdMTestnetConfig | None = None,
        clock: Callable[[], datetime] | None = None,
        normalizer: BinanceUsdMNormalizer | None = None,
    ) -> None:
        self._transport = transport
        self._config = config if config is not None else BinanceUsdMTestnetConfig()
        self._clock = clock if clock is not None else _utc_now
        self._normalizer = normalizer if normalizer is not None else BinanceUsdMNormalizer()
        self._capabilities = VenueCapabilities(
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

    @property
    def capabilities(self) -> VenueCapabilities:
        return self._capabilities

    @property
    def normalization_profile(self) -> VenueNormalizationProfile:
        return self._normalizer.profile

    async def submit_order(self, request: VenueOrderRequest) -> VenueOrderResult:
        self._require_testnet_write()
        _require_account(request.account_id)
        _require_instrument(request.instrument_id)
        params = {
            "symbol": _binance_symbol(request.instrument_id),
            "side": request.side.value,
            "type": request.order_type.value,
            "quantity": _decimal_text(request.quantity),
            "newClientOrderId": request.client_order_id.value,
        }
        if request.order_type is OrderType.LIMIT:
            if request.limit_price is None:
                raise ValueError("LIMIT request requires limit_price")
            params["price"] = _decimal_text(request.limit_price)
            params["timeInForce"] = "GTC"
        if request.reduce_only:
            params["reduceOnly"] = "true"
        response = await self._transport.request("POST", "/fapi/v1/order", params)
        row = _mapping_response(response)
        return self._normalizer.normalize_order(row)

    async def cancel_order(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId,
        venue_order_id: VenueOrderId,
    ) -> VenueOrderResult:
        self._require_testnet_write()
        _require_account(account_id)
        _require_instrument(instrument_id)
        response = await self._transport.request(
            "DELETE",
            "/fapi/v1/order",
            {"symbol": _binance_symbol(instrument_id), "orderId": venue_order_id.value},
        )
        return self._normalizer.normalize_order(
            _mapping_response(response),
            context=OrderNormalizationContext(fallback_venue_order_id=venue_order_id),
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
            "/fapi/v1/order",
            {"symbol": _binance_symbol(instrument_id), "orderId": venue_order_id.value},
        )
        return self._normalizer.normalize_order(
            _mapping_response(response),
            context=OrderNormalizationContext(fallback_venue_order_id=venue_order_id),
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
            params["symbol"] = _binance_symbol(instrument_id)
        response = await self._transport.request("GET", "/fapi/v1/openOrders", params)
        return tuple(
            self._normalizer.normalize_order(row)
            for row in _list_response(response)
        )

    async def get_positions(self, *, account_id: AccountId) -> tuple[VenuePosition, ...]:
        _require_account(account_id)
        observed_at = self._observed_at()
        response = await self._transport.request("GET", "/fapi/v2/positionRisk", {})
        context = PositionNormalizationContext(account_id=account_id, observed_at=observed_at)
        positions: list[VenuePosition] = []
        for row in _list_response(response):
            position = self._normalizer.normalize_position(row, context=context)
            if position is not None:
                positions.append(position)
        return tuple(positions)

    async def get_account_state(self, *, account_id: AccountId) -> VenueAccountState:
        _require_account(account_id)
        response = await self._transport.request("GET", "/fapi/v2/balance", {})
        balances = tuple(self._normalizer.normalize_balance(row) for row in _list_response(response))
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
            raise ValueError("Binance USD-M fill query requires instrument_id")
        _require_instrument(instrument_id)
        params = {"symbol": _binance_symbol(instrument_id)}
        if since is not None:
            params["startTime"] = str(_milliseconds(since))
        observed_at = self._observed_at()
        response = await self._transport.request("GET", "/fapi/v1/userTrades", params)
        context = FillNormalizationContext(
            account_id=account_id,
            fallback_instrument=instrument_id,
            observed_at=observed_at,
        )
        return tuple(
            self._normalizer.normalize_fill(row, context=context)
            for row in _list_response(response)
        )

    def _require_testnet_write(self) -> None:
        if not self._config.allow_testnet_writes:
            raise PermissionError("Binance USD-M TESTNET writes are disabled")

    def _observed_at(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("adapter clock must return timezone-aware datetime")
        return value.astimezone(UTC)


def _require_account(account_id: AccountId) -> None:
    if not isinstance(account_id, AccountId):
        raise ValueError("account_id must be an AccountId")
    if account_id.venue_id != BINANCE_USDM_VENUE_ID:
        raise ValueError("account_id must belong to BINANCE")


def _require_instrument(instrument_id: InstrumentId) -> None:
    if not isinstance(instrument_id, InstrumentId):
        raise ValueError("instrument_id must be an InstrumentId")
    if instrument_id.venue_id != BINANCE_USDM_VENUE_ID:
        raise ValueError("instrument_id must belong to BINANCE")
    if instrument_id.instrument_type is not InstrumentType.PERPETUAL:
        raise ValueError("Binance USD-M adapter requires PERPETUAL instrument")
    if instrument_id.asset_class is not AssetClass.CRYPTO:
        raise ValueError("Binance USD-M adapter requires CRYPTO asset class")


def _binance_symbol(instrument_id: InstrumentId) -> str:
    _require_instrument(instrument_id)
    symbol = instrument_id.native_symbol.strip().upper().replace("-", "")
    if not symbol:
        raise ValueError("Binance symbol must be non-empty")
    return symbol


def _instrument_from_symbol(value: object) -> InstrumentId:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Binance payload requires symbol")
    return InstrumentId(
        venue_id=BINANCE_USDM_VENUE_ID,
        native_symbol=value.strip().upper().replace("-", ""),
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )


def _mapping_response(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("Binance response must be a mapping")
    row = cast(Mapping[str, object], value)
    _raise_api_error(row)
    return row


def _list_response(value: object) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, Mapping):
        row = cast(Mapping[str, object], value)
        _raise_api_error(row)
        raise ValueError("Binance list response must be a list")
    if not isinstance(value, list):
        raise ValueError("Binance list response must be a list")
    rows: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("Binance list item must be a mapping")
        rows.append(cast(Mapping[str, object], item))
    return tuple(rows)


def _raise_api_error(row: Mapping[str, object]) -> None:
    code_raw = row.get("code")
    if code_raw is None:
        return
    try:
        code = int(str(code_raw))
    except ValueError as exc:
        raise ValueError("Binance response code must be integer") from exc
    if code < 0:
        raise BinanceUsdMApiError(
            code=code,
            message=str(row.get("msg") or "unknown Binance error"),
            retryable=code in _RETRYABLE_CODES,
        )


def _client_order_id(row: Mapping[str, object]) -> ClientOrderId:
    raw = row.get("clientOrderId") or row.get("origClientOrderId")
    if raw is None or not str(raw).strip():
        order_id = row.get("orderId")
        if order_id is None or not str(order_id).strip():
            raise ValueError("Binance order requires clientOrderId or orderId")
        raw = f"venue:{order_id}"
    return ClientOrderId(str(raw))


def _optional_venue_order_id(value: object) -> VenueOrderId | None:
    if value is None or not str(value).strip():
        return None
    return VenueOrderId(str(value))


def _normalize_position_side(raw: object, quantity_signed: Decimal) -> VenuePositionSide:
    text = str(raw or "").upper()
    if text == "LONG":
        return VenuePositionSide.LONG
    if text == "SHORT":
        return VenuePositionSide.SHORT
    if text not in {"", "BOTH"}:
        raise ValueError("unsupported Binance positionSide")
    return VenuePositionSide.LONG if quantity_signed > 0 else VenuePositionSide.SHORT


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _decimal(value: object, *, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid Binance decimal field: {field_name}") from exc
    if not result.is_finite():
        raise ValueError(f"non-finite Binance decimal field: {field_name}")
    return result


def _positive_decimal_or_none(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    result = _decimal(value, field_name="positive_decimal")
    return result if result > Decimal("0") else None


def _timestamp_datetime(value: object) -> datetime:
    if value is None:
        raise ValueError("Binance fill requires execution timestamp")
    try:
        milliseconds = int(str(value))
    except ValueError as exc:
        raise ValueError("invalid Binance execution timestamp") from exc
    return datetime.fromtimestamp(milliseconds / 1000, tz=UTC)


def _milliseconds(value: datetime) -> int:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("since must be timezone-aware")
    return int(value.timestamp() * 1000)


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)
