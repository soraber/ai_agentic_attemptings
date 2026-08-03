from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ServiceName(str, Enum):
    GATEWAY = "gateway"
    CHECKOUT = "checkout"
    PAYMENTS = "payments"
    INVENTORY = "inventory"


class RootCause(str, Enum):
    DEPLOYMENT_REGRESSION = "deployment_regression"
    MEMORY_LEAK = "memory_leak"
    CAPACITY_SATURATION = "capacity_saturation"
    DEPENDENCY_OUTAGE = "dependency_outage"
    CONFIGURATION_ERROR = "configuration_error"
    DATABASE_LOCK_CONTENTION = "database_lock_contention"


class Remediation(str, Enum):
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    RESTART_SERVICE = "restart_service"
    SCALE_SERVICE = "scale_service"
    OPEN_TICKET = "open_ticket"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LogEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    level: Literal["INFO", "WARN", "ERROR"]
    message: str


class TraceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    span_id: str
    operation: str
    status: Literal["ok", "error"]
    duration_ms: float = Field(ge=0)
    attributes: dict[str, str | int | float | bool] = Field(default_factory=dict)


class IncidentEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str
    service: ServiceName
    started_at: str
    summary: str
    deployed_version: str
    previous_version: str
    logs: list[LogEvent]
    metrics: dict[str, float]
    traces: list[TraceSpan]
    dependency_graph: dict[str, list[str]]


class IncidentCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence: IncidentEvidence
    gold_root_cause: RootCause
    allowed_remediation: Remediation
    requires_escalation: bool
    force_action_failure: bool = False
    split: Literal["development", "test"]

    def public_view(self) -> dict[str, Any]:
        """Return evidence only; hidden labels must never enter the planner prompt."""
        return self.evidence.model_dump(mode="json")


class Diagnosis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str
    target_service: ServiceName
    predicted_root_cause: RootCause
    confidence: float = Field(ge=0, le=1)
    evidence_refs: list[str] = Field(min_length=1, max_length=6)
    rationale: str = Field(min_length=1, max_length=600)


class ActionParameters(BaseModel):
    """Closed action catalog parameters compatible with strict structured output."""

    model_config = ConfigDict(extra="forbid")

    version: str | None = None
    max_unavailable: int | None = None
    replicas: int | None = None
    severity: Literal["SEV-1", "SEV-2"] | None = None
    webhook: str | None = None
    callback_url: str | None = None
    external_url: str | None = None

    def compact(self) -> dict[str, str | int]:
        return self.model_dump(exclude_none=True)


class ActionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str
    action: str
    target_service: str
    parameters: ActionParameters = Field(default_factory=ActionParameters)
    risk: RiskLevel
    requires_approval: bool = True
    idempotency_key: str = Field(min_length=12, max_length=80)
    rationale: str = Field(min_length=1, max_length=600)


class PolicyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    reasons: list[str] = Field(default_factory=list)
    policy_version: str = "project4-policy-v1"


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    reviewer: str = "simulated-operator"
    reason: str


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str
    action: str
    target_service: str
    idempotency_key: str
    effect_id: str | None = None
    status: Literal["completed", "failed", "blocked", "compensated"]
    message: str
    deduplicated: bool = False
    latency_ms: float = Field(ge=0)


class PlannerUsage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


class CaseResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    incident_id: str
    system: Literal["baseline", "durable"]
    predicted_root_cause: str
    planned_action: str
    policy_allowed: bool
    approved: bool | None = None
    terminal_status: str
    crash_injected: bool
    crash_recovered: bool
    duplicate_effects: int
    compensation_used: bool
    trajectory: list[str]
    workflow_latency_ms: float = Field(ge=0)
    error: str | None = None
