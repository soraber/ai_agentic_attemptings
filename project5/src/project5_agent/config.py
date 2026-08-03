from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Project5Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = "project5"
    seed: int = 20260802
    planner_mode: str = "deterministic"
    model: str = "gpt-5.6-luna"
    reasoning_effort: str = "low"
    development_case_count: int = 10
    test_case_count: int = 40
    max_repair_attempts: int = Field(default=2, ge=0, le=3)
    max_result_rows: int = Field(default=100, ge=1, le=1000)
    authorized_regions: list[str] = ["NA"]
    max_model_calls: int = Field(default=180, ge=1)
    max_output_tokens: int = Field(default=500, ge=64)
    max_retries: int = Field(default=2, ge=0, le=5)
    max_estimated_cost_usd: float = Field(default=6.0, ge=0)
    input_price_per_million_usd: float = Field(default=1.0, ge=0)
    output_price_per_million_usd: float = Field(default=6.0, ge=0)
    local_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    local_device: str = "cuda"
    local_max_new_tokens: int = Field(default=500, ge=64, le=2048)
    schema_top_k: int = Field(default=5, ge=1, le=7)


def load_config(path: str | Path) -> Project5Config:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if os.getenv("PROJECT5_MODEL"):
        payload["model"] = os.environ["PROJECT5_MODEL"]
    if os.getenv("PROJECT5_REASONING_EFFORT"):
        payload["reasoning_effort"] = os.environ["PROJECT5_REASONING_EFFORT"]
    return Project5Config.model_validate(payload)
