from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Protocol

from .config import ExperimentConfig
from .schemas import (
    ActionPlan,
    ActionParameters,
    Diagnosis,
    IncidentCase,
    PlannerUsage,
    Remediation,
    RiskLevel,
    RootCause,
)


ROOT_CAUSE_TO_ACTION = {
    RootCause.DEPLOYMENT_REGRESSION: Remediation.ROLLBACK_DEPLOYMENT,
    RootCause.MEMORY_LEAK: Remediation.RESTART_SERVICE,
    RootCause.CAPACITY_SATURATION: Remediation.SCALE_SERVICE,
    RootCause.DEPENDENCY_OUTAGE: Remediation.OPEN_TICKET,
    RootCause.CONFIGURATION_ERROR: Remediation.ROLLBACK_DEPLOYMENT,
    RootCause.DATABASE_LOCK_CONTENTION: Remediation.OPEN_TICKET,
}


class Planner(Protocol):
    usage: PlannerUsage

    def diagnose(self, evidence: dict[str, Any]) -> Diagnosis: ...

    def plan(self, evidence: dict[str, Any], diagnosis: Diagnosis) -> ActionPlan: ...


def stable_idempotency_key(
    incident_id: str,
    action: str,
    target_service: str,
    parameters: dict[str, Any] | ActionParameters,
) -> str:
    if isinstance(parameters, ActionParameters):
        parameters = parameters.compact()
    payload = json.dumps(
        [incident_id, action, target_service, parameters],
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"p4-{incident_id.lower()}-{digest}"


def action_parameters(action: Remediation, evidence: dict[str, Any]) -> dict[str, Any]:
    if action is Remediation.ROLLBACK_DEPLOYMENT:
        return {"version": evidence["previous_version"]}
    if action is Remediation.RESTART_SERVICE:
        return {"max_unavailable": 1}
    if action is Remediation.SCALE_SERVICE:
        return {"replicas": 4}
    return {"severity": "SEV-1"}


class DeterministicPlanner:
    """A reproducible planner used to isolate workflow reliability from model quality."""

    def __init__(self) -> None:
        self.usage = PlannerUsage()

    def diagnose(self, evidence: dict[str, Any]) -> Diagnosis:
        logs = " ".join(item["message"].lower() for item in evidence["logs"])
        metrics = evidence["metrics"]
        if "downstream=" in logs or "circuit breaker" in logs:
            cause = RootCause.DEPENDENCY_OUTAGE
            refs = ["log-1", "span-1"]
        elif metrics.get("db_lock_wait_ms", 0) > 500:
            cause = RootCause.DATABASE_LOCK_CONTENTION
            refs = ["metric:db_lock_wait_ms", "log-1"]
        elif metrics.get("memory_percent", 0) > 90:
            cause = RootCause.MEMORY_LEAK
            refs = ["metric:memory_percent", "log-2"]
        elif metrics.get("cpu_percent", 0) > 90 and metrics.get("queue_depth", 0) > 100:
            cause = RootCause.CAPACITY_SATURATION
            refs = ["metric:cpu_percent", "metric:queue_depth"]
        elif "configuration bundle changed" in logs or metrics.get("auth_failure_rate", 0) > 0.5:
            cause = RootCause.CONFIGURATION_ERROR
            refs = ["log-1", "metric:auth_failure_rate"]
        else:
            cause = RootCause.DEPLOYMENT_REGRESSION
            refs = ["log-1", "metric:error_rate"]

        return Diagnosis(
            incident_id=evidence["incident_id"],
            target_service=evidence["service"],
            predicted_root_cause=cause,
            confidence=0.94,
            evidence_refs=refs,
            rationale="Deterministic signal precedence matched the strongest observable evidence.",
        )

    def plan(self, evidence: dict[str, Any], diagnosis: Diagnosis) -> ActionPlan:
        action = ROOT_CAUSE_TO_ACTION[diagnosis.predicted_root_cause]
        parameters = action_parameters(action, evidence)
        target = diagnosis.target_service.value
        return ActionPlan(
            incident_id=diagnosis.incident_id,
            action=action.value,
            target_service=target,
            parameters=parameters,
            risk=RiskLevel.HIGH,
            requires_approval=True,
            idempotency_key=stable_idempotency_key(
                diagnosis.incident_id, action.value, target, parameters
            ),
            rationale="Select the least expansive catalog action matching the diagnosis.",
        )


@dataclass
class FrozenPlanner:
    """Replays one decision so both workflow variants receive identical model output."""

    diagnosis: Diagnosis
    action_plan: ActionPlan

    def __post_init__(self) -> None:
        self.usage = PlannerUsage()

    def diagnose(self, evidence: dict[str, Any]) -> Diagnosis:
        if evidence["incident_id"] != self.diagnosis.incident_id:
            raise ValueError("FrozenPlanner received a different incident")
        return self.diagnosis.model_copy(deep=True)

    def plan(self, evidence: dict[str, Any], diagnosis: Diagnosis) -> ActionPlan:
        return self.action_plan.model_copy(deep=True)


class OpenAIPlanner:
    """Responses API planner with structured outputs, retries, and a hard budget guard."""

    def __init__(self, config: ExperimentConfig, client: object | None = None):
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self.client = client
        self.config = config
        self.usage = PlannerUsage()

    def _estimated_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens * self.config.input_usd_per_million
            + output_tokens * self.config.output_usd_per_million
        ) / 1_000_000

    def _check_budget(self) -> None:
        if self.usage.model_calls >= self.config.max_model_calls:
            raise RuntimeError("Project 4 model-call budget exhausted")
        reserved = self._estimated_cost(0, self.config.max_output_tokens)
        if self.usage.estimated_cost_usd + reserved > self.config.max_estimated_cost_usd:
            raise RuntimeError("Project 4 estimated-cost budget would be exceeded")

    def _parse(self, schema: type[Diagnosis] | type[ActionPlan], prompt: str):
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            self._check_budget()
            self.usage.model_calls += 1
            try:
                response = self.client.responses.parse(
                    model=self.config.model,
                    input=[
                        {
                            "role": "system",
                            "content": (
                                "You are a cautious incident-response planner. Use only the "
                                "provided evidence and approved simulated action catalog."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    text_format=schema,
                    reasoning={"effort": self.config.reasoning_effort},
                    max_output_tokens=self.config.max_output_tokens,
                )
                usage = getattr(response, "usage", None)
                input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
                output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
                self.usage.input_tokens += input_tokens
                self.usage.output_tokens += output_tokens
                self.usage.estimated_cost_usd += self._estimated_cost(
                    input_tokens, output_tokens
                )
                parsed = response.output_parsed
                if parsed is None:
                    raise ValueError("Responses API returned no parsed object")
                return parsed
            except Exception as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    break
                time.sleep(0.5 * (2**attempt))
        raise RuntimeError("Structured planner call failed after bounded retries") from last_error

    def diagnose(self, evidence: dict[str, Any]) -> Diagnosis:
        allowed_causes = ", ".join(item.value for item in RootCause)
        prompt = (
            "Diagnose this incident. Cite concrete log, metric, or trace IDs. "
            f"Allowed root causes: {allowed_causes}. Evidence:\n"
            + json.dumps(evidence, sort_keys=True)
        )
        return self._parse(Diagnosis, prompt)

    def plan(self, evidence: dict[str, Any], diagnosis: Diagnosis) -> ActionPlan:
        catalog = {
            "rollback_deployment": {"version": evidence["previous_version"]},
            "restart_service": {"max_unavailable": 1},
            "scale_service": {"replicas": "integer 2..8"},
            "open_ticket": {"severity": "SEV-1 or SEV-2"},
        }
        prompt = (
            "Create exactly one minimal simulated remediation. Approval is mandatory. "
            "Use the incident service as target. The idempotency key must be a stable, "
            "non-secret identifier of at least 12 characters.\nDiagnosis:\n"
            + diagnosis.model_dump_json()
            + "\nCatalog:\n"
            + json.dumps(catalog, sort_keys=True)
            + "\nEvidence:\n"
            + json.dumps(evidence, sort_keys=True)
        )
        plan = self._parse(ActionPlan, prompt)
        plan.idempotency_key = stable_idempotency_key(
            plan.incident_id, plan.action, plan.target_service, plan.parameters
        )
        return plan


def freeze_case_decision(planner: Planner, case: IncidentCase) -> FrozenPlanner:
    evidence = case.public_view()
    diagnosis = planner.diagnose(evidence)
    action_plan = planner.plan(evidence, diagnosis)
    return FrozenPlanner(diagnosis=diagnosis, action_plan=action_plan)
