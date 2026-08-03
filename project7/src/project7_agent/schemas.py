from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class AgentCard(BaseModel):
    model_config=ConfigDict(extra="forbid")
    name: str
    version: str
    capabilities: list[str]
    scopes: list[str]


class ToolContract(BaseModel):
    model_config=ConfigDict(extra="forbid")
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    side_effect: bool
    required_scope: str


class A2ATask(BaseModel):
    model_config=ConfigDict(extra="forbid")
    task_id: str
    correlation_id: str
    sender: str
    recipient: str
    action: str
    payload: dict[str, Any]
    status: Literal["submitted","working","completed","failed","blocked"]="submitted"


class GatewayCase(BaseModel):
    model_config=ConfigDict(extra="forbid")
    case_id: str
    category: Literal["benign","incomplete","unauthorized","malicious_document","poisoned_metadata","duplicate","secret_exfiltration","schema_invalid"]
    task: dict[str, Any]
    retrieved_text: str
    tamper_metadata: bool=False
    duplicate_delivery: bool=False
    human_approved: bool=False
    split: Literal["development","test"]


class PolicyRecommendation(BaseModel):
    model_config=ConfigDict(extra="forbid")
    action: Literal["approve","request_clarification","reject"]
    rationale: str=Field(min_length=1,max_length=500)


class GatewayResult(BaseModel):
    model_config=ConfigDict(extra="allow")
    case_id: str
    system: Literal["undefended","defended"]
    status: str
    benign_success: bool
    attack_succeeded: bool
    unauthorized_call: bool
    unsafe_write: bool
    secret_leaked: bool
    duplicate_effects: int
    contract_valid: bool
    trace_complete: bool
    latency_ms: float=Field(ge=0)
    artifact: dict[str,Any]=Field(default_factory=dict)
    trace: list[dict[str,Any]]=Field(default_factory=list)
