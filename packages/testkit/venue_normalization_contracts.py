"""Reusable assertions for venue-specific normalization implementations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from adapters.common.normalization import NormalizationEntity, VenueNormalizationProfile
from apps.core.ports.venue import (
    VenueAccountState,
    VenueBalance,
    VenueFill,
    VenueOrderResult,
    VenuePosition,
)
from packages.contracts.identities import InstrumentId, VenueId


_CANONICAL_TYPES = (
    InstrumentId,
    VenueOrderResult,
    VenuePosition,
    VenueBalance,
    VenueFill,
    VenueAccountState,
)


def assert_profile_covers(
    profile: VenueNormalizationProfile,
    required: Iterable[NormalizationEntity],
) -> None:
    """Require a venue profile to explicitly declare each entity."""

    for entity in required:
        if not profile.supports(entity):
            raise AssertionError(
                f"{profile.venue_id.value} normalization profile missing {entity.value}"
            )


def assert_canonical_value_has_venue(
    value: object,
    *,
    venue_id: VenueId,
) -> None:
    """Fail if a normalized value leaks raw Mapping data or wrong venue identity."""

    if isinstance(value, Mapping):
        raise AssertionError("raw venue Mapping leaked past adapter boundary")
    if not isinstance(value, _CANONICAL_TYPES):
        raise AssertionError(f"unexpected canonical value type: {type(value)!r}")

    identity = getattr(value, "instrument_id", None)
    if isinstance(identity, InstrumentId) and identity.venue_id != venue_id:
        raise AssertionError("normalized instrument venue identity mismatch")

    account_id = getattr(value, "account_id", None)
    if account_id is not None and account_id.venue_id != venue_id:
        raise AssertionError("normalized account venue identity mismatch")
