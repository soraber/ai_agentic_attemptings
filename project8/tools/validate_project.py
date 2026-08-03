#!/usr/bin/env python3
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; EXPECTED=[f"P08-C{i:02d}" for i in range(11)]


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--require-results",action="store_true"); args=parser.parse_args(); required=["README.md","RUNBOOK.md","data/locomo_selection.json","data/lifecycle_cases.json","project8_long_term_memory.ipynb","src/project8_agent/memory.py","tools/fetch_locomo.py","tools/generate_report.py","background/project8_background.md"]; errors=[f"missing {p}" for p in required if not (ROOT/p).exists()]
    selection=json.loads((ROOT/"data/locomo_selection.json").read_text());
    if len(selection["commit"])!=40 or selection["qa_per_sample"]*len(selection["sample_indices"])!=80: errors.append("invalid LoCoMo selection")
    nb=ROOT/"project8_long_term_memory.ipynb"
    if nb.exists() and [c.get("id") for c in json.loads(nb.read_text())["cells"]]!=EXPECTED: errors.append("notebook cell IDs differ")
    patterns=[re.compile(r"sk-[A-Za-z0-9_-]{20,}"),re.compile(re.escape("/"+"Users/")+r"[^/\s]+/")]
    for p in ROOT.rglob("*"):
        if not p.is_file() or ".git" in p.parts or p.suffix in {".pdf",".png",".pyc"}: continue
        try: text=p.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        if any(pattern.search(text) for pattern in patterns): errors.append(f"privacy-sensitive token in {p.relative_to(ROOT)}")
    if args.require_results:
        for name in ["project8_final_summary.json","project8_representative_samples.json","project8_traces.jsonl","project8_report.pdf"]:
            if not (ROOT/"output"/name).exists(): errors.append(f"missing output/{name}")
    if errors: raise SystemExit("Project 8 validation failed:\n- "+"\n- ".join(errors))
    print("Project 8 structure and privacy checks passed.")


if __name__=="__main__": main()
