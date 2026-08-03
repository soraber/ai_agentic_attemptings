from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .schemas import (
    IncidentCase,
    IncidentEvidence,
    LogEvent,
    Remediation,
    RootCause,
    ServiceName,
    TraceSpan,
)


SERVICES = list(ServiceName)
ARCHETYPES: list[tuple[RootCause, Remediation, bool]] = [
    (RootCause.DEPLOYMENT_REGRESSION, Remediation.ROLLBACK_DEPLOYMENT, False),
    (RootCause.MEMORY_LEAK, Remediation.RESTART_SERVICE, False),
    (RootCause.CAPACITY_SATURATION, Remediation.SCALE_SERVICE, False),
    (RootCause.DEPENDENCY_OUTAGE, Remediation.OPEN_TICKET, True),
    (RootCause.CONFIGURATION_ERROR, Remediation.ROLLBACK_DEPLOYMENT, False),
    (RootCause.DATABASE_LOCK_CONTENTION, Remediation.OPEN_TICKET, True),
]

DEPENDENCY_GRAPH = {
    "gateway": ["checkout"],
    "checkout": ["payments", "inventory"],
    "payments": ["external-bank"],
    "inventory": ["warehouse-db"],
    "external-bank": [],
    "warehouse-db": [],
}


def _evidence_for(
    incident_id: str,
    service: ServiceName,
    cause: RootCause,
    index: int,
) -> IncidentEvidence:
    deployed = f"2026.08.{index % 9 + 1}.{index % 4 + 1}"
    previous = f"2026.07.{20 + index % 8}.{index % 3 + 1}"
    base_time = datetime(2026, 8, 1, 14, 0, tzinfo=timezone.utc) + timedelta(minutes=7 * index)

    metrics = {
        "error_rate": 0.02,
        "p95_latency_ms": 180.0,
        "cpu_percent": 42.0,
        "memory_percent": 51.0,
        "queue_depth": 8.0,
        "auth_failure_rate": 0.01,
        "db_lock_wait_ms": 4.0,
    }
    logs: list[LogEvent]
    traces: list[TraceSpan]
    summary: str

    if cause is RootCause.DEPLOYMENT_REGRESSION:
        metrics.update(error_rate=0.31, p95_latency_ms=1850.0)
        summary = f"{service.value} errors rose immediately after deployment {deployed}."
        logs = [
            LogEvent(event_id="log-1", level="INFO", message=f"deployed version={deployed}"),
            LogEvent(event_id="log-2", level="ERROR", message="response serialization failed after release"),
        ]
        traces = [TraceSpan(span_id="span-1", operation="handle_request", status="error", duration_ms=1840.0)]
    elif cause is RootCause.MEMORY_LEAK:
        metrics.update(memory_percent=96.0, p95_latency_ms=820.0)
        summary = f"{service.value} memory grows steadily until workers are killed."
        logs = [
            LogEvent(event_id="log-1", level="WARN", message="heap usage increased for 45 consecutive minutes"),
            LogEvent(event_id="log-2", level="ERROR", message="worker terminated by out-of-memory guard"),
        ]
        traces = [TraceSpan(span_id="span-1", operation="background_worker", status="error", duration_ms=790.0)]
    elif cause is RootCause.CAPACITY_SATURATION:
        metrics.update(cpu_percent=98.0, queue_depth=340.0, p95_latency_ms=1410.0)
        summary = f"{service.value} is healthy but cannot keep up with a traffic spike."
        logs = [
            LogEvent(event_id="log-1", level="WARN", message="request queue above saturation threshold"),
            LogEvent(event_id="log-2", level="INFO", message="all workers busy; no application errors detected"),
        ]
        traces = [TraceSpan(span_id="span-1", operation="queue_wait", status="ok", duration_ms=1280.0)]
    elif cause is RootCause.DEPENDENCY_OUTAGE:
        dependency = DEPENDENCY_GRAPH[service.value][0] if DEPENDENCY_GRAPH[service.value] else "external-service"
        metrics.update(error_rate=0.48, p95_latency_ms=2200.0)
        summary = f"{service.value} fails while calling downstream dependency {dependency}."
        logs = [
            LogEvent(event_id="log-1", level="ERROR", message=f"downstream={dependency} returned HTTP 503"),
            LogEvent(event_id="log-2", level="WARN", message="circuit breaker opened after repeated failures"),
        ]
        traces = [
            TraceSpan(
                span_id="span-1",
                operation=f"call_{dependency}",
                status="error",
                duration_ms=2150.0,
                attributes={"http.status_code": 503},
            )
        ]
    elif cause is RootCause.CONFIGURATION_ERROR:
        metrics.update(error_rate=0.38, auth_failure_rate=0.71)
        summary = f"{service.value} rejects valid requests after a configuration rollout."
        logs = [
            LogEvent(event_id="log-1", level="INFO", message="configuration bundle changed without binary deployment"),
            LogEvent(event_id="log-2", level="ERROR", message="token audience does not match configured audience"),
        ]
        traces = [TraceSpan(span_id="span-1", operation="authorize", status="error", duration_ms=22.0)]
    else:
        metrics.update(db_lock_wait_ms=1890.0, p95_latency_ms=2050.0)
        summary = f"{service.value} requests wait on a database lock held by another transaction."
        logs = [
            LogEvent(event_id="log-1", level="WARN", message="transaction waiting on row lock beyond threshold"),
            LogEvent(event_id="log-2", level="ERROR", message="deadlock detector selected request as victim"),
        ]
        traces = [TraceSpan(span_id="span-1", operation="database_query", status="error", duration_ms=1980.0)]

    return IncidentEvidence(
        incident_id=incident_id,
        service=service,
        started_at=base_time.isoformat(),
        summary=summary,
        deployed_version=deployed,
        previous_version=previous,
        logs=logs,
        metrics=metrics,
        traces=traces,
        dependency_graph=DEPENDENCY_GRAPH,
    )


