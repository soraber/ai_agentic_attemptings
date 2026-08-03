#!/usr/bin/env python3
from __future__ import annotations

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
subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade-strategy", "only-if-needed", "-r", "requirements-colab.txt"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".", "--no-deps"], check=True)
check = subprocess.run([sys.executable, "-m", "pip", "check"], text=True, capture_output=True)
if check.returncode: print(check.stdout or check.stderr)
from project5_agent.analyst import run_governed
print("Project 5 imports passed", sys.version.split()[0])"""),
    cell("P05-C02", "code", """import getpass, os, sys
from project5_agent.config import load_config
RUN_API_EVAL = False
RUN_FULL_EVAL = False
config = load_config(PROJECT_ROOT/"config/default.json")
if RUN_API_EVAL and not os.getenv("OPENAI_API_KEY"):
    if "google.colab" in sys.modules:
        from google.colab import userdata
        key = userdata.get("OPENAI_API_KEY")
    else: key = getpass.getpass("OPENAI_API_KEY (hidden): ")
    if not key: raise RuntimeError("OPENAI_API_KEY is required for API mode")
    os.environ["OPENAI_API_KEY"] = key
config = config.model_copy(update={"planner_mode": "openai" if RUN_API_EVAL else "deterministic"})
print(config.model_dump())"""),
    cell("P05-C03", "code", """import subprocess, sys
database_path = PROJECT_ROOT/"data/cache/project5_ecommerce.duckdb"
benchmark_path = PROJECT_ROOT/"data/cache/project5_questions.json"
subprocess.run([sys.executable, "tools/generate_dataset.py"], check=True)
from project5_agent.dataset import load_benchmark
cases = load_benchmark(benchmark_path)
print({"questions": len(cases), "database": str(database_path)})"""),
    cell("P05-C04", "code", """development_cases = [case for case in cases if case.split == "development"]
test_cases = [case for case in cases if case.split == "test"]
assert (len(development_cases), len(test_cases)) == (10, 40)
assert "gold_sql" not in development_cases[0].public_view()
print({"development": 10, "test": 40})"""),
    cell("P05-C05", "code", """from project5_agent.analyst import run_baseline
case = next(case for case in development_cases if case.first_attempt_sql)
print(run_baseline(case, database_path).model_dump())"""),
    cell("P05-C06", "code", """from project5_agent.analyst import DeterministicSQLPlanner, run_governed
repair_case = next(case for case in cases if case.category == "repair")
result = run_governed(repair_case, database_path, config, DeterministicSQLPlanner())
assert result.repaired and result.result_correct
print(result.model_dump())"""),
    cell("P05-C07", "code", """import subprocess, sys
result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], text=True, capture_output=True)
print(result.stdout)
if result.returncode: print(result.stderr); raise RuntimeError("Project 5 tests failed")"""),
    cell("P05-C08", "code", """from project5_agent.analyst import DeterministicSQLPlanner, OpenAISQLPlanner
from project5_agent.evaluation import evaluate_project5
if not RUN_FULL_EVAL:
    print("Set RUN_FULL_EVAL=True in P05-C02 after deterministic tests pass.")
else:
    source_planner = OpenAISQLPlanner(config) if RUN_API_EVAL else DeterministicSQLPlanner()
    summary = evaluate_project5(cases, database_path, config, PROJECT_ROOT/"output", source_planner)
    print(summary)"""),
    cell("P05-C09", "code", """import json
path = PROJECT_ROOT/"output/project5_representative_samples.json"
print(json.loads(path.read_text()) if path.exists() else "Run P05-C08 first.")"""),
    cell("P05-C10", "code", """import subprocess, sys
if (PROJECT_ROOT/"output/project5_final_summary.json").exists():
    subprocess.run([sys.executable, "tools/generate_report.py"], check=True)
    subprocess.run([sys.executable, "tools/validate_project.py", "--require-results"], check=True)
else: print("Measured summary absent; report generation skipped.")"""),
]


def main() -> None:
    notebook = {"cells": CELLS, "metadata": {"colab": {"name": OUTPUT.name, "provenance": []}, "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.12"}}, "nbformat": 4, "nbformat_minor": 5}
    OUTPUT.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(CELLS)} cells")


if __name__ == "__main__": main()
