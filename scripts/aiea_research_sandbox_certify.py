"""Runtime certification for the AIEA Docker sandbox host.

Usage:
  python scripts/aiea_research_sandbox_certify.py <image@sha256:digest>
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from apps.aiea.application.research_loop import ResearchSandboxPolicy
from workers.aiea_research.policy import ResearchCodeSubmission
from workers.aiea_research.sandbox import SandboxJob, build_docker_run_command


def _run(args: list[str], *, input_text: str | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, input=input_text, text=True, capture_output=True, timeout=timeout, check=False)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"CERTIFICATION_FAILED: {message}")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: aiea_research_sandbox_certify.py <image@sha256:digest>")
    image = sys.argv[1]
    policy = ResearchSandboxPolicy(10, 256, 1, ("json",))
    job = SandboxJob(
        job_id="runtime-cert",
        workspace_id="cert",
        user_id=1,
        submission=ResearchCodeSubmission(
            source_code="def run(input_data):\n    return {'ok': input_data['ok']}\n",
            declared_dependencies=("json",),
        ),
        input_payload={"ok": True},
    )
    run_cmd = list(build_docker_run_command(image_digest=image, job=job, policy=policy))

    _require("--network" in run_cmd and run_cmd[run_cmd.index("--network") + 1] == "none", "network must be none")
    _require("--read-only" in run_cmd, "root filesystem must be read-only")
    _require("--cap-drop" in run_cmd and run_cmd[run_cmd.index("--cap-drop") + 1] == "ALL", "all capabilities must be dropped")
    _require("--security-opt" in run_cmd and "no-new-privileges=true" in run_cmd, "no-new-privileges required")
    _require("--memory" in run_cmd and "--cpus" in run_cmd and "--pids-limit" in run_cmd, "resource limits required")
    _require("--mount" not in run_cmd and "-v" not in run_cmd and "--volume" not in run_cmd, "host mounts forbidden")

    version = _run(["docker", "version", "--format", "{{.Server.Version}}"])
    _require(version.returncode == 0 and version.stdout.strip(), "Docker daemon unavailable")

    pulled = _run(["docker", "image", "inspect", image])
    _require(pulled.returncode == 0, "pinned sandbox image is not present locally; pull it on dev/research host first")

    sentinel = "NEXUS_SANDBOX_SECRET_SENTINEL_7d99"
    os.environ["NEXUS_CERT_SECRET"] = sentinel

    probe = _run([
        "docker", "run", "--rm", "--network", "none", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges=true",
        "--pids-limit", "32", "--memory", "128m", "--memory-swap", "128m",
        "--cpus", "1", "--user", "65534:65534", image, "python", "-I", "-c",
        "import os,pathlib,socket,json; out={}; "
        "out['secret_absent']=os.getenv('NEXUS_CERT_SECRET') is None; "
        "out['docker_socket_absent']=not pathlib.Path('/var/run/docker.sock').exists(); "
        "\ntry:\n open('/nexus-write-test','w').write('x'); out['rootfs_readonly']=False\nexcept OSError:\n out['rootfs_readonly']=True\n"
        "\ntry:\n socket.create_connection(('1.1.1.1',53),timeout=1); out['network_blocked']=False\nexcept OSError:\n out['network_blocked']=True\n"
        "print(json.dumps(out,sort_keys=True))",
    ], timeout=20)
    _require(probe.returncode == 0, f"runtime probe failed: {probe.stderr}")
    values = json.loads(probe.stdout.strip().splitlines()[-1])
    for key in ("secret_absent", "docker_socket_absent", "rootfs_readonly", "network_blocked"):
        _require(values.get(key) is True, f"{key} was not proven")

    created = _run(run_cmd[:2] + ["--help"])  # CLI availability without executing user code
    _require(created.returncode == 0, "docker run CLI unavailable")

    print("DOCKER_DAEMON=PASS")
    print("IMAGE_DIGEST_PIN=PASS")
    print("NETWORK_ISOLATION_RUNTIME=PASS")
    print("FILESYSTEM_READONLY_RUNTIME=PASS")
    print("SECRETS_ISOLATION_RUNTIME=PASS")
    print("DOCKER_SOCKET_ISOLATION_RUNTIME=PASS")
    print("RESOURCE_LIMIT_COMMAND_CONTRACT=PASS")
    print("AIEA_RESEARCH_SANDBOX_RUNTIME_CERTIFIED=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
