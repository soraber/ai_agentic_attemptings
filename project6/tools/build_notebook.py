#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
exact rollback. Gold corrected programs never enter planner context.

Upgrade v1: generated code requires Docker isolation. Hidden tests are used only
once after public-test candidate selection. Historical scores are not new results.
Build the executor on a Docker-enabled host: `docker build -f tools/Dockerfile.sandbox
-t project6-test-runner:upgrade-v1 .`. Standard Colab may not provide this runtime."""),
cell("P06-C01","code","""from pathlib import Path
import os,subprocess,sys
candidates=[Path.cwd(),Path.cwd()/"project6",Path("/content/ai_agentic_attemptings/project6")]
PROJECT_ROOT=next((p.resolve() for p in candidates if (p/"config/default.json").exists()),None)
if PROJECT_ROOT is None:
    repo=Path("/content/ai_agentic_attemptings")
    if not repo.exists(): subprocess.run(["git","clone","https://github.com/soraber/ai_agentic_attemptings.git",str(repo)],check=True)
    else: subprocess.run(["git","-C",str(repo),"pull","--ff-only"],check=True)
    PROJECT_ROOT=repo/"project6"
os.chdir(PROJECT_ROOT)
if not os.getenv("AI_PROJECT_SKIP_INSTALL"):
    subprocess.run([sys.executable,"-m","pip","install","--upgrade-strategy","only-if-needed","-r","requirements-colab.txt"],check=True)
    subprocess.run([sys.executable,"-m","pip","install","-e",".","--no-deps"],check=True)
source_root=PROJECT_ROOT/"src"
if str(source_root) not in sys.path: sys.path.insert(0,str(source_root))
if not os.getenv("AI_PROJECT_SKIP_INSTALL"):
    check=subprocess.run([sys.executable,"-m","pip","check"],text=True,capture_output=True)
    if check.returncode: print(check.stdout or check.stderr)
from project6_agent.agent import RepairAgent
try: import torch
except ImportError: torch=None
print("Project 6 imports passed")
print({"cuda":bool(torch and torch.cuda.is_available()),"gpu":torch.cuda.get_device_name(0) if torch and torch.cuda.is_available() else None})"""),
cell("P06-C02","code","""import getpass,os,sys
from project6_agent.config import load_config
EVAL_BACKEND="local_gpu"  # openai | local_gpu
RUN_FULL_EVAL=True; RUN_API_EVAL=EVAL_BACKEND=="openai"; RUN_LOCAL_GPU_EVAL=EVAL_BACKEND=="local_gpu"
config=load_config(PROJECT_ROOT/"config/default.json")
if RUN_API_EVAL and not os.getenv("OPENAI_API_KEY"):
    if "google.colab" in sys.modules:
        from google.colab import userdata
        key=userdata.get("OPENAI_API_KEY")
    else: key=getpass.getpass("OPENAI_API_KEY (hidden): ")
    if not key: raise RuntimeError("OPENAI_API_KEY required for API mode")
    os.environ["OPENAI_API_KEY"]=key
if RUN_LOCAL_GPU_EVAL:
    import gc,torch
    if not torch.cuda.is_available(): raise RuntimeError("Select a Colab GPU runtime for local_gpu mode")
    stale_names=("source_planner","schema_retriever","local_backend","planners","planner","embedding_retriever","local_answerer")
    released=[name for name in stale_names if globals().pop(name,None) is not None]
    gc.collect(); torch.cuda.empty_cache(); free_bytes,total_bytes=torch.cuda.mem_get_info()
    print({"released_gpu_objects":released,"free_gpu_gib":round(free_bytes/2**30,2),"total_gpu_gib":round(total_bytes/2**30,2)})
print(config.model_dump())"""),
cell("P06-C03","code","""import subprocess,sys
subprocess.run([sys.executable,"tools/fetch_quixbugs.py"],check=True)
QUIXBUGS_ROOT=PROJECT_ROOT/'data/cache/QuixBugs'"""),
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
cell("P06-C07","code","""import os,subprocess,sys
test_env=os.environ.copy(); test_env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
result=subprocess.run([sys.executable,"-m","pytest","-q","tests"],text=True,capture_output=True,env=test_env,timeout=120); print(result.stdout)
if result.returncode: print(result.stderr); raise RuntimeError("Project 6 tests failed")"""),
cell("P06-C08","code","""from project6_agent.agent import RepairAgent
from project6_agent.evaluation import summarize_results
from project6_agent.planners import LocalPatchPlanner, OpenAIPatchPlanner, PatchCallBudget, TransformersPatchBackend
from project6_agent.structured_edits import OpenAIStructuredEditPlanner
from project6_agent.quixbugs import prepare_case
from project6_agent.runner import sandbox_preflight
from datetime import datetime, timezone
import json
if not RUN_FULL_EVAL:
    print("Set RUN_FULL_EVAL=True and RUN_API_EVAL=True after P06-C07 passes.")
