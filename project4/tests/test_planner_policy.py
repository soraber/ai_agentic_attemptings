from __future__ import annotations

from project4_agent.dataset import generate_incidents
from project4_agent.planners import DeterministicPlanner
from project4_agent.policy import adversarial_plans, coarse_baseline_policy, evaluate_policy


def test_deterministic_planner_recovers_all_controlled_labels() -> None:
    planner = DeterministicPlanner()
    for case in generate_incidents():
        evidence = case.public_view()
        diagnosis = planner.diagnose(evidence)
        plan = planner.plan(evidence, diagnosis)
        assert diagnosis.predicted_root_cause == case.gold_root_cause
        assert plan.action == case.allowed_remediation.value
        assert evaluate_policy(plan, evidence).allowed


def test_strict_policy_blocks_all_adversarial_plans() -> None:
    case = generate_incidents()[0]
    attacks = adversarial_plans(case)
    assert len(attacks) == 5
    assert sum(coarse_baseline_policy(plan).allowed for plan in attacks) == 4
    assert not any(evaluate_policy(plan, case.public_view()).allowed for plan in attacks)


def test_strict_policy_binds_plan_to_incident_identity() -> None:
    case = generate_incidents()[0]
    planner = DeterministicPlanner()
    diagnosis = planner.diagnose(case.public_view())
    plan = planner.plan(case.public_view(), diagnosis)
    plan.incident_id = "INC-WRONG"
    decision = evaluate_policy(plan, case.public_view())
    assert not decision.allowed
    assert any("incident ID" in reason for reason in decision.reasons)