def generate_incidents(seed: int = 20260802) -> list[IncidentCase]:
    cases: list[IncidentCase] = []
    index = 0
    for service in SERVICES:
        for cause, remediation, escalation in ARCHETYPES:
            index += 1
            incident_id = f"INC-{index:03d}"
            cases.append(
                IncidentCase(
                    evidence=_evidence_for(incident_id, service, cause, index),
                    gold_root_cause=cause,
                    allowed_remediation=remediation,
                    requires_escalation=escalation,
                    force_action_failure=(index % 11 == 0),
                    split="test",
                )
            )

    random.Random(seed).shuffle(cases)
    for position, case in enumerate(cases):
        case.split = "development" if position < 8 else "test"
    return cases


def dataset_bytes(cases: list[IncidentCase]) -> bytes:
    payload = [case.model_dump(mode="json") for case in cases]
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def dataset_sha256(cases: list[IncidentCase]) -> str:
    return hashlib.sha256(dataset_bytes(cases)).hexdigest()


def write_dataset(path: str | Path, seed: int = 20260802) -> tuple[Path, Path, str]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cases = generate_incidents(seed)
    raw = dataset_bytes(cases)
    checksum = hashlib.sha256(raw).hexdigest()
    path.write_bytes(raw)
    checksum_path = path.with_suffix(".sha256")
    checksum_path.write_text(f"{checksum}  {path.name}\n", encoding="utf-8")
    return path, checksum_path, checksum


def load_dataset(path: str | Path, verify_checksum: bool = True) -> list[IncidentCase]:
    path = Path(path)
    raw = path.read_bytes()
    if verify_checksum:
        checksum_path = path.with_suffix(".sha256")
        expected = checksum_path.read_text(encoding="utf-8").split()[0]
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError(f"Dataset checksum mismatch: expected {expected}, got {actual}")
    payload = json.loads(raw)
    return [IncidentCase.model_validate(item) for item in payload]
