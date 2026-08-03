#!/usr/bin/env python3
import argparse,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run(command,cwd=None): return subprocess.run(command,cwd=cwd,text=True,capture_output=True,check=True).stdout.strip()


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--selection",type=Path,default=ROOT/"data/locomo_selection.json"); parser.add_argument("--repo",type=Path,default=ROOT/"data/cache/locomo"); parser.add_argument("--output",type=Path,default=ROOT/"data/cache/locomo_subset.json"); args=parser.parse_args(); selection=json.loads(args.selection.read_text())
    if not (args.repo/".git").exists(): args.repo.parent.mkdir(parents=True,exist_ok=True); run(["git","clone",selection["repository"],str(args.repo)])
    run(["git","checkout","--detach",selection["commit"]],cwd=args.repo)
    if run(["git","rev-parse","HEAD"],cwd=args.repo)!=selection["commit"]: raise SystemExit("LoCoMo commit mismatch")
    source=json.loads((args.repo/selection["source_path"]).read_text()); subset=[]
    for index in selection["sample_indices"]:
        sample=source[index]; subset.append({"sample_id":sample["sample_id"],"conversation":sample["conversation"],"session_summary":sample.get("session_summary",{}),"qa":sample["qa"][:selection["qa_per_sample"]]})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(subset,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(f"Prepared {len(subset)} conversations and {sum(len(s['qa']) for s in subset)} QA items")


if __name__=="__main__": main()
