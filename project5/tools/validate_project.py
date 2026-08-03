#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from project5_agent.dataset import load_benchmark


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = [f"P05-C{index:02d}" for index in range(11)]
REQUIRED = [
    "README.md", "RUNBOOK.md", "config/default.json", "data/cache/project5_questions.json",
    "data/cache/project5_questions.sha256", "project5_governed_text_to_sql.ipynb",
    "src/project5_agent/analyst.py", "src/project5_agent/governance.py", "src/project5_agent/local_models.py",
    "tools/build_notebook.py", "tools/generate_report.py", "background/project5_background.md",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-results", action="store_true")
    args = parser.parse_args()
    errors = [f"missing {path}" for path in REQUIRED if not (ROOT / path).exists()]
    notebook = ROOT / "project5_governed_text_to_sql.ipynb"
    if notebook.exists():
        ids = [cell.get("id") for cell in json.loads(notebook.read_text())["cells"]]
        if ids != EXPECTED_IDS:
            errors.append(f"notebook cell IDs differ: {ids}")
    benchmark = ROOT / "data/cache/project5_questions.json"
    if benchmark.exists() and len(load_benchmark(benchmark)) != 50:
        errors.append("benchmark does not contain 50 questions")
    patterns = [re.compile(r"sk-[A-Za-z0-9_-]{20,}"), re.compile(re.escape("/" + "Users/") + r"[^/\s]+/")]
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix in {".duckdb", ".pdf", ".png", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in patterns):
            errors.append(f"privacy-sensitive token in {path.relative_to(ROOT)}")
    if args.require_results:
        for name in ["project5_final_summary.json", "project5_representative_samples.json", "project5_traces.jsonl", "project5_report.pdf"]:
            if not (ROOT / "output" / name).exists():
                errors.append(f"missing output/{name}")
    if errors:
        raise SystemExit("Project 5 validation failed:\n- " + "\n- ".join(errors))
    print("Project 5 structure and privacy checks passed.")


if __name__ == "__main__":
    main()
