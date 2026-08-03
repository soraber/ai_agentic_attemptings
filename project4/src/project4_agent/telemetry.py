from __future__ import annotations

import json
import re
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(re.escape("/" + "Users/") + r"[^/\s]+"),
    re.compile(re.escape("/" + "home/") + r"[^/\s]+"),
)


def redact(value: Any) -> Any:
    """Redact common secret and local-user-path patterns before persistence."""
    if isinstance(value, dict):
        return {str(key): redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if not isinstance(value, str):
        return value
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


class TraceRecorder:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: list[dict[str, Any]] = []

    def emit(self, event: str, **attributes: Any) -> dict[str, Any]:
        record = redact({"timestamp": time.time(), "event": event, **attributes})
        self.records.append(record)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[dict[str, Any]]:
        started = time.perf_counter()
        state = self.emit("span.start", span=name, **attributes)
        try:
            yield state
        except Exception as exc:
            self.emit(
                "span.end",
                span=name,
                status="error",
                error_type=type(exc).__name__,
                duration_ms=(time.perf_counter() - started) * 1000,
                **attributes,
            )
            raise
        else:
            self.emit(
                "span.end",
                span=name,
                status="ok",
                duration_ms=(time.perf_counter() - started) * 1000,
                **attributes,
            )


def configure_local_opentelemetry(service_name: str = "project4-agent") -> object | None:
    """Configure a local in-memory provider when OpenTelemetry is installed."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
    except ImportError:
        return None

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)
