#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "project4_durable_incident_response_agent.ipynb"


def cell(cell_id: str, cell_type: str, source: str) -> dict:
    payload = {
        "cell_type": cell_type,
        "id": cell_id,
        "metadata": {},
        "source": source.strip("\n").splitlines(keepends=True),
    }
    if cell_type == "code":
        payload.update({"execution_count": None, "outputs": []})
    return payload


CELLS = [
    cell(
        "P04-C00",
        "markdown",
        """
# Project 4: Durable Incident-Response Agent

This notebook compares a stateless action loop with a LangGraph workflow that
checkpoints state, pauses for human approval, deduplicates replayed side effects,
and compensates failed actions. All tools are local simulations. Final figures
must be generated from measured output, never placeholder values.

**Cell IDs are stable.** Record any future edit by ID in
`debug_log/project4_debug_log.md`.
""",
    ),
    cell(
        "P04-C01",
        "code",
        """
# Environment bootstrap: clone once in Colab, then install the project's bounded dependencies.
from pathlib import Path
import os, platform, subprocess, sys

candidates = [
    Path.cwd(),
    Path.cwd() / "project4",
    Path("/content/ai_agentic_attemptings/project4"),
]
PROJECT_ROOT = next((path.resolve() for path in candidates if (path / "config/default.json").exists()), None)
if PROJECT_ROOT is None:
    repo_root = Path("/content/ai_agentic_attemptings")
    if not repo_root.exists():
        subprocess.run(
            ["git", "clone", "https://github.com/soraber/ai_agentic_attemptings.git", str(repo_root)],
            check=True,
        )
    PROJECT_ROOT = repo_root / "project4"

os.chdir(PROJECT_ROOT)
subprocess.run(
    [sys.executable, "-m", "pip", "install", "--upgrade-strategy", "only-if-needed", "-r", "requirements-colab.txt"],
    check=True,
)
subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".", "--no-deps"], check=True)
dependency_check = subprocess.run(
    [sys.executable, "-m", "pip", "check"], text=True, capture_output=True
)
if dependency_check.returncode:
    print("pip check reported preinstalled-runtime conflicts; inspect before changing packages:")
    print(dependency_check.stdout or dependency_check.stderr)
from project4_agent.config import load_config as _import_smoke_config
from project4_agent.workflow import DurableIncidentWorkflow as _import_smoke_workflow
print({"python": sys.version.split()[0], "platform": platform.platform(), "project_root": str(PROJECT_ROOT)})
""",
    ),
    cell(
        "P04-C02",
        "code",
        """
# Experiment flags and secret loading. The secret value is never printed or written to disk.
import getpass, os, sys
from project4_agent.config import load_config

RUN_API_EVAL = False
RUN_FULL_EVAL = False
config = load_config(PROJECT_ROOT / "config/default.json")

if RUN_API_EVAL and not os.getenv("OPENAI_API_KEY"):
    if "google.colab" in sys.modules:
        from google.colab import userdata
        key = userdata.get("OPENAI_API_KEY")
    else:
        key = getpass.getpass("OPENAI_API_KEY (input hidden): ")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required only when RUN_API_EVAL=True")
    os.environ["OPENAI_API_KEY"] = key

config = config.model_copy(update={"planner_mode": "openai" if RUN_API_EVAL else "deterministic"})
print(config.model_dump(exclude={"input_usd_per_million", "output_usd_per_million"}))
""",
    ),
    cell(
        "P04-C03",
        "code",
        """
# Generate once, then reuse the checksum-verified local cache on later runs.
from project4_agent.dataset import load_dataset, write_dataset

dataset_path = PROJECT_ROOT / "data/cache/project4_incidents.json"
checksum_path = dataset_path.with_suffix(".sha256")
if dataset_path.exists() and checksum_path.exists():
    print(f"Reusing cached benchmark: {dataset_path}")
else:
    _, _, checksum = write_dataset(dataset_path, config.seed)
    print(f"Generated benchmark once with SHA-256 {checksum}")
cases = load_dataset(dataset_path, verify_checksum=True)
print({"incidents": len(cases), "checksum": checksum_path.read_text().split()[0]})
""",
    ),
    cell(
        "P04-C04",
        "code",
        """
# Keep development and held-out test incidents separate.
development_cases = [case for case in cases if case.split == "development"]
test_cases = [case for case in cases if case.split == "test"]
assert len(development_cases) == config.development_case_count
assert len(test_cases) == config.test_case_count
print({"development": len(development_cases), "test": len(test_cases)})
print("Example public fields:", sorted(development_cases[0].public_view()))
""",
    ),
    cell(
        "P04-C05",
        "code",
        """
# Baseline smoke test: stateless, coarse policy, no approval interrupt or idempotency ledger.
from project4_agent.planners import DeterministicPlanner
from project4_agent.simulator import ActionExecutor
from project4_agent.telemetry import TraceRecorder
from project4_agent.workflow import run_stateless_baseline

runtime_dir = PROJECT_ROOT / "output/runtime"
runtime_dir.mkdir(parents=True, exist_ok=True)
baseline_executor = ActionExecutor(runtime_dir / "smoke_baseline.sqlite")
baseline_executor.reset()
smoke_trace = TraceRecorder(runtime_dir / "smoke_traces.jsonl")
baseline_smoke = run_stateless_baseline(
    development_cases[0], DeterministicPlanner(), baseline_executor, smoke_trace
)
assert baseline_smoke["terminal_status"] in {"resolved", "action_failed"}
print({
    "terminal_status": baseline_smoke["terminal_status"],
    "trajectory": baseline_smoke["trajectory"],
    "effects": baseline_executor.count_effects(),
})
""",
    ),
    cell(
        "P04-C06",
        "code",
        """
# Durable smoke test: pause at the approval interrupt, then resume the same thread.
from project4_agent.planners import DeterministicPlanner
from project4_agent.policy import simulated_operator_decision
from project4_agent.simulator import ActionExecutor
from project4_agent.telemetry import TraceRecorder
from project4_agent.workflow import DurableIncidentWorkflow

case = development_cases[1]
planner = DeterministicPlanner()
executor = ActionExecutor(runtime_dir / "smoke_durable.sqlite")
executor.reset()
checkpoint = runtime_dir / "smoke_checkpoint.sqlite"
checkpoint.unlink(missing_ok=True)
workflow = DurableIncidentWorkflow(planner, executor, checkpoint, smoke_trace)
thread_id = f"smoke-{case.evidence.incident_id}"
paused = workflow.start(case, thread_id)
assert paused.get("__interrupt__"), "workflow did not pause for approval"
plan = planner.plan(case.public_view(), planner.diagnose(case.public_view()))
decision = simulated_operator_decision(plan, case)
final_state = workflow.resume_approval(thread_id, decision)
workflow.close()
print({"paused": True, "approved": decision.approved, "terminal_status": final_state["terminal_status"], "trajectory": final_state["trajectory"]})
""",
    ),
    cell(
        "P04-C07",
        "code",
        """
# Deterministic reliability checks: data isolation, policy attacks, replay, crash recovery, and compensation.
import subprocess, sys

completed = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "tests"],
    text=True,
    capture_output=True,
)
print(completed.stdout)
if completed.returncode:
    print(completed.stderr)
    raise RuntimeError("Project 4 deterministic tests failed")
""",
    ),
    cell(
        "P04-C08",
        "code",
        """
# Paired evaluation. API mode makes 64 structured calls by default (16 cases x 2 calls x 2 repetitions).
from project4_agent.evaluation import evaluate_project
from project4_agent.planners import DeterministicPlanner, OpenAIPlanner

if not RUN_FULL_EVAL:
    print("Full evaluation is disabled. Set RUN_FULL_EVAL=True in P04-C02 after P04-C07 passes.")
else:
    source_planner = OpenAIPlanner(config) if RUN_API_EVAL else DeterministicPlanner()
    summary = evaluate_project(
        cases,
        source_planner,
        config,
        PROJECT_ROOT / "output",
        PROJECT_ROOT / "output/runtime/evaluation",
    )
    print(summary)
""",
    ),
    cell(
        "P04-C09",
        "code",
        """
# Error analysis uses persisted evidence so notebook display cannot diverge from the report.
import json

samples_path = PROJECT_ROOT / "output/project4_representative_samples.json"
if not samples_path.exists():
    print("No measured samples yet; run P04-C08 with RUN_FULL_EVAL=True.")
else:
    samples = json.loads(samples_path.read_text())
    print("Crash examples:", len(samples["crash_examples"]))
    print("Compensation examples:", len(samples["compensation_examples"]))
    print("Runtime errors:", len(samples["runtime_errors"]))
    for row in samples["runtime_errors"][:3]:
        print(row["incident_id"], row["system"], row["error"])
""",
    ),
    cell(
        "P04-C10",
        "code",
        """
# Build measured charts/PDF and validate the final artifact contract.
import subprocess, sys

summary_path = PROJECT_ROOT / "output/project4_final_summary.json"
if not summary_path.exists():
    print("No measured summary yet; report generation is intentionally skipped.")
else:
    subprocess.run([sys.executable, "tools/generate_report.py"], check=True)
    subprocess.run([sys.executable, "tools/validate_project.py", "--require-results"], check=True)
    print("Project 4 artifacts are complete:", PROJECT_ROOT / "output")
""",
    ),
]


def main() -> None:
    notebook = {
        "cells": CELLS,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"name": OUTPUT.name, "provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUTPUT.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(CELLS)} stable cells")


if __name__ == "__main__":
    main()
