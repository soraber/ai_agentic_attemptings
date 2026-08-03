#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUTPUT=ROOT/"project8_long_term_memory.ipynb"


def cell(i,k,s):
    v={"cell_type":k,"id":i,"metadata":{},"source":s.strip("\n").splitlines(keepends=True)}
    if k=="code": v.update({"execution_count":None,"outputs":[]})
    return v


CELLS=[
cell("P08-C00","markdown","""# Project 8: Long-Term Memory Agent

Compare recent-window, episodic, and hybrid semantic/temporal memory. Test
corrections, conflicts, evidence, consolidation, and deletion across all stores."""),
cell("P08-C01","code","""from pathlib import Path
import os,subprocess,sys
candidates=[Path.cwd(),Path.cwd()/"project8",Path("/content/ai_agentic_attemptings/project8")]
PROJECT_ROOT=next((p.resolve() for p in candidates if (p/"config/default.json").exists()),None)
if PROJECT_ROOT is None:
    repo=Path("/content/ai_agentic_attemptings")
    if not repo.exists(): subprocess.run(["git","clone","https://github.com/soraber/ai_agentic_attemptings.git",str(repo)],check=True)
    else: subprocess.run(["git","-C",str(repo),"pull","--ff-only"],check=True)
    PROJECT_ROOT=repo/"project8"
os.chdir(PROJECT_ROOT)
if not os.getenv("AI_PROJECT_SKIP_INSTALL"):
    subprocess.run([sys.executable,"-m","pip","install","--upgrade-strategy","only-if-needed","-r","requirements-colab.txt"],check=True)
    subprocess.run([sys.executable,"-m","pip","install","-e",".","--no-deps"],check=True)
source_root=PROJECT_ROOT/"src"
if str(source_root) not in sys.path: sys.path.insert(0,str(source_root))
if not os.getenv("AI_PROJECT_SKIP_INSTALL"):
    check=subprocess.run([sys.executable,"-m","pip","check"],text=True,capture_output=True)
    if check.returncode: print(check.stdout or check.stderr)
from project8_agent.memory import MemoryStore
try: import torch
except ImportError: torch=None
print("Project 8 imports passed")
print({"cuda":bool(torch and torch.cuda.is_available()),"gpu":torch.cuda.get_device_name(0) if torch and torch.cuda.is_available() else None})"""),
cell("P08-C02","code","""import getpass,os,sys
from project8_agent.config import load_config
EVAL_BACKEND="local_gpu"  # deterministic | openai | local_gpu
RUN_FULL_EVAL=True; RUN_API_EVAL=EVAL_BACKEND=="openai"; RUN_LOCAL_GPU_EVAL=EVAL_BACKEND=="local_gpu"; config=load_config(PROJECT_ROOT/"config/default.json")
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
cell("P08-C03","code","""import subprocess,sys
subprocess.run([sys.executable,"tools/fetch_locomo.py"],check=True)
subset_path=PROJECT_ROOT/"data/cache/locomo_subset.json"
print("LoCoMo subset:",subset_path.relative_to(PROJECT_ROOT).as_posix())"""),
cell("P08-C04","code","""import json
subset=json.loads(subset_path.read_text()); lifecycle=json.loads((PROJECT_ROOT/"data/lifecycle_cases.json").read_text())
assert len(subset)==2 and sum(len(item["qa"]) for item in subset)==80
print({"conversations":2,"qa":80,"lifecycle_events":len(lifecycle["events"])})"""),
cell("P08-C05","code","""from project8_agent.memory import MemoryStore
from project8_agent.schemas import MemoryEvent,MemoryQuery
runtime=PROJECT_ROOT/"output/runtime"; runtime.mkdir(parents=True,exist_ok=True); store=MemoryStore(runtime/"memory.sqlite"); store.reset()
for item in lifecycle["events"]: store.ingest(MemoryEvent.model_validate(item))
query=MemoryQuery.model_validate(lifecycle["queries"][0]); print(store.answer(query,"window").model_dump()); print(store.answer(query,"episodic").model_dump())
embedding_retriever=None
if RUN_LOCAL_GPU_EVAL:
    from project8_agent.local_models import EmbeddingEventRetriever
    from project8_agent.locomo import conversation_events
    embedding_retriever=EmbeddingEventRetriever(config.embedding_model,config.local_device)
    sample_events=conversation_events(subset[0]); print({"dense_retrieval":[item["event_id"] for item in embedding_retriever.retrieve(sample_events,subset[0]["qa"][0]["question"],"hybrid",config.working_window_size,config.episodic_top_k)]})"""),
cell("P08-C06","code","""for event_id in lifecycle["delete_event_ids"]: store.delete_event(event_id)
correction=MemoryQuery.model_validate(lifecycle["queries"][1]); conflict=MemoryQuery.model_validate(lifecycle["queries"][2])
print(store.answer(correction,"hybrid").model_dump()); print(store.answer(conflict,"hybrid").model_dump()); assert all(store.deletion_verified(e) for e in lifecycle["delete_event_ids"])"""),
cell("P08-C07","code","""import os,subprocess,sys
test_env=os.environ.copy(); test_env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
try:
    result=subprocess.run([sys.executable,"-m","pytest","-q","tests"],text=True,capture_output=True,env=test_env,timeout=120)
except subprocess.TimeoutExpired as exc:
    raise RuntimeError("Project 8 tests exceeded the 120-second Colab limit") from exc
print(result.stdout)
if result.returncode: print(result.stderr); raise RuntimeError("Project 8 tests failed")"""),
cell("P08-C08","code","""from project8_agent.evaluation import evaluate_lifecycle
from project8_agent.locomo import CachedLocalAnswerer, evaluate_locomo
if not RUN_FULL_EVAL: print("Set RUN_FULL_EVAL=True after P08-C07 passes.")
else:
    lifecycle_summary=evaluate_lifecycle(PROJECT_ROOT/"data/lifecycle_cases.json",runtime/"evaluation.sqlite",runtime/"lifecycle_output")
    if RUN_LOCAL_GPU_EVAL:
        result_dir=PROJECT_ROOT/"output/gpu"; local_answerer=CachedLocalAnswerer(config,runtime/"locomo_local_answer_cache.json")
        summary=evaluate_locomo(subset_path,config,runtime/"unused.json",result_dir,lifecycle_summary,answerer=local_answerer,retriever=embedding_retriever,evaluation_mode="locomo_local_gpu")
    elif RUN_API_EVAL:
        summary=evaluate_locomo(subset_path,config,runtime/"locomo_answer_cache.json",PROJECT_ROOT/"output",lifecycle_summary)
    else:
        summary=evaluate_lifecycle(PROJECT_ROOT/"data/lifecycle_cases.json",runtime/"evaluation.sqlite",PROJECT_ROOT/"output")
    print(summary)"""),
cell("P08-C09","code","""import json
result_dir=PROJECT_ROOT/("output/gpu" if RUN_LOCAL_GPU_EVAL else "output")
path=result_dir/"project8_representative_samples.json"; print(json.loads(path.read_text()) if path.exists() else "Run P08-C08 first.")"""),
cell("P08-C10","code","""import subprocess,sys
result_dir=PROJECT_ROOT/("output/gpu" if RUN_LOCAL_GPU_EVAL else "output"); summary_path=result_dir/"project8_final_summary.json"
if summary_path.exists():
    subprocess.run([sys.executable,"tools/generate_report.py","--summary",str(summary_path),"--output",str(result_dir/"project8_report.pdf")],check=True); subprocess.run([sys.executable,"tools/validate_project.py"]+([] if RUN_LOCAL_GPU_EVAL else ["--require-results"]),check=True)
else: print("Measured summary absent; report generation skipped.")""")]


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--patch-gpu-cells",action="store_true"); args=parser.parse_args()
    if args.patch_gpu_cells:
        notebook=json.loads(OUTPUT.read_text(encoding="utf-8")); replacements={item["id"]:item for item in CELLS}; changed={"P08-C01","P08-C02","P08-C05","P08-C08","P08-C09","P08-C10"}
        for item in notebook["cells"]:
            if item.get("id") in changed:
                item["source"]=replacements[item["id"]]["source"]; item["execution_count"]=None; item["outputs"]=[]
        OUTPUT.write_text(json.dumps(notebook,indent=1)+"\n",encoding="utf-8"); print(f"Patched {', '.join(sorted(changed))} without changing other cells"); return
    nb={"cells":CELLS,"metadata":{"colab":{"name":OUTPUT.name,"provenance":[]},"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"}},"nbformat":4,"nbformat_minor":5}; OUTPUT.write_text(json.dumps(nb,indent=1)+"\n",encoding="utf-8"); print(f"Wrote {OUTPUT} with {len(CELLS)} cells")


if __name__=="__main__": main()
