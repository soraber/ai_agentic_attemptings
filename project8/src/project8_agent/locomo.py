from __future__ import annotations

import hashlib,json,re,statistics
from pathlib import Path
from typing import Any

from pydantic import BaseModel,ConfigDict,Field

from .config import Project8Config
from .evaluation import token_f1


class GeneratedAnswer(BaseModel):
    model_config=ConfigDict(extra="forbid")
    answer:str
    evidence_ids:list[str]=Field(default_factory=list)
    abstained:bool=False


STOPWORDS={"a","an","the","i","we","you","he","she","they","did","do","does","where","what","when","to","is","are","was","were"}


def _tokens(text:str)->set[str]:
    output=set()
    for token in re.findall(r"[a-z0-9]+",text.lower()):
        if token in STOPWORDS: continue
        if token.endswith("ed") and len(token)>4: token=token[:-2]
        elif token.endswith("e") and len(token)>3: token=token[:-1]
        output.add(token)
    return output


def conversation_events(sample:dict[str,Any])->list[dict[str,str]]:
    conversation=sample["conversation"]; events=[]
    session_keys=sorted((key for key in conversation if re.fullmatch(r"session_\d+",key)),key=lambda key:int(key.split("_")[1]))
    for key in session_keys:
        date=conversation.get(f"{key}_date_time","")
        for turn in conversation.get(key,[]) or []:
            events.append({"event_id":turn["dia_id"],"speaker":turn["speaker"],"text":turn["text"],"timestamp":date,"session":key})
    return events


def retrieve(events:list[dict[str,str]],question:str,system:str,window_size:int=6,top_k:int=5)->list[dict[str,str]]:
    if system=="window": return events[-window_size:]
    query=_tokens(question); scored=[]
    for position,event in enumerate(events):
        values=_tokens(event["text"]); score=len(query&values)/(len(query|values) or 1); recency=position/max(1,len(events)-1)
        combined=score if system=="episodic" else score+.05*recency
        scored.append((combined,position,event))
    return [event for score,_,event in sorted(scored,key=lambda item:(item[0],item[1]),reverse=True)[:top_k] if score>0]


class CachedOpenAIAnswerer:
    def __init__(self,config:Project8Config,cache_path:str|Path,client:object|None=None):
        if client is None:
            from openai import OpenAI

            client=OpenAI()
        self.client=client; self.config=config; self.cache_path=Path(cache_path); self.cache_path.parent.mkdir(parents=True,exist_ok=True); self.cache=json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}; self.calls=0; self.input_tokens=0; self.output_tokens=0
    def answer(self,sample_id:str,question:str,system:str,context:list[dict[str,str]])->GeneratedAnswer:
        key=hashlib.sha256(json.dumps([self.config.model,sample_id,question,system,context],sort_keys=True).encode()).hexdigest()
        if key in self.cache: return GeneratedAnswer.model_validate(self.cache[key])
        if self.calls>=self.config.max_model_calls: raise RuntimeError("Project 8 model-call budget exhausted")
        self.calls+=1; prompt={"question":question,"context":context,"instructions":"Answer only from context. Cite dialogue event IDs. Abstain if unsupported or conflicting."}
        response=self.client.responses.parse(model=self.config.model,input=json.dumps(prompt),text_format=GeneratedAnswer,reasoning={"effort":self.config.reasoning_effort},max_output_tokens=self.config.max_output_tokens)
        if response.output_parsed is None: raise ValueError("No structured memory answer returned")
        usage=getattr(response,"usage",None); self.input_tokens+=int(getattr(usage,"input_tokens",0) or 0); self.output_tokens+=int(getattr(usage,"output_tokens",0) or 0); self.cache[key]=response.output_parsed.model_dump(mode="json"); self.cache_path.write_text(json.dumps(self.cache,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return response.output_parsed


def _normalize(value:str)->str: return " ".join(re.findall(r"[a-z0-9]+",value.lower()))


def evaluate_locomo(subset_path:str|Path,config:Project8Config,cache_path:str|Path,output_dir:str|Path,lifecycle_summary:dict|None=None,client:object|None=None)->dict:
    subset=json.loads(Path(subset_path).read_text()); answerer=CachedOpenAIAnswerer(config,cache_path,client); rows=[]
    for sample in subset:
        events=conversation_events(sample)
        for index,qa in enumerate(sample["qa"]):
            for system in ["window","episodic","hybrid"]:
                context=retrieve(events,qa["question"],system,config.working_window_size,config.episodic_top_k); answer=answerer.answer(sample["sample_id"],qa["question"],system,context); gold=str(qa["answer"]); evidence=set(qa.get("evidence",[])); rows.append({"sample_id":sample["sample_id"],"qa_index":index,"system":system,"question":qa["question"],"gold":gold,"answer":answer.answer,"exact_match":_normalize(answer.answer)==_normalize(gold),"token_f1":token_f1(answer.answer,gold),"evidence_recall":len(set(answer.evidence_ids)&evidence)/len(evidence) if evidence else 1.0,"context_tokens":sum(len(item["text"].split()) for item in context),"evidence_ids":answer.evidence_ids})
    def summarize(system):
        selected=[r for r in rows if r["system"]==system]; return {"exact_match_pct":100*sum(r["exact_match"] for r in selected)/len(selected),"mean_token_f1":statistics.fmean(r["token_f1"] for r in selected),"mean_evidence_recall":statistics.fmean(r["evidence_recall"] for r in selected),"mean_context_tokens":statistics.fmean(r["context_tokens"] for r in selected)}
    summary={"project":"Long-Term Memory Agent","result_status":"measured","evaluation_mode":"locomo_api","qa_items":sum(len(s["qa"]) for s in subset),"window":summarize("window"),"episodic":summarize("episodic"),"hybrid":summarize("hybrid"),"model":config.model,"model_calls":answerer.calls,"input_tokens":answerer.input_tokens,"output_tokens":answerer.output_tokens,"deletion_compliance_pct":lifecycle_summary.get("deletion_compliance_pct",0) if lifecycle_summary else 0,"lifecycle_validation":lifecycle_summary}
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True); (output_dir/"project8_case_results.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n",encoding="utf-8"); (output_dir/"project8_final_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8"); samples={"best_hybrid":[r for r in rows if r["system"]=="hybrid" and r["exact_match"]][:5],"hybrid_failures":[r for r in rows if r["system"]=="hybrid" and not r["exact_match"]][:5]}; (output_dir/"project8_representative_samples.json").write_text(json.dumps(samples,indent=2,sort_keys=True)+"\n",encoding="utf-8");
    with (output_dir/"project8_traces.jsonl").open("w",encoding="utf-8") as handle:
        for row in rows: handle.write(json.dumps(row,sort_keys=True)+"\n")
    return summary
