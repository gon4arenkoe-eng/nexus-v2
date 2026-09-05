from __future__ import annotations

from dataclasses import fields
from inspect import signature

from packages.contracts.events import EventEnvelope
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)
from packages.contracts.providers import Clock, IdProvider
from packages.contracts.product_access import (
    EntitlementDecision,
    FeatureKey,
    QuotaResult,
)
from packages.contracts.results import (
    ErrorInfo,
    Failure,
    Success,
)
from packages.contracts.workspace import (
    WidgetContext,
    WidgetManifest,
    WidgetPlacement,
    WidgetSize,
    WorkspaceLayout,
)


def _field_names(contract_type: type[object]) -> tuple[str, ...]:
    return tuple(field.name for field in fields(contract_type))


def test_asset_class_values_are_compatible() -> None:
    assert {
        member.name: member.value
        for member in AssetClass
    } == {
        "CRYPTO": "CRYPTO",
        "EQUITY": "EQUITY",
        "ETF": "ETF",
        "FOREX": "FOREX",
        "COMMODITY": "COMMODITY",
        "FUTURE": "FUTURE",
        "OPTION": "OPTION",
        "BOND": "BOND",
        "INDEX": "INDEX",
        "CFD": "CFD",
    }


def test_instrument_type_values_are_compatible() -> None:
    assert {
        member.name: member.value
        for member in InstrumentType
    } == {
        "SPOT": "SPOT",
        "PERPETUAL": "PERPETUAL",
        "FUTURE": "FUTURE",
        "OPTION": "OPTION",
        "STOCK": "STOCK",
        "ETF": "ETF",
        "FX_PAIR": "FX_PAIR",
        "CFD": "CFD",
    }


def test_venue_id_public_fields_are_compatible() -> None:
    assert _field_names(VenueId) == (
        "value",
    )


def test_account_id_public_fields_are_compatible() -> None:
    assert _field_names(AccountId) == (
        "venue_id",
        "value",
    )


def test_instrument_id_public_fields_are_compatible() -> None:
    assert _field_names(InstrumentId) == (
        "venue_id",
        "native_symbol",
        "instrument_type",
        "asset_class",
    )


def test_event_envelope_public_fields_are_compatible() -> None:
    assert _field_names(EventEnvelope) == (
        "event_id",
        "event_type",
        "event_version",
        "source",
        "occurred_at",
        "recorded_at",
        "payload",
        "correlation_id",
        "causation_id",
    )


def test_error_info_public_fields_are_compatible() -> None:
    assert _field_names(ErrorInfo) == (
        "code",
        "message",
        "retryable",
    )


def test_success_public_fields_are_compatible() -> None:
    assert _field_names(Success) == (
        "value",
    )


def test_failure_public_fields_are_compatible() -> None:
    assert _field_names(Failure) == (
        "error",
    )


def test_feature_key_public_fields_are_compatible() -> None:
    assert _field_names(FeatureKey) == ("value",)


def test_entitlement_decision_public_fields_are_compatible() -> None:
    assert _field_names(EntitlementDecision) == (
        "workspace_id",
        "feature_key",
        "granted",
        "reason",
    )


def test_quota_result_public_fields_are_compatible() -> None:
    assert _field_names(QuotaResult) == (
        "workspace_id",
        "quota_key",
        "permitted",
        "limit",
        "usage",
    )


def test_workspace_contract_public_fields_are_compatible() -> None:
    assert _field_names(WidgetSize) == ("columns", "rows")
    assert _field_names(WidgetManifest) == (
        "widget_key",
        "version",
        "supported_context_keys",
        "minimum_size",
        "default_size",
        "required_feature",
        "required_permission",
        "safety_policy",
    )
    assert _field_names(WidgetPlacement) == (
        "instance_id",
        "widget_key",
        "widget_version",
        "column",
        "row",
        "size",
        "context_group",
    )
    assert _field_names(WorkspaceLayout) == (
        "workspace_id",
        "version",
        "widgets",
    )
    assert _field_names(WidgetContext) == ("key", "value")


def test_clock_protocol_surface_is_compatible() -> None:
    assert callable(getattr(Clock, "now"))

    parameters = tuple(
        signature(Clock.now).parameters
    )

    assert parameters == ("self",)


def test_id_provider_protocol_surface_is_compatible() -> None:
    assert callable(getattr(IdProvider, "next_id"))

    parameters = tuple(
        signature(IdProvider.next_id).parameters
    )

    assert parameters == ("self",)


def test_phase1_contract_modules_remain_importable() -> None:
    from packages.contracts import events
    from packages.contracts import identities
    from packages.contracts import primitives
    from packages.contracts import product_access
    from packages.contracts import providers
    from packages.contracts import results
    from packages.contracts import workspace

    assert identities is not None
    assert primitives is not None
    assert events is not None
    assert results is not None
    assert providers is not None
    assert product_access is not None
    assert workspace is not None
