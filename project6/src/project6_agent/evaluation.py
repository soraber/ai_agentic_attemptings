from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Iterable

from .schemas import RepairResult


def summarize_results(results: Iterable[RepairResult], output_dir: str | Path) -> dict:
    rows = [result.model_dump(mode="json") for result in results]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    def system_summary(system: str) -> dict:
        selected = [row for row in rows if row["system"] == system]
        return {
            "cases": len(selected),
            "verified_repair_rate_pct": 100 * sum(row["verified"] for row in selected) / len(selected) if selected else 0,
            "hidden_pass_rate_pct": 100 * sum(row["hidden_passed"] for row in selected) / len(selected) if selected else 0,
            "overfit_rate_pct": 100 * sum(row["overfit_detected"] for row in selected) / len(selected) if selected else 0,
            "rollback_success_pct": 100 * sum(row["rollback_verified"] for row in selected) / len(selected) if selected else 0,
            "mean_changed_lines": statistics.fmean(row["changed_lines"] for row in selected) if selected else 0,
            "median_latency_seconds": statistics.median(row["latency_seconds"] for row in selected) if selected else 0,
        }

    summary = {"project": "Test-Driven Code-Repair Agent", "result_status": "measured", "one_shot": system_summary("one_shot"), "repair_loop": system_summary("repair_loop")}
    samples = {"verified": [row for row in rows if row["verified"]][:4], "overfit": [row for row in rows if row["overfit_detected"]][:4], "failed": [row for row in rows if not row["verified"]][:4]}
    (output_dir / "project6_case_results.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (output_dir / "project6_trajectories.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({"bug_id": row["bug_id"], "system": row["system"], "trajectory": row["trajectory"]}, sort_keys=True) + "\n")
    (output_dir / "project6_final_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "project6_representative_samples.json").write_text(json.dumps(samples, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
