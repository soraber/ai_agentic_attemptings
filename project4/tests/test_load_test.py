from project4_agent.load_test import run_load_test


def test_concurrent_workflow_timing_and_effect_counts(tmp_path):
    summary = run_load_test(tmp_path / "load", concurrency_levels=(1, 2), requests=4)
    assert summary["model_calls"] == 0
    for row in summary["concurrency_runs"]:
        assert row["resolved"] == row["effects"] == 4
        assert row["errors"] == 0
        assert row["p95_ms"] >= row["p50_ms"] > 0
        assert any(node["node"] == "approval" and node["status"] == "interrupted" for node in row["node_timing"])
