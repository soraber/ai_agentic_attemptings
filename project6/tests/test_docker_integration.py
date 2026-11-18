"""Opt-in real-container checks; mock tests cannot establish these boundaries."""
import os
import pytest

from project6_agent.runner import run_tests, sandbox_preflight

pytestmark = pytest.mark.skipif(os.environ.get("PROJECT6_DOCKER_TESTS") != "1",
                                reason="Set PROJECT6_DOCKER_TESTS=1 with a running Docker engine")


def test_real_container_boundary(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "authored-not-a-real-credential")
    probe = '''import os, pathlib, socket
import pytest

def test_boundary():
    assert os.getuid() == 65534
    assert "OPENAI_API_KEY" not in os.environ
    assert "HF_TOKEN" not in os.environ
    assert not pathlib.Path("/var/run/docker.sock").exists()
    assert not pathlib.Path("/Users").exists()
    for path in ["/workspace/forbidden", "/etc/forbidden"]:
        with pytest.raises(OSError):
            pathlib.Path(path).write_text("must not write")
    status = pathlib.Path("/proc/self/status").read_text()
    assert "NoNewPrivs:\\t1" in status
    assert "CapEff:\\t0000000000000000" in status
    assert pathlib.Path("/sys/fs/cgroup/memory.max").read_text().strip() == "536870912"
    assert pathlib.Path("/sys/fs/cgroup/pids.max").read_text().strip() == "64"
    # Docker's VM can expose down tunnel devices; absence of routes is what matters.
    routes = pathlib.Path("/proc/net/route").read_text().splitlines()[1:]
    assert not any(row.split()[0] != "lo" for row in routes if row.split())
    with socket.socket() as connection:
        connection.settimeout(1)
        with pytest.raises(OSError):
            connection.connect(("192.0.2.1", 80))
'''
    (tmp_path / "test_boundary.py").write_text(probe)
    assert sandbox_preflight("project6-test-runner:p0-20261117")["image_id"].startswith("sha256:")
    result = run_tests(tmp_path, ["test_boundary.py"], timeout_seconds=30)
    assert result.passed, result.output
    assert not (tmp_path / "forbidden").exists()


def test_real_container_timeout_and_output_bound(tmp_path):
    (tmp_path / "test_slow.py").write_text("import time\ndef test_slow(): time.sleep(60)\n")
    result = run_tests(tmp_path, ["test_slow.py"], timeout_seconds=2)
    assert result.timed_out
    (tmp_path / "test_loud.py").write_text("def test_loud():\n    print('x'*50000)\n    assert False\n")
    result = run_tests(tmp_path, ["test_loud.py"], max_output_chars=1000, timeout_seconds=30)
    assert not result.passed and not result.timed_out
    assert len(result.output) <= 1000
