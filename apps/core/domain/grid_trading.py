"""Canonical Grid Trading Desk domain contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from apps.core.domain.orders import OrderSide
from packages.contracts.identities import AccountId, FillId, InstrumentId
from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_non_negative_decimal,
    require_positive_decimal,
)


class GridSpacingType(StrEnum):
    ARITHMETIC = "ARITHMETIC"
    GEOMETRIC = "GEOMETRIC"
    DYNAMIC = "DYNAMIC"


class GridBias(StrEnum):
    NEUTRAL = "NEUTRAL"
    LONG = "LONG"
    SHORT = "SHORT"


class GridProgramState(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    HALTED = "HALTED"


class GridInstanceState(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    RECENTERING = "RECENTERING"
    RECOVERY = "RECOVERY"
    STOPPED = "STOPPED"
    CLOSED = "CLOSED"


class GridCycleState(StrEnum):
    OPEN = "OPEN"
    RECENTERING = "RECENTERING"
    RECOVERY = "RECOVERY"
    CLOSED = "CLOSED"


class GridLevelState(StrEnum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


class GridReconciliationState(StrEnum):
    MATCHED = "MATCHED"
    DISCREPANCY = "DISCREPANCY"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class GridStuckPositionPolicy(StrEnum):
    HALT = "HALT"
    HOLD = "HOLD"
    REDUCE_ONLY = "REDUCE_ONLY"


def _text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _ratio(value: Decimal, *, field_name: str) -> Decimal:
    value = require_non_negative_decimal(value, field_name=field_name)
    if value > Decimal("1"):
        raise ValueError(f"{field_name} must be <= 1")
    return value


@dataclass(frozen=True, slots=True)
class GridRiskBudget:
    reserved_capital: Decimal
    max_gross_exposure: Decimal
    max_inventory_notional: Decimal
    max_drawdown_ratio: Decimal
    max_stuck_seconds: int
    stuck_policy: GridStuckPositionPolicy = GridStuckPositionPolicy.HALT

    def __post_init__(self) -> None:
        for name in (
            "reserved_capital",
            "max_gross_exposure",
            "max_inventory_notional",
        ):
            object.__setattr__(
                self,
                name,
                require_positive_decimal(getattr(self, name), field_name=name),
            )
        object.__setattr__(
            self,
            "max_drawdown_ratio",
            _ratio(self.max_drawdown_ratio, field_name="max_drawdown_ratio"),
        )
        if (
            isinstance(self.max_stuck_seconds, bool)
            or not isinstance(self.max_stuck_seconds, int)
            or self.max_stuck_seconds <= 0
        ):
            raise ValueError("max_stuck_seconds must be a positive integer")
        if not isinstance(self.stuck_policy, GridStuckPositionPolicy):
            raise ValueError("stuck_policy must be GridStuckPositionPolicy")


@dataclass(frozen=True, slots=True)
class GridConfiguration:
    lower_price: Decimal
    upper_price: Decimal
    center_price: Decimal
    spacing_type: GridSpacingType
    levels_per_side: int
    order_quantity: Decimal
    dynamic_step_ratio: Decimal
    bias: GridBias
    recenter_threshold_ratio: Decimal
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal
    max_slippage_bps: Decimal
    allowed_regimes: tuple[str, ...] = ("SIDEWAYS",)

    def __post_init__(self) -> None:
        for name in (
            "lower_price",
            "upper_price",
            "center_price",
            "order_quantity",
        ):
            object.__setattr__(
                self,
                name,
                require_positive_decimal(getattr(self, name), field_name=name),
            )
        if not self.lower_price < self.center_price < self.upper_price:
            raise ValueError("center_price must be inside grid range")
        if not isinstance(self.spacing_type, GridSpacingType):
            raise ValueError("spacing_type must be GridSpacingType")
        if (
            isinstance(self.levels_per_side, bool)
            or not isinstance(self.levels_per_side, int)
            or self.levels_per_side <= 0
        ):
            raise ValueError("levels_per_side must be a positive integer")
        if not isinstance(self.bias, GridBias):
            raise ValueError("bias must be GridBias")
        object.__setattr__(
            self,
            "dynamic_step_ratio",
            _ratio(self.dynamic_step_ratio, field_name="dynamic_step_ratio"),
        )
        object.__setattr__(
            self,
            "recenter_threshold_ratio",
            _ratio(
                self.recenter_threshold_ratio,
                field_name="recenter_threshold_ratio",
            ),
        )
        for name in ("maker_fee_rate", "taker_fee_rate"):
            object.__setattr__(self, name, _ratio(getattr(self, name), field_name=name))  # noqa: E501
        object.__setattr__(
            self,
            "max_slippage_bps",
            require_non_negative_decimal(
                self.max_slippage_bps,
                field_name="max_slippage_bps",
            ),
        )
        if not isinstance(self.allowed_regimes, tuple) or not self.allowed_regimes:  # noqa: E501
            raise ValueError("allowed_regimes must be a non-empty tuple")
        normalized_regimes = tuple(
            _text(item, field_name="allowed_regime").upper()
            for item in self.allowed_regimes
        )
        if len(normalized_regimes) != len(set(normalized_regimes)):
            raise ValueError("allowed_regimes must be unique")
        object.__setattr__(self, "allowed_regimes", normalized_regimes)


@dataclass(frozen=True, slots=True)
class GridProgram:
    program_id: str
    user_id: int
    account_id: AccountId
    instrument_id: InstrumentId
    state: GridProgramState
    risk_budget: GridRiskBudget

    def __post_init__(self) -> None:
        object.__setattr__(self, "program_id", _text(self.program_id, field_name="program_id"))  # noqa: E501
        if isinstance(self.user_id, bool) or not isinstance(self.user_id, int) or self.user_id <= 0:  # noqa: E501
            raise ValueError("user_id must be positive")
        if not isinstance(self.account_id, AccountId):
            raise ValueError("account_id must be AccountId")
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be InstrumentId")
        if self.account_id.venue_id != self.instrument_id.venue_id:
            raise ValueError("account venue must match instrument venue")
        if not isinstance(self.state, GridProgramState):
            raise ValueError("state must be GridProgramState")
        if not isinstance(self.risk_budget, GridRiskBudget):
            raise ValueError("risk_budget must be GridRiskBudget")


@dataclass(frozen=True, slots=True)
class GridLevel:
    level_index: int
    side: OrderSide
    price: Decimal
    quantity: Decimal
    state: GridLevelState = GridLevelState.PENDING
    client_order_ref: str | None = None
    filled_quantity: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if isinstance(self.level_index, bool) or not isinstance(self.level_index, int) or self.level_index == 0:  # noqa: E501
            raise ValueError("level_index must be a non-zero integer")
        if not isinstance(self.side, OrderSide):
            raise ValueError("side must be OrderSide")
        object.__setattr__(self, "price", require_positive_decimal(self.price, field_name="price"))  # noqa: E501
        object.__setattr__(
            self,
            "quantity",
            require_positive_decimal(self.quantity, field_name="quantity"),
        )
        object.__setattr__(
            self,
            "filled_quantity",
            require_non_negative_decimal(
                self.filled_quantity,
                field_name="filled_quantity",
            ),
        )
        if self.filled_quantity > self.quantity:
            raise ValueError("filled_quantity cannot exceed quantity")
        if not isinstance(self.state, GridLevelState):
            raise ValueError("state must be GridLevelState")
        if self.client_order_ref is not None:
            object.__setattr__(
                self,
                "client_order_ref",
                _text(self.client_order_ref, field_name="client_order_ref"),
            )


@dataclass(frozen=True, slots=True)
class GridCycle:
    cycle_id: str
    sequence: int
    state: GridCycleState
    center_price: Decimal
    levels: tuple[GridLevel, ...]
    opened_at: datetime
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "cycle_id", _text(self.cycle_id, field_name="cycle_id"))  # noqa: E501
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence <= 0:  # noqa: E501
            raise ValueError("sequence must be positive")
        if not isinstance(self.state, GridCycleState):
            raise ValueError("state must be GridCycleState")
        object.__setattr__(
            self,
            "center_price",
            require_positive_decimal(self.center_price, field_name="center_price"),  # noqa: E501
        )
        if not isinstance(self.levels, tuple) or not self.levels:
            raise ValueError("levels must be a non-empty tuple")
        indices = tuple(level.level_index for level in self.levels)
        if len(indices) != len(set(indices)):
            raise ValueError("grid level indices must be unique")
        object.__setattr__(
            self,
            "opened_at",
            normalize_utc_datetime(self.opened_at, field_name="opened_at"),
        )
        if self.closed_at is not None:
            object.__setattr__(
                self,
                "closed_at",
                normalize_utc_datetime(self.closed_at, field_name="closed_at"),
            )


@dataclass(frozen=True, slots=True)
class GridInstance:
    instance_id: str
    program_id: str
    user_id: int
    account_id: AccountId
    instrument_id: InstrumentId
    state: GridInstanceState
    config: GridConfiguration
    risk_budget: GridRiskBudget
    cycle: GridCycle
    inventory_quantity: Decimal
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "instance_id", _text(self.instance_id, field_name="instance_id"))  # noqa: E501
        object.__setattr__(self, "program_id", _text(self.program_id, field_name="program_id"))  # noqa: E501
        if isinstance(self.user_id, bool) or not isinstance(self.user_id, int) or self.user_id <= 0:  # noqa: E501
            raise ValueError("user_id must be positive")
        if not isinstance(self.account_id, AccountId):
            raise ValueError("account_id must be AccountId")
        if not isinstance(self.instrument_id, InstrumentId):
            raise ValueError("instrument_id must be InstrumentId")
        if self.account_id.venue_id != self.instrument_id.venue_id:
            raise ValueError("account venue must match instrument venue")
        if not isinstance(self.state, GridInstanceState):
            raise ValueError("state must be GridInstanceState")
        object.__setattr__(
            self,
            "inventory_quantity",
            require_non_negative_decimal(
                self.inventory_quantity.copy_abs(),
                field_name="inventory_quantity",
            ) * (Decimal("-1") if self.inventory_quantity < 0 else Decimal("1")),  # noqa: E501
        )
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_datetime(self.created_at, field_name="created_at"),
        )
        object.__setattr__(
            self,
            "updated_at",
            normalize_utc_datetime(self.updated_at, field_name="updated_at"),
        )


@dataclass(frozen=True, slots=True)
class GridFillAttribution:
    fill_id: FillId
    cycle_id: str
    level_index: int
    side: OrderSide
    quantity: Decimal
    price: Decimal
    fee: Decimal
    maker: bool
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.fill_id, FillId):
            raise ValueError("fill_id must be FillId")
        object.__setattr__(self, "cycle_id", _text(self.cycle_id, field_name="cycle_id"))  # noqa: E501
        if isinstance(self.level_index, bool) or not isinstance(self.level_index, int) or self.level_index == 0:  # noqa: E501
            raise ValueError("level_index must be non-zero")
        if not isinstance(self.side, OrderSide):
            raise ValueError("side must be OrderSide")
        object.__setattr__(self, "quantity", require_positive_decimal(self.quantity, field_name="quantity"))  # noqa: E501
        object.__setattr__(self, "price", require_positive_decimal(self.price, field_name="price"))  # noqa: E501
        object.__setattr__(self, "fee", require_non_negative_decimal(self.fee, field_name="fee"))  # noqa: E501
        if not isinstance(self.maker, bool):
            raise ValueError("maker must be bool")
        object.__setattr__(
            self,
            "occurred_at",
            normalize_utc_datetime(self.occurred_at, field_name="occurred_at"),
        )


@dataclass(frozen=True, slots=True)
class GridPnL:
    instance_id: str
    cycle_id: str
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    fees: Decimal
    net_pnl: Decimal
    inventory_quantity: Decimal
    mark_price: Decimal


@dataclass(frozen=True, slots=True)
class GridSimulationAssumptions:
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal
    slippage_bps: Decimal
    adverse_selection_bps: Decimal
    queue_fill_fraction: Decimal
    latency_ms: int

    def __post_init__(self) -> None:
        for name in ("maker_fee_rate", "taker_fee_rate", "queue_fill_fraction"):  # noqa: E501
            object.__setattr__(self, name, _ratio(getattr(self, name), field_name=name))  # noqa: E501
        for name in ("slippage_bps", "adverse_selection_bps"):
            object.__setattr__(
                self,
                name,
                require_non_negative_decimal(getattr(self, name), field_name=name),  # noqa: E501
            )
        if isinstance(self.latency_ms, bool) or not isinstance(self.latency_ms, int) or self.latency_ms < 0:  # noqa: E501
            raise ValueError("latency_ms must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class GridMarketEvent:
    bid: Decimal
    ask: Decimal
    available_bid_quantity: Decimal
    available_ask_quantity: Decimal
    occurred_at: datetime

    def __post_init__(self) -> None:
        for name in ("bid", "ask"):
            object.__setattr__(self, name, require_positive_decimal(getattr(self, name), field_name=name))  # noqa: E501
        if self.bid >= self.ask:
            raise ValueError("bid must be below ask")
        for name in ("available_bid_quantity", "available_ask_quantity"):
            object.__setattr__(
                self,
                name,
                require_non_negative_decimal(getattr(self, name), field_name=name),  # noqa: E501
            )
        object.__setattr__(
            self,
            "occurred_at",
            normalize_utc_datetime(self.occurred_at, field_name="occurred_at"),
        )
