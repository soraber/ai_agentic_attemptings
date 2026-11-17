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


def test_node_percentiles_and_interrupt_spans(tmp_path):
    import pytest
    from project4_agent.telemetry import summarize_node_spans
    trace = TraceRecorder(tmp_path / "spans.jsonl")
    with pytest.raises(KeyboardInterrupt):
        with trace.span("workflow.approval"):
            raise KeyboardInterrupt()
    assert trace.records[-1]["status"] == "interrupted"
    result = summarize_node_spans([{"event": "span.end", "span": "workflow.plan", "status": "ok", "duration_ms": value}
                                   for value in [1, 2, 3, 4]])
    assert result[0]["p50_ms"] == 2.5
    assert result[0]["p95_ms"] == pytest.approx(3.85)
