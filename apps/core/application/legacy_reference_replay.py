"""Safe deterministic foundation for Phase 14 legacy-reference replay.

This module deliberately owns no production credentials, exchange transport or
production database connection.  It provides a BingX-shaped in-memory venue,
a fixed replay clock and fail-closed provenance helpers that can be injected
around the frozen legacy decision graph in a later integration slice.
"""

from __future__ import annotations

import copy
import os
import socket
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Final

from apps.core.application.shadow_parity import (
    ShadowBehaviorEvidence,
    ShadowEvidenceState,
    ShadowParityDimension,
)

JsonObject = dict[str, Any]

_BLOCKED_SECRET_NAMES: Final = (
    "BINGX_API_KEY",
    "BINGX_SECRET_KEY",
    "BINGX_SECRET",
    "GROQ_API_KEY",
)
_ACTIVE_ORDER_STATES: Final = frozenset({"NEW", "PENDING"})


class ReplaySafetyError(RuntimeError):
    (
        "Raised when the replay harness would cross a forbidden authority "
        "boundary."
    )


class HistoricalAIState(StrEnum):
    VERIFIED = "VERIFIED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ReplayClock:
    as_of: datetime

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("replay as_of must be timezone-aware")
        object.__setattr__(self, "as_of", self.as_of.astimezone(UTC))

    def now(self) -> datetime:
        return self.as_of


@dataclass(frozen=True, slots=True)
class HistoricalAIResolution:
    state: HistoricalAIState
    plan: Mapping[str, Any] | None
    reason: str


