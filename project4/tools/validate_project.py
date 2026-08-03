#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from project4_agent.config import load_config
from project4_agent.dataset import load_dataset


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = {
    "README.md",
    "RUNBOOK.md",
    "requirements-colab.txt",
    "pyproject.toml",
    "config/default.json",
    "background/project4_background.md",
    "debug_log/project4_debug_log.md",
    "project4_durable_incident_response_agent.ipynb",
    "src/project4_agent/evaluation.py",
    "src/project4_agent/planners.py",
    "src/project4_agent/policy.py",
    "src/project4_agent/simulator.py",
    "src/project4_agent/telemetry.py",
    "src/project4_agent/workflow.py",
    "tools/build_notebook.py",
    "tools/generate_incident_dataset.py",
    "tools/generate_report.py",
}
EXPECTED_CELL_IDS = [f"P04-C{index:02d}" for index in range(11)]


def validate(require_results: bool) -> None:
    errors: list[str] = []
    missing = sorted(path for path in REQUIRED_FILES if not (ROOT / path).exists())
    if missing:
        errors.append("Missing files: " + ", ".join(missing))

    config = load_config(ROOT / "config/default.json")
    if config.development_case_count + config.test_case_count != 24:
        errors.append("Configured development and test counts must total 24")

    notebook_path = ROOT / "project4_durable_incident_response_agent.ipynb"
    if notebook_path.exists():
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        ids = [cell.get("id") for cell in notebook.get("cells", [])]
        if ids != EXPECTED_CELL_IDS:
            errors.append(f"Notebook IDs/order differ: {ids}")

    dataset_path = ROOT / "data/cache/project4_incidents.json"
    if dataset_path.exists():
        cases = load_dataset(dataset_path)
        if len(cases) != 24:
            errors.append(f"Dataset has {len(cases)} rows, expected 24")

    secret_patterns = {
        "plaintext OpenAI key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
        "absolute macOS user path": re.compile(re.escape("/" + "Users/") + r"[^/\s]+/"),
        "absolute Linux user path": re.compile(re.escape("/" + "home/") + r"[^/\s]+/"),
    }
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", ".venv"} for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".pdf", ".sqlite", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in secret_patterns.items():
            if pattern.search(text):
                errors.append(f"{label} found in {path.relative_to(ROOT)}")

    if require_results:
        expected_outputs = [
            "output/project4_final_summary.json",
            "output/project4_representative_samples.json",
            "output/project4_traces.jsonl",
            "output/project4_report.pdf",
        ]
        missing_outputs = [path for path in expected_outputs if not (ROOT / path).exists()]
        if missing_outputs:
            errors.append("Missing measured outputs: " + ", ".join(missing_outputs))

    if errors:
        raise SystemExit("Project 4 validation failed:\n- " + "\n- ".join(errors))
    print("Project 4 structure and safety checks passed.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-results", action="store_true")
    args = parser.parse_args()
    validate(args.require_results)


if __name__ == "__main__":
    main()
