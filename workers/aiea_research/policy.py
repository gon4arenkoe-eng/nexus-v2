"""Isolation policy checks for off-production AIEA research workers."""

from __future__ import annotations

from dataclasses import dataclass

from apps.aiea.application.research_loop import ResearchSandboxPolicy


FORBIDDEN_TOKENS = (
    "VenueAdapter",
    "ExecutionCoordinator",
    "submit_order",
    "cancel_order",
    "exchange_credentials",
    "api_secret",
    "withdraw",
)


@dataclass(frozen=True, slots=True)
class ResearchCodeSubmission:
    source_code: str
    declared_dependencies: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_code, str) or not self.source_code.strip():  # noqa: E501
            raise ValueError("source_code must be non-empty")
        if not isinstance(self.declared_dependencies, tuple):
            raise ValueError("declared_dependencies must be a tuple")
        if not all(isinstance(item, str) and item.strip() for item in self.declared_dependencies):  # noqa: E501
            raise ValueError("declared_dependencies must contain non-empty strings")  # noqa: E501


def validate_submission(
    submission: ResearchCodeSubmission,
    policy: ResearchSandboxPolicy,
) -> None:
    if not isinstance(submission, ResearchCodeSubmission):
        raise ValueError("submission must be ResearchCodeSubmission")
    if not isinstance(policy, ResearchSandboxPolicy):
        raise ValueError("policy must be ResearchSandboxPolicy")
    lowered = submission.source_code.lower()
    for token in FORBIDDEN_TOKENS:
        if token.lower() in lowered:
            raise ValueError(f"forbidden research token: {token}")
    allowlist = {item.strip().lower() for item in policy.allowed_dependencies}
    requested = {item.strip().lower() for item in submission.declared_dependencies}  # noqa: E501
    denied = requested - allowlist
    if denied:
        names = ",".join(sorted(denied))
        raise ValueError(f"research dependency not allowlisted: {names}")
