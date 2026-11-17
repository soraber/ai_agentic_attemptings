"""Local, process-separated synthetic action service over bounded JSON stdin/stdout.

This is a recovery test boundary, not network authentication or an OS sandbox.
Only the fixture controller can request fault injection; no model is given this API.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .schemas import ActionPlan, ExecutionResult
from .simulator import ActionExecutor, ToolTimeout


class UnknownActionOutcome(ToolTimeout):
    """The caller lacks acknowledgement and must reconcile before another write."""


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: Literal["lookup", "execute", "compensate"]
    plan: ActionPlan
    force_failure: bool = False
    crash_after_commit: bool = False
    effect_id: str | None = None


class ProcessActionClient:
    def __init__(self, database_path: str | Path, timeout_seconds: float = 10):
        self.database_path = Path(database_path)
        self.timeout_seconds = timeout_seconds
        self.observed_unknown_outcomes = 0
        self.reconciled_outcomes = 0

    def _rpc(self, request: Request):
        data = request.model_dump_json()
        if len(data.encode()) > 65536: raise ValueError("Action request exceeds byte limit")
        env = {"PATH": os.defpath, "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
               "PYTHONDONTWRITEBYTECODE": "1"}
        try:
            result = subprocess.run([sys.executable, "-m", "project4_agent.action_service", str(self.database_path)],
                input=data, text=True, capture_output=True, env=env, timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            raise UnknownActionOutcome("Action service timed out; outcome is unknown") from exc
        if result.returncode == 2:
            raise PermissionError("Action service rejected the contract or action binding")
        if result.returncode or len(result.stdout.encode()) > 65536:
            raise UnknownActionOutcome("Action acknowledgement was lost")
        try:
            payload = json.loads(result.stdout)
            return ExecutionResult.model_validate(payload) if payload is not None else None
        except (ValueError, TypeError) as exc:
            raise UnknownActionOutcome("Action acknowledgement was malformed") from exc

    def reconcile(self, plan):
        return self._rpc(Request(operation="lookup", plan=plan))

    def execute(self, plan, *, idempotent=True, inject_crash_after_commit=False,
                force_failure=False, simulate_timeout=False):
        if not idempotent: raise PermissionError("Process service requires idempotent writes")
        if simulate_timeout: raise ToolTimeout("Synthetic pre-request timeout")
        previous = self.reconcile(plan)
        if previous is not None: return previous
        try:
            return self._rpc(Request(operation="execute", plan=plan,
                force_failure=force_failure, crash_after_commit=inject_crash_after_commit))
        except UnknownActionOutcome:
            self.observed_unknown_outcomes += 1
            confirmed = self.reconcile(plan)
            if confirmed is None:
                raise UnknownActionOutcome("No committed outcome confirmed; no blind write retry")
            self.reconciled_outcomes += 1
            return confirmed

    def compensate(self, plan, effect_id):
        # Compensation has its own persisted idempotency key in the action service.
        return self._rpc(Request(operation="compensate", plan=plan, effect_id=effect_id))


def main():
    raw = sys.stdin.buffer.read(65537)
    try:
        if len(raw) > 65536: raise ValueError("Request too large")
        request = Request.model_validate_json(raw)
        executor = ActionExecutor(Path(sys.argv[1]))
        if request.operation == "lookup":
            result = executor.reconcile(request.plan)
        elif request.operation == "compensate":
            result = executor.compensate(request.plan, request.effect_id)
        else:
            result = executor.execute(request.plan, idempotent=True, force_failure=request.force_failure)
            if request.crash_after_commit: os._exit(73)
        print(result.model_dump_json() if result is not None else "null", flush=True)
    except (ValueError, PermissionError):
        print('{"error":"request_rejected"}', flush=True)
        raise SystemExit(2)
    except Exception:
        print('{"error":"outcome_unknown"}', flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
