from __future__ import annotations

import pytest

from project4_agent.dataset import generate_incidents
from project4_agent.planners import DeterministicPlanner
from project4_agent.policy import simulated_operator_decision
from project4_agent.simulator import ActionExecutor, InjectedCrash
from project4_agent.telemetry import TraceRecorder
from project4_agent.workflow import DurableIncidentWorkflow


def _run_until_approval(workflow, case, planner, thread_id, **kwargs):
    paused = workflow.start(case, thread_id, **kwargs)
    assert paused.get("__interrupt__")
    evidence = case.public_view()
    plan = planner.plan(evidence, planner.diagnose(evidence))
    return simulated_operator_decision(plan, case)


def test_graph_pauses_and_resumes_same_thread(tmp_path) -> None:
    case = next(case for case in generate_incidents() if not case.force_action_failure)
    planner = DeterministicPlanner()
    executor = ActionExecutor(tmp_path / "effects.sqlite")
    workflow = DurableIncidentWorkflow(
        planner,
        executor,
        tmp_path / "checkpoints.sqlite",
        TraceRecorder(tmp_path / "traces.jsonl"),
    )
    decision = _run_until_approval(workflow, case, planner, "approval-thread")
    final = workflow.resume_approval("approval-thread", decision)
    workflow.close()
    assert final["terminal_status"] == "resolved"
    assert final["trajectory"] == [
        "diagnose",
        "verify",
        "plan",
        "policy",
        "approval",
        "execute",
        "validate",
        "close",
    ]


def test_graph_recovers_post_commit_crash_without_duplicate(tmp_path) -> None:
    case = next(case for case in generate_incidents() if not case.force_action_failure)
    planner = DeterministicPlanner()
    executor = ActionExecutor(tmp_path / "effects.sqlite")
    workflow = DurableIncidentWorkflow(
        planner,
        executor,
        tmp_path / "checkpoints.sqlite",
        TraceRecorder(tmp_path / "traces.jsonl"),
    )
    decision = _run_until_approval(
        workflow, case, planner, "crash-thread", inject_crash=True
    )
    with pytest.raises(InjectedCrash):
        workflow.resume_approval("crash-thread", decision)
    final = workflow.recover_after_crash("crash-thread")
    workflow.close()
    assert final["terminal_status"] == "resolved"
    assert final["execution"]["deduplicated"] is True
    assert executor.count_effects(case.evidence.incident_id) == 1
