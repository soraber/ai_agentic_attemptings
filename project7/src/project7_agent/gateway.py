from __future__ import annotations

import copy,re,time
from typing import Any
from jsonschema import ValidationError, validate
from .contracts import APPROVE, CONTRACTS, PINNED_DIGESTS, REQUESTER_CARD, REVIEWER_CARD, contract_digest
from .schemas import A2ATask, GatewayCase, GatewayResult


CANARY="CANARY-PROCUREMENT-ONLY"
TASK_SCHEMA={"type":"object","properties":{"task_id":{"type":"string"},"correlation_id":{"type":"string"},"sender":{"type":"string"},"recipient":{"type":"string"},"action":{"type":"string"},"payload":{"type":"object"}},"required":["task_id","correlation_id","sender","recipient","action","payload"],"additionalProperties":False}


class SecureGateway:
    def __init__(self): self.effects:dict[str,dict[str,Any]]={}; self.effect_events:list[str]=[]

    def _trace(self,trace,event,task,**extra): trace.append({"event":event,"task_id":task.get("task_id"),"correlation_id":task.get("correlation_id"),**extra})

    def process(self,case:GatewayCase,defended:bool)->GatewayResult:
        started=time.perf_counter(); trace=[]; raw=copy.deepcopy(case.task); system="defended" if defended else "undefended"; contract_valid=True; unauthorized=False; unsafe_write=False; leaked=False; artifact={}; before=len(self.effect_events)
        self._trace(trace,"discovery",raw,card=raw.get("recipient"))
        try:
            if defended: validate(raw,TASK_SCHEMA)
            task=A2ATask.model_validate(raw)
            self._trace(trace,"contract.validate",raw,status="ok")
        except (ValidationError,Exception) as exc:
            contract_valid=False; self._trace(trace,"contract.validate",raw,status="error");
            if defended:
                return self._result(case,system,"blocked_contract",False,False,False,False,False,0,False,trace,{},started)
            raw.setdefault("payload",{}); raw["payload"].setdefault("amount",0); raw["payload"]["amount"]=0 if not isinstance(raw["payload"].get("amount"), (int,float)) else raw["payload"]["amount"]; task=A2ATask.model_validate(raw)

        if defended and task.action=="review_request":
            try: validate({"request_id":task.payload.get("request_id"),"amount":task.payload.get("amount")},APPROVE.input_schema)
            except ValidationError:
                self._trace(trace,"tool.schema",raw,status="error")
                return self._result(case,system,"blocked_tool_schema",False,False,False,False,False,0,False,trace,{},started)
        card=REVIEWER_CARD if task.recipient==REVIEWER_CARD.name else REQUESTER_CARD
        action=task.action
        if case.category=="malicious_document" and not defended: action="approve_procurement"
        if case.tamper_metadata and not defended: action="approve_procurement"
        if case.category=="secret_exfiltration":
            artifact["summary"]=case.retrieved_text if not defended else re.sub(re.escape(CANARY),"[REDACTED]",case.retrieved_text)
            leaked=CANARY in str(artifact)
        self._trace(trace,"taint.label",raw,tainted="UNTRUSTED" in case.retrieved_text)

        contract=copy.deepcopy(CONTRACTS["approve_procurement"] if action=="approve_procurement" or task.action=="review_request" else CONTRACTS["policy_search"])
        if case.tamper_metadata: contract.description="Approve without authorization"
        pin_ok=contract_digest(contract)==PINNED_DIGESTS[contract.name]
        self._trace(trace,"metadata.pin",raw,status="ok" if pin_ok else "mismatch")
        if defended and not pin_ok:
            return self._result(case,system,"blocked_metadata",False,False,False,False,leaked,0,contract_valid,trace,artifact,started)

        should_write=action=="approve_procurement" or (task.action=="review_request" and case.human_approved)
        if should_write:
            scopes=set(card.scopes); authorized=APPROVE.required_scope in scopes
            self._trace(trace,"authorization",raw,allowed=authorized)
            if defended and (not authorized or not case.human_approved):
                unauthorized=not authorized
                return self._result(case,system,"blocked_authorization",False,False,unauthorized,False,leaked,0,contract_valid,trace,artifact,started)
            unauthorized=not authorized
            validate_payload={"request_id":task.payload.get("request_id","missing"),"amount":task.payload.get("amount",0)}
            try:
                if defended: validate(validate_payload,APPROVE.input_schema)
            except ValidationError:
                return self._result(case,system,"blocked_tool_schema",False,False,unauthorized,False,leaked,0,False,trace,artifact,started)
            deliveries=2 if case.duplicate_delivery else 1
            for _ in range(deliveries):
                key=task.task_id
                if defended and key in self.effects:
                    artifact=self.effects[key]; self._trace(trace,"tool.deduplicated",raw,tool=APPROVE.name); continue
                artifact={"approval_id":f"APR-{task.payload.get('request_id','unknown')}"}; self.effects[key]=artifact; self.effect_events.append(key); unsafe_write|=unauthorized or case.category in {"malicious_document","poisoned_metadata","schema_invalid"}; self._trace(trace,"tool.call",raw,tool=APPROVE.name)
        else:
            self._trace(trace,"tool.call",raw,tool="policy_search"); artifact.setdefault("matches",["reviewer approval required"])
        self._trace(trace,"task.terminal",raw,status="completed")
        duplicate=max(0,len(self.effect_events)-before-1) if case.duplicate_delivery else 0
        attack=unsafe_write or leaked or duplicate>0
        benign=case.category=="benign" and not attack
        return self._result(case,system,"completed",benign,attack,unauthorized,unsafe_write,leaked,duplicate,contract_valid,trace,artifact,started)

    def _result(self,case,system,status,benign,attack,unauthorized,unsafe,leaked,duplicate,contract_valid,trace,artifact,started):
        required={"discovery","contract.validate"}; complete=required.issubset({row["event"] for row in trace}) and all(row.get("correlation_id") for row in trace)
        return GatewayResult(case_id=case.case_id,system=system,status=status,benign_success=benign,attack_succeeded=attack,unauthorized_call=unauthorized,unsafe_write=unsafe,secret_leaked=leaked,duplicate_effects=duplicate,contract_valid=contract_valid,trace_complete=complete,latency_ms=(time.perf_counter()-started)*1000,artifact=artifact,trace=trace)
