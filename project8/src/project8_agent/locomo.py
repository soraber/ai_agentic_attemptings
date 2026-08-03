from __future__ import annotations

import hashlib,json,re,statistics,time
from pathlib import Path
from typing import Any

from pydantic import BaseModel,ConfigDict,Field

from .config import Project8Config
from .evaluation import token_f1
from .local_models import TransformersAnswerBackend, extract_json_object


class GeneratedAnswer(BaseModel):
    model_config=ConfigDict(extra="forbid")
    answer:str
    evidence_ids:list[str]=Field(default_factory=list)
    abstained:bool=False


ABSTENTION_PHRASES=("cannot determine","can't determine","does not contain","doesn't contain","not enough","not mentioned","not provided","missing","unsupported","conflict","unknown")


def normalize_local_answer(payload:dict[str,Any])->GeneratedAnswer:
    """Repair common open-model JSON type errors before strict validation."""
    raw_answer=payload.get("answer","")
    answer=raw_answer if isinstance(raw_answer,str) else str(raw_answer or "")
    raw_evidence=payload.get("evidence_ids",[])
    if isinstance(raw_evidence,str): evidence_ids=[raw_evidence]
    elif isinstance(raw_evidence,list): evidence_ids=[str(value) for value in raw_evidence if value is not None]
    else: evidence_ids=[]
    raw_abstained=payload.get("abstained",False)
    if isinstance(raw_abstained,bool): abstained=raw_abstained
    elif isinstance(raw_abstained,(int,float)) and raw_abstained in (0,1): abstained=bool(raw_abstained)
    elif isinstance(raw_abstained,str):
        normalized=raw_abstained.strip().lower()
        if normalized in {"true","yes","1"}: abstained=True
        elif normalized in {"false","no","0"}: abstained=False
        else:
            abstained=any(phrase in normalized for phrase in ABSTENTION_PHRASES)
            if not answer and not abstained: answer=raw_abstained.strip()
    else: abstained=False
    if abstained: answer=""
    return GeneratedAnswer(answer=answer,evidence_ids=evidence_ids,abstained=abstained)


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
        self.client=client; self.config=config; self.model_name=config.model; self.cache_path=Path(cache_path); self.cache_path.parent.mkdir(parents=True,exist_ok=True); self.cache=json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}; self.calls=0; self.cache_hits=0; self.input_tokens=0; self.output_tokens=0

    @property
    def estimated_cost_usd(self)->float:
        return (self.input_tokens*self.config.input_price_per_million_usd+self.output_tokens*self.config.output_price_per_million_usd)/1_000_000

    def usage_summary(self)->dict[str,int|float]:
        return {"model_calls":self.calls,"cache_hits":self.cache_hits,"input_tokens":self.input_tokens,"output_tokens":self.output_tokens,"estimated_cost_usd":round(self.estimated_cost_usd,6)}

    def _check_budget(self,prompt:str)->None:
        if self.calls>=self.config.max_model_calls: raise RuntimeError("Project 8 model-call budget exhausted")
        estimated_input_tokens=max(1,(len(prompt)+3)//4)
        projected=((self.input_tokens+estimated_input_tokens)*self.config.input_price_per_million_usd+(self.output_tokens+self.config.max_output_tokens)*self.config.output_price_per_million_usd)/1_000_000
        if projected>self.config.max_estimated_cost_usd: raise RuntimeError("Project 8 estimated API-cost budget exhausted")

    def _record_usage(self,response:object)->None:
        usage=getattr(response,"usage",None)
        if usage is None: return
        getter=usage.get if isinstance(usage,dict) else lambda key,default=0:getattr(usage,key,default)
        self.input_tokens+=int(getter("input_tokens",0) or 0); self.output_tokens+=int(getter("output_tokens",0) or 0)

    def answer(self,sample_id:str,question:str,system:str,context:list[dict[str,str]])->GeneratedAnswer:
        key=hashlib.sha256(json.dumps([self.config.model,sample_id,question,system,context],sort_keys=True).encode()).hexdigest()
        if key in self.cache:
            self.cache_hits+=1
            return GeneratedAnswer.model_validate(self.cache[key])
        prompt={"question":question,"context":context,"instructions":"Answer only from context. Cite dialogue event IDs. Abstain if unsupported or conflicting."}; serialized_prompt=json.dumps(prompt); last_error:Exception|None=None
        for retry in range(self.config.max_retries+1):
            self._check_budget(serialized_prompt); self.calls+=1
            try:
                response=self.client.responses.parse(model=self.config.model,input=serialized_prompt,text_format=GeneratedAnswer,reasoning={"effort":self.config.reasoning_effort},max_output_tokens=self.config.max_output_tokens)
                self._record_usage(response)
                if response.output_parsed is None: raise ValueError("No structured memory answer returned")
                self.cache[key]=response.output_parsed.model_dump(mode="json"); self.cache_path.write_text(json.dumps(self.cache,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return response.output_parsed
            except Exception as exc:
                last_error=exc
                if retry==self.config.max_retries: raise
                time.sleep(0.5*(2**retry))
        raise RuntimeError("Project 8 answerer failed") from last_error


class CachedLocalAnswerer:
    def __init__(self,config:Project8Config,cache_path:str|Path,backend:object|None=None):
        self.config=config; self.model_name=config.local_model; self.backend=backend or TransformersAnswerBackend(config.local_model,config.local_device); self.cache_path=Path(cache_path); self.cache_path.parent.mkdir(parents=True,exist_ok=True); self.cache=json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}; self.cache_hits=0

    def answer(self,sample_id:str,question:str,system:str,context:list[dict[str,str]])->GeneratedAnswer:
        key=hashlib.sha256(json.dumps([self.model_name,sample_id,question,system,context],sort_keys=True).encode()).hexdigest()
        if key in self.cache:
            self.cache_hits+=1
            return GeneratedAnswer.model_validate(self.cache[key])
        raw=self.backend.generate({"question":question,"context":context},self.config.local_max_new_tokens)
        answer=normalize_local_answer(extract_json_object(raw)); self.cache[key]=answer.model_dump(mode="json"); self.cache_path.write_text(json.dumps(self.cache,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return answer

    def usage_summary(self)->dict:
        usage=dict(self.backend.usage_summary()) if hasattr(self.backend,"usage_summary") else {"model_calls":0,"input_tokens":0,"output_tokens":0,"estimated_cost_usd":0.0}
        usage["cache_hits"]=self.cache_hits
        return usage


def _normalize(value:str)->str: return " ".join(re.findall(r"[a-z0-9]+",value.lower()))


def evaluate_locomo(subset_path:str|Path,config:Project8Config,cache_path:str|Path,output_dir:str|Path,lifecycle_summary:dict|None=None,client:object|None=None,answerer:object|None=None,retriever:object|None=None,evaluation_mode:str="locomo_api")->dict:
    subset=json.loads(Path(subset_path).read_text()); answerer=answerer or CachedOpenAIAnswerer(config,cache_path,client); rows=[]; output_dir=Path(output_dir)
    for sample in subset:
        events=conversation_events(sample)
        for index,qa in enumerate(sample["qa"]):
            for system in ["window","episodic","hybrid"]:
                context=retriever.retrieve(events,qa["question"],system,config.working_window_size,config.episodic_top_k) if retriever is not None else retrieve(events,qa["question"],system,config.working_window_size,config.episodic_top_k); answer=answerer.answer(sample["sample_id"],qa["question"],system,context); gold=str(qa["answer"]); evidence=set(qa.get("evidence",[])); rows.append({"sample_id":sample["sample_id"],"qa_index":index,"system":system,"question":qa["question"],"gold":gold,"answer":answer.answer,"exact_match":_normalize(answer.answer)==_normalize(gold),"token_f1":token_f1(answer.answer,gold),"evidence_recall":len(set(answer.evidence_ids)&evidence)/len(evidence) if evidence else 1.0,"context_tokens":sum(len(item["text"].split()) for item in context),"evidence_ids":answer.evidence_ids})
    def summarize(system):
        selected=[r for r in rows if r["system"]==system]; return {"exact_match_pct":100*sum(r["exact_match"] for r in selected)/len(selected),"mean_token_f1":statistics.fmean(r["token_f1"] for r in selected),"mean_evidence_recall":statistics.fmean(r["evidence_recall"] for r in selected),"mean_context_tokens":statistics.fmean(r["context_tokens"] for r in selected)}
    selected_model=getattr(answerer,"model_name",config.model); usage=dict(answerer.usage_summary()); prior_path=output_dir/"project8_final_summary.json"
    if usage.get("cache_hits",0) and prior_path.exists():
        prior=json.loads(prior_path.read_text())
        if prior.get("result_status")=="measured" and prior.get("evaluation_mode")==evaluation_mode and prior.get("model")==selected_model:
            for key in ("model_calls","input_tokens","output_tokens","estimated_cost_usd"):
                usage[key]=prior.get(key,0)+usage.get(key,0)
            usage["usage_source"]="cumulative measured cache population"
    summary={"project":"Long-Term Memory Agent","result_status":"measured","evaluation_mode":evaluation_mode,"qa_items":sum(len(s["qa"]) for s in subset),"window":summarize("window"),"episodic":summarize("episodic"),"hybrid":summarize("hybrid"),"model":selected_model,"retrieval_model":getattr(retriever,"model_name","lexical"),**usage,"deletion_compliance_pct":lifecycle_summary.get("deletion_compliance_pct",0) if lifecycle_summary else 0,"lifecycle_validation":lifecycle_summary}
    output_dir.mkdir(parents=True,exist_ok=True); (output_dir/"project8_case_results.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n",encoding="utf-8"); (output_dir/"project8_final_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8"); samples={"best_hybrid":[r for r in rows if r["system"]=="hybrid" and r["exact_match"]][:5],"hybrid_failures":[r for r in rows if r["system"]=="hybrid" and not r["exact_match"]][:5]}; (output_dir/"project8_representative_samples.json").write_text(json.dumps(samples,indent=2,sort_keys=True)+"\n",encoding="utf-8");
    with (output_dir/"project8_traces.jsonl").open("w",encoding="utf-8") as handle:
        for row in rows: handle.write(json.dumps(row,sort_keys=True)+"\n")
    return summary
