from __future__ import annotations

import time
from pathlib import Path
from typing import Protocol

from .config import Project6Config
from .patching import RepairWorkspace, apply_unified_diff, validate_unified_diff
from .repository import build_repository_map, localize_trace
from .runner import run_tests
from .schemas import PatchProposal, RepairResult


class Planner(Protocol):
    def propose(self, failure: str, attempt: int) -> PatchProposal: ...


class ScriptedPlanner:
    def __init__(self, proposals: list[PatchProposal]):
        self.proposals = proposals

    def propose(self, failure: str, attempt: int) -> PatchProposal:
        if attempt >= len(self.proposals):
            raise RuntimeError("scripted planner exhausted")
        return self.proposals[attempt]


class RepairAgent:
    def __init__(self, config: Project6Config):
        self.config = config

    def run(
        self,
        bug_id: str,
        system: str,
        source_root: str | Path,
        work_root: str | Path,
        allowed_paths: list[str],
        public_tests: list[str],
        hidden_tests: list[str],
        planner: Planner,
    ) -> RepairResult:
        started = time.perf_counter()
        workspace = RepairWorkspace(source_root, work_root)
        trajectory = ["map_repository"]
        build_repository_map(workspace.destination)
        initial = run_tests(workspace.destination, public_tests, self.config.test_timeout_seconds, self.config.max_test_output_chars)
        trajectory.extend(["run_public_tests", "localize_failure"])
        localize_trace(initial.output)
        failure = initial.output
        attempts = 1 if system == "one_shot" else self.config.max_patch_attempts
        last_error: str | None = None
        overfit = False
        rollback_verified = True
        changed_lines = 0

        for attempt in range(attempts):
            trajectory.append("plan_patch")
            try:
                proposal = planner.propose(failure, attempt)
                decision = validate_unified_diff(proposal.unified_diff, allowed_paths, self.config.max_changed_lines)
                changed_lines = decision.changed_lines
                if not decision.allowed:
                    raise PermissionError("; ".join(decision.reasons))
                apply_unified_diff(workspace.destination, proposal.unified_diff)
                trajectory.append("apply_patch")
                public = run_tests(workspace.destination, public_tests, self.config.test_timeout_seconds, self.config.max_test_output_chars)
                trajectory.append("public_tests")
                if not public.passed:
                    failure = public.output
                    rollback_verified &= workspace.rollback()
                    trajectory.extend(["reflect", "rollback"])
                    continue
                hidden = run_tests(workspace.destination, hidden_tests, self.config.test_timeout_seconds, self.config.max_test_output_chars)
                trajectory.append("hidden_tests")
                if not hidden.passed:
                    overfit = True
                    failure = "Candidate passed public tests but failed hidden regression checks."
                    rollback_verified &= workspace.rollback()
                    trajectory.extend(["overfit_detected", "rollback"])
                    continue
                trajectory.append("accept")
                return RepairResult(bug_id=bug_id, system=system, verified=True, attempts=attempt + 1, public_passed=True, hidden_passed=True, overfit_detected=overfit, rollback_verified=rollback_verified, changed_lines=changed_lines, trajectory=trajectory, latency_seconds=time.perf_counter() - started)
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                rollback_verified &= workspace.rollback()
                trajectory.extend(["reject_patch", "rollback"])
                failure = last_error

        final_public = run_tests(workspace.destination, public_tests, self.config.test_timeout_seconds, self.config.max_test_output_chars)
        return RepairResult(bug_id=bug_id, system=system, verified=False, attempts=attempts, public_passed=final_public.passed, hidden_passed=False, overfit_detected=overfit, rollback_verified=rollback_verified and not workspace.changed_paths(), changed_lines=changed_lines, trajectory=trajectory, latency_seconds=time.perf_counter() - started, error=last_error or "attempt budget exhausted")
