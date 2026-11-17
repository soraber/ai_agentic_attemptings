from __future__ import annotations

from project6_agent.runner import run_tests


def test_runner_reports_pass_and_timeout(buggy_repo) -> None:
    failed = run_tests(buggy_repo, ["test_public.py"], backend="trusted_fixture")
    assert not failed.passed and not failed.timed_out
    (buggy_repo / "test_slow.py").write_text("import time\n\ndef test_slow():\n    time.sleep(2)\n", encoding="utf-8")
    timeout = run_tests(buggy_repo, ["test_slow.py"], timeout_seconds=0.1, backend="trusted_fixture")
    assert timeout.timed_out


def test_no_ambient_secret_is_inherited(buggy_repo, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-not-a-real-key")
    (buggy_repo / "test_env.py").write_text(
        "import os\ndef test_env():\n    assert 'OPENAI_API_KEY' not in os.environ\n")
    assert run_tests(buggy_repo, ["test_env.py"], backend="trusted_fixture").passed


def test_container_boundary_and_fail_closed(buggy_repo, monkeypatch):
    import pytest
    from project6_agent.runner import runner_command
    command = runner_command(buggy_repo, ["test_public.py"], "docker", "test-image", "test-name")
    for flag in ["--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--user=65534:65534"]:
        assert flag in command
    assert any("dst=/workspace,readonly" in arg for arg in command)
    monkeypatch.setattr("project6_agent.runner.shutil.which", lambda _: None)
    with pytest.raises(RuntimeError, match="Docker"):
        run_tests(buggy_repo, ["test_public.py"])
    with pytest.raises(PermissionError):
        runner_command(buggy_repo, ["../escape.py"], "docker", "test-image", "test-name")
