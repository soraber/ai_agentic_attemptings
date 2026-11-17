"""Execute authored controls into new run folders; never relabel them as model scores."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("projects", type=int, nargs="+", choices=[4, 5, 7, 8])
    args = parser.parse_args()
    for number in args.projects:
        project = ROOT / f"project{number}"
        sys.path.insert(0, str(project / "src"))
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = project / "output/runs/upgrade-v1/deterministic" / stamp
        output.mkdir(parents=True, exist_ok=False)
        runtime = output / "runtime"
        runtime.mkdir()
        if number == 4:
            from project4_agent.config import load_config
            from project4_agent.dataset import generate_incidents
            from project4_agent.evaluation import evaluate_project
            from project4_agent.planners import DeterministicPlanner
            config = load_config(project / "config/default.json").model_copy(update={"planner_mode": "deterministic"})
            summary = evaluate_project(generate_incidents(config.seed), DeterministicPlanner(), config, output, runtime)
        elif number == 5:
            from project5_agent.config import load_config
            from project5_agent.dataset import build_database, generate_benchmark
            from project5_agent.evaluation import evaluate_project5
            config = load_config(project / "config/default.json").model_copy(update={"planner_mode": "deterministic"})
            database = build_database(runtime / "fixtures.duckdb", config.seed)
            summary = evaluate_project5(generate_benchmark(database, config.seed), database, config, output)
        elif number == 7:
            from project7_agent.dataset import generate_cases
            from project7_agent.evaluation import evaluate_project7
            summary = evaluate_project7(generate_cases(), output)
        else:
            from project8_agent.evaluation import evaluate_lifecycle
            summary = evaluate_lifecycle(project / "data/lifecycle_cases.json", runtime / "memory.sqlite", output)
        summary.update(evaluation_version="upgrade-v1", evaluation_scope="authored deterministic controls; not model quality")
        (output / f"project{number}_final_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        manifest = {"generated_at_utc": stamp, "python": platform.python_version(), "platform": platform.platform(),
                    "model_calls": 0, "scope": summary["evaluation_scope"],
                    "source_sha256": {p.relative_to(project).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in sorted((project / "src").rglob("*.py"))}}
        (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"project": number, "output": output.relative_to(ROOT).as_posix(), "summary": summary}), flush=True)


if __name__ == "__main__":
    main()
