from __future__ import annotations

import json, os
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field


class Project7Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str = "project7"
    seed: int = 20260802
    model: str = "gpt-5.6-luna"
    reasoning_effort: str = "low"
    development_case_count: int = 8
    test_case_count: int = 32
    max_model_calls: int = Field(default=160, ge=1)
    max_output_tokens: int = Field(default=500, ge=64)
    max_retries: int = Field(default=2, ge=0, le=5)
    max_estimated_cost_usd: float = Field(default=6, ge=0)


def load_config(path: str | Path) -> Project7Config:
    payload=json.loads(Path(path).read_text())
    if os.getenv("PROJECT7_MODEL"): payload["model"]=os.environ["PROJECT7_MODEL"]
    return Project7Config.model_validate(payload)
