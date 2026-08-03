from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Project6Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = "project6"
    seed: int = 20260802
    model: str = "gpt-5.6-sol"
    reasoning_effort: str = "medium"
    max_patch_attempts: int = Field(default=3, ge=1, le=5)
    max_changed_lines: int = Field(default=30, ge=1, le=200)
    test_timeout_seconds: float = Field(default=20, gt=0)
    max_test_output_chars: int = Field(default=12000, ge=1000)
    max_model_calls: int = Field(default=220, ge=1)
    max_output_tokens: int = Field(default=900, ge=128)
    max_retries: int = Field(default=2, ge=0, le=5)
    max_estimated_cost_usd: float = Field(default=8.0, ge=0)
    input_price_per_million_usd: float = Field(default=5.0, ge=0)
    output_price_per_million_usd: float = Field(default=30.0, ge=0)
    local_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    local_device: str = "cuda"
    local_max_new_tokens: int = Field(default=900, ge=128, le=2048)
    development_case_count: int = 4
    test_case_count: int = 8


def load_config(path: str | Path) -> Project6Config:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if os.getenv("PROJECT6_MODEL"):
        payload["model"] = os.environ["PROJECT6_MODEL"]
    return Project6Config.model_validate(payload)
