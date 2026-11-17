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


def test_expired_or_mismatched_approval_cannot_execute(tmp_path):
    case=next(case for case in generate_incidents() if not case.force_action_failure)
    for index, change in enumerate([{"expires_at":0.0},{"plan_digest":"wrong"}]):
        planner=DeterministicPlanner()
        executor=ActionExecutor(tmp_path/f"effects-{index}.sqlite")
        workflow=DurableIncidentWorkflow(planner,executor,tmp_path/f"checkpoints-{index}.sqlite",TraceRecorder(tmp_path/f"trace-{index}.jsonl"))
        decision=_run_until_approval(workflow,case,planner,f"approval-{index}")
        result=workflow.resume_approval(f"approval-{index}",decision.model_copy(update=change))
        workflow.close()
        assert result["terminal_status"]=="rejected_by_operator"
        assert executor.count_effects()==0


def test_checkpoint_recovers_after_whole_workflow_process_exits(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    script = '''
import os,sys
from pathlib import Path
from project4_agent.dataset import generate_incidents
from project4_agent.planners import DeterministicPlanner
from project4_agent.policy import simulated_operator_decision
from project4_agent.simulator import ActionExecutor
from project4_agent.telemetry import TraceRecorder
from project4_agent.workflow import DurableIncidentWorkflow
root=Path(sys.argv[1])
class CrashExecutor(ActionExecutor):
    def execute(self,plan,**kwargs):
        kwargs['inject_crash_after_commit']=False
        super().execute(plan,**kwargs)
        os._exit(73)
case=next(c for c in generate_incidents() if not c.force_action_failure)
planner=DeterministicPlanner()
workflow=DurableIncidentWorkflow(planner,CrashExecutor(root/'effects.sqlite'),root/'checkpoints.sqlite',TraceRecorder(root/'traces.jsonl'))
workflow.start(case,'restart-thread')
evidence=case.public_view()
plan=planner.plan(evidence,planner.diagnose(evidence))
workflow.resume_approval('restart-thread',simulated_operator_decision(plan,case))
'''
    env = {"PATH": os.defpath, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
           "PYTHONDONTWRITEBYTECODE": "1"}
    child = subprocess.run([sys.executable, "-c", script, str(tmp_path)], env=env, timeout=30)
    assert child.returncode == 73
    executor = ActionExecutor(tmp_path / "effects.sqlite")
    workflow = DurableIncidentWorkflow(DeterministicPlanner(), executor,
        tmp_path / "checkpoints.sqlite", TraceRecorder(tmp_path / "traces.jsonl"))
    try:
        result = workflow.recover_after_crash("restart-thread")
        assert result["terminal_status"] == "resolved"
        assert result["execution"]["deduplicated"]
        assert executor.count_effects() == 1
    finally:
        workflow.close()
