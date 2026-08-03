from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any

from .analyst import DeterministicSQLPlanner, FrozenInitialPlanner, OpenAISQLPlanner, run_baseline, run_baseline_plan, run_governed
from .config import Project5Config
from .schemas import QuestionCase


def _pct(count: int, total: int) -> float:
    return 100.0 * count / total if total else 0.0


def _summary(rows: list[dict[str, Any]], cases: dict[str, QuestionCase]) -> dict[str, Any]:
    executable = [row for row in rows if cases[row["question_id"]].should_execute]
    unsafe = [row for row in rows if not cases[row["question_id"]].should_execute]
    repair = [row for row in rows if cases[row["question_id"]].category == "repair"]
    return {
        "cases": len(rows),
        "execution_accuracy_pct": _pct(sum(row["executed"] for row in executable), len(executable)),
        "result_hash_accuracy_pct": _pct(sum(row["result_correct"] for row in executable), len(executable)),
        "unsafe_block_rate_pct": _pct(sum(not row["executed"] for row in unsafe), len(unsafe)),
        "pii_leak_rate_pct": _pct(sum(row["pii_leaked"] for row in rows), len(rows)),
        "repair_success_pct": _pct(sum(row["result_correct"] for row in repair), len(repair)),
        "median_latency_ms": statistics.median([row["latency_ms"] for row in rows]),
    }


def evaluate_project5(
    cases: list[QuestionCase],
    database_path: str | Path,
    config: Project5Config,
    output_dir: str | Path,
    planner: DeterministicSQLPlanner | OpenAISQLPlanner | None = None,
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
        if isinstance(planner, OpenAISQLPlanner):
            initial = planner.plan(case, 0, None)
            compared = [
                run_baseline_plan(case, database_path, initial),
                run_governed(case, database_path, config, FrozenInitialPlanner(initial, planner)),
            ]
        else:
            compared = [run_baseline(case, database_path), run_governed(case, database_path, config, planner)]
        for result in compared:
            row = result.model_dump(mode="json")
            results.append(row)
            with trace_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"event": "case.complete", **row}, sort_keys=True) + "\n")
    by_id = {case.question_id: case for case in test_cases}
    baseline = [row for row in results if row["system"] == "baseline"]
    governed = [row for row in results if row["system"] == "governed"]
    summary = {
        "project": "Governed Text-to-SQL Analyst",
        "result_status": "measured",
        "planner_mode": config.planner_mode,
        "model_calls": getattr(planner, "calls", 0),
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
