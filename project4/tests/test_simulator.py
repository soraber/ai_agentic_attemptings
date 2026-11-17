from __future__ import annotations

import pytest

from project4_agent.dataset import generate_incidents
from project4_agent.planners import DeterministicPlanner
from project4_agent.simulator import ActionExecutor, InjectedCrash


def _plan():
    case = generate_incidents()[0]
    planner = DeterministicPlanner()
    diagnosis = planner.diagnose(case.public_view())
    return case, planner.plan(case.public_view(), diagnosis)


def test_idempotent_replay_after_commit_has_one_effect(tmp_path) -> None:
    case, plan = _plan()
    executor = ActionExecutor(tmp_path / "ledger.sqlite")
    with pytest.raises(InjectedCrash):
        executor.execute(plan, idempotent=True, inject_crash_after_commit=True)
    replay = executor.execute(plan, idempotent=True)
    assert replay.deduplicated
    assert executor.count_effects(case.evidence.incident_id) == 1


def test_stateless_replay_duplicates_effect(tmp_path) -> None:
    case, plan = _plan()
    executor = ActionExecutor(tmp_path / "baseline.sqlite")
    with pytest.raises(InjectedCrash):
        executor.execute(plan, idempotent=False, inject_crash_after_commit=True)
    executor.execute(plan, idempotent=False)
    assert executor.count_effects(case.evidence.incident_id) == 2


def test_compensation_is_itself_idempotent(tmp_path) -> None:
    case, plan = _plan()
    executor = ActionExecutor(tmp_path / "compensation.sqlite")
    failed = executor.execute(plan, idempotent=True, force_failure=True)
    first = executor.compensate(plan, failed.effect_id)
    replay = executor.compensate(plan, failed.effect_id)
    assert first.status == "compensated"
    assert replay.deduplicated
    assert executor.count_effects(case.evidence.incident_id) == 2


def test_concurrent_deliveries_have_one_committed_effect(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    case, plan = _plan()
    executor = ActionExecutor(tmp_path / "concurrent.sqlite")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: executor.execute(plan, idempotent=True), range(8)))
    assert executor.count_effects() == 1
    assert sum(result.deduplicated for result in results) == 7
    with pytest.raises(PermissionError):
        executor.execute(plan.model_copy(update={"target_service":"different"}), idempotent=True)


def test_replay_after_real_process_exit(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    _, plan = _plan()
    ledger = tmp_path / "process.sqlite"
    ActionExecutor(ledger)
    script = "from project4_agent.schemas import ActionPlan\nfrom project4_agent.simulator import ActionExecutor\nimport os,sys\nActionExecutor(sys.argv[1]).execute(ActionPlan.model_validate_json(sys.argv[2]),idempotent=True)\nos._exit(73)"
    env={"PATH":os.defpath,"PYTHONPATH":str(Path(__file__).resolve().parents[1]/"src"),"PYTHONDONTWRITEBYTECODE":"1"}
    process=subprocess.run([sys.executable,"-c",script,str(ledger),plan.model_dump_json()],env=env,timeout=20)
    assert process.returncode==73
    executor=ActionExecutor(ledger)
    assert executor.execute(plan,idempotent=True).deduplicated
    assert executor.count_effects()==1
