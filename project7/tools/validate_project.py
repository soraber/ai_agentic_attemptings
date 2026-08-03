#!/usr/bin/env python3
import argparse,json,re
from pathlib import Path
from project7_agent.dataset import load_cases

ROOT=Path(__file__).resolve().parents[1]; EXPECTED=[f"P07-C{i:02d}" for i in range(11)]


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--require-results",action="store_true"); args=parser.parse_args(); required=["README.md","RUNBOOK.md","data/cache/project7_cases.json","data/cache/project7_cases.sha256","project7_secure_agent_gateway.ipynb","src/project7_agent/gateway.py","tools/generate_report.py","background/project7_background.md"]; errors=[f"missing {p}" for p in required if not (ROOT/p).exists()]
    path=ROOT/"data/cache/project7_cases.json"
    if path.exists() and len(load_cases(path))!=40: errors.append("benchmark must contain 40 cases")
    nb=ROOT/"project7_secure_agent_gateway.ipynb"
    if nb.exists() and [c.get("id") for c in json.loads(nb.read_text())["cells"]]!=EXPECTED: errors.append("notebook cell IDs differ")
    patterns=[re.compile(r"sk-[A-Za-z0-9_-]{20,}"),re.compile(re.escape("/"+"Users/")+r"[^/\s]+/")]
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix in {".pdf",".png",".pyc"}: continue
        try: text=p.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        if any(pattern.search(text) for pattern in patterns): errors.append(f"privacy-sensitive token in {p.relative_to(ROOT)}")
    if args.require_results:
        for name in ["project7_final_summary.json","project7_representative_samples.json","project7_traces.jsonl","project7_report.pdf"]:
            if not (ROOT/"output"/name).exists(): errors.append(f"missing output/{name}")
    if errors: raise SystemExit("Project 7 validation failed:\n- "+"\n- ".join(errors))
    print("Project 7 structure and privacy checks passed.")


if __name__=="__main__": main()
