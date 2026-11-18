from __future__ import annotations

import os
import shutil
import signal
import subprocess
import threading
import time
import uuid
from collections import deque
from pathlib import Path

from .schemas import TestOutcome


def runner_command(root: Path, targets: list[str], backend: str, image: str, name: str) -> list[str]:
    root = root.resolve()
    for target in targets:
        path = Path(target)
        if path.is_absolute() or ".." in path.parts or target.startswith("-"):
            raise PermissionError("Tests must be relative paths, not options")
        if not (root / path).is_file() or not (root / path).resolve().is_relative_to(root):
            raise PermissionError("Test target is outside the execution workspace")
    if any(path.is_symlink() for path in root.rglob("*")):
        raise PermissionError("Execution workspaces must not contain symlinks")
    pytest = ["-m", "pytest", "-q", "-p", "no:cacheprovider", *targets]
    if backend == "trusted_fixture":
        return [os.sys.executable, *pytest]
    if backend != "docker":
        raise ValueError("Unknown execution backend")
    return ["docker", "run", "--pull=never", "--rm", "--name", name,
            "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--pids-limit=64", "--memory=512m",
            "--cpus=1", "--user=65534:65534",
            "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=64m",
            "--mount", f"type=bind,src={root},dst=/workspace,readonly",
            "--workdir=/workspace", "--env=PYTHONDONTWRITEBYTECODE=1",
            "--env=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1", "--env=HOME=/tmp",
            "--entrypoint=python", image, *pytest]


def sandbox_preflight(image: str) -> dict:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is required; trusted_fixture is only for authored unit-test fixtures")
    result = subprocess.run(["docker", "image", "inspect", image, "--format", "{{.Id}}"],
                            text=True, capture_output=True, timeout=20)
    if result.returncode:
        raise RuntimeError("Start Docker and build the project6 sandbox image before model evaluation")
    return {"backend": "docker", "image": image, "image_id": result.stdout.strip()}


def run_tests(root: str | Path, targets: list[str], timeout_seconds: float = 20,
              max_output_chars: int = 12000, *, backend: str = "docker",
              image: str = "project6-test-runner:p0-20261117") -> TestOutcome:
    root = Path(root).resolve()
    started = time.perf_counter()
    name = "project6-" + uuid.uuid4().hex
    command = runner_command(root, targets, backend, image, name)
    if backend == "docker":
        sandbox_preflight(image)
    # Never pass API keys or other ambient variables to test Python.
    env = {"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1",
           "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONHASHSEED": "0"}
    if backend == "docker":
        command[0] = shutil.which("docker")
        # Client socket context never enters the container.
        for key in ("HOME", "DOCKER_HOST", "DOCKER_CONTEXT"):
            if key in os.environ:
                env[key] = os.environ[key]
    tail: deque[bytes] = deque(maxlen=max(2, max_output_chars // 4096 + 2))
    process = subprocess.Popen(command, cwd=root, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, start_new_session=True)

    def drain():
        for chunk in iter(lambda: process.stdout.read(4096), b""):
            tail.append(chunk)

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    timed_out = False
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()
    finally:
        if backend == "docker":
            subprocess.run([command[0], "rm", "-f", name], capture_output=True, timeout=20)
        reader.join(timeout=2)
    output = b"".join(tail).decode("utf-8", errors="replace")[-max_output_chars:]
    return TestOutcome(passed=process.returncode == 0 and not timed_out,
                       returncode=None if timed_out else process.returncode, timed_out=timed_out,
                       duration_seconds=time.perf_counter() - started, output=output)
