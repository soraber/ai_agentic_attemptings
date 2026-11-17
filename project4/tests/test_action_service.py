import pytest

from project4_agent.action_service import ProcessActionClient, UnknownActionOutcome
from project4_agent.dataset import generate_incidents
from project4_agent.planners import DeterministicPlanner
from project4_agent.policy import simulated_operator_decision
from project4_agent.simulator import ActionExecutor
from project4_agent.telemetry import TraceRecorder
from project4_agent.workflow import DurableIncidentWorkflow


def plan_case():
    case = next(c for c in generate_incidents() if not c.force_action_failure)
    planner = DeterministicPlanner()
    return case, planner.plan(case.public_view(), planner.diagnose(case.public_view()))


def test_process_death_after_commit_is_reconciled_before_retry(tmp_path):
    case, plan = plan_case()
    client = ProcessActionClient(tmp_path / "service.sqlite")
    result = client.execute(plan, inject_crash_after_commit=True)
    assert result.deduplicated
    assert client.observed_unknown_outcomes == client.reconciled_outcomes == 1
    restarted = ProcessActionClient(tmp_path / "service.sqlite")
    assert restarted.execute(plan).effect_id == result.effect_id
    assert ActionExecutor(tmp_path / "service.sqlite").count_effects() == 1
    with pytest.raises(PermissionError):
        restarted.execute(plan.model_copy(update={"target_service": "different"}))


def test_workflow_uses_separate_action_service(tmp_path):
    case, plan = plan_case()
    client = ProcessActionClient(tmp_path / "service.sqlite")
    workflow = DurableIncidentWorkflow(DeterministicPlanner(), client,
        tmp_path / "checkpoint.sqlite", TraceRecorder(tmp_path / "trace.jsonl"))
    try:
        assert workflow.start(case, "remote", inject_crash=True).get("__interrupt__")
        result = workflow.resume_approval("remote", simulated_operator_decision(plan, case))
        assert result["terminal_status"] == "resolved"
        assert result["execution"]["deduplicated"]
    finally:
        workflow.close()


def test_unknown_outcome_without_confirmation_is_not_blindly_retried(tmp_path, monkeypatch):
    _, plan = plan_case()
    client = ProcessActionClient(tmp_path / "service.sqlite")
    calls = []
    def rpc(request):
        calls.append(request.operation)
        if request.operation == "execute": raise UnknownActionOutcome("no acknowledgement")
        return None
    monkeypatch.setattr(client, "_rpc", rpc)
    with pytest.raises(UnknownActionOutcome, match="No committed"):
        client.execute(plan)
    assert calls == ["lookup", "execute", "lookup"]
