"""Development-only comparison of model-written diffs and exact source edits."""
import hashlib
import json
import random
import time
from pathlib import Path

from .agent import RepairAgent
from .planners import OpenAIPatchPlanner, PatchCallBudget
from .quixbugs import prepare_case
from .runner import sandbox_preflight
from .structured_edits import OpenAIStructuredEditPlanner


def compare_development_edits(api, config, project_root, output):
    root, output = Path(project_root), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    runtime = output / "runtime"
    runtime.mkdir()
    sandbox = sandbox_preflight(config.sandbox_image)
    source_start = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((root / "src").rglob("*.py"))}
    shared = PatchCallBudget(config.model_copy(update={"max_model_calls": 48, "max_estimated_cost_usd": 2.0}))
    manifest = json.loads((root / "data/quixbugs_manifest.json").read_text())
    cases = [case for case in manifest["cases"] if case["split"] == "development"]
    if len(cases) != 4:
        raise ValueError("Review changed development set before running")
    planners, rows = [], []
    rng = random.Random(config.seed)
    started = time.perf_counter()
    for case in cases:
        prepared = prepare_case(root / "data/cache/QuixBugs", case, runtime / ("source-" + case["bug_id"]))
        formats = ["unified_diff", "structured_edits"]
        rng.shuffle(formats)
        for edit_format in formats:
            used_calls = sum(p.calls for p in planners)
            used_cost = sum(p.estimated_cost_usd for p in planners)
            if used_calls >= 48 or used_cost >= 2.0:
                raise RuntimeError("Development comparison budget exhausted")
            bounded = config.model_copy(update={"max_model_calls": 48 - used_calls,
                "max_estimated_cost_usd": 2.0 - used_cost, "max_retries": 0})
            factory = OpenAIPatchPlanner if edit_format == "unified_diff" else OpenAIStructuredEditPlanner
            planner = factory(bounded, prepared["root"] / prepared["source"], case["bug_id"],
                              allowed_path=prepared["source"], client=api, budget=shared)
            planners.append(planner)
            result = RepairAgent(bounded).run(case["bug_id"], "repair_loop", prepared["root"],
                runtime / f"work-{case['bug_id']}-{edit_format}", [prepared["source"]],
                prepared["public_tests"], prepared["hidden_tests"], planner)
            row = {**result.model_dump(), "edit_format": edit_format, "split": "development",
                   "usage": planner.usage_summary()}
            rows.append(row)
            with (output / "development_cases.jsonl").open("a") as handle:
                handle.write(json.dumps(row) + "\n")
            print(json.dumps({key: row[key] for key in ["bug_id", "edit_format", "verified", "attempts"]}), flush=True)
    summary = {"evaluation_version": "edit-interface-dev-v1", "scope": "development only; not a final holdout score",
        "model": config.model, "config": config.model_dump(), "sandbox": sandbox,
        "dataset_commit": manifest["commit"], "runtime_seconds": time.perf_counter() - started,
        "model_calls": sum(p.calls for p in planners), "estimated_cost_usd": sum(p.estimated_cost_usd for p in planners),
        "reserved_unreported_cost_usd": shared.reserved,
        "source_sha256_at_start": source_start,
        "source_sha256": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted((root / "src").rglob("*.py"))}}
    for edit_format in ["unified_diff", "structured_edits"]:
        selected = [row for row in rows if row["edit_format"] == edit_format]
        summary[edit_format] = {"cases": len(selected), "verified": sum(row["verified"] for row in selected),
            "model_calls": sum(row["usage"]["model_calls"] for row in selected),
            "rollback_success_pct": 100 * sum(row["rollback_verified"] for row in selected) / len(selected),
            "terminal_errors": [row["error"] for row in selected if row["error"]]}
    (output / "development_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
