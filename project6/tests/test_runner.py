from __future__ import annotations

from project6_agent.runner import run_tests


def test_runner_reports_pass_and_timeout(buggy_repo) -> None:
    failed = run_tests(buggy_repo, ["test_public.py"])
    assert not failed.passed and not failed.timed_out
    (buggy_repo / "test_slow.py").write_text("import time\n\ndef test_slow():\n    time.sleep(2)\n", encoding="utf-8")
    timeout = run_tests(buggy_repo, ["test_slow.py"], timeout_seconds=0.1)
    assert timeout.timed_out
