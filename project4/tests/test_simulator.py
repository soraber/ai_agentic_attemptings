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
