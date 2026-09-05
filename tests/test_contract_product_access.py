from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from packages.contracts.product_access import (
    EntitlementDecision,
    FeatureKey,
    QuotaResult,
)


def test_feature_key_is_stable_and_normalized() -> None:
    assert str(FeatureKey(" AIEA.EXPERIMENT.RUN ")) == "aiea.experiment.run"


@pytest.mark.parametrize("value", ["", "plan.pro", "AIEA", "aiea..run", "aiea.experiment.run!"])
def test_feature_key_rejects_non_capability_identifiers(value: str) -> None:
    with pytest.raises(ValueError):
        FeatureKey(value)


def test_entitlement_decision_is_tenant_scoped_and_immutable() -> None:
    decision = EntitlementDecision(
        workspace_id="workspace-1",
        feature_key=FeatureKey("grid.instance.create"),
        granted=True,
        reason="plan entitlement",
    )
    assert decision.workspace_id == "workspace-1"
    with pytest.raises(FrozenInstanceError):
        decision.granted = False  # type: ignore[misc]


def test_finite_quota_decision_matches_usage() -> None:
    result = QuotaResult(
        workspace_id="workspace-1",
        quota_key=FeatureKey("workspace.member.create"),
        permitted=True,
        limit=3,
        usage=2,
    )
    assert result.permitted is True


@pytest.mark.parametrize(
    ("limit", "usage", "permitted"),
    [(3, 3, True), (3, 2, False), (None, 0, False), (-1, 0, False)],
)
def test_quota_result_fails_closed_for_inconsistent_policy(
    limit: int | None, usage: int, permitted: bool
) -> None:
    with pytest.raises(ValueError):
        QuotaResult(
            workspace_id="workspace-1",
            quota_key=FeatureKey("workspace.member.create"),
            permitted=permitted,
            limit=limit,
            usage=usage,
        )
