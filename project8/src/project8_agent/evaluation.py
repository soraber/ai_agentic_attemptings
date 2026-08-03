from __future__ import annotations
import json,re,statistics
from pathlib import Path
from .memory import MemoryStore
from .schemas import MemoryEvent,MemoryQuery


def token_f1(prediction:str|None,gold:str|None)->float:
    p=re.findall(r"\w+",(prediction or "").lower()); g=re.findall(r"\w+",(gold or "").lower())
    if not p and not g:return 1.0
    if not p or not g:return 0.0
    common=sum(min(p.count(t),g.count(t)) for t in set(p)); precision=common/len(p); recall=common/len(g); return 2*precision*recall/(precision+recall) if common else 0.0


def evaluate_lifecycle(fixture_path:str|Path,database_path:str|Path,output_dir:str|Path)->dict:
    fixture=json.loads(Path(fixture_path).read_text()); store=MemoryStore(database_path); store.reset()
    for item in fixture["events"]: store.ingest(MemoryEvent.model_validate(item))
    for event_id in fixture["delete_event_ids"]: store.delete_event(event_id)
    queries=[MemoryQuery.model_validate(item) for item in fixture["queries"]]; rows=[]
    for query in queries:
        for system in ["window","episodic","hybrid"]:
            answer=store.answer(query,system); row=answer.model_dump(mode="json"); row.update({"gold":query.answer,"exact_match":answer.answer==query.answer and answer.abstained==(query.answer is None),"token_f1":token_f1(answer.answer,query.answer),"evidence_recall":len(set(answer.evidence_ids)&set(query.evidence))/len(query.evidence) if query.evidence else float(answer.abstained)}); rows.append(row)
    def summarize(system):
        selected=[r for r in rows if r["system"]==system]; return {"exact_match_pct":100*sum(r["exact_match"] for r in selected)/len(selected),"mean_token_f1":statistics.fmean(r["token_f1"] for r in selected),"mean_evidence_recall":statistics.fmean(r["evidence_recall"] for r in selected),"mean_context_tokens":statistics.fmean(r["context_tokens"] for r in selected),"median_latency_ms":statistics.median(r["latency_ms"] for r in selected)}
    summary={"project":"Long-Term Memory Agent","result_status":"measured","window":summarize("window"),"episodic":summarize("episodic"),"hybrid":summarize("hybrid"),"deletion_compliance_pct":100*sum(store.deletion_verified(e) for e in fixture["delete_event_ids"])/len(fixture["delete_event_ids"]),"store_stats":store.stats()}
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True); (output_dir/"project8_case_results.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n",encoding="utf-8"); (output_dir/"project8_final_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8"); samples={"corrections":[r for r in rows if r["query_id"]=="Q02"],"conflicts":[r for r in rows if r["query_id"]=="Q03"],"deletions":[r for r in rows if r["query_id"]=="Q04"]}; (output_dir/"project8_representative_samples.json").write_text(json.dumps(samples,indent=2,sort_keys=True)+"\n",encoding="utf-8");
    with (output_dir/"project8_traces.jsonl").open("w",encoding="utf-8") as handle:
        for row in rows: handle.write(json.dumps(row,sort_keys=True)+"\n")
    return summary
