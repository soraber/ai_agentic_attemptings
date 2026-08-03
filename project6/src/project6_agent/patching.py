from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from .schemas import PatchDecision


HEADER = re.compile(r"^\+\+\+\s+(?:b/)?(.+)$", re.MULTILINE)


def validate_unified_diff(
    diff: str, allowed_paths: list[str], max_changed_lines: int
) -> PatchDecision:
    reasons: list[str] = []
    paths = [value.strip() for value in HEADER.findall(diff) if value.strip() != "/dev/null"]
    if not diff.startswith("--- ") or not paths:
        reasons.append("patch must be a complete unified diff")
    normalized = []
    for value in paths:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            reasons.append(f"unsafe patch path: {value}")
        normalized.append(path.as_posix())
    if set(normalized) - set(allowed_paths):
        reasons.append(f"path outside allowlist: {sorted(set(normalized) - set(allowed_paths))}")
    changed_lines = sum(
        1
        for line in diff.splitlines()
        if (line.startswith("+") and not line.startswith("+++"))
        or (line.startswith("-") and not line.startswith("---"))
    )
    if changed_lines > max_changed_lines:
        reasons.append(f"changed-line budget exceeded: {changed_lines}>{max_changed_lines}")
    return PatchDecision(allowed=not reasons, reasons=reasons or ["patch satisfies project6-policy-v1"], changed_lines=changed_lines, paths=normalized)


def apply_unified_diff(root: str | Path, diff: str) -> None:
    root = Path(root)
    check = subprocess.run(["git", "apply", "--check", "-"], cwd=root, input=diff, text=True, capture_output=True)
    if check.returncode:
        raise ValueError((check.stderr or check.stdout).strip())
    applied = subprocess.run(["git", "apply", "-"], cwd=root, input=diff, text=True, capture_output=True)
    if applied.returncode:
        raise RuntimeError((applied.stderr or applied.stdout).strip())


class RepairWorkspace:
    def __init__(self, source: str | Path, destination: str | Path):
        self.source = Path(source)
        self.destination = Path(destination)
        if self.destination.exists():
            shutil.rmtree(self.destination)
        shutil.copytree(self.source, self.destination)
        self._snapshot = self._read_files()

    def _read_files(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.destination).as_posix(): path.read_bytes()
            for path in self.destination.rglob("*")
            if path.is_file() and ".pytest_cache" not in path.parts and "__pycache__" not in path.parts
        }

    def changed_paths(self) -> list[str]:
        current = self._read_files()
        return sorted(path for path in set(current) | set(self._snapshot) if current.get(path) != self._snapshot.get(path))

    def rollback(self) -> bool:
        for path in list(self.destination.rglob("*")):
            if path.is_file() and path.relative_to(self.destination).as_posix() not in self._snapshot:
                path.unlink()
        for relative, content in self._snapshot.items():
            path = self.destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return not self.changed_paths()
