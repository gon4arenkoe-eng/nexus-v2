"""Phase 10 persistence application services."""
from __future__ import annotations

from datetime import datetime
import json
from typing import Any

from sqlalchemy.exc import IntegrityError

from apps.core.application.platform_security import SettingChangeEvidence
from infra.persistence.repositories.platform_security import (
    PlatformSecurityRepository,
)
from packages.contracts.security import (
    AuditEvent,
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
)


class PlatformSecurityStore:
    def __init__(self, repository: PlatformSecurityRepository) -> None:
        self._repository = repository

    async def persist_setting_change(
        self,
        evidence: SettingChangeEvidence,
    ) -> None:
        await self._repository.append_setting(evidence.setting)
        await self._repository.append_audit(evidence.audit_event)


class WorkspaceBootstrapError(RuntimeError):
    """Base tenant-workspace bootstrap failure."""


class WorkspaceBootstrapConflict(WorkspaceBootstrapError):
    """Existing tenant security state conflicts with bootstrap request."""


def _bootstrap_event_id(workspace_id: str) -> str:
    return f"workspace-bootstrap:{workspace_id}"


def _bootstrap_audit_payload(
    *,
    workspace_id: str,
    workspace_name: str,
    owner_user_id: int,
) -> str:
    return json.dumps(
        {
            "workspace_id": workspace_id,
            "workspace_name": workspace_name,
            "owner_user_id": owner_user_id,
            "owner_role": WorkspaceRole.OWNER.value,
            "membership_active": True,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


async def bootstrap_workspace(
    *,
    session_factory: Any,
    workspace_id: str,
    workspace_name: str,
    owner_user_id: int,
    reason: str,
    created_at: datetime,
) -> tuple[Workspace, WorkspaceMembership]:
    workspace = Workspace(
        workspace_id=workspace_id,
        name=workspace_name,
        owner_user_id=owner_user_id,
        created_at=created_at,
    )
    owner_membership = WorkspaceMembership(
        workspace_id=workspace_id,
        user_id=owner_user_id,
        role=WorkspaceRole.OWNER,
        active=True,
    )
    audit_event = AuditEvent(
        event_id=_bootstrap_event_id(workspace_id),
        workspace_id=workspace_id,
        actor_user_id=owner_user_id,
        action="workspace.bootstrap",
        resource_type="workspace",
        resource_id=workspace_id,
        old_value_json=None,
        new_value_json=_bootstrap_audit_payload(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            owner_user_id=owner_user_id,
        ),
        reason=reason,
        occurred_at=created_at,
    )

    async with session_factory() as session:
        repository = PlatformSecurityRepository(session)

        try:
            existing_workspace = await repository.get_workspace(
                workspace_id=workspace_id,
            )
            existing_membership = await repository.get_membership(
                workspace_id=workspace_id,
                user_id=owner_user_id,
            )

            if existing_workspace is None:
                if existing_membership is not None:
                    raise WorkspaceBootstrapConflict(
                        "membership exists without workspace"
                    )

                await repository.add_workspace(workspace)
                await repository.put_membership(owner_membership)

            else:
                if (
                    existing_workspace.owner_user_id != owner_user_id
                    or existing_workspace.name != workspace_name
                ):
                    raise WorkspaceBootstrapConflict(
                        "workspace identity or ownership conflict"
                    )

                if existing_membership is None:
                    raise WorkspaceBootstrapConflict(
                        "workspace exists without owner membership"
                    )

                if (
                    existing_membership.role is not WorkspaceRole.OWNER
                    or not existing_membership.active
                ):
                    raise WorkspaceBootstrapConflict(
                        "owner membership conflict"
                    )

                workspace = existing_workspace
                owner_membership = existing_membership

            await repository.append_audit(audit_event)
            await session.commit()

        except WorkspaceBootstrapConflict:
            await session.rollback()
            raise

        except (ValueError, IntegrityError) as exc:
            await session.rollback()
            raise WorkspaceBootstrapConflict(
                "workspace bootstrap persistence conflict"
            ) from exc

        except Exception:
            await session.rollback()
            raise

    return workspace, owner_membership
