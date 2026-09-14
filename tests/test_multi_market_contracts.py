from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from packages.contracts.identities import (
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)
from packages.contracts.market_structure import (
    InstrumentDefinition,
    MarketStructureCapability,
    OptionRight,
    OptionStyle,
    SettlementType,
    TradingSessionPolicy,
    VenueMarketProfile,
)


def instrument(
    venue: str,
    symbol: str,
    instrument_type: InstrumentType,
    asset_class: AssetClass,
) -> InstrumentId:
    return InstrumentId(
        VenueId(venue),
        symbol,
        instrument_type,
        asset_class,
    )


def test_equity_definition_does_not_require_crypto_pair_semantics() -> None:
    definition = InstrumentDefinition(
        instrument_id=instrument(
            "XNAS",
            "AAPL",
            InstrumentType.STOCK,
            AssetClass.EQUITY,
        ),
        price_increment=Decimal("0.01"),
        quantity_increment=Decimal("1"),
        settlement_currency="usd",
        settlement_type=SettlementType.CASH,
        session_policy=TradingSessionPolicy.CALENDAR,
        calendar_id="XNYS-US-EQUITY",
        capabilities=frozenset(
            {
                MarketStructureCapability.TRADING_SESSIONS,
                MarketStructureCapability.CORPORATE_ACTIONS,
                MarketStructureCapability.SHORT_SELLING,
                MarketStructureCapability.SETTLEMENT,
            }
        ),
    )

    assert definition.base_currency is None
    assert definition.expiry_at is None
    assert definition.settlement_currency == "USD"


def test_fx_pair_supports_base_and_settlement_currency() -> None:
    definition = InstrumentDefinition(
        instrument_id=instrument(
            "FXBROKER",
            "EURUSD",
            InstrumentType.FX_PAIR,
            AssetClass.FOREX,
        ),
        price_increment=Decimal("0.00001"),
        quantity_increment=Decimal("1000"),
        base_currency="eur",
        settlement_currency="usd",
        settlement_type=SettlementType.CASH,
        session_policy=TradingSessionPolicy.VENUE_DEFINED,
        capabilities=frozenset(
            {
                MarketStructureCapability.TRADING_SESSIONS,
                MarketStructureCapability.MARGIN,
                MarketStructureCapability.SETTLEMENT,
            }
        ),
    )

    assert definition.base_currency == "EUR"
    assert definition.settlement_currency == "USD"


def test_future_supports_expiry_multiplier_and_underlying() -> None:
    underlying = instrument(
        "CME",
        "ES",
        InstrumentType.SPOT,
        AssetClass.INDEX,
    )
    future = InstrumentDefinition(
        instrument_id=instrument(
            "CME",
            "ESZ26",
            InstrumentType.FUTURE,
            AssetClass.FUTURE,
        ),
        price_increment=Decimal("0.25"),
        quantity_increment=Decimal("1"),
        contract_multiplier=Decimal("50"),
        settlement_currency="USD",
        settlement_type=SettlementType.CASH,
        expiry_at=datetime(2026, 12, 18, 14, 30, tzinfo=UTC),
        underlying_instrument_id=underlying,
        capabilities=frozenset(
            {
                MarketStructureCapability.EXPIRY,
                MarketStructureCapability.CONTRACT_MULTIPLIER,
                MarketStructureCapability.UNDERLYING_REFERENCE,
                MarketStructureCapability.SETTLEMENT,
            }
        ),
    )

    assert future.contract_multiplier == Decimal("50")
    assert future.expiry_at == datetime(2026, 12, 18, 14, 30, tzinfo=UTC)


def test_option_requires_explicit_contract_metadata() -> None:
    underlying = instrument(
        "XNAS",
        "AAPL",
        InstrumentType.STOCK,
        AssetClass.EQUITY,
    )
    option = InstrumentDefinition(
        instrument_id=instrument(
            "OPRA",
            "AAPL261218C00200000",
            InstrumentType.OPTION,
            AssetClass.OPTION,
        ),
        price_increment=Decimal("0.01"),
        quantity_increment=Decimal("1"),
        contract_multiplier=Decimal("100"),
        settlement_currency="USD",
        settlement_type=SettlementType.PHYSICAL,
        expiry_at=datetime(2026, 12, 18, 21, 0, tzinfo=UTC),
        underlying_instrument_id=underlying,
        strike_price=Decimal("200"),
        option_right=OptionRight.CALL,
        option_style=OptionStyle.AMERICAN,
        capabilities=frozenset(
            {
                MarketStructureCapability.EXPIRY,
                MarketStructureCapability.EXERCISE,
                MarketStructureCapability.CONTRACT_MULTIPLIER,
                MarketStructureCapability.UNDERLYING_REFERENCE,
            }
        ),
    )

    assert option.option_right is OptionRight.CALL
    assert option.strike_price == Decimal("200")


def test_option_missing_metadata_fails_closed() -> None:
    with pytest.raises(ValueError, match="OPTION requires expiry_at"):
        InstrumentDefinition(
            instrument_id=instrument(
                "OPRA",
                "INVALID",
                InstrumentType.OPTION,
                AssetClass.OPTION,
            ),
            price_increment=Decimal("0.01"),
            quantity_increment=Decimal("1"),
        )


def test_crypto_perpetual_remains_continuous_and_funding_capable() -> None:
    perpetual = InstrumentDefinition(
        instrument_id=instrument(
            "BINGX",
            "BTC-USDT",
            InstrumentType.PERPETUAL,
            AssetClass.CRYPTO,
        ),
        price_increment=Decimal("0.1"),
        quantity_increment=Decimal("0.001"),
        base_currency="BTC",
        settlement_currency="USDT",
        session_policy=TradingSessionPolicy.CONTINUOUS_24_7,
        capabilities=frozenset(
            {
                MarketStructureCapability.FUNDING,
                MarketStructureCapability.MARGIN,
            }
        ),
    )

    assert perpetual.expiry_at is None
    assert MarketStructureCapability.FUNDING in perpetual.capabilities


def test_venue_profile_can_describe_mixed_asset_classes() -> None:
    profile = VenueMarketProfile(
        venue_id=VenueId("MULTI"),
        asset_classes=frozenset(
            {
                AssetClass.EQUITY,
                AssetClass.FOREX,
                AssetClass.FUTURE,
                AssetClass.OPTION,
            }
        ),
        instrument_types=frozenset(
            {
                InstrumentType.STOCK,
                InstrumentType.FX_PAIR,
                InstrumentType.FUTURE,
                InstrumentType.OPTION,
            }
        ),
        capabilities=frozenset(
            {
                MarketStructureCapability.TRADING_SESSIONS,
                MarketStructureCapability.SETTLEMENT,
            }
        ),
    )

    assert profile.supports_asset_class(AssetClass.FOREX)
    assert profile.supports_instrument_type(InstrumentType.OPTION)
    assert profile.supports_capability(MarketStructureCapability.SETTLEMENT)
