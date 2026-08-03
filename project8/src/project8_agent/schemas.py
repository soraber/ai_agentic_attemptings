from __future__ import annotations
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field


class MemoryEvent(BaseModel):
    model_config=ConfigDict(extra="forbid")
    event_id:str; session_id:str; timestamp:str; speaker:str; text:str


class MemoryQuery(BaseModel):
    model_config=ConfigDict(extra="forbid")
    query_id:str; question:str; fact_key:str|None=None; answer:str|None=None; evidence:list[str]=Field(default_factory=list); system_expectation:str="answer"


class MemoryAnswer(BaseModel):
    model_config=ConfigDict(extra="forbid")
    query_id:str; system:Literal["window","episodic","hybrid"]; answer:str|None; evidence_ids:list[str]; abstained:bool; conflict:bool=False; context_tokens:int=0; latency_ms:float=Field(ge=0)
