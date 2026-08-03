from __future__ import annotations

from project4_agent.evaluation import _summarize_system


def _row(*, crash_injected: bool, crash_recovered: bool, terminal_status: str) -> dict:
    return {
        "crash_injected": crash_injected,
        "crash_recovered": crash_recovered,
        "terminal_status": terminal_status,
        "root_cause_correct": True,
        "remediation_correct": True,
        "duplicate_effects": 0,
        "compensation_used": False,
        "workflow_latency_ms": 1.0,
        "trajectory": ["close"],
    }


def test_crash_recovery_excludes_workflows_stopped_before_execution() -> None:
    rows = [
        _row(crash_injected=True, crash_recovered=True, terminal_status="resolved"),
        _row(
            crash_injected=True,
            crash_recovered=False,
            terminal_status="rejected_by_operator",
        ),
        _row(crash_injected=False, crash_recovered=False, terminal_status="resolved"),
    ]

    summary = _summarize_system(rows)

    assert summary["executed_crash_trials"] == 1
    assert summary["crash_recovery_pct"] == 100.0
