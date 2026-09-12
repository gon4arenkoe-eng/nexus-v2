"""Phase 10 persistence application services."""
from __future__ import annotations

from infra.persistence.repositories.platform_security import PlatformSecurityRepository  # noqa: E501
from apps.core.application.platform_security import SettingChangeEvidence


class PlatformSecurityStore:
    def __init__(self, repository: PlatformSecurityRepository) -> None:
        self._repository = repository

    async def persist_setting_change(self, evidence: SettingChangeEvidence) -> None:  # noqa: E501
        await self._repository.append_setting(evidence.setting)
        await self._repository.append_audit(evidence.audit_event)
