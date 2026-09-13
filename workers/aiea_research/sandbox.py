"""Docker-isolated execution boundary for AI-generated AIEA research code.

The container receives source/input only over stdin. No host filesystem mounts,
network, production secrets, Docker socket, VenueAdapter or ExecutionCoordinator
access are granted by this adapter.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from hashlib import sha256
import json
import re
import subprocess
from typing import Mapping

from apps.aiea.application.research_loop import ResearchSandboxPolicy
from workers.aiea_research.policy import ResearchCodeSubmission, validate_submission

_SAFE_STDLIB = frozenset({
    "collections", "datetime", "decimal", "functools", "itertools", "json",
    "math", "random", "statistics",
})
_FORBIDDEN_CALLS = frozenset({
    "__import__", "compile", "eval", "exec", "input", "open",
})
_FORBIDDEN_ATTRS = frozenset({
    "connect", "fork", "popen", "remove", "rmdir", "socket", "system",
    "unlink",
})
_IMAGE_RE = re.compile(r"^[A-Za-z0-9._:/-]+@sha256:[0-9a-f]{64}$")
_JOB_RE = re.compile(r"[^a-z0-9_.-]+")


@dataclass(frozen=True, slots=True)
class SandboxJob:
    job_id: str
    workspace_id: str
    user_id: int
    submission: ResearchCodeSubmission
    input_payload: Mapping[str, object]

    def __post_init__(self) -> None:
        for field in ("job_id", "workspace_id"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be non-empty")
        if isinstance(self.user_id, bool) or not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValueError("user_id must be positive")
        if not isinstance(self.submission, ResearchCodeSubmission):
            raise ValueError("submission must be ResearchCodeSubmission")
        if not isinstance(self.input_payload, Mapping):
            raise ValueError("input_payload must be a mapping")


@dataclass(frozen=True, slots=True)
class SandboxResult:
    job_id: str
    workspace_id: str
    user_id: int
    image_digest: str
    exit_code: int
    stdout: str
    stderr: str
    evidence_hash: str


class SandboxRejected(ValueError):
    """Submission or runtime contract is unsafe and must not execute."""


class SandboxExecutionError(RuntimeError):
    """Sandbox runtime failed, timed out, or returned a non-zero exit."""


def validate_source_ast(submission: ResearchCodeSubmission, policy: ResearchSandboxPolicy) -> None:
    """Fail closed on imports and operations outside the research allowlist."""
    validate_submission(submission, policy)
    try:
        tree = ast.parse(submission.source_code, filename="<aiea-research>")
    except SyntaxError as exc:
        raise SandboxRejected("research source is not valid Python") from exc

    allowed = _SAFE_STDLIB | {item.strip().lower() for item in policy.allowed_dependencies}
    violations: list[str] = []
    has_run = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "run":
            has_run = True
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0].lower()
                if root not in allowed:
                    violations.append(f"import:{root}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0].lower()
            if not root or root not in allowed:
                violations.append(f"import:{root or '<relative>'}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_CALLS:
                violations.append(f"call:{node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in _FORBIDDEN_ATTRS:
                violations.append(f"call:{node.func.attr}")

    if not has_run:
        violations.append("missing:run")
    if violations:
        raise SandboxRejected("unsafe research source: " + ",".join(sorted(set(violations))))


def _container_name(job_id: str) -> str:
    normalized = _JOB_RE.sub("-", job_id.strip().lower()).strip("-.") or "job"
    suffix = sha256(job_id.encode("utf-8")).hexdigest()[:10]
    return f"nexus-aiea-{normalized[:32]}-{suffix}"


def build_docker_run_command(*, image_digest: str, job: SandboxJob, policy: ResearchSandboxPolicy) -> tuple[str, ...]:
    if not isinstance(image_digest, str) or not _IMAGE_RE.fullmatch(image_digest):
        raise SandboxRejected("sandbox image must be pinned by sha256 digest")
    validate_source_ast(job.submission, policy)
    memory = f"{policy.max_memory_mb}m"
    cpus = str(policy.max_cpu_cores)
    return (
        "docker", "run", "--rm", "--init", "--name", _container_name(job.job_id),
        "--pull", "never",
        "--network", "none",
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges=true",
        "--pids-limit", "64",
        "--memory", memory,
        "--memory-swap", memory,
        "--cpus", cpus,
        "--ulimit", "nofile=64:64",
        "--user", "65534:65534",
        "--workdir", "/tmp",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        image_digest,
        "python", "-I", "-c", _BOOTSTRAP,
    )


def _payload(job: SandboxJob) -> str:
    body = {
        "source_code": job.submission.source_code,
        "input_payload": dict(job.input_payload),
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class DockerResearchSandboxExecutor:
    """Execute one validated research job in a locked-down Docker container."""

    def __init__(self, *, image_digest: str, docker_executable: str = "docker") -> None:
        if not _IMAGE_RE.fullmatch(image_digest):
            raise ValueError("image_digest must be an immutable sha256 Docker reference")
        if not isinstance(docker_executable, str) or not docker_executable.strip():
            raise ValueError("docker_executable must be non-empty")
        self._image_digest = image_digest
        self._docker_executable = docker_executable.strip()

    def execute(self, *, job: SandboxJob, policy: ResearchSandboxPolicy) -> SandboxResult:
        command = list(build_docker_run_command(image_digest=self._image_digest, job=job, policy=policy))
        command[0] = self._docker_executable
        payload = _payload(job)
        timeout = policy.max_wall_seconds
        try:
            completed = subprocess.run(
                command,
                input=payload,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            self._force_remove(_container_name(job.job_id))
            raise SandboxExecutionError(f"research sandbox timed out after {timeout}s") from exc

        evidence_hash = sha256(
            "|".join((
                job.job_id, job.workspace_id, str(job.user_id), self._image_digest,
                sha256(payload.encode("utf-8")).hexdigest(), str(completed.returncode),
                completed.stdout, completed.stderr,
            )).encode("utf-8")
        ).hexdigest()
        result = SandboxResult(
            job_id=job.job_id,
            workspace_id=job.workspace_id,
            user_id=job.user_id,
            image_digest=self._image_digest,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            evidence_hash=evidence_hash,
        )
        if completed.returncode != 0:
            raise SandboxExecutionError(
                f"research sandbox exited with code {completed.returncode}: {completed.stderr[:400]}"
            )
        return result

    def _force_remove(self, name: str) -> None:
        subprocess.run(
            [self._docker_executable, "rm", "-f", name],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )


_BOOTSTRAP = r'''
import json, sys
payload = json.loads(sys.stdin.read())
source = payload["source_code"]
namespace = {"__name__": "__aiea_research__"}
exec(compile(source, "<aiea-research>", "exec"), namespace, namespace)
run = namespace.get("run")
if not callable(run):
    raise RuntimeError("research source must define run(input_data)")
result = run(payload["input_payload"])
print(json.dumps(result, sort_keys=True, separators=(",", ":"), default=str))
'''.strip()
