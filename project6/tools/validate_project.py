#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [f"P06-C{index:02d}" for index in range(11)]


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--require-results", action="store_true"); args = parser.parse_args()
    required = ["README.md", "RUNBOOK.md", "data/quixbugs_manifest.json", "project6_test_driven_code_repair.ipynb", "src/project6_agent/agent.py", "tools/fetch_quixbugs.py", "tools/generate_report.py", "background/project6_background.md"]
    errors = [f"missing {path}" for path in required if not (ROOT/path).exists()]
    manifest = json.loads((ROOT/"data/quixbugs_manifest.json").read_text())
    if len(manifest["cases"]) != 12 or len(manifest["commit"]) != 40: errors.append("invalid QuixBugs manifest")
    notebook = ROOT/"project6_test_driven_code_repair.ipynb"
    if notebook.exists() and [cell.get("id") for cell in json.loads(notebook.read_text())["cells"]] != EXPECTED: errors.append("notebook cell IDs differ")
    patterns = [re.compile(r"sk-[A-Za-z0-9_-]{20,}"), re.compile(re.escape("/"+"Users/")+r"[^/\s]+/")]
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix in {".pdf", ".png", ".pyc"}: continue
        try: text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        if any(pattern.search(text) for pattern in patterns): errors.append(f"privacy-sensitive token in {path.relative_to(ROOT)}")
    if args.require_results:
        for name in ["project6_final_summary.json", "project6_representative_samples.json", "project6_trajectories.jsonl", "project6_report.pdf"]:
            if not (ROOT/"output"/name).exists(): errors.append(f"missing output/{name}")
    if errors: raise SystemExit("Project 6 validation failed:\n- " + "\n- ".join(errors))
    print("Project 6 structure and privacy checks passed.")


if __name__ == "__main__": main()
