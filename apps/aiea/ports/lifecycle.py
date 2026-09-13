"""Ports for stage-aware AIEA experiment lifecycle execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from apps.aiea.domain.research import ExperimentRecord, ExperimentStage

if TYPE_CHECKING:
    from apps.aiea.application.research_loop import ResearchTask


class ExperimentStageWorkerPort(Protocol):
    async def execute_stage(
        self,
        task: ResearchTask,
        *,
        stage: ExperimentStage,
        prior_experiments: tuple[ExperimentRecord, ...],
    ) -> ExperimentRecord: ...