class ReplayAIProvenanceGate:
    """Never regenerates historical AI decisions with a current live model."""

    def __init__(
        self,
        plans: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self._plans = {
            str(symbol).replace("-", "").upper(): copy.deepcopy(dict(plan))
            for symbol, plan in (plans or {}).items()
        }

    def resolve(self, symbol: str) -> HistoricalAIResolution:
        key = str(symbol).replace("-", "").upper()
        plan = self._plans.get(key)
        if plan is None:
            return HistoricalAIResolution(
                state=HistoricalAIState.UNKNOWN,
                plan=None,
                reason=(
                    "historical Groq output is unavailable; "
                    "live regeneration is forbidden"
                ),
            )
        return HistoricalAIResolution(
            state=HistoricalAIState.VERIFIED,
            plan=copy.deepcopy(plan),
            reason="frozen historical AI output supplied",
        )


@dataclass(frozen=True, slots=True)
class ReplayScenario:
    as_of: datetime
    contracts: tuple[Mapping[str, Any], ...]
    market_tickers_24h: tuple[Mapping[str, Any], ...]
    tickers: Mapping[str, Mapping[str, Any]]
    klines: Mapping[tuple[str, str], Sequence[Sequence[Any]]]
    balance: Mapping[str, float]
    positions: tuple[Mapping[str, Any], ...] = ()
    open_orders: tuple[Mapping[str, Any], ...] = ()
    income: tuple[Mapping[str, Any], ...] = ()
    historical_ai_plans: Mapping[str, Mapping[str, Any]] = field(
        default_factory=dict
    )
    commission_rate: float = 0.0

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("replay scenario as_of must be timezone-aware")
        if self.commission_rate < 0:
            raise ValueError("commission_rate must be >= 0")


@dataclass(frozen=True, slots=True)
class ReplayWriteEvent:
    sequence: int
    operation: str
    payload: Mapping[str, Any]


class ReplayNotificationSink:
    (
        "Side-effect-free replacement for the legacy Telegram notification "
        "surface."
    )

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def _record(self, kind: str, **payload: Any) -> None:
        self.events.append({"kind": kind, **copy.deepcopy(payload)})

    def send_trade_notification(self, **payload: Any) -> None:
        self._record("trade", **payload)

    def send_risk_alert(self, **payload: Any) -> None:
        self._record("risk", **payload)

    def send_system_notification(self, **payload: Any) -> None:
        self._record("system", **payload)


@contextmanager
def replay_environment(
    *,
    database_url: str = "sqlite+aiosqlite:///:memory:",
) -> Iterator[None]:
    """Scrub production credentials and force an isolated replay DB target."""

    if database_url != "sqlite+aiosqlite:///:memory:":
        raise ReplaySafetyError(
            "Phase14 replay database must be in-memory SQLite"
        )

    names = (*_BLOCKED_SECRET_NAMES, "DATABASE_URL")
    previous = {name: os.environ.get(name) for name in names}
    try:
        for name in _BLOCKED_SECRET_NAMES:
            os.environ.pop(name, None)
        os.environ["DATABASE_URL"] = database_url
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


@contextmanager
def block_outbound_network() -> Iterator[None]:
    """Fail closed on any accidental TCP connection from frozen legacy code."""

    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def denied_connect(_socket: socket.socket, _address: Any) -> None:
        raise ReplaySafetyError(
            "outbound network is blocked in Phase14 legacy replay"
        )

    def denied_connect_ex(_socket: socket.socket, _address: Any) -> int:
        raise ReplaySafetyError(
            "outbound network is blocked in Phase14 legacy replay"
        )

    setattr(socket.socket, "connect", denied_connect)
    setattr(socket.socket, "connect_ex", denied_connect_ex)
    try:
        yield
    finally:
        setattr(socket.socket, "connect", original_connect)
        setattr(socket.socket, "connect_ex", original_connect_ex)


class ReplayBingXClient:
    (
        "BingX-shaped, credential-free deterministic simulated venue.\n"
        "\n"
        "    The public method names intentionally match the frozen legacy "
        "call surface.\n"
        "    No method performs HTTP, reads exchange credentials or reaches "
        "production DB.\n"
        "    "
    )

    def __init__(self, scenario: ReplayScenario) -> None:
        self.clock = ReplayClock(scenario.as_of)
        self._contracts = [
            copy.deepcopy(dict(item)) for item in scenario.contracts
        ]
        self._market_tickers_24h = [
            copy.deepcopy(dict(item)) for item in scenario.market_tickers_24h
        ]
        self._tickers = {
            self._internal_symbol(symbol): copy.deepcopy(dict(value))
            for symbol, value in scenario.tickers.items()
        }
        self._klines = {
            (self._internal_symbol(symbol), interval): [
                list(row) for row in rows
            ]
            for (symbol, interval), rows in scenario.klines.items()
        }
        self._balance = {
            str(key): float(value)
            for key, value in scenario.balance.items()
        }
        self._positions = [
            copy.deepcopy(dict(item)) for item in scenario.positions
        ]
        self._orders: dict[str, JsonObject] = {}
        for item in scenario.open_orders:
            order = copy.deepcopy(dict(item))
            order_id = str(order.get("orderId") or "").strip()
            if not order_id:
                raise ValueError("replay open order requires orderId")
            self._orders[order_id] = order
        self._income = [copy.deepcopy(dict(item)) for item in scenario.income]
        self._commission_rate = float(scenario.commission_rate)
        self._precision_cache: dict[str, tuple[int, int]] = {}
        self._contract_cache: dict[str, JsonObject] = {}
        self._sequence = 0
        self._writes: list[ReplayWriteEvent] = []
        self._fills: list[JsonObject] = []
        self._load_contracts_sync()

    @property
    def write_events(self) -> tuple[ReplayWriteEvent, ...]:
        return tuple(self._writes)

    @property
    def fills(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(copy.deepcopy(self._fills))

    @property
    def income_snapshot(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(copy.deepcopy(self._income))

    @staticmethod
    def _internal_symbol(symbol: str) -> str:
        return str(symbol).replace("-", "").upper()

    def _record_write(
        self,
        operation: str,
        payload: Mapping[str, Any],
    ) -> None:
        self._sequence += 1
        self._writes.append(
            ReplayWriteEvent(
                sequence=self._sequence,
                operation=operation,
                payload=copy.deepcopy(dict(payload)),
            )
        )

    def _next_order_id(self) -> str:
        return f"replay-order-{self._sequence + 1:06d}"

    def _load_contracts_sync(self) -> dict[str, tuple[int, int]]:
        precision_cache: dict[str, tuple[int, int]] = {}
        contract_cache: dict[str, JsonObject] = {}
        for contract in self._contracts:
            symbol = str(contract.get("symbol", "")).strip()
            if not symbol:
                continue
            precision_cache[symbol] = (
                int(contract.get("quantityPrecision", 6)),
                int(contract.get("pricePrecision", 8)),
            )
            contract_cache[symbol] = copy.deepcopy(contract)
        self._precision_cache = precision_cache
        self._contract_cache = contract_cache
        return dict(precision_cache)

    async def _load_contracts(self) -> dict[str, tuple[int, int]]:
        return self._load_contracts_sync()

    def _normalize_symbol(self, symbol: str) -> str:
        if not symbol or "-" in symbol:
            return symbol
        for quote in ("USDT", "BUSD", "USDC", "BTC", "ETH", "USD"):
            if symbol.endswith(quote):
                return f"{symbol[:-len(quote)]}-{quote}"
        return symbol

    def _get_precision(self, symbol: str) -> tuple[int, int]:
        normalized = self._normalize_symbol(symbol)
        return self._precision_cache.get(normalized, (6, 8))

    async def get_available_symbols(self) -> list[str]:
        await self._load_contracts()
        crypto_symbols: set[str] = set()
        synthetic_prefixes = ("NCCO", "NCFX", "NCS")
        synthetic_markers = (
            "GOLD",
            "SILVER",
            "OIL",
            "NASDAQ",
            "SP500",
            "USDJPY",
            "GBPJPY",
            "AUDJPY",
            "CADJPY",
            "NZDJPY",
            "CHFJPY",
            "XAU",
            "XAG",
        )
        for symbol, contract in self._contract_cache.items():
            internal = self._internal_symbol(symbol)
            currency = str(contract.get("currency", "")).upper()
            status = contract.get("status")
            asset = str(contract.get("asset", "")).strip().upper()
            display = str(contract.get("displayName", "")).strip().upper()
            if (
                not internal.endswith("USDT")
                or currency != "USDT"
                or status != 1
            ):
                continue
            if (
                not asset
                or asset == "INDEX"
                or internal == "INDEXUSDT"
                or asset.startswith(synthetic_prefixes)
                or internal.startswith(synthetic_prefixes)
                or any(marker in display for marker in synthetic_markers)
            ):
                continue
            crypto_symbols.add(internal)

        ranked: list[tuple[float, str]] = []
        for ticker in self._market_tickers_24h:
            internal = self._internal_symbol(str(ticker.get("symbol", "")))
            if internal not in crypto_symbols:
                continue
            raw_volume = (
                ticker.get("quoteVolume")
                or ticker.get("quoteVolume24h")
                or ticker.get("turnover")
                or 0
            )
            try:
                volume = float(raw_volume)
            except (TypeError, ValueError):
                continue
            if volume > 0:
                ranked.append((volume, internal))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [symbol for _, symbol in ranked[:100]]

    async def get_balance(self) -> dict[str, float]:
        return copy.deepcopy(self._balance)

    async def get_income(
        self,
        start_time: int | None = None,
        end_time: int | None = None,
        symbol: str | None = None,
        income_type: str | None = None,
        limit: int = 100,
    ) -> list[JsonObject]:
        normalized = self._normalize_symbol(symbol) if symbol else None
        rows: list[JsonObject] = []
        for item in self._income:
            item_symbol = str(item.get("symbol", ""))
            if (
                normalized
                and self._normalize_symbol(item_symbol) != normalized
            ):
                continue
            if income_type and str(item.get("incomeType", "")) != income_type:
                continue
            raw_time = item.get("time", item.get("timestamp"))
            if raw_time is not None:
                item_time = int(raw_time)
                if start_time is not None and item_time < start_time:
                    continue
                if end_time is not None and item_time > end_time:
                    continue
            rows.append(copy.deepcopy(item))
        return rows[:limit]

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
    ) -> list[list[Any]]:
        rows = self._klines.get((self._internal_symbol(symbol), interval), [])
        return copy.deepcopy(rows[-limit:])

    async def get_open_orders(
        self,
        symbol: str | None = None,
    ) -> list[JsonObject]:
        normalized = self._normalize_symbol(symbol) if symbol else None
        result = []
        for order in self._orders.values():
            if (
                str(order.get("status", "")).upper()
                not in _ACTIVE_ORDER_STATES
            ):
                continue
            if normalized and str(order.get("symbol", "")) != normalized:
                continue
            result.append(copy.deepcopy(order))
        result.sort(key=lambda item: str(item.get("orderId", "")))
        return result

    async def get_order(self, symbol: str, order_id: str) -> JsonObject:
        order = self._orders.get(str(order_id))
        if (
            order is None
            or str(order.get("symbol", ""))
            != self._normalize_symbol(symbol)
        ):
            return {}
        return copy.deepcopy(order)

    async def get_positions(self) -> list[JsonObject]:
        result: list[JsonObject] = []
        for position in self._positions:
            item = copy.deepcopy(position)
            symbol = self._internal_symbol(str(item.get("symbol", "")))
            ticker = self._tickers.get(symbol, {})
            mark_price = float(
                ticker.get("mark_price")
                or ticker.get("last_price")
                or ticker.get("price")
                or item.get("mark_price")
                or 0
            )
            entry = float(item.get("entry_price", 0) or 0)
            size = float(item.get("size", 0) or 0)
            side = str(
                item.get("positionSide") or item.get("side") or ""
            ).upper()
            if side == "LONG":
                unrealized = (mark_price - entry) * size
            elif side == "SHORT":
                unrealized = (entry - mark_price) * size
            else:
                unrealized = float(item.get("unrealized_pnl", 0) or 0)
            item.update(
                {
                    "symbol": self._normalize_symbol(symbol),
                    "side": side,
                    "positionSide": side,
                    "size": size,
                    "entry_price": entry,
                    "mark_price": mark_price,
                    "unrealized_pnl": unrealized,
                }
            )
            result.append(item)
        result.sort(
            key=lambda item: (
                str(item.get("symbol")),
                str(item.get("side")),
            )
        )
        return result

    async def get_ticker(self, symbol: str) -> JsonObject:
        internal = self._internal_symbol(symbol)
        data = self._tickers.get(internal)
        if data is None:
            raise KeyError(f"replay ticker unavailable for {internal}")
        item = copy.deepcopy(data)
        last_price = float(
            item.get("last_price")
            or item.get("lastPrice")
            or item.get("price")
            or 0
        )
        return {
            "symbol": self._normalize_symbol(internal),
            "last_price": last_price,
            "bid_price": float(
                item.get("bid_price") or item.get("bidPrice") or last_price
            ),
            "ask_price": float(
                item.get("ask_price") or item.get("askPrice") or last_price
            ),
            "high_24h": float(
                item.get("high_24h") or item.get("highPrice") or last_price
            ),
            "low_24h": float(
                item.get("low_24h") or item.get("lowPrice") or last_price
            ),
            "volume_24h": float(
                item.get("volume_24h") or item.get("volume") or 0
            ),
            "price_change_24h": float(
                item.get("price_change_24h")
                or item.get("priceChange")
                or 0
            ),
            "price": last_price,
        }

    def _upsert_position(
        self,
        *,
        symbol: str,
        position_side: str,
        quantity: float,
        fill_price: float,
        leverage: int,
        reduce_only: bool,
    ) -> None:
        normalized = self._normalize_symbol(symbol)
        for index, position in enumerate(self._positions):
            if (
                self._normalize_symbol(str(position.get("symbol", "")))
                == normalized
                and str(
                    position.get("positionSide")
                    or position.get("side")
                    or ""
                ).upper()
                == position_side
            ):
                current = float(position.get("size", 0) or 0)
                if reduce_only:
                    remaining = max(0.0, current - quantity)
                    if remaining == 0:
                        self._positions.pop(index)
                    else:
                        position["size"] = remaining
                    return
                new_total = current + quantity
                old_entry = float(position.get("entry_price", 0) or 0)
                position["entry_price"] = (
                    (
                        (old_entry * current) + (fill_price * quantity)
                    )
                    / new_total
                    if new_total > 0
                    else fill_price
                )
                position["size"] = new_total
                position["leverage"] = leverage
                return
        if reduce_only:
            return
        self._positions.append(
            {
                "symbol": normalized,
                "side": position_side,
                "positionSide": position_side,
                "size": quantity,
                "entry_price": fill_price,
                "leverage": leverage,
                "order_id": "",
            }
        )

    async def place_order(
        self,
        symbol: str,
        side: str,
        size: float,
        order_type: str = "MARKET",
        price: float | None = None,
        leverage: int = 1,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        position_side: str | None = None,
        configure_leverage: bool = True,
        reduce_only: bool = False,
    ) -> JsonObject:
        del stop_loss, take_profit
        normalized = self._normalize_symbol(symbol)
        side_upper = side.upper()
        order_type_upper = order_type.upper()
        position_side_upper = (
            position_side.upper()
            if position_side
            else ("LONG" if side_upper == "BUY" else "SHORT")
        )
        if position_side_upper not in {"LONG", "SHORT"}:
            return {"error": f"Invalid position_side: {position_side_upper}"}
        if float(size) <= 0:
            return {"error": "size must be > 0"}

        ticker = await self.get_ticker(normalized)
        if order_type_upper == "MARKET":
            fill_price = float(
                (
                    ticker.get("ask_price")
                    if side_upper == "BUY"
                    else ticker.get("bid_price")
                )
                or ticker.get("last_price")
                or 0
            )
        elif (
            order_type_upper == "LIMIT"
            and price is not None
            and float(price) > 0
        ):
            fill_price = float(price)
        else:
            return {"error": "unsupported replay order type or missing price"}
        if fill_price <= 0:
            return {"error": "replay fill price unavailable"}

        order_id = self._next_order_id()
        status = "FILLED" if order_type_upper == "MARKET" else "NEW"
        order = {
            "orderId": order_id,
            "symbol": normalized,
            "side": side_upper,
            "positionSide": position_side_upper,
            "type": order_type_upper,
            "origQty": float(size),
            "executedQty": float(size) if status == "FILLED" else 0.0,
            "avgPrice": fill_price if status == "FILLED" else 0.0,
            "price": fill_price if order_type_upper == "LIMIT" else 0.0,
            "status": status,
            "reduceOnly": bool(reduce_only),
            "configureLeverage": bool(configure_leverage),
            "leverage": int(leverage),
        }
        self._orders[order_id] = order
        self._record_write("place_order", order)

        commission = 0.0
        if status == "FILLED":
            self._upsert_position(
                symbol=normalized,
                position_side=position_side_upper,
                quantity=float(size),
                fill_price=fill_price,
                leverage=int(leverage),
                reduce_only=bool(reduce_only),
            )
            commission = abs(float(size) * fill_price * self._commission_rate)
            fill = {
                "order_id": order_id,
                "symbol": normalized,
                "side": side_upper,
                "position_side": position_side_upper,
                "size": float(size),
                "price": fill_price,
                "commission": commission,
                "filled_at": self.clock.now().isoformat(),
            }
            self._fills.append(fill)
            if commission:
                self._income.append(
                    {
                        "symbol": normalized,
                        "incomeType": "COMMISSION",
                        "income": -commission,
                        "time": int(self.clock.now().timestamp() * 1000),
                    }
                )

        return {
            "order_id": order_id,
            "avg_price": fill_price if status == "FILLED" else 0.0,
            "size": float(size) if status == "FILLED" else 0.0,
            "commission": commission,
            "status": status,
        }

    async def set_stop_loss_take_profit(
        self,
        symbol: str,
        position_side: str,
        size: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> list[JsonObject]:
        normalized = self._normalize_symbol(symbol)
        position_side_upper = position_side.upper()
        if position_side_upper not in {"LONG", "SHORT"}:
            return [
                {
                    "type": "ERROR",
                    "result": {
                        "error": (
                            "Invalid position_side: "
                            f"{position_side_upper}"
                        )
                    },
                }
            ]
        close_side = "SELL" if position_side_upper == "LONG" else "BUY"
        results: list[JsonObject] = []
        for item_type, order_type, stop_price in (
            ("STOP_LOSS", "STOP_MARKET", stop_loss),
            ("TAKE_PROFIT", "TAKE_PROFIT_MARKET", take_profit),
        ):
            if stop_price is None or float(stop_price) <= 0:
                continue
            order_id = self._next_order_id()
            order = {
                "orderId": order_id,
                "symbol": normalized,
                "side": close_side,
                "positionSide": position_side_upper,
                "type": order_type,
                "origQty": float(size),
                "stopPrice": float(stop_price),
                "status": "NEW",
            }
            self._orders[order_id] = order
            self._record_write("set_protection", order)
            results.append(
                {
                    "type": item_type,
                    "result": {
                        "code": 0,
                        "msg": "",
                        "data": {
                            "orderId": order_id,
                            "order": copy.deepcopy(order),
                        },
                    },
                }
            )
        return results

    async def cancel_order(self, order_id: str, symbol: str) -> JsonObject:
        normalized = self._normalize_symbol(symbol)
        order = self._orders.get(str(order_id))
        if order is None or str(order.get("symbol", "")) != normalized:
            return {"error": "order not found", "orderId": str(order_id)}
        if str(order.get("status", "")).upper() in _ACTIVE_ORDER_STATES:
            order["status"] = "CANCELLED"
        self._record_write(
            "cancel_order",
            {
                "orderId": str(order_id),
                "symbol": normalized,
                "status": order["status"],
            },
        )
        return {"code": 0, "data": {"order": copy.deepcopy(order)}}

    async def simulate_limit_fill(
        self,
        order_id: str,
        *,
        fill_price: float | None = None,
    ) -> JsonObject:
        order = self._orders.get(str(order_id))
        if order is None:
            raise KeyError(order_id)
        if str(order.get("type", "")).upper() != "LIMIT":
            raise ValueError("only LIMIT orders can be manually filled")
        if str(order.get("status", "")).upper() not in _ACTIVE_ORDER_STATES:
            return copy.deepcopy(order)
        resolved_price = float(fill_price or order.get("price") or 0)
        if resolved_price <= 0:
            raise ValueError("limit fill price must be > 0")
        order["status"] = "FILLED"
        order["executedQty"] = float(order.get("origQty", 0) or 0)
        order["avgPrice"] = resolved_price
        self._upsert_position(
            symbol=str(order["symbol"]),
            position_side=str(order["positionSide"]),
            quantity=float(order["origQty"]),
            fill_price=resolved_price,
            leverage=int(order.get("leverage", 1) or 1),
            reduce_only=bool(order.get("reduceOnly", False)),
        )
        self._fills.append(
            {
                "order_id": str(order["orderId"]),
                "symbol": str(order["symbol"]),
                "side": str(order["side"]),
                "position_side": str(order["positionSide"]),
                "size": float(order["origQty"]),
                "price": resolved_price,
                "commission": 0.0,
                "filled_at": self.clock.now().isoformat(),
            }
        )
        self._record_write("simulate_limit_fill", order)
        return copy.deepcopy(order)


class LegacyReferenceReplayHarness:
    """Owns deterministic replay state and emits comparator-ready evidence."""

    def __init__(self, scenario: ReplayScenario) -> None:
        self.scenario = scenario
        self.clock = ReplayClock(scenario.as_of)
        self.client = ReplayBingXClient(scenario)
        self.notifications = ReplayNotificationSink()
        self.ai = ReplayAIProvenanceGate(scenario.historical_ai_plans)

    async def build_evidence(
        self,
        *,
        signals_intents: Any,
        risk_decisions: Any,
        failures_stale_states: Any = None,
    ) -> ShadowBehaviorEvidence:
        positions = await self.client.get_positions()
        open_orders = await self.client.get_open_orders()
        dimensions = {
            ShadowParityDimension.SIGNALS_INTENTS: copy.deepcopy(
                signals_intents
            ),
            ShadowParityDimension.RISK_DECISIONS: copy.deepcopy(
                risk_decisions
            ),
            ShadowParityDimension.ORDER_INTENT: [
                {
                    "sequence": event.sequence,
                    "operation": event.operation,
                    "payload": copy.deepcopy(dict(event.payload)),
                }
                for event in self.client.write_events
            ],
            ShadowParityDimension.POSITIONS: positions,
            ShadowParityDimension.FILLS_RECONCILIATION: {
                "fills": [
                    copy.deepcopy(dict(item)) for item in self.client.fills
                ],
                "open_orders": open_orders,
            },
            ShadowParityDimension.PNL_ATTRIBUTION: {
                "income": [
                    copy.deepcopy(dict(item))
                    for item in self.client.income_snapshot
                ],
            },
            ShadowParityDimension.EXECUTION_QUALITY: {
                "fills": [
                    copy.deepcopy(dict(item)) for item in self.client.fills
                ],
            },
            ShadowParityDimension.FAILURES_STALE_STATES: copy.deepcopy(
                failures_stale_states
                if failures_stale_states is not None
                else []
            ),
        }
        return ShadowBehaviorEvidence(
            source="LEGACY_REFERENCE_REPLAY",
            observed_at=self.clock.now(),
            state=ShadowEvidenceState.CURRENT,
            dimensions=dimensions,
        )
