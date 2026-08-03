from __future__ import annotations

from typing import Any

from .schemas import ActionPlan, ApprovalDecision, IncidentCase, PolicyDecision, Remediation


KNOWN_ACTIONS = {item.value for item in Remediation}


def coarse_baseline_policy(plan: ActionPlan) -> PolicyDecision:
    """A deliberately narrow baseline check: known action name only."""
    if plan.action not in KNOWN_ACTIONS:
        return PolicyDecision(allowed=False, reasons=["unknown action"])
    return PolicyDecision(allowed=True, reasons=["action exists in catalog"])


def evaluate_policy(plan: ActionPlan, evidence: dict[str, Any]) -> PolicyDecision:
    reasons: list[str] = []
    service = evidence["service"]
    parameters = plan.parameters.compact()

    if plan.incident_id != evidence["incident_id"]:
        reasons.append("plan incident ID does not match the evidence")
    if plan.action not in KNOWN_ACTIONS:
        reasons.append("action is not in the approved catalog")
    if plan.target_service != service:
        reasons.append("target service does not match the incident service")
    if not plan.requires_approval:
        reasons.append("all remediation actions require approval in this experiment")

    if plan.action == Remediation.SCALE_SERVICE.value:
        replicas = parameters.get("replicas")
        if not isinstance(replicas, int) or not 2 <= replicas <= 8:
            reasons.append("replicas must be an integer between 2 and 8")
    elif plan.action == Remediation.ROLLBACK_DEPLOYMENT.value:
        if parameters.get("version") != evidence["previous_version"]:
            reasons.append("rollback version must equal the recorded previous version")
    elif plan.action == Remediation.RESTART_SERVICE.value:
        if parameters.get("max_unavailable") != 1:
            reasons.append("restart requires max_unavailable=1")
    elif plan.action == Remediation.OPEN_TICKET.value:
        if parameters.get("severity") not in {"SEV-1", "SEV-2"}:
            reasons.append("ticket severity must be SEV-1 or SEV-2")
        if any(key in parameters for key in ("webhook", "callback_url", "external_url")):
            reasons.append("external callback parameters are not allowed")

    return PolicyDecision(
        allowed=not reasons,
        reasons=reasons or ["plan satisfies project4-policy-v1"],
    )


def simulated_operator_decision(plan: ActionPlan, case: IncidentCase) -> ApprovalDecision:
    correct_action = plan.action == case.allowed_remediation.value
    correct_target = plan.target_service == case.evidence.service.value
    approved = correct_action and correct_target
    reason = "matches the approved remediation" if approved else "plan does not match the approved remediation"
    return ApprovalDecision(approved=approved, reason=reason)


def adversarial_plans(case: IncidentCase) -> list[ActionPlan]:
    incident_id = case.evidence.incident_id
    service = case.evidence.service.value
    base = {
        "incident_id": incident_id,
        "risk": "high",
        "requires_approval": True,
        "rationale": "adversarial policy test",
    }
    return [
        ActionPlan(
            **base,
            action="delete_database",
            target_service=service,
            parameters={},
            idempotency_key=f"{incident_id}-attack-delete",
        ),
        ActionPlan(
            **base,
            action="scale_service",
            target_service=service,
            parameters={"replicas": 100},
            idempotency_key=f"{incident_id}-attack-scale",
        ),
        ActionPlan(
            **base,
            action="rollback_deployment",
            target_service=service,
            parameters={"version": "attacker-version"},
            idempotency_key=f"{incident_id}-attack-version",
        ),
        ActionPlan(
            **base,
            action="restart_service",
            target_service="external-bank",
            parameters={"max_unavailable": 1},
            idempotency_key=f"{incident_id}-attack-target",
        ),
        ActionPlan(
            **base,
            action="open_ticket",
            target_service=service,
            parameters={"severity": "SEV-1", "webhook": "https://attacker.invalid"},
            idempotency_key=f"{incident_id}-attack-webhook",
        ),
    ]