else:
    if config.execution_backend != "docker": raise RuntimeError("Model-generated patches require Docker, not trusted_fixture mode")
    if RUN_LOCAL_GPU_EVAL and config.edit_format != "unified_diff":
        raise RuntimeError("Structured edits currently require API mode; no untested local-model adapter")
    sandbox = sandbox_preflight(config.sandbox_image)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    result_dir=PROJECT_ROOT/"output/runs/upgrade-v1"/EVAL_BACKEND/run_id
    result_dir.mkdir(parents=True, exist_ok=False)
    (result_dir/"run_config.json").write_text(json.dumps({"config": config.model_dump(), "sandbox": sandbox}, indent=2))
    results=[]; planners=[]; agent=RepairAgent(config); runtime=result_dir/"runtime/quixbugs"; runtime.mkdir(parents=True,exist_ok=True)
    local_backend=TransformersPatchBackend(config) if RUN_LOCAL_GPU_EVAL else None
    api_budget = PatchCallBudget(config) if RUN_API_EVAL else None
    for case in test_cases:
        prepared=prepare_case(QUIXBUGS_ROOT,case,runtime/f"source-{case['bug_id']}")
        for system in ["one_shot","repair_loop"]:
            if RUN_LOCAL_GPU_EVAL:
                planner=LocalPatchPlanner(config,prepared["root"]/prepared["source"],case["bug_id"],prepared["source"],local_backend)
            else:
                planner_class = OpenAIStructuredEditPlanner if config.edit_format == "structured_edits" else OpenAIPatchPlanner
                planner=planner_class(config,prepared["root"]/prepared["source"],case["bug_id"],allowed_path=prepared["source"],budget=api_budget)
            planners.append(planner)
            results.append(agent.run(case["bug_id"],system,prepared["root"],runtime/f"work-{case['bug_id']}-{system}",[prepared["source"]],prepared["public_tests"],prepared["hidden_tests"],planner))
    usage=local_backend.usage_summary() if RUN_LOCAL_GPU_EVAL else {"model_calls":sum(p.calls for p in planners),"input_tokens":sum(p.input_tokens for p in planners),"output_tokens":sum(p.output_tokens for p in planners),"estimated_cost_usd":round(sum(p.estimated_cost_usd for p in planners),6)}
    selected_model=config.local_model if RUN_LOCAL_GPU_EVAL else config.model
    if api_budget is not None: usage["reserved_unreported_cost_usd"] = api_budget.reserved
    summary=summarize_results(results,result_dir,planner_usage=usage,model=selected_model,evaluation_backend=EVAL_BACKEND); print(summary)"""),
cell("P06-C09","code","""import json
if "result_dir" not in globals(): raise RuntimeError("Run P06-C08 first; historical results are not reused")
path=result_dir/"project6_representative_samples.json"
print(json.loads(path.read_text()) if path.exists() else "Run the paired evaluator first.")"""),
cell("P06-C10","code","""import subprocess,sys
if "result_dir" not in globals(): raise RuntimeError("Run P06-C08 first; historical results are not reused")
summary_path=result_dir/"project6_final_summary.json"
if summary_path.exists():
    subprocess.run([sys.executable,"tools/generate_report.py","--summary",str(summary_path),"--output",str(result_dir/"project6_report.pdf")],check=True)
    subprocess.run([sys.executable,"tools/validate_project.py"]+([] if RUN_LOCAL_GPU_EVAL else ["--require-results"]),check=True)
else: print("Measured summary absent; report generation skipped.")""")]

CELLS.extend([
cell("P06-C11", "markdown", """## Development-Only Edit Interface Comparison

This optional local/Docker experiment compares model-written unified diffs with
exact source replacements on the four development bugs, under the same three-attempt
budget. The harness validates unique, non-overlapping anchors, Python syntax, paths,
and changed-line limits before generating a diff. It does not retry using final-test
feedback or overwrite the eight-bug test results. Run setup/config/data/tests first;
the test-set evaluation cell is not required. This is API-only, not a GPU workload."""),
cell("P06-C12", "code", """RUN_EDIT_FORMAT_DEVELOPMENT = False
if RUN_EDIT_FORMAT_DEVELOPMENT:
    import os
    from datetime import datetime, timezone
    from openai import OpenAI
    from project6_agent.edit_comparison import compare_development_edits
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Use the hidden API-key prompt in the configuration cell; never paste a key into source")
    development_output = PROJECT_ROOT/"output/runs/upgrade-v1/development_edits"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    development_config = config.model_copy(update={"max_output_tokens": 2048, "reasoning_effort": "low", "max_retries": 0})
    with OpenAI(max_retries=0, timeout=60) as api:
        development_summary = compare_development_edits(api, development_config, PROJECT_ROOT, development_output)
    print(development_summary)
else:
    print("Development-only comparison not requested; no API calls.")""")])


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--patch-gpu-cells",action="store_true"); args=parser.parse_args()
    if args.patch_gpu_cells:
        notebook=json.loads(OUTPUT.read_text(encoding="utf-8")); replacements={item["id"]:item for item in CELLS}; changed={"P06-C01","P06-C02","P06-C08","P06-C09","P06-C10"}
        for item in notebook["cells"]:
            if item.get("id") in changed:
                item["source"]=replacements[item["id"]]["source"]; item["execution_count"]=None; item["outputs"]=[]
        OUTPUT.write_text(json.dumps(notebook,indent=1)+"\n",encoding="utf-8"); print(f"Patched {', '.join(sorted(changed))} without changing other cells"); return
    notebook={"cells":CELLS,"metadata":{"colab":{"name":OUTPUT.name,"provenance":[]},"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"}},"nbformat":4,"nbformat_minor":5}
    OUTPUT.write_text(json.dumps(notebook,indent=1)+"\n",encoding="utf-8"); print(f"Wrote {OUTPUT} with {len(CELLS)} cells")


if __name__=="__main__": main()
