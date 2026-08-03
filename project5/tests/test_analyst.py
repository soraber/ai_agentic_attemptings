from __future__ import annotations

from project5_agent.analyst import DeterministicSQLPlanner, run_baseline, run_governed
from project5_agent.config import Project5Config


def test_governed_agent_repairs_typo(project5_data) -> None:
    database, cases = project5_data
    case = next(case for case in cases if case.category == "repair")
    baseline = run_baseline(case, database)
    governed = run_governed(case, database, Project5Config(), DeterministicSQLPlanner())
    assert baseline.status == "execution_error"
    assert governed.status == "completed"
    assert governed.repaired and governed.result_correct


def test_governed_agent_blocks_pii_while_baseline_leaks(project5_data) -> None:
    database, cases = project5_data
    case = next(case for case in cases if case.category == "pii")
    baseline = run_baseline(case, database)
    governed = run_governed(case, database, Project5Config(), DeterministicSQLPlanner())
    assert baseline.executed and baseline.pii_leaked
    assert governed.status == "blocked_policy" and not governed.executed
