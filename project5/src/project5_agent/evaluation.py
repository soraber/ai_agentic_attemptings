from __future__ import annotations

import json
import hashlib
import statistics
import time
from pathlib import Path
from typing import Any

from .analyst import DeterministicSQLPlanner, FrozenInitialPlanner, LocalSQLPlanner, OpenAISQLPlanner, run_baseline, run_baseline_plan, run_governed
from .config import Project5Config
from .schemas import AnalystResult, QuestionCase
from .semantic_scoring import grade_saved_queries


def _pct(count: int, total: int) -> float:
    return 100.0 * count / total if total else 0.0


def _summary(rows: list[dict[str, Any]], cases: dict[str, QuestionCase]) -> dict[str, Any]:
    executable = [row for row in rows if cases[row["question_id"]].should_execute]
    unsafe = [row for row in rows if not cases[row["question_id"]].should_execute]
    repair = [row for row in rows if cases[row["question_id"]].category == "repair"]
    total_times = sorted(row.get("end_to_end_latency_ms", row["latency_ms"]) for row in rows)
    value_scored = [row for row in executable if row.get('value_result_correct') is not None]
    return {
        "cases": len(rows),
        "execution_accuracy_pct": _pct(sum(row["executed"] for row in executable), len(executable)),
        "result_hash_accuracy_pct": _pct(sum(row["result_correct"] for row in executable), len(executable)),
        "value_result_accuracy_pct": _pct(sum(row['value_result_correct'] for row in value_scored), len(value_scored)) if value_scored else None,
        "value_result_cases": len(value_scored),
        "value_evaluation_errors": sum(row.get('value_evaluation_error') is not None for row in rows),
        "unsafe_block_rate_pct": _pct(sum(not row["executed"] for row in unsafe), len(unsafe)),
        "unsafe_policy_or_abstention_pct": _pct(sum(row["status"] in ("blocked_policy", "abstained") for row in unsafe), len(unsafe)),
        "execution_or_repair_error_pct": _pct(sum(row["status"] in ("execution_error", "repair_exhausted") for row in rows), len(rows)),
        "planning_error_pct": _pct(sum(row["status"] == "planning_error" for row in rows), len(rows)),
        "pii_leak_rate_pct": _pct(sum(row["pii_leaked"] for row in rows), len(rows)),
        "repair_success_pct": _pct(sum(row["result_correct"] for row in repair), len(repair)),
        "median_latency_ms": statistics.median([row["latency_ms"] for row in rows]),
        "end_to_end_p50_ms": statistics.median(total_times),
        "end_to_end_p95_ms": total_times[min(len(total_times)-1, int(.95*len(total_times)))],
    }


def evaluate_project5(
    cases: list[QuestionCase],
    database_path: str | Path,
    config: Project5Config,
    output_dir: str | Path,
    planner: DeterministicSQLPlanner | OpenAISQLPlanner | LocalSQLPlanner | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    test_cases = [case for case in cases if case.split == "test"]
    planner = planner or DeterministicSQLPlanner()
    results = []
    trace_path = output_dir / "project5_traces.jsonl"
    trace_path.unlink(missing_ok=True)
    started = time.perf_counter()
    for case in test_cases:
        shared_planning_ms = 0.0
        if isinstance(planner, (OpenAISQLPlanner, LocalSQLPlanner)):
            planning_started = time.perf_counter()
            try:
                initial = planner.plan(case, 0, None)
            except Exception as exc:
                shared_planning_ms = 1000 * (time.perf_counter() - planning_started)
                compared = [AnalystResult(question_id=case.question_id, system=system,
                    status="planning_error", sql=None, executed=False, policy_allowed=None,
                    attempts=1, latency_ms=0, error=type(exc).__name__)
                    for system in ['baseline', 'governed']]
            else:
                shared_planning_ms = 1000 * (time.perf_counter() - planning_started)
                compared = [
                    run_baseline_plan(case, database_path, initial),
                    run_governed(case, database_path, config, FrozenInitialPlanner(initial, planner)),
                ]
        else:
            compared = [run_baseline(case, database_path), run_governed(case, database_path, config, planner)]
        for result in compared:
            row = result.model_dump(mode="json")
            row["shared_initial_planning_ms"] = shared_planning_ms
            row["end_to_end_latency_ms"] = shared_planning_ms + row["latency_ms"]
            results.append(row)
            with trace_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"event": "case.complete", **row}, sort_keys=True) + "\n")
    # Final evaluator only: gold SQL/results never feed planner repair decisions.
    results = grade_saved_queries(results, test_cases, database_path)
    by_id = {case.question_id: case for case in test_cases}
    baseline = [row for row in results if row["system"] == "baseline"]
    governed = [row for row in results if row["system"] == "governed"]
    planner_usage = (
        planner.usage_summary()
        if isinstance(planner, (OpenAISQLPlanner, LocalSQLPlanner))
        else {"model_calls": 0, "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}
    )
    summary = {
        "project": "Governed Text-to-SQL Analyst",
        "evaluation_version": "upgrade-v1",
        "execution_boundary": "tenant-filtered PII-free snapshot for both systems",
        "value_metric_definition": "Ignore output aliases; preserve column positions, duplicate rows, NULLs and gold ORDER BY; numeric tolerance abs=1e-6/rel=1e-9. Fixed-data value equivalence is not proof of general SQL semantics. Gold results are final-evaluator-only.",
        "comparison_note": "Not directly comparable to historical unrestricted-baseline metrics",
        "latency_definition": "end_to_end includes the same frozen initial planning latency in both arms plus each arm's execution/repair; median_latency_ms is the legacy post-plan metric",
        "unsafe_block_definition": "Legacy non-execution rate includes execution errors; policy/abstention and execution/repair errors are reported separately",
        "test_cases_sha256": hashlib.sha256(json.dumps([case.model_dump(mode='json') for case in test_cases], sort_keys=True).encode()).hexdigest(),
        "config": config.model_dump(mode="json"),
        "result_status": "measured",
        "planner_mode": config.planner_mode,
        "model_calls": planner_usage["model_calls"],
        "planner_usage": planner_usage,
        "test_questions": len(test_cases),
        "baseline": _summary(baseline, by_id),
        "governed": _summary(governed, by_id),
        "runtime_seconds": time.perf_counter() - started,
    }
    samples = {
        "repaired": [row for row in governed if row["repaired"]][:5],
        "blocked": [row for row in governed if row["status"] == "blocked_policy"][:5],
        "errors": [row for row in results if row["error"]][:5],
    }
    (output_dir / "project5_case_results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "project5_final_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "project5_representative_samples.json").write_text(json.dumps(samples, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
