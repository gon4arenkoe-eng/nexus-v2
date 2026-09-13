from __future__ import annotations

import subprocess

import pytest

from apps.aiea.application.research_loop import ResearchSandboxPolicy
from workers.aiea_research.policy import ResearchCodeSubmission
from workers.aiea_research.sandbox import (
    DockerResearchSandboxExecutor,
    SandboxExecutionError,
    SandboxJob,
    SandboxRejected,
    build_docker_run_command,
    validate_source_ast,
)

IMAGE = "ghcr.io/example/nexus-aiea-sandbox@sha256:" + "a" * 64


def policy() -> ResearchSandboxPolicy:
    return ResearchSandboxPolicy(7, 256, 1, ("numpy", "json"))


def job(source: str = "def run(input_data):\n    return {'x': input_data['x'] + 1}\n") -> SandboxJob:
    return SandboxJob(
        job_id="job-1", workspace_id="ws-1", user_id=7,
        submission=ResearchCodeSubmission(source_code=source, declared_dependencies=()),
        input_payload={"x": 2},
    )


def test_command_is_immutable_digest_and_hard_isolated() -> None:
    cmd = build_docker_run_command(image_digest=IMAGE, job=job(), policy=policy())
    joined = " ".join(cmd)
    assert cmd[0:2] == ("docker", "run")
    assert "--network none" in joined
    assert "--read-only" in cmd
    assert "--cap-drop ALL" in joined
    assert "no-new-privileges=true" in cmd
    assert "--pids-limit 64" in joined
    assert "--memory 256m" in joined
    assert "--memory-swap 256m" in joined
    assert "--cpus 1" in joined
    assert "--user 65534:65534" in joined
    assert "--pull never" in joined
    assert "--mount" not in cmd and "--volume" not in cmd and "-v" not in cmd
    assert IMAGE in cmd


def test_image_tag_without_digest_is_rejected() -> None:
    with pytest.raises(SandboxRejected, match="pinned"):
        build_docker_run_command(image_digest="python:3.13", job=job(), policy=policy())


@pytest.mark.parametrize("source", [
    "import os\ndef run(input_data): return 1\n",
    "import socket\ndef run(input_data): return 1\n",
    "def run(input_data):\n    return open('/etc/passwd').read()\n",
    "def run(input_data):\n    return eval('1+1')\n",
    "import subprocess\ndef run(input_data): return 1\n",
])
def test_static_ast_rejects_filesystem_network_process_and_dynamic_code(source: str) -> None:
    with pytest.raises(SandboxRejected, match="unsafe research source"):
        validate_source_ast(ResearchCodeSubmission(source, ()), policy())


def test_dependency_allowlist_is_enforced() -> None:
    submission = ResearchCodeSubmission(
        "import requests\ndef run(input_data): return 1\n", ("requests",),
    )
    with pytest.raises(ValueError, match="not allowlisted"):
        validate_source_ast(submission, policy())


def test_declared_allowlisted_dependency_is_accepted() -> None:
    submission = ResearchCodeSubmission(
        "import numpy\ndef run(input_data): return float(numpy.mean([1,2]))\n", ("numpy",),
    )
    validate_source_ast(submission, policy())


def test_run_entrypoint_is_required() -> None:
    with pytest.raises(SandboxRejected, match="missing:run"):
        validate_source_ast(ResearchCodeSubmission("x = 1", ()), policy())


def test_executor_returns_deterministic_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout='{"x":3}\n', stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    executor = DockerResearchSandboxExecutor(image_digest=IMAGE)
    first = executor.execute(job=job(), policy=policy())
    second = executor.execute(job=job(), policy=policy())
    assert first.evidence_hash == second.evidence_hash
    assert first.workspace_id == "ws-1" and first.user_id == 7
    assert first.image_digest == IMAGE


def test_executor_timeout_force_removes_container(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    def fake_run(command, **kwargs):
        calls.append(list(command))
        if command[1] == "run":
            raise subprocess.TimeoutExpired(command, 7)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    executor = DockerResearchSandboxExecutor(image_digest=IMAGE)
    with pytest.raises(SandboxExecutionError, match="timed out"):
        executor.execute(job=job(), policy=policy())
    assert any(call[1:3] == ["rm", "-f"] for call in calls)


def test_nonzero_runtime_exit_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess, "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 9, stdout="", stderr="boom"),
    )
    executor = DockerResearchSandboxExecutor(image_digest=IMAGE)
    with pytest.raises(SandboxExecutionError, match="code 9"):
        executor.execute(job=job(), policy=policy())
