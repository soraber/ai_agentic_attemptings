#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUTPUT=ROOT/"project7_secure_agent_gateway.ipynb"


def cell(i,k,s):
    v={"cell_type":k,"id":i,"metadata":{},"source":s.strip("\n").splitlines(keepends=True)}
    if k=="code": v.update({"execution_count":None,"outputs":[]})
    return v


CELLS=[
cell("P07-C00","markdown","""# Project 7: Secure Interoperable Agent Gateway

Compare local A2A/MCP-style workflows with defenses disabled and enabled across
benign and attack cases. Credentials, records, effects, and canaries are synthetic."""),
cell("P07-C01","code","""from pathlib import Path
import os,subprocess,sys
candidates=[Path.cwd(),Path.cwd()/"project7",Path("/content/ai_agentic_attemptings/project7")]
PROJECT_ROOT=next((p.resolve() for p in candidates if (p/"config/default.json").exists()),None)
if PROJECT_ROOT is None:
    repo=Path("/content/ai_agentic_attemptings")
    if not repo.exists(): subprocess.run(["git","clone","https://github.com/soraber/ai_agentic_attemptings.git",str(repo)],check=True)
    PROJECT_ROOT=repo/"project7"
os.chdir(PROJECT_ROOT)
if not os.getenv("AI_PROJECT_SKIP_INSTALL"):
    subprocess.run([sys.executable,"-m","pip","install","--upgrade-strategy","only-if-needed","-r","requirements-colab.txt"],check=True)
    subprocess.run([sys.executable,"-m","pip","install","-e",".","--no-deps"],check=True)
source_root=PROJECT_ROOT/"src"
if str(source_root) not in sys.path: sys.path.insert(0,str(source_root))
if not os.getenv("AI_PROJECT_SKIP_INSTALL"):
    check=subprocess.run([sys.executable,"-m","pip","check"],text=True,capture_output=True)
    if check.returncode: print(check.stdout or check.stderr)
from project7_agent.gateway import SecureGateway
print("Project 7 imports passed")"""),
cell("P07-C02","code","""import getpass,os,sys
from project7_agent.config import load_config
RUN_API_EVAL=False
RUN_FULL_EVAL=False
config=load_config(PROJECT_ROOT/"config/default.json")
if RUN_API_EVAL and not os.getenv("OPENAI_API_KEY"):
    if "google.colab" in sys.modules:
        from google.colab import userdata
        key=userdata.get("OPENAI_API_KEY")
    else: key=getpass.getpass("OPENAI_API_KEY (hidden): ")
    if not key: raise RuntimeError("OPENAI_API_KEY required for API mode")
    os.environ["OPENAI_API_KEY"]=key
print(config.model_dump())"""),
cell("P07-C03","code","""import subprocess,sys
subprocess.run([sys.executable,"tools/generate_dataset.py"],check=True)
from project7_agent.dataset import load_cases
cases=load_cases(PROJECT_ROOT/"data/cache/project7_cases.json")
print(len(cases))"""),
cell("P07-C04","code","""from collections import Counter
development_cases=[c for c in cases if c.split=="development"]
test_cases=[c for c in cases if c.split=="test"]
assert (len(development_cases),len(test_cases))==(8,32)
print(Counter(c.category for c in cases))"""),
cell("P07-C05","code","""from project7_agent.gateway import SecureGateway
attack=next(c for c in development_cases if c.category!="benign")
print(SecureGateway().process(attack,False).model_dump())"""),
cell("P07-C06","code","""secure=SecureGateway().process(attack,True)
assert not secure.attack_succeeded
print({"status":secure.status,"trace_events":[e["event"] for e in secure.trace]})"""),
cell("P07-C07","code","""import subprocess,sys
result=subprocess.run([sys.executable,"-m","pytest","-q","tests"],text=True,capture_output=True)
print(result.stdout)
if result.returncode:
    print(result.stderr)
    raise RuntimeError("Project 7 tests failed")"""),
cell("P07-C08","code","""from project7_agent.evaluation import evaluate_project7
from project7_agent.reviewers import OpenAIPolicyReviewer
if not RUN_FULL_EVAL:
    print("Set RUN_FULL_EVAL=True after P07-C07 passes.")
else:
    reviewer=OpenAIPolicyReviewer(config) if RUN_API_EVAL else None
    summary=evaluate_project7(cases,PROJECT_ROOT/"output",reviewer=reviewer)
    print(summary)"""),
cell("P07-C09","code","""import json
path=PROJECT_ROOT/"output/project7_representative_samples.json"
print(json.loads(path.read_text()) if path.exists() else "Run P07-C08 first.")"""),
cell("P07-C10","code","""import subprocess,sys
if (PROJECT_ROOT/"output/project7_final_summary.json").exists():
    subprocess.run([sys.executable,"tools/generate_report.py"],check=True)
    subprocess.run([sys.executable,"tools/validate_project.py","--require-results"],check=True)
else:
    print("Measured summary absent; report generation skipped.")""")]


def main():
    nb={"cells":CELLS,"metadata":{"colab":{"name":OUTPUT.name,"provenance":[]},"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"}},"nbformat":4,"nbformat_minor":5}
    OUTPUT.write_text(json.dumps(nb,indent=1)+"\n",encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(CELLS)} cells")


if __name__=="__main__": main()
