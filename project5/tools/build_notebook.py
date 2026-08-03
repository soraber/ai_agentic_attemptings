#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "project5_governed_text_to_sql.ipynb"


def cell(cell_id: str, kind: str, source: str) -> dict:
    value = {"cell_type": kind, "id": cell_id, "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}
    if kind == "code":
        value.update({"execution_count": None, "outputs": []})
    return value


CELLS = [
    cell("P05-C00", "markdown", """# Project 5: Governed Text-to-SQL Analyst

Compare one-shot SQL with schema retrieval, typed planning, SQLGlot AST policy,
read-only DuckDB execution, bounded repair, PII controls, and export approval.
All data is synthetic and final figures must come from saved measured output."""),
    cell("P05-C01", "code", """from pathlib import Path
import os, subprocess, sys
candidates = [Path.cwd(), Path.cwd()/"project5", Path("/content/ai_agentic_attemptings/project5")]
PROJECT_ROOT = next((p.resolve() for p in candidates if (p/"config/default.json").exists()), None)
if PROJECT_ROOT is None:
    repo = Path("/content/ai_agentic_attemptings")
    if not repo.exists(): subprocess.run(["git", "clone", "https://github.com/soraber/ai_agentic_attemptings.git", str(repo)], check=True)
    PROJECT_ROOT = repo/"project5"
os.chdir(PROJECT_ROOT)
if not os.getenv("AI_PROJECT_SKIP_INSTALL"):
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade-strategy", "only-if-needed", "-r", "requirements-colab.txt"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".", "--no-deps"], check=True)
source_root = PROJECT_ROOT/"src"
if str(source_root) not in sys.path: sys.path.insert(0, str(source_root))
if not os.getenv("AI_PROJECT_SKIP_INSTALL"):
    check = subprocess.run([sys.executable, "-m", "pip", "check"], text=True, capture_output=True)
    if check.returncode: print(check.stdout or check.stderr)
from project5_agent.analyst import run_governed
try: import torch
except ImportError: torch=None
print("Project 5 imports passed", sys.version.split()[0])
print({"cuda": bool(torch and torch.cuda.is_available()), "gpu": torch.cuda.get_device_name(0) if torch and torch.cuda.is_available() else None})"""),
    cell("P05-C02", "code", """import getpass, os, sys
from project5_agent.config import load_config
EVAL_BACKEND = "local_gpu"  # deterministic | openai | local_gpu
RUN_FULL_EVAL = True
RUN_API_EVAL = EVAL_BACKEND == "openai"
RUN_LOCAL_GPU_EVAL = EVAL_BACKEND == "local_gpu"
config = load_config(PROJECT_ROOT/"config/default.json")
if RUN_API_EVAL and not os.getenv("OPENAI_API_KEY"):
    if "google.colab" in sys.modules:
        from google.colab import userdata
        key = userdata.get("OPENAI_API_KEY")
    else: key = getpass.getpass("OPENAI_API_KEY (hidden): ")
    if not key: raise RuntimeError("OPENAI_API_KEY is required for API mode")
    os.environ["OPENAI_API_KEY"] = key
if RUN_LOCAL_GPU_EVAL:
    import torch
    if not torch.cuda.is_available(): raise RuntimeError("Select a Colab GPU runtime for local_gpu mode")
config = config.model_copy(update={"planner_mode": EVAL_BACKEND})
print(config.model_dump())"""),
    cell("P05-C03", "code", """import subprocess, sys
database_path = PROJECT_ROOT/"data/cache/project5_ecommerce.duckdb"
benchmark_path = PROJECT_ROOT/"data/cache/project5_questions.json"
subprocess.run([sys.executable, "tools/generate_dataset.py"], check=True)
from project5_agent.dataset import load_benchmark
cases = load_benchmark(benchmark_path)
print({"questions": len(cases), "database": database_path.relative_to(PROJECT_ROOT).as_posix()})"""),
    cell("P05-C04", "code", """development_cases = [case for case in cases if case.split == "development"]
test_cases = [case for case in cases if case.split == "test"]
assert (len(development_cases), len(test_cases)) == (10, 40)
assert "gold_sql" not in development_cases[0].public_view()
print({"development": 10, "test": 40})"""),
    cell("P05-C05", "code", """from project5_agent.analyst import run_baseline
case = next(case for case in development_cases if case.first_attempt_sql)
print(run_baseline(case, database_path).model_dump())"""),
    cell("P05-C06", "code", """from project5_agent.analyst import DeterministicSQLPlanner, SCHEMA_CATALOG, run_governed
from project5_agent.local_models import EmbeddingSchemaRetriever
repair_case = next(case for case in cases if case.category == "repair")
result = run_governed(repair_case, database_path, config, DeterministicSQLPlanner())
assert result.repaired and result.result_correct
schema_retriever = None
if RUN_LOCAL_GPU_EVAL:
    schema_retriever = EmbeddingSchemaRetriever(SCHEMA_CATALOG, config.embedding_model, config.local_device)
    print({"dense_schema_matches": schema_retriever.retrieve(repair_case.question, config.schema_top_k)})
print(result.model_dump())"""),
    cell("P05-C07", "code", """import subprocess, sys
result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], text=True, capture_output=True)
print(result.stdout)
if result.returncode: print(result.stderr); raise RuntimeError("Project 5 tests failed")"""),
    cell("P05-C08", "code", """from project5_agent.analyst import DeterministicSQLPlanner, LocalSQLPlanner, OpenAISQLPlanner
from project5_agent.evaluation import evaluate_project5
if not RUN_FULL_EVAL:
    print("Set RUN_FULL_EVAL=True in P05-C02 after deterministic tests pass.")
else:
    if RUN_LOCAL_GPU_EVAL:
        source_planner = LocalSQLPlanner(config, retriever=schema_retriever)
        result_dir = PROJECT_ROOT/"output/gpu"
    elif RUN_API_EVAL:
        source_planner = OpenAISQLPlanner(config)
        result_dir = PROJECT_ROOT/"output"
    else:
        source_planner = DeterministicSQLPlanner()
        result_dir = PROJECT_ROOT/"output/deterministic"
    summary = evaluate_project5(cases, database_path, config, result_dir, source_planner)
    print(summary)"""),
    cell("P05-C09", "code", """import json
result_dir = PROJECT_ROOT/("output/gpu" if RUN_LOCAL_GPU_EVAL else ("output" if RUN_API_EVAL else "output/deterministic"))
path = result_dir/"project5_representative_samples.json"
print(json.loads(path.read_text()) if path.exists() else "Run P05-C08 first.")"""),
    cell("P05-C10", "code", """import subprocess, sys
result_dir = PROJECT_ROOT/("output/gpu" if RUN_LOCAL_GPU_EVAL else ("output" if RUN_API_EVAL else "output/deterministic"))
summary_path = result_dir/"project5_final_summary.json"
if summary_path.exists():
    subprocess.run([sys.executable, "tools/generate_report.py", "--summary", str(summary_path), "--output", str(result_dir/"project5_report.pdf")], check=True)
    subprocess.run([sys.executable, "tools/validate_project.py"] + ([] if RUN_LOCAL_GPU_EVAL else ["--require-results"]), check=True)
else: print("Measured summary absent; report generation skipped.")"""),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch-gpu-cells", action="store_true")
    args = parser.parse_args()
    if args.patch_gpu_cells:
        notebook = json.loads(OUTPUT.read_text(encoding="utf-8"))
        replacements = {item["id"]: item for item in CELLS}
        changed = {"P05-C01", "P05-C02", "P05-C06", "P05-C08", "P05-C09", "P05-C10"}
        for item in notebook["cells"]:
            if item.get("id") in changed:
                item["source"] = replacements[item["id"]]["source"]
                item["execution_count"] = None
                item["outputs"] = []
        OUTPUT.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
        print(f"Patched {', '.join(sorted(changed))} without changing other cells")
        return
    notebook = {"cells": CELLS, "metadata": {"colab": {"name": OUTPUT.name, "provenance": []}, "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.12"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTPUT.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(CELLS)} cells")


if __name__ == "__main__": main()
