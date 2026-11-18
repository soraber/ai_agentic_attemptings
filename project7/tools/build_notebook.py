#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUTPUT=ROOT/"project7_secure_agent_gateway.ipynb"


def cell(i,k,s):
    if i == 'P07-C08':
        s = runpy.run_path(str(ROOT.parent/'tools/notebook_run_metadata.py'))['wrap'](s, 7)
    v={"cell_type":k,"id":i,"metadata":{},"source":s.strip("\n").splitlines(keepends=True)}
    if k=="code": v.update({"execution_count":None,"outputs":[]})
    return v


import runpy
environment_source = runpy.run_path(str(ROOT.parent / "tools/notebook_environment.py"))["source"]

CELLS=[
cell("P07-C00","markdown","""# Project 7: Secure Interoperable Agent Gateway

Compare local A2A/MCP-style workflows with defenses disabled and enabled across
benign and attack cases. Credentials, records, effects, and canaries are synthetic.

Upgrade v1 adds a real MCP v2 stdio server/client and persistent, approval-bound
effects. Fixture attack metrics do not measure adaptive model prompt injection.
Upgrade v2 verifies issuer/audience-bound signed access tokens over HTTP, checks
tool scopes, and binds durable approvals to the authenticated subject and client.
Tests use ephemeral synthetic identities; a production identity provider and TLS
deployment are not claimed. A2A envelopes remain illustrative."""),
cell("P07-C01", "code", environment_source(7)),
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
print({"status":secure.status,"trace_events":[e["event"] for e in secure.trace]})
from mcp import Client, StdioServerParameters
runtime = PROJECT_ROOT/"output/runtime/upgrade-v1"
runtime.mkdir(parents=True, exist_ok=True)
parameters = StdioServerParameters(command=sys.executable, args=["-m", "project7_agent.mcp_server"],
    env={"PATH": os.defpath, "PYTHONPATH": str(PROJECT_ROOT/"src"),
         "PYTHONDONTWRITEBYTECODE": "1", "PROJECT7_LEDGER": str(runtime/"mcp.sqlite")})
async with Client(parameters, read_timeout_seconds=10) as client:
    tools = await client.list_tools()
    print({"mcp_tools": [tool.name for tool in tools.tools]})
    response = await client.call_tool("policy_search", {"query": "purchase approval"})
    assert not response.is_error
    print(response.structured_content)"""),
cell("P07-C07","code","""import subprocess,sys
result=subprocess.run([sys.executable,"-m","pytest","-q","tests"],text=True,capture_output=True)
print(result.stdout)
if result.returncode:
    print(result.stderr)
    raise RuntimeError("Project 7 tests failed")"""),
cell("P07-C08","code","""from project7_agent.evaluation import evaluate_project7
from project7_agent.model_evaluation import evaluate_model_gateway, CallBudget
from datetime import datetime, timezone
if not RUN_FULL_EVAL:
    print("Set RUN_FULL_EVAL=True after P07-C07 passes.")
else:
    result_dir=PROJECT_ROOT/"output/runs/upgrade-v1"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    summary=evaluate_project7(cases,result_dir,reviewer=None)
    print(summary)
    if RUN_API_EVAL:
        from openai import AsyncOpenAI
        async with AsyncOpenAI(max_retries=0, timeout=60) as api:
            model_summary = await evaluate_model_gateway(api, result_dir/"model_mcp", model=config.model,
                budget=CallBudget(max_calls=config.max_model_calls, max_cost=config.max_estimated_cost_usd,
                    input_price=config.input_price_per_million_usd, output_price=config.output_price_per_million_usd))
        print(model_summary)  # Separate from authored fixture scores and historical advisory reviews."""),
cell("P07-C09","code","""import json
if "result_dir" not in globals(): raise RuntimeError("Run P07-C08 first; historical results are not reused")
path=result_dir/"project7_representative_samples.json"
print(json.loads(path.read_text()) if path.exists() else "Run P07-C08 first.")"""),
cell("P07-C10","code","""import subprocess,sys
if "result_dir" not in globals(): raise RuntimeError("Run P07-C08 first; historical results are not reused")
if (result_dir/"project7_final_summary.json").exists():
    subprocess.run([sys.executable,"tools/generate_report.py","--summary",str(result_dir/"project7_final_summary.json"),"--output",str(result_dir/"project7_report.pdf")],check=True)
    subprocess.run([sys.executable,"tools/validate_project.py","--require-results"],check=True)
else:
    print("Measured summary absent; report generation skipped.")""")]


def main():
    nb={"cells":CELLS,"metadata":{"colab":{"name":OUTPUT.name,"provenance":[]},"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"}},"nbformat":4,"nbformat_minor":5}
    OUTPUT.write_text(json.dumps(nb,indent=1)+"\n",encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(CELLS)} cells")


if __name__=="__main__": main()
