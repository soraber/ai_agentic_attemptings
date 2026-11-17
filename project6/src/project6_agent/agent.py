from __future__ import annotations

import time
import shutil
import tempfile
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
        for target in hidden_tests:
            if Path(target).is_absolute() or ".." in Path(target).parts:
                raise PermissionError("Hidden test paths must be relative")
        workspace = RepairWorkspace(source_root, work_root, excluded_paths=hidden_tests)
        runner_options = {"backend": self.config.execution_backend, "image": self.config.sandbox_image}
        def execute(root, targets):
            return run_tests(root, targets, self.config.test_timeout_seconds,
                             self.config.max_test_output_chars, **runner_options)
        trajectory = ["map_repository"]
        repository_map = build_repository_map(workspace.destination)
        initial = execute(workspace.destination, public_tests)
        trajectory.extend(["run_public_tests", "localize_failure"])
        locations = localize_trace(initial.output)
        if hasattr(planner, "set_context"):
            planner.set_context([item.model_dump() for item in repository_map][:100], locations[:20])
        failure = initial.output
        attempts = 1 if system == "one_shot" else self.config.max_patch_attempts
        last_error: str | None = None
        overfit = False
        rollback_verified = True
        changed_lines = 0
        candidate_selected = False

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
                public = execute(workspace.destination, public_tests)
                trajectory.append("public_tests")
                if not public.passed:
                    failure = public.output
                    rollback_verified &= workspace.rollback()
                    trajectory.extend(["reflect", "rollback"])
                    continue
                # Holdout feedback never returns to the planner after candidate selection.
                candidate_selected = True
                with tempfile.TemporaryDirectory(prefix="heldout-", dir=Path(work_root).parent) as staging:
                    evaluation_root = Path(staging) / "evaluation"
                    shutil.copytree(workspace.destination, evaluation_root)
                    for relative in hidden_tests:
                        destination = evaluation_root / relative
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(Path(source_root) / relative, destination)
                    hidden = execute(evaluation_root, hidden_tests)
                trajectory.append("final_hidden_evaluation")
                if not hidden.passed:
                    overfit = True
                    rollback_verified &= workspace.rollback()
                    trajectory.extend(["overfit_detected", "rollback"])
                    return RepairResult(bug_id=bug_id, system=system, verified=False, attempts=attempt + 1,
                        public_passed=True, hidden_passed=False, overfit_detected=True,
                        rollback_verified=rollback_verified, changed_lines=changed_lines, trajectory=trajectory,
                        latency_seconds=time.perf_counter() - started, error="Final holdout rejected selected candidate")
                trajectory.append("accept")
                return RepairResult(bug_id=bug_id, system=system, verified=True, attempts=attempt + 1, public_passed=True, hidden_passed=True, overfit_detected=overfit, rollback_verified=rollback_verified, changed_lines=changed_lines, trajectory=trajectory, latency_seconds=time.perf_counter() - started)
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                rollback_verified &= workspace.rollback()
                if candidate_selected:
                    trajectory.append("final_evaluator_error")
                    return RepairResult(bug_id=bug_id, system=system, verified=False,
                        attempts=attempt + 1, public_passed=True, hidden_passed=False, overfit_detected=False,
                        rollback_verified=rollback_verified, changed_lines=changed_lines,
                        trajectory=trajectory, latency_seconds=time.perf_counter() - started,
                        error="Final evaluator infrastructure error; no additional patch selection")
                trajectory.extend(["reject_patch", "rollback"])
                failure = last_error

        final_public = execute(workspace.destination, public_tests)
        return RepairResult(bug_id=bug_id, system=system, verified=False, attempts=attempts, public_passed=final_public.passed, hidden_passed=False, overfit_detected=overfit, rollback_verified=rollback_verified and not workspace.changed_paths(), changed_lines=changed_lines, trajectory=trajectory, latency_seconds=time.perf_counter() - started, error=last_error or "attempt budget exhausted")
