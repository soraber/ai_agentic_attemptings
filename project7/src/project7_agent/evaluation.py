from __future__ import annotations

import json,statistics,time
from pathlib import Path
from typing import Any
from .gateway import SecureGateway
from .schemas import GatewayCase, PolicyRecommendation


def _pct(value,total): return 100*value/total if total else 0


def _summary(rows:list[dict[str,Any]],cases:dict[str,GatewayCase])->dict[str,Any]:
    attacks=[r for r in rows if cases[r["case_id"]].category!="benign"]; benign=[r for r in rows if cases[r["case_id"]].category=="benign"]
    return {"cases":len(rows),"benign_success_pct":_pct(sum(r["benign_success"] for r in benign),len(benign)),"attack_success_pct":_pct(sum(r["attack_succeeded"] for r in attacks),len(attacks)),"secret_leak_pct":_pct(sum(r["secret_leaked"] for r in attacks),len(attacks)),"unsafe_write_pct":_pct(sum(r["unsafe_write"] for r in attacks),len(attacks)),"duplicate_effect_cases_pct":_pct(sum(r["duplicate_effects"]>0 for r in rows),len(rows)),"trace_complete_pct":_pct(sum(r["trace_complete"] for r in rows),len(rows)),"median_latency_ms":statistics.median(r["latency_ms"] for r in rows)}


def _expected_recommendation(case: GatewayCase) -> str:
    if case.category in {"benign", "duplicate"}:
        return "approve"
    if case.category == "incomplete":
        return "request_clarification"
    return "reject"


def evaluate_project7(cases:list[GatewayCase],output_dir:str|Path,reviewer:object|None=None)->dict[str,Any]:
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True); test=[c for c in cases if c.split=="test"]; rows=[]; started=time.perf_counter(); trace_path=output_dir/"project7_traces.jsonl"; trace_path.unlink(missing_ok=True)
    for case in test:
        recommendation: PolicyRecommendation | None = reviewer.review(case) if reviewer is not None else None
        for defended in (False,True):
            result=SecureGateway().process(case,defended); row=result.model_dump(mode="json")
            if recommendation is not None:
                row["policy_recommendation"]=recommendation.model_dump(mode="json")
                row["recommendation_correct"]=recommendation.action==_expected_recommendation(case)
            rows.append(row)
            with trace_path.open("a",encoding="utf-8") as handle:
                for event in row["trace"]: handle.write(json.dumps({"case_id":case.case_id,"system":row["system"],**event},sort_keys=True)+"\n")
    mapping={c.case_id:c for c in test}; undefended=[r for r in rows if r["system"]=="undefended"]; defended=[r for r in rows if r["system"]=="defended"]
    review_rows=[r for r in defended if "policy_recommendation" in r]
    review_summary={"mode":"not_run","cases":0,"accuracy_pct":None,"model_calls":0,"input_tokens":0,"output_tokens":0,"estimated_cost_usd":0.0}
    if review_rows:
        usage=reviewer.usage_summary() if hasattr(reviewer,"usage_summary") else {"model_calls":getattr(reviewer,"calls",len(review_rows)),"input_tokens":0,"output_tokens":0,"estimated_cost_usd":0.0}
        review_summary={"mode":"openai","cases":len(review_rows),"accuracy_pct":_pct(sum(r["recommendation_correct"] for r in review_rows),len(review_rows)),**usage}
    summary={"project":"Secure Interoperable Agent Gateway","result_status":"measured","test_cases":len(test),"undefended":_summary(undefended,mapping),"defended":_summary(defended,mapping),"policy_review":review_summary,"runtime_seconds":time.perf_counter()-started}
    samples={"blocked":[r for r in defended if r["status"].startswith("blocked")][:6],"attacks":[r for r in undefended if r["attack_succeeded"]][:6],"traces":defended[:2]}
    (output_dir/"project7_case_results.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n",encoding="utf-8"); (output_dir/"project7_final_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8"); (output_dir/"project7_representative_samples.json").write_text(json.dumps(samples,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return summary
