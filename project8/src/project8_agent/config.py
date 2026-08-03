from __future__ import annotations
import json,os
from pathlib import Path
from pydantic import BaseModel,ConfigDict,Field


class Project8Config(BaseModel):
    model_config=ConfigDict(extra="forbid")
    project_id:str="project8"; seed:int=20260802; model:str="gpt-5.6-luna"; reasoning_effort:str="low"
    working_window_size:int=Field(default=6,ge=1); episodic_top_k:int=Field(default=5,ge=1)
    qa_per_conversation:int=40; selected_conversations:int=2; max_model_calls:int=300; max_output_tokens:int=500; max_retries:int=2; max_estimated_cost_usd:float=8
    input_price_per_million_usd:float=Field(default=1.0,ge=0); output_price_per_million_usd:float=Field(default=6.0,ge=0)
    local_model:str="Qwen/Qwen2.5-7B-Instruct"; embedding_model:str="sentence-transformers/all-MiniLM-L6-v2"; local_device:str="cuda"; local_max_new_tokens:int=Field(default=300,ge=64,le=1024)


def load_config(path:str|Path)->Project8Config:
    payload=json.loads(Path(path).read_text());
    if os.getenv("PROJECT8_MODEL"): payload["model"]=os.environ["PROJECT8_MODEL"]
    return Project8Config.model_validate(payload)
