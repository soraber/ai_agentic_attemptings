"""Local deterministic closed-loop load test, not an API serving benchmark."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .dataset import generate_incidents
from .planners import DeterministicPlanner
from .policy import simulated_operator_decision
from .simulator import ActionExecutor
from .telemetry import TraceRecorder, summarize_node_spans
from .workflow import DurableIncidentWorkflow


def run_load_test(output, concurrency_levels=(1, 4, 8), requests=32):
    if not 1 <= requests <= 128 or any(not 1 <= workers <= 16 for workers in concurrency_levels):
        raise ValueError("Load test exceeds the bounded local experiment")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    all_rows, summaries = [], []
    case = next(case for case in generate_incidents(20260802)
                if case.gold_root_cause.value == "deployment_regression" and not case.requires_escalation)
    for workers in concurrency_levels:
        runtime = output / "runtime" / f"c{workers}"
        runtime.mkdir(parents=True)
        executor = ActionExecutor(runtime / "shared-actions.sqlite")
        def one(index):
            started = time.perf_counter()
            request = case.model_copy(deep=True)
            request.evidence.incident_id = f"load-{workers}-{index}"
            planner = DeterministicPlanner()
            trace = TraceRecorder(runtime / f"trace-{index}.jsonl")
            workflow = DurableIncidentWorkflow(planner, executor, runtime / f"checkpoint-{index}.sqlite", trace)
            error = None
            try:
                paused = workflow.start(request, request.evidence.incident_id)
                if not paused.get("__interrupt__"):
                    raise RuntimeError("Expected approval interrupt")
                plan = planner.plan(request.public_view(), planner.diagnose(request.public_view()))
                final = workflow.resume_approval(request.evidence.incident_id, simulated_operator_decision(plan, request))
                status = final["terminal_status"]
            except Exception as exc:
                status, error = "error", type(exc).__name__
            finally:
                workflow.close()
            return {"request": index, "concurrency": workers, "status": status, "error_type": error,
                    "latency_ms": (time.perf_counter() - started) * 1000, "spans": trace.records}
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(one, range(requests)))
        elapsed = time.perf_counter() - started
        durations = sorted(row["latency_ms"] for row in rows)
        def quantile(q):
            position = (len(durations) - 1) * q
            low = int(position)
            high = min(low + 1, len(durations) - 1)
            return durations[low] + (durations[high] - durations[low]) * (position - low)
        summaries.append({"concurrency": workers, "requests": requests, "seconds": elapsed,
            "throughput_requests_per_second": requests / elapsed,
            "p50_ms": quantile(0.5), "p95_ms": quantile(0.95),
            "resolved": sum(row["status"] == "resolved" for row in rows),
            "effects": executor.count_effects(), "errors": sum(row["error_type"] is not None for row in rows),
            "node_timing": summarize_node_spans([span for row in rows for span in row["spans"]])})
        all_rows.extend(rows)
    summary = {"scope": "local closed-loop deterministic workflow load; includes cold initialization, no API or human wait",
               "latency_scope": "worker entry to workflow completion; excludes pending executor-queue wait",
               "model_calls": 0, "concurrency_runs": summaries}
    (output / "load_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (output / "load_traces.jsonl").open("w") as handle:
        for row in all_rows:
            handle.write(json.dumps(row) + "\n")
    return summary
