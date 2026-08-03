from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from .schemas import TestOutcome


def _limits() -> None:
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    except (ImportError, OSError, ValueError):
        pass


def run_tests(
    root: str | Path,
    targets: list[str],
    timeout_seconds: float = 20,
    max_output_chars: int = 12000,
) -> TestOutcome:
    started = time.perf_counter()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"}
    try:
        completed = subprocess.run(
            [os.sys.executable, "-m", "pytest", "-q", *targets],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            env=env,
            preexec_fn=_limits if os.name == "posix" else None,
        )
        output = (completed.stdout + "\n" + completed.stderr)[-max_output_chars:]
        return TestOutcome(passed=completed.returncode == 0, returncode=completed.returncode, timed_out=False, duration_seconds=time.perf_counter() - started, output=output)
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout or "") + "\n" + (exc.stderr or ""))[-max_output_chars:]
        return TestOutcome(passed=False, returncode=None, timed_out=True, duration_seconds=time.perf_counter() - started, output=output)
