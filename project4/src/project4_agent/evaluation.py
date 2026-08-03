from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any

from .config import ExperimentConfig
from .planners import Planner, freeze_case_decision
from .policy import adversarial_plans, coarse_baseline_policy, evaluate_policy, simulated_operator_decision
from .schemas import ApprovalDecision, CaseResult, IncidentCase, PolicyDecision
from .simulator import ActionExecutor, InjectedCrash
from .telemetry import TraceRecorder
from .workflow import DurableIncidentWorkflow, run_stateless_baseline


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _percent(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _duplicate_primary_effects(
    executor: ActionExecutor, incident_id: str, action: str
) -> int:
    count = sum(
        1
        for effect in executor.list_effects(incident_id)
        if effect["action"] == action
    )
    return max(0, count - 1)


def _case_result(
    *,
    case: IncidentCase,
    system: str,
    diagnosis: Any,
    plan: Any,
    policy: PolicyDecision,
    approved: bool | None,
    terminal_status: str,
    crash_injected: bool,
    crash_recovered: bool,
    duplicate_effects: int,
    compensation_used: bool,
    trajectory: list[str],
    workflow_latency_ms: float,
    error: str | None,
    repetition: int,
) -> CaseResult:
    return CaseResult.model_validate(
        {
            "incident_id": case.evidence.incident_id,
            "system": system,
            "predicted_root_cause": diagnosis.predicted_root_cause.value,
            "planned_action": plan.action,
            "policy_allowed": policy.allowed,
            "approved": approved,
            "terminal_status": terminal_status,
            "crash_injected": crash_injected,
            "crash_recovered": crash_recovered,
            "duplicate_effects": duplicate_effects,
            "compensation_used": compensation_used,
            "trajectory": trajectory,
            "workflow_latency_ms": workflow_latency_ms,
            "error": error,
            "repetition": repetition,
            "root_cause_correct": diagnosis.predicted_root_cause == case.gold_root_cause,
            "remediation_correct": plan.action == case.allowed_remediation.value,
            "requires_escalation": case.requires_escalation,
        }
    )


def _summarize_system(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nonexecuting_statuses = {"rejected_by_operator", "blocked_policy"}
    crash_rows = [
        row
        for row in rows
        if row["crash_injected"] and row["terminal_status"] not in nonexecuting_statuses
    ]
    failed_action_rows = [row for row in rows if row["terminal_status"] in {"action_failed", "compensated"}]
    latencies = [float(row["workflow_latency_ms"]) for row in rows]
    return {
        "cases": len(rows),
        "root_cause_accuracy_pct": _percent(
            sum(bool(row["root_cause_correct"]) for row in rows), len(rows)
        ),
        "remediation_accuracy_pct": _percent(
            sum(bool(row["remediation_correct"]) for row in rows), len(rows)
        ),
        "controlled_completion_pct": _percent(
            sum(
                row["terminal_status"]
                in {"resolved", "compensated", "rejected_by_operator", "blocked_policy"}
                for row in rows
            ),
            len(rows),
        ),
        "crash_recovery_pct": _percent(
            sum(bool(row["crash_recovered"]) for row in crash_rows), len(crash_rows)
        ),
        "executed_crash_trials": len(crash_rows),
        "cases_with_duplicate_effects_pct": _percent(
            sum(row["duplicate_effects"] > 0 for row in rows), len(rows)
        ),
        "failed_actions_compensated_pct": _percent(
            sum(bool(row["compensation_used"]) for row in failed_action_rows),
            len(failed_action_rows),
        ),
        "mean_workflow_latency_ms": _mean(latencies),
        "p50_workflow_latency_ms": _percentile(latencies, 0.50),
        "p95_workflow_latency_ms": _percentile(latencies, 0.95),
        "mean_trajectory_steps": _mean([len(row["trajectory"]) for row in rows]),
    }


def _policy_challenge(cases: list[IncidentCase]) -> dict[str, Any]:
    baseline_allowed = 0
    durable_allowed = 0
    total = 0
    for case in cases:
        for plan in adversarial_plans(case):
            total += 1
            baseline_allowed += int(coarse_baseline_policy(plan).allowed)
            durable_allowed += int(evaluate_policy(plan, case.public_view()).allowed)
    return {
        "adversarial_plans": total,
        "baseline_unsafe_allow_rate_pct": _percent(baseline_allowed, total),
        "durable_unsafe_allow_rate_pct": _percent(durable_allowed, total),
        "baseline_block_rate_pct": _percent(total - baseline_allowed, total),
        "durable_block_rate_pct": _percent(total - durable_allowed, total),
    }


def evaluate_project(
    cases: list[IncidentCase],
    planner: Planner,
    config: ExperimentConfig,
    output_dir: str | Path,
    runtime_dir: str | Path,
) -> dict[str, Any]:
    """Run a paired comparison and persist only measured results."""
    output_dir = Path(output_dir)
    runtime_dir = Path(runtime_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    trace_path = output_dir / "project4_traces.jsonl"
    trace_path.unlink(missing_ok=True)
    trace = TraceRecorder(trace_path)

    test_cases = [case for case in cases if case.split == "test"]
    if len(test_cases) != config.test_case_count:
        raise ValueError(
            f"Expected {config.test_case_count} test cases, found {len(test_cases)}"
        )
    crash_count = round(len(test_cases) * config.crash_case_fraction)
    result_rows: list[CaseResult] = []
    started = time.perf_counter()

    for repetition in range(config.evaluation_repetitions):
        for position, case in enumerate(test_cases):
            crash_injected = position < crash_count
            frozen = freeze_case_decision(planner, case)

            baseline_executor = ActionExecutor(runtime_dir / "baseline.sqlite")
            baseline_executor.reset()
            baseline = run_stateless_baseline(
                case,
                frozen,
                baseline_executor,
                trace,
                inject_crash=crash_injected,
            )
            result_rows.append(
                _case_result(
                    case=case,
                    system="baseline",
                    diagnosis=baseline["diagnosis"],
                    plan=baseline["plan"],
                    policy=baseline["policy"],
                    approved=None,
                    terminal_status=baseline["terminal_status"],
                    crash_injected=crash_injected,
                    crash_recovered=baseline["crash_recovered"],
                    duplicate_effects=_duplicate_primary_effects(
                        baseline_executor,
                        case.evidence.incident_id,
                        baseline["plan"].action,
                    ),
                    compensation_used=False,
                    trajectory=baseline["trajectory"],
                    workflow_latency_ms=baseline["workflow_latency_ms"],
                    error=baseline["error"],
                    repetition=repetition,
                )
            )

            durable_executor = ActionExecutor(runtime_dir / "durable.sqlite")
            durable_executor.reset()
            checkpoint = runtime_dir / f"checkpoint-r{repetition}-{case.evidence.incident_id}.sqlite"
            checkpoint.unlink(missing_ok=True)
            workflow = DurableIncidentWorkflow(
                frozen, durable_executor, checkpoint, trace
            )
            thread_id = f"r{repetition}-{case.evidence.incident_id}"
            durable_started = time.perf_counter()
            crash_recovered = False
            error: str | None = None
            paused: dict[str, Any] = {}
            decision: ApprovalDecision | None = None
            try:
                paused = workflow.start(
                    case, thread_id, inject_crash=crash_injected
                )
                plan = frozen.action_plan
                if paused.get("__interrupt__"):
                    decision = simulated_operator_decision(plan, case)
                    try:
                        final_state = workflow.resume_approval(thread_id, decision)
                    except InjectedCrash:
                        crash_recovered = True
                        final_state = workflow.recover_after_crash(thread_id)
                else:
                    final_state = paused
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                final_state = paused
            finally:
                workflow.close()

            diagnosis = frozen.diagnosis
            plan = frozen.action_plan
            policy = PolicyDecision.model_validate(
                final_state.get("policy", evaluate_policy(plan, case.public_view()))
            )
            terminal_status = final_state.get("terminal_status", "runtime_error")
            trajectory = final_state.get("trajectory", [])
            result_rows.append(
                _case_result(
                    case=case,
                    system="durable",
                    diagnosis=diagnosis,
                    plan=plan,
                    policy=policy,
                    approved=decision.approved if decision is not None else None,
                    terminal_status=terminal_status,
                    crash_injected=crash_injected,
                    crash_recovered=crash_recovered,
                    duplicate_effects=_duplicate_primary_effects(
                        durable_executor, case.evidence.incident_id, plan.action
                    ),
                    compensation_used="compensate" in trajectory,
                    trajectory=trajectory,
                    workflow_latency_ms=(time.perf_counter() - durable_started) * 1000,
                    error=error,
                    repetition=repetition,
                )
            )

    rows = [row.model_dump(mode="json") for row in result_rows]
    baseline_rows = [row for row in rows if row["system"] == "baseline"]
    durable_rows = [row for row in rows if row["system"] == "durable"]
    summary = {
        "project": "Durable Incident-Response Agent",
        "generated_at_epoch": time.time(),
        "planner_mode": config.planner_mode,
        "model": config.model if config.planner_mode == "openai" else None,
        "seed": config.seed,
        "test_incidents": len(test_cases),
        "evaluation_repetitions": config.evaluation_repetitions,
        "paired_observations_per_system": len(baseline_rows),
        "baseline": _summarize_system(baseline_rows),
        "durable": _summarize_system(durable_rows),
        "policy_challenge": _policy_challenge(test_cases),
        "planner_usage": planner.usage.model_dump(mode="json"),
        "total_runtime_seconds": time.perf_counter() - started,
        "result_status": "measured",
    }
    samples = {
        "crash_examples": [row for row in rows if row["crash_injected"]][:4],
        "compensation_examples": [row for row in rows if row["compensation_used"]][:4],
        "runtime_errors": [row for row in rows if row["error"]][:8],
    }
    (output_dir / "project4_case_results.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "project4_final_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "project4_representative_samples.json").write_text(
        json.dumps(samples, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary
