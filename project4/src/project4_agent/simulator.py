from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path

from .schemas import ActionPlan, ExecutionResult


class InjectedCrash(RuntimeError):
    """Raised after a committed effect to emulate process loss before acknowledgement."""


class ToolTimeout(TimeoutError):
    """Raised by the simulated action catalog when a timeout is injected."""


class ActionExecutor:
    """A local-only action catalog backed by an auditable SQLite ledger."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS execution_ledger (
                    idempotency_key TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target_service TEXT NOT NULL,
                    status TEXT NOT NULL,
                    effect_id TEXT,
                    result_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS effects (
                    effect_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL,
                    incident_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target_service TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                """
            )

    def reset(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM execution_ledger")
            connection.execute("DELETE FROM effects")

    def count_effects(self, incident_id: str | None = None) -> int:
        query = "SELECT COUNT(*) FROM effects"
        parameters: tuple[str, ...] = ()
        if incident_id is not None:
            query += " WHERE incident_id = ?"
            parameters = (incident_id,)
        with self._connect() as connection:
            return int(connection.execute(query, parameters).fetchone()[0])

    def list_effects(self, incident_id: str | None = None) -> list[dict[str, object]]:
        query = "SELECT * FROM effects"
        parameters: tuple[str, ...] = ()
        if incident_id is not None:
            query += " WHERE incident_id = ?"
            parameters = (incident_id,)
        query += " ORDER BY created_at, effect_id"
        with self._connect() as connection:
            return [dict(row) for row in connection.execute(query, parameters)]

    def execute(
        self,
        plan: ActionPlan,
        *,
        idempotent: bool,
        inject_crash_after_commit: bool = False,
        force_failure: bool = False,
        simulate_timeout: bool = False,
    ) -> ExecutionResult:
        started = time.perf_counter()
        if simulate_timeout:
            raise ToolTimeout(f"simulated timeout for {plan.incident_id}")

        if idempotent:
            prior = self._lookup(plan.idempotency_key)
            if prior is not None:
                payload = json.loads(prior["result_json"])
                payload["deduplicated"] = True
                payload["latency_ms"] = (time.perf_counter() - started) * 1000
                return ExecutionResult.model_validate(payload)

        effect_id = f"effect-{uuid.uuid4().hex[:16]}"
        status = "failed" if force_failure else "completed"
        result = ExecutionResult(
            incident_id=plan.incident_id,
            action=plan.action,
            target_service=plan.target_service,
            idempotency_key=plan.idempotency_key,
            effect_id=effect_id,
            status=status,
            message="simulated action failed" if force_failure else "simulated action completed",
            latency_ms=(time.perf_counter() - started) * 1000,
        )

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """INSERT INTO effects
                   (effect_id, idempotency_key, incident_id, action, target_service, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    effect_id,
                    plan.idempotency_key,
                    plan.incident_id,
                    plan.action,
                    plan.target_service,
                    status,
                    time.time(),
                ),
            )
            if idempotent:
                connection.execute(
                    """INSERT INTO execution_ledger
                       (idempotency_key, incident_id, action, target_service, status,
                        effect_id, result_json, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        plan.idempotency_key,
                        plan.incident_id,
                        plan.action,
                        plan.target_service,
                        status,
                        effect_id,
                        result.model_dump_json(),
                        time.time(),
                    ),
                )

        if inject_crash_after_commit:
            raise InjectedCrash(
                f"injected crash after effect {effect_id} committed for {plan.incident_id}"
            )
        return result

    def compensate(self, plan: ActionPlan, effect_id: str | None) -> ExecutionResult:
        started = time.perf_counter()
        compensation_key = f"{plan.idempotency_key}:compensate"
        prior = self._lookup(compensation_key)
        if prior is not None:
            payload = json.loads(prior["result_json"])
            payload["deduplicated"] = True
            payload["latency_ms"] = (time.perf_counter() - started) * 1000
            return ExecutionResult.model_validate(payload)

        compensation_effect = f"comp-{uuid.uuid4().hex[:16]}"
        result = ExecutionResult(
            incident_id=plan.incident_id,
            action=f"compensate_{plan.action}",
            target_service=plan.target_service,
            idempotency_key=compensation_key,
            effect_id=compensation_effect,
            status="compensated",
            message=f"simulated compensation recorded for {effect_id or 'unknown effect'}",
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """INSERT INTO effects
                   (effect_id, idempotency_key, incident_id, action, target_service, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    compensation_effect,
                    compensation_key,
                    plan.incident_id,
                    result.action,
                    plan.target_service,
                    "compensated",
                    time.time(),
                ),
            )
            connection.execute(
                """INSERT INTO execution_ledger
                   (idempotency_key, incident_id, action, target_service, status,
                    effect_id, result_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    compensation_key,
                    plan.incident_id,
                    result.action,
                    plan.target_service,
                    "compensated",
                    compensation_effect,
                    result.model_dump_json(),
                    time.time(),
                ),
            )
        return result

    def _lookup(self, idempotency_key: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(
                "SELECT * FROM execution_ledger WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
