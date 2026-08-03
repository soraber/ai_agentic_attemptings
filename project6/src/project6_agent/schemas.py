from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RepositorySymbol(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    name: str
    kind: Literal["function", "class"]
    line: int
    imports: list[str] = Field(default_factory=list)
    docstring: str | None = None


class PatchProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rationale: str
    unified_diff: str
    targeted_paths: list[str]


class PatchDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    reasons: list[str]
    changed_lines: int = 0
    paths: list[str] = Field(default_factory=list)


class TestOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    returncode: int | None
    timed_out: bool
    duration_seconds: float = Field(ge=0)
    output: str


class RepairResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    bug_id: str
    system: Literal["one_shot", "repair_loop"]
    verified: bool
    attempts: int
    public_passed: bool
    hidden_passed: bool
    overfit_detected: bool
    rollback_verified: bool
    changed_lines: int
    trajectory: list[str]
    latency_seconds: float = Field(ge=0)
    error: str | None = None
