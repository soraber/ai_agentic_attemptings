#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OUTPUT=ROOT/"project6_test_driven_code_repair.ipynb"


def cell(cell_id,kind,source):
    item={"cell_type":kind,"id":cell_id,"metadata":{},"source":source.strip("\n").splitlines(keepends=True)}
    if kind=="code": item.update({"execution_count":None,"outputs":[]})
    return item


CELLS=[
cell("P06-C00","markdown","""# Project 6: Test-Driven Code-Repair Agent

Compare a one-shot patch with a three-attempt repair loop using AST mapping,
failure localization, constrained unified diffs, public and hidden tests, and
exact rollback. Gold corrected programs never enter planner context."""),
cell("P06-C01","code","""from pathlib import Path
import os,subprocess,sys
candidates=[Path.cwd(),Path.cwd()/"project6",Path("/content/ai_agentic_attemptings/project6")]
PROJECT_ROOT=next((p.resolve() for p in candidates if (p/"config/default.json").exists()),None)
if PROJECT_ROOT is None:
    repo=Path("/content/ai_agentic_attemptings")
    if not repo.exists(): subprocess.run(["git","clone","https://github.com/soraber/ai_agentic_attemptings.git",str(repo)],check=True)
    PROJECT_ROOT=repo/"project6"
os.chdir(PROJECT_ROOT)
subprocess.run([sys.executable,"-m","pip","install","--upgrade-strategy","only-if-needed","-r","requirements-colab.txt"],check=True)
subprocess.run([sys.executable,"-m","pip","install","-e",".","--no-deps"],check=True)
check=subprocess.run([sys.executable,"-m","pip","check"],text=True,capture_output=True)
if check.returncode: print(check.stdout or check.stderr)
from project6_agent.agent import RepairAgent
print("Project 6 imports passed")"""),
cell("P06-C02","code","""import getpass,os,sys
from project6_agent.config import load_config
RUN_API_EVAL=False; RUN_FULL_EVAL=False
config=load_config(PROJECT_ROOT/"config/default.json")
if RUN_API_EVAL and not os.getenv("OPENAI_API_KEY"):
    if "google.colab" in sys.modules:
        from google.colab import userdata
        key=userdata.get("OPENAI_API_KEY")
    else: key=getpass.getpass("OPENAI_API_KEY (hidden): ")
    if not key: raise RuntimeError("OPENAI_API_KEY required for API mode")
    os.environ["OPENAI_API_KEY"]=key
print(config.model_dump())"""),
cell("P06-C03","code","""import subprocess,sys
subprocess.run([sys.executable,"tools/fetch_quixbugs.py"],check=True)
QUIXBUGS_ROOT=PROJECT_ROOT/"data/cache/QuixBugs"""),
cell("P06-C04","code","""import json
manifest=json.loads((PROJECT_ROOT/"data/quixbugs_manifest.json").read_text())
development_cases=[c for c in manifest["cases"] if c["split"]=="development"]
test_cases=[c for c in manifest["cases"] if c["split"]=="test"]
assert (len(development_cases),len(test_cases))==(4,8)
print({"commit":manifest["commit"],"development":4,"test":8})"""),
cell("P06-C05","code","""print("One-shot fixture behavior is covered by tests/test_agent.py; run P06-C07 before API patches.")"""),
cell("P06-C06","code","""from project6_agent.repository import build_repository_map
symbols=build_repository_map(QUIXBUGS_ROOT/"python_programs")
print({"mapped_symbols":len(symbols),"example":symbols[0].model_dump()})"""),
cell("P06-C07","code","""import subprocess,sys
result=subprocess.run([sys.executable,"-m","pytest","-q","tests"],text=True,capture_output=True); print(result.stdout)
if result.returncode: print(result.stderr); raise RuntimeError("Project 6 tests failed")"""),
cell("P06-C08","code","""from project6_agent.agent import RepairAgent
from project6_agent.evaluation import summarize_results
from project6_agent.planners import OpenAIPatchPlanner
from project6_agent.quixbugs import prepare_case
if not RUN_FULL_EVAL:
    print("Set RUN_FULL_EVAL=True and RUN_API_EVAL=True after P06-C07 passes.")
elif not RUN_API_EVAL:
    print("The held-out repair comparison requires the configured API patch planner.")
else:
    results=[]; agent=RepairAgent(config); runtime=PROJECT_ROOT/"output/runtime/quixbugs"; runtime.mkdir(parents=True,exist_ok=True)
    for case in test_cases:
        prepared=prepare_case(QUIXBUGS_ROOT,case,runtime/f"source-{case['bug_id']}")
        for system in ["one_shot","repair_loop"]:
            planner=OpenAIPatchPlanner(config,prepared["root"]/prepared["source"],case["bug_id"])
            results.append(agent.run(case["bug_id"],system,prepared["root"],runtime/f"work-{case['bug_id']}-{system}",[prepared["source"]],prepared["public_tests"],prepared["hidden_tests"],planner))
    summary=summarize_results(results,PROJECT_ROOT/"output"); print(summary)"""),
cell("P06-C09","code","""import json
path=PROJECT_ROOT/"output/project6_representative_samples.json"
print(json.loads(path.read_text()) if path.exists() else "Run the paired evaluator first.")"""),
cell("P06-C10","code","""import subprocess,sys
if (PROJECT_ROOT/"output/project6_final_summary.json").exists():
    subprocess.run([sys.executable,"tools/generate_report.py"],check=True)
    subprocess.run([sys.executable,"tools/validate_project.py","--require-results"],check=True)
else: print("Measured summary absent; report generation skipped.")""")]


def main():
    notebook={"cells":CELLS,"metadata":{"colab":{"name":OUTPUT.name,"provenance":[]},"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"}},"nbformat":4,"nbformat_minor":5}
    OUTPUT.write_text(json.dumps(notebook,indent=1)+"\n",encoding="utf-8"); print(f"Wrote {OUTPUT} with {len(CELLS)} cells")


if __name__=="__main__": main()
