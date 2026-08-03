from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class QuestionCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    question: str
    category: Literal["benign", "repair", "pii", "unauthorized", "ambiguous", "injection"]
    gold_sql: str | None
    first_attempt_sql: str | None
    expected_result_hash: str | None
    requested_regions: list[str] = Field(default_factory=list)
    authorized_regions: list[str] = Field(default_factory=list)
    should_execute: bool
    split: Literal["development", "test"]

    def public_view(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "authorized_regions": self.authorized_regions,
        }


class QueryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    intent: str
    selected_tables: list[str]
    requested_regions: list[str] = Field(default_factory=list)
    sql: str
    export_requested: bool = False
    rationale: str


class PolicyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    reasons: list[str]
    parsed_expression: str | None = None
    tables: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)


class QueryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[str]
    rows: list[list[Any]]
    result_hash: str
    masked_cells: int = 0
    latency_ms: float = Field(ge=0)


class AnalystResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    question_id: str
    system: Literal["baseline", "governed"]
    status: str
    sql: str | None
    executed: bool
    policy_allowed: bool | None
    repaired: bool = False
    attempts: int = 0
    result_hash: str | None = None
    result_correct: bool = False
    pii_leaked: bool = False
    latency_ms: float = Field(ge=0)
    error: str | None = None
