from __future__ import annotations

from project4_agent.telemetry import TraceRecorder


def test_trace_recorder_redacts_keys_and_local_user_paths(tmp_path) -> None:
    path = tmp_path / "traces.jsonl"
    trace = TraceRecorder(path)
    trace.emit(
        "test",
        token="sk-" + "exampleplaintextsecret123456789",
        path="/" + "Users/example/private/project",
    )
    text = path.read_text(encoding="utf-8")
    assert "sk-" + "exampleplaintext" not in text
    assert "/" + "Users/example" not in text
    assert text.count("[REDACTED]") == 2
