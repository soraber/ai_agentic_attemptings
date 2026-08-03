from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = "project4"
    seed: int = 20260802
    planner_mode: str = "deterministic"
    model: str = "gpt-5.6-luna"
    reasoning_effort: str = "low"
    max_model_calls: int = Field(default=120, ge=1)
    max_output_tokens: int = Field(default=450, ge=64)
    max_retries: int = Field(default=2, ge=0, le=5)
    max_estimated_cost_usd: float = Field(default=5.0, ge=0)
    input_usd_per_million: float = Field(default=1.0, ge=0)
    output_usd_per_million: float = Field(default=6.0, ge=0)
    development_case_count: int = Field(default=8, ge=1)
    test_case_count: int = Field(default=16, ge=1)
    evaluation_repetitions: int = Field(default=2, ge=1, le=5)
    crash_case_fraction: float = Field(default=0.5, ge=0, le=1)
    tool_timeout_seconds: float = Field(default=5.0, gt=0)
    report_title: str = "Durable Incident-Response Agent"


def load_config(path: str | Path) -> ExperimentConfig:
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    overrides = {
        "model": os.getenv("PROJECT4_MODEL"),
        "reasoning_effort": os.getenv("PROJECT4_REASONING_EFFORT"),
        "input_usd_per_million": os.getenv("PROJECT4_INPUT_USD_PER_MILLION"),
        "output_usd_per_million": os.getenv("PROJECT4_OUTPUT_USD_PER_MILLION"),
    }
    for key, value in overrides.items():
        if value not in (None, ""):
            payload[key] = value

    return ExperimentConfig.model_validate(payload)
