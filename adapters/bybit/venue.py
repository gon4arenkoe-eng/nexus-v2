"""Bybit V5 adapter foundation for canonical NEXUS V2 venue contracts.

Raw Bybit V5 payloads remain inside this adapter package.  The adapter uses an
injected transport so authentication, credentials, HTTP retry policy, and real
Demo Trading runtime certification remain separate Phase-13 slices.

Foundation scope is deliberately fail-closed to:
- Bybit Demo Trading semantics;
- linear USDT perpetual instruments;
- one-way position mode;
- writes disabled by default.
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


BYBIT_VENUE_ID = VenueId("BYBIT")


class BybitTransport(Protocol):
    """Authenticated transport boundary owned outside canonical Core."""

    async def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, str],
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class BybitDemoConfig:
    """Phase-13 Bybit adapter foundation settings."""

    environment: str = "DEMO"
    allow_demo_writes: bool = False
    position_mode: str = "ONEWAY"
    settle_coin: str = "USDT"

    def __post_init__(self) -> None:
        environment = self.environment.strip().upper()
        if environment != "DEMO":
            raise ValueError("Bybit foundation supports DEMO only")
        object.__setattr__(self, "environment", environment)
        if not isinstance(self.allow_demo_writes, bool):
            raise ValueError("allow_demo_writes must be boolean")
        position_mode = self.position_mode.strip().upper()
        if position_mode != "ONEWAY":
            raise ValueError(
                "Bybit foundation is fail-closed to ONEWAY mode; "
                "hedge mode requires a separate canonical position-mode slice"
            )
        object.__setattr__(self, "position_mode", position_mode)
        settle_coin = self.settle_coin.strip().upper()
        if settle_coin != "USDT":
            raise ValueError("Bybit foundation currently supports USDT settlement only")
        object.__setattr__(self, "settle_coin", settle_coin)


class BybitApiError(RuntimeError):
    """Normalized Bybit business/API failure at the adapter boundary."""

    def __init__(self, *, code: int, message: str, retryable: bool) -> None:
        super().__init__(f"Bybit V5 error {code}: {message}")
        self.code = code
        self.retryable = retryable


# Conservative transient/retry candidates. Runtime transport owns actual retry policy.
_RETRYABLE_CODES = frozenset({10000, 10002, 10006, 10016})
_ORDER_STATES = {
    "NEW": VenueOrderState.ACCEPTED,
    "PARTIALLYFILLED": VenueOrderState.PARTIALLY_FILLED,
    "FILLED": VenueOrderState.FILLED,
    "CANCELLED": VenueOrderState.CANCELLED,
    "CANCELED": VenueOrderState.CANCELLED,
    "PARTIALLYFILLEDCANCELED": VenueOrderState.CANCELLED,
    "DEACTIVATED": VenueOrderState.CANCELLED,
    "REJECTED": VenueOrderState.REJECTED,
    "UNTRIGGERED": VenueOrderState.PENDING,
    "TRIGGERED": VenueOrderState.PENDING,
}


class BybitNormalizer:
    """Venue-specific Bybit V5 payload mapper into canonical NEXUS values."""

    venue_id = BYBIT_VENUE_ID

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
        return _instrument_from_symbol(raw.get("symbol"))

    def normalize_order(
        self,
        raw: Mapping[str, object],
        *,
        context: OrderNormalizationContext = OrderNormalizationContext(),
    ) -> VenueOrderResult:
        requested_quantity = _decimal(raw.get("qty", "0"), field_name="qty")
        if requested_quantity <= Decimal("0"):
            raise ValueError("Bybit order quantity must be positive")
        filled_quantity = _decimal(raw.get("cumExecQty", "0"), field_name="cumExecQty")
        state_key = str(raw.get("orderStatus") or "UNKNOWN").replace("_", "").upper()
        state = _ORDER_STATES.get(state_key, VenueOrderState.UNKNOWN)
        average_fill_price = _positive_decimal_or_none(raw.get("avgPrice"))
        if filled_quantity > Decimal("0") and average_fill_price is None:
            exec_value = _positive_decimal_or_none(raw.get("cumExecValue"))
            if exec_value is not None:
                average_fill_price = exec_value / filled_quantity
        if filled_quantity > Decimal("0") and average_fill_price is None:
            raise ValueError("Bybit filled quantity requires average fill price")
        rejection_reason = None
        if state is VenueOrderState.REJECTED:
            rejection_reason = str(raw.get("rejectReason") or "Bybit rejected order")
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
        position_idx = _integer(raw.get("positionIdx", 0), field_name="positionIdx")
        if position_idx != 0:
            raise ValueError("Bybit foundation supports one-way positionIdx=0 only")
        quantity = _decimal(raw.get("size", "0"), field_name="size")
        if quantity == Decimal("0"):
            return None
        if quantity < Decimal("0"):
            raise ValueError("Bybit position size must be non-negative")
        side_raw = str(raw.get("side") or "").strip().upper()
        if side_raw == "BUY":
            side = VenuePositionSide.LONG
        elif side_raw == "SELL":
            side = VenuePositionSide.SHORT
        else:
            raise ValueError("Bybit open position side must be Buy or Sell")
        entry_price = _positive_decimal_or_none(raw.get("avgPrice"))
        if entry_price is None:
            raise ValueError("Bybit open position requires avgPrice")
        return VenuePosition(
            account_id=context.account_id,
            instrument_id=_instrument_from_symbol(raw.get("symbol")),
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            observed_at=context.observed_at,
        )

    def normalize_balance(self, raw: Mapping[str, object]) -> VenueBalance:
        """Normalize safe account-level USD availability for a UNIFIED account.

        Bybit deprecated per-coin ``availableToWithdraw`` for UNIFIED accounts.
        The foundation therefore uses documented account-level
        totalWalletBalance/totalAvailableBalance rather than inventing a
        per-coin available amount.
        """

        return VenueBalance(
            asset="USD",
            total=_decimal(raw.get("totalWalletBalance", "0"), field_name="totalWalletBalance"),
            available=_decimal(
                raw.get("totalAvailableBalance", "0"),
                field_name="totalAvailableBalance",
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
        side_raw = str(raw.get("side") or "").strip().upper()
        if side_raw not in {"BUY", "SELL"}:
            raise ValueError("Bybit fill side must be Buy or Sell")
        fee = _decimal(raw.get("execFee", "0"), field_name="execFee")
        fee_currency_raw = str(raw.get("feeCurrency") or "").strip().upper()
        return VenueFill(
            account_id=context.account_id,
            instrument_id=instrument,
            venue_fill_id=(
                VenueFillId(str(raw.get("execId"))) if raw.get("execId") else None
            ),
            venue_order_id=_optional_venue_order_id(raw.get("orderId")),
            client_order_id=(
                ClientOrderId(str(raw.get("orderLinkId")))
                if raw.get("orderLinkId")
                else None
            ),
            side=OrderSide(side_raw),
            quantity=_decimal(raw.get("execQty", "0"), field_name="execQty"),
            price=_decimal(raw.get("execPrice", "0"), field_name="execPrice"),
            fee=fee,
            fee_currency=fee_currency_raw if fee > Decimal("0") and fee_currency_raw else None,
            executed_at=_timestamp_datetime(raw.get("execTime")),
            observed_at=context.observed_at,
        )


class BybitVenueAdapter(VenueAdapter):
    """Canonical Bybit V5 linear-USDT adapter foundation for Demo Trading."""

    def __init__(
        self,
        *,
        transport: BybitTransport,
        config: BybitDemoConfig | None = None,
        clock: Callable[[], datetime] | None = None,
        normalizer: BybitNormalizer | None = None,
    ) -> None:
        self._transport = transport
        self._config = config if config is not None else BybitDemoConfig()
        self._clock = clock if clock is not None else _utc_now
        self._normalizer = normalizer if normalizer is not None else BybitNormalizer()
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
        self._require_demo_write()
        _require_account(request.account_id)
        _require_instrument(request.instrument_id)
        params = {
            "category": "linear",
            "symbol": _bybit_symbol(request.instrument_id),
            "side": "Buy" if request.side is OrderSide.BUY else "Sell",
            "orderType": "Market" if request.order_type is OrderType.MARKET else "Limit",
            "qty": _decimal_text(request.quantity),
            "orderLinkId": request.client_order_id.value,
            "positionIdx": "0",
        }
        if request.order_type is OrderType.LIMIT:
            if request.limit_price is None:
                raise ValueError("LIMIT request requires limit_price")
            params["price"] = _decimal_text(request.limit_price)
            params["timeInForce"] = "GTC"
        if request.reduce_only:
            params["reduceOnly"] = "true"
        response = await self._transport.request("POST", "/v5/order/create", params)
        result = _result_mapping(response)
        venue_order_id = _required_venue_order_id(result.get("orderId"))
        # Bybit create acknowledgement is asynchronous. Query canonical state
        # instead of pretending the acknowledgement is a final order status.
        return await self.get_order(
            account_id=request.account_id,
            instrument_id=request.instrument_id,
            venue_order_id=venue_order_id,
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
            "POST",
            "/v5/order/cancel",
            {
                "category": "linear",
                "symbol": _bybit_symbol(instrument_id),
                "orderId": venue_order_id.value,
            },
        )
        # Cancel acknowledgement is asynchronous; confirm observable state.
        return await self.get_order(
            account_id=account_id,
            instrument_id=instrument_id,
            venue_order_id=venue_order_id,
        )


    async def get_historical_order(
        self,
        *,
        account_id: AccountId,
        venue_order_id: VenueOrderId | None = None,
        client_order_id: ClientOrderId | None = None,
    ) -> VenueOrderResult:
        """Query one historical Bybit order through the history endpoint.

        The request is GET-only and requires at least one concrete order
        identity. The adapter intentionally does not broaden this method into
        an unrestricted historical order sweep.
        """

        if venue_order_id is None and client_order_id is None:
            raise ValueError(
                "historical order lookup requires venue_order_id "
                "or client_order_id"
            )

        params: dict[str, str] = {
            "category": "linear",
            "settleCoin": self._config.settle_coin,
            "limit": "50",
        }

        if venue_order_id is not None:
            params["orderId"] = str(venue_order_id)

        if client_order_id is not None:
            params["orderLinkId"] = str(client_order_id)

        rows: list[Mapping[str, object]] = []

        cursor: str | None = None
        seen_cursors: set[str] = set()

        while True:
            page = dict(params)

            if cursor is not None:
                page["cursor"] = cursor

            response = await self._transport.request(
                "GET",
                "/v5/order/history",
                page,
            )

            result = _result_mapping(response)
            items = result.get("list")

            if not isinstance(items, list):
                raise ValueError(
                    "Bybit response result.list must be a list"
                )

            for item in items:
                if not isinstance(item, Mapping):
                    raise ValueError(
                        "Bybit order history row must be a mapping"
                    )
                rows.append(item)

            raw_cursor = result.get("nextPageCursor")

            if raw_cursor is None:
                next_cursor = ""
            elif isinstance(raw_cursor, str):
                next_cursor = raw_cursor.strip()
            else:
                raise ValueError(
                    "Bybit nextPageCursor must be a string"
                )

            if not next_cursor:
                break

            if next_cursor in seen_cursors:
                raise ValueError(
                    "Bybit order-history pagination cursor repeated"
                )

            seen_cursors.add(next_cursor)
            cursor = next_cursor

        if not rows:
            raise LookupError(
                "Bybit historical order not found"
            )

        # A point lookup may return several rows only when the supplied
        # identity is insufficiently selective. Resolve deterministically.
        matches: list[Mapping[str, object]] = []

        requested_venue_id = (
            str(venue_order_id)
            if venue_order_id is not None
            else None
        )
        requested_client_id = (
            str(client_order_id)
            if client_order_id is not None
            else None
        )

        for row in rows:
            row_venue_id = str(
                row.get("orderId") or ""
            ).strip()

            row_client_id = str(
                row.get("orderLinkId") or ""
            ).strip()

            if (
                requested_venue_id is not None
                and row_venue_id == requested_venue_id
            ):
                matches.append(row)
                continue

            if (
                requested_client_id is not None
                and row_client_id == requested_client_id
            ):
                matches.append(row)

        if not matches:
            raise LookupError(
                "Bybit historical order identity did not match response"
            )

        if len(matches) > 1:
            canonical = {
                (
                    str(row.get("orderId") or "").strip(),
                    str(row.get("orderLinkId") or "").strip(),
                    str(row.get("orderStatus") or "").strip(),
                    str(row.get("cumExecQty") or "").strip(),
                    str(row.get("avgPrice") or "").strip(),
                )
                for row in matches
            }

            if len(canonical) != 1:
                raise ValueError(
                    "Bybit historical order lookup returned "
                    "conflicting identity matches"
                )

        return self._normalizer.normalize_order(
            matches[0]
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
            "/v5/order/realtime",
            {
                "category": "linear",
                "symbol": _bybit_symbol(instrument_id),
                "orderId": venue_order_id.value,
            },
        )
        rows = _result_list(response)
        if len(rows) != 1:
            raise ValueError("Bybit order query must return exactly one order")
        return self._normalizer.normalize_order(
            rows[0],
            context=OrderNormalizationContext(fallback_venue_order_id=venue_order_id),
        )

    async def get_open_orders(
        self,
        *,
        account_id: AccountId,
        instrument_id: InstrumentId | None = None,
    ) -> tuple[VenueOrderResult, ...]:
        _require_account(account_id)
        params = {"category": "linear", "openOnly": "0"}
        if instrument_id is not None:
            _require_instrument(instrument_id)
            params["symbol"] = _bybit_symbol(instrument_id)
        else:
            params["settleCoin"] = self._config.settle_coin
        response = await self._request_complete_read("GET", "/v5/order/realtime", params)
        return tuple(self._normalizer.normalize_order(row) for row in _result_list(response))

    async def get_positions(self, *, account_id: AccountId) -> tuple[VenuePosition, ...]:
        _require_account(account_id)
        observed_at = self._observed_at()
        response = await self._request_complete_read(
            "GET",
            "/v5/position/list",
            {"category": "linear", "settleCoin": self._config.settle_coin},
        )
        context = PositionNormalizationContext(account_id=account_id, observed_at=observed_at)
        positions: list[VenuePosition] = []
        for row in _result_list(response):
            position = self._normalizer.normalize_position(row, context=context)
            if position is not None:
                positions.append(position)
        return tuple(positions)

    async def get_account_state(self, *, account_id: AccountId) -> VenueAccountState:
        _require_account(account_id)
        response = await self._transport.request(
            "GET",
            "/v5/account/wallet-balance",
            {"accountType": "UNIFIED"},
        )
        rows = _result_list(response)
        if len(rows) != 1:
            raise ValueError("Bybit UNIFIED wallet query must return exactly one account row")
        return VenueAccountState(
            account_id=account_id,
            state=VenueAccountObservationState.CURRENT,
            balances=(self._normalizer.normalize_balance(rows[0]),),
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
            raise ValueError("Bybit fill query requires instrument_id")
        _require_instrument(instrument_id)
        params = {"category": "linear", "symbol": _bybit_symbol(instrument_id)}
        if since is not None:
            params["startTime"] = str(_milliseconds(since))
        observed_at = self._observed_at()
        response = await self._request_complete_read("GET", "/v5/execution/list", params)
        context = FillNormalizationContext(
            account_id=account_id,
            fallback_instrument=instrument_id,
            observed_at=observed_at,
        )
        return tuple(
            self._normalizer.normalize_fill(row, context=context)
            for row in _result_list(response)
        )


    async def _request_complete_read(
        self,
        method: str,
        path: str,
        params: Mapping[str, str],
    ) -> Mapping[str, object]:
        """Collect complete cursor-paginated reconciliation truth.

        Execution history with an explicit startTime is additionally split
        into Bybit-compliant windows no wider than seven days.
        """

        method_normalized = method.strip().upper()

        if method_normalized != "GET":
            raise PermissionError(
                "Bybit complete reconciliation reads are GET-only"
            )

        if path != "/v5/execution/list" or "startTime" not in params:
            return await self._request_all_pages(
                path=path,
                params=params,
            )

        try:
            requested_start = int(str(params["startTime"]))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Bybit execution startTime must be integer milliseconds"
            ) from exc

        now_ms = int(
            self._observed_at().timestamp() * 1000
        )

        if requested_start > now_ms:
            raise ValueError(
                "Bybit execution startTime cannot be in the future"
            )

        seven_days_ms = 7 * 24 * 60 * 60 * 1000

        base_params = dict(params)
        base_params.pop("startTime", None)
        base_params.pop("endTime", None)
        base_params.pop("cursor", None)
        base_params.pop("limit", None)

        rows: list[Mapping[str, object]] = []
        seen_exec_ids: dict[
            str,
            Mapping[str, object],
        ] = {}

        # Walk newest -> oldest so the aggregate retains Bybit's
        # documented newest-first execution-history direction.
        window_end = now_ms

        while window_end >= requested_start:
            window_start = max(
                requested_start,
                window_end - seven_days_ms,
            )

            window_params = dict(base_params)
            window_params["startTime"] = str(window_start)
            window_params["endTime"] = str(window_end)

            response = await self._request_all_pages(
                path=path,
                params=window_params,
            )

            result = _result_mapping(response)
            items = result.get("list")

            if not isinstance(items, list):
                raise ValueError(
                    "Bybit response result.list must be a list"
                )

            for item in items:
                if not isinstance(item, Mapping):
                    raise ValueError(
                        "Bybit result.list item must be a mapping"
                    )

                exec_id = str(
                    item.get("execId") or ""
                ).strip()

                if not exec_id:
                    raise ValueError(
                        "Bybit execution row requires execId"
                    )

                existing = seen_exec_ids.get(exec_id)

                if existing is not None:
                    if dict(existing) != dict(item):
                        raise ValueError(
                            "Bybit execution history contains "
                            "conflicting duplicate execId"
                        )
                    continue

                seen_exec_ids[exec_id] = item
                rows.append(item)

            if window_start == requested_start:
                break

            # Adjacent inclusive millisecond windows must not overlap.
            window_end = window_start - 1

        return {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": rows,
                "nextPageCursor": "",
            },
        }

    async def _request_all_pages(
        self,
        *,
        path: str,
        params: Mapping[str, str],
    ) -> Mapping[str, object]:
        """Follow Bybit nextPageCursor until the required read is complete."""

        page_limits = {
            "/v5/order/realtime": 50,
            "/v5/position/list": 200,
            "/v5/execution/list": 100,
        }

        page_limit = page_limits.get(path)

        if page_limit is None:
            # This helper is intentionally narrow: adding another
            # paginated endpoint requires an explicit certification slice.
            raise ValueError(
                f"unsupported complete Bybit read path: {path}"
            )

        base_params = dict(params)
        base_params.pop("cursor", None)
        base_params["limit"] = str(page_limit)

        rows: list[Mapping[str, object]] = []
        seen_cursors: set[str] = set()

        cursor: str | None = None

        while True:
            page_params = dict(base_params)

            if cursor is not None:
                page_params["cursor"] = cursor

            response = await self._transport.request(
                "GET",
                path,
                page_params,
            )

            result = _result_mapping(response)
            items = result.get("list")

            if not isinstance(items, list):
                raise ValueError(
                    "Bybit response result.list must be a list"
                )

            for item in items:
                if not isinstance(item, Mapping):
                    raise ValueError(
                        "Bybit result.list item must be a mapping"
                    )
                rows.append(item)

            raw_cursor = result.get("nextPageCursor")

            if raw_cursor is None:
                next_cursor = ""
            elif isinstance(raw_cursor, str):
                next_cursor = raw_cursor.strip()
            else:
                raise ValueError(
                    "Bybit nextPageCursor must be a string"
                )

            if not next_cursor:
                break

            if next_cursor in seen_cursors:
                raise ValueError(
                    "Bybit pagination cursor repeated"
                )

            seen_cursors.add(next_cursor)
            cursor = next_cursor

        return {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": rows,
                "nextPageCursor": "",
            },
        }

    def _require_demo_write(self) -> None:
        if not self._config.allow_demo_writes:
            raise PermissionError("Bybit DEMO writes are disabled")

    def _observed_at(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("adapter clock must return timezone-aware datetime")
        return value.astimezone(UTC)


def _require_account(account_id: AccountId) -> None:
    if not isinstance(account_id, AccountId):
        raise ValueError("account_id must be an AccountId")
    if account_id.venue_id != BYBIT_VENUE_ID:
        raise ValueError("account_id must belong to BYBIT")


def _require_instrument(instrument_id: InstrumentId) -> None:
    if not isinstance(instrument_id, InstrumentId):
        raise ValueError("instrument_id must be an InstrumentId")
    if instrument_id.venue_id != BYBIT_VENUE_ID:
        raise ValueError("instrument_id must belong to BYBIT")
    if instrument_id.instrument_type is not InstrumentType.PERPETUAL:
        raise ValueError("Bybit foundation requires PERPETUAL instrument")
    if instrument_id.asset_class is not AssetClass.CRYPTO:
        raise ValueError("Bybit foundation requires CRYPTO asset class")


def _bybit_symbol(instrument_id: InstrumentId) -> str:
    _require_instrument(instrument_id)
    symbol = instrument_id.native_symbol.strip().upper().replace("-", "")
    if not symbol:
        raise ValueError("Bybit symbol must be non-empty")
    return symbol


def _instrument_from_symbol(value: object) -> InstrumentId:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Bybit payload requires symbol")
    return InstrumentId(
        venue_id=BYBIT_VENUE_ID,
        native_symbol=value.strip().upper().replace("-", ""),
        instrument_type=InstrumentType.PERPETUAL,
        asset_class=AssetClass.CRYPTO,
    )


def _response_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("Bybit response must be a mapping")
    row = cast(Mapping[str, object], value)
    _raise_api_error(row)
    return row


def _result_mapping(value: object) -> Mapping[str, object]:
    envelope = _response_mapping(value)
    result = envelope.get("result")
    if not isinstance(result, Mapping):
        raise ValueError("Bybit response result must be a mapping")
    return cast(Mapping[str, object], result)


def _result_list(value: object) -> tuple[Mapping[str, object], ...]:
    result = _result_mapping(value)
    items = result.get("list")
    if not isinstance(items, list):
        raise ValueError("Bybit response result.list must be a list")
    rows: list[Mapping[str, object]] = []
    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError("Bybit result.list item must be a mapping")
        rows.append(cast(Mapping[str, object], item))
    return tuple(rows)


def _raise_api_error(row: Mapping[str, object]) -> None:
    raw_code = row.get("retCode")
    if raw_code is None:
        raise ValueError("Bybit response requires retCode")
    try:
        code = int(str(raw_code))
    except ValueError as exc:
        raise ValueError("Bybit retCode must be integer") from exc
    if code != 0:
        raise BybitApiError(
            code=code,
            message=str(row.get("retMsg") or "unknown Bybit error"),
            retryable=code in _RETRYABLE_CODES,
        )


def _client_order_id(row: Mapping[str, object]) -> ClientOrderId:
    raw = row.get("orderLinkId")
    if raw is not None and str(raw).strip():
        return ClientOrderId(str(raw))
    order_id = row.get("orderId")
    if order_id is None or not str(order_id).strip():
        raise ValueError("Bybit order requires orderLinkId or orderId")
    return ClientOrderId(f"venue:{order_id}")


def _optional_venue_order_id(value: object) -> VenueOrderId | None:
    if value is None or not str(value).strip():
        return None
    return VenueOrderId(str(value))


def _required_venue_order_id(value: object) -> VenueOrderId:
    result = _optional_venue_order_id(value)
    if result is None:
        raise ValueError("Bybit write acknowledgement requires orderId")
    return result


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _decimal(value: object, *, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid Bybit decimal field: {field_name}") from exc
    if not result.is_finite():
        raise ValueError(f"non-finite Bybit decimal field: {field_name}")
    return result


def _integer(value: object, *, field_name: str) -> int:
    try:
        return int(str(value))
    except ValueError as exc:
        raise ValueError(f"invalid Bybit integer field: {field_name}") from exc


def _positive_decimal_or_none(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    result = _decimal(value, field_name="positive_decimal")
    return result if result > Decimal("0") else None


def _timestamp_datetime(value: object) -> datetime:
    if value is None:
        raise ValueError("Bybit fill requires execTime")
    try:
        milliseconds = int(str(value))
    except ValueError as exc:
        raise ValueError("invalid Bybit execution timestamp") from exc
    return datetime.fromtimestamp(milliseconds / 1000, tz=UTC)


def _milliseconds(value: datetime) -> int:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("since must be timezone-aware")
    return int(value.timestamp() * 1000)


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)
