from __future__ import annotations

import operator
import sqlite3
import time
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .planners import Planner
from .policy import coarse_baseline_policy, evaluate_policy
from .schemas import (
    ActionPlan,
    ApprovalDecision,
    Diagnosis,
    ExecutionResult,
    IncidentCase,
    PolicyDecision,
)
from .simulator import ActionExecutor, InjectedCrash, ToolTimeout
from .telemetry import TraceRecorder


class AgentState(TypedDict, total=False):
    evidence: dict[str, Any]
    diagnosis: dict[str, Any]
    plan: dict[str, Any]
    policy: dict[str, Any]
    approval: dict[str, Any]
    execution: dict[str, Any]
    compensation: dict[str, Any]
    force_action_failure: bool
    inject_crash: bool
    simulate_timeout: bool
    terminal_status: str
    error: str | None
    trajectory: Annotated[list[str], operator.add]


class DurableIncidentWorkflow:
    """Checkpointed incident-response graph with approval and idempotent effects."""

    def __init__(
        self,
        planner: Planner,
        executor: ActionExecutor,
        checkpoint_path: str | Path,
        trace_recorder: TraceRecorder,
    ):
        self.planner = planner
        self.executor = executor
        self.trace = trace_recorder
        checkpoint_path = Path(checkpoint_path)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self._checkpoint_connection = sqlite3.connect(
            checkpoint_path, check_same_thread=False
        )
        self.checkpointer = SqliteSaver(self._checkpoint_connection)
        self.graph = self._build_graph()

    def close(self) -> None:
        self._checkpoint_connection.close()

    def _record(self, node: str, state: AgentState, **extra: Any) -> None:
        self.trace.emit(
            "workflow.node",
            system="durable",
            node=node,
            incident_id=state["evidence"]["incident_id"],
            **extra,
        )

    def _diagnose(self, state: AgentState) -> AgentState:
        diagnosis = self.planner.diagnose(state["evidence"])
        self._record("diagnose", state, prediction=diagnosis.predicted_root_cause.value)
        return {"diagnosis": diagnosis.model_dump(mode="json"), "trajectory": ["diagnose"]}

    def _verify(self, state: AgentState) -> AgentState:
        diagnosis = Diagnosis.model_validate(state["diagnosis"])
        valid_refs = {
            item["event_id"] for item in state["evidence"]["logs"]
        } | {item["span_id"] for item in state["evidence"]["traces"]}
        valid_refs |= {f"metric:{key}" for key in state["evidence"]["metrics"]}
        grounded = bool(set(diagnosis.evidence_refs) & valid_refs)
        identity_matches = (
            diagnosis.incident_id == state["evidence"]["incident_id"]
            and diagnosis.target_service.value == state["evidence"]["service"]
        )
        self._record("verify", state, grounded=grounded)
        if not grounded or not identity_matches:
            return {
                "terminal_status": "blocked_verification",
                "error": "diagnosis identity mismatch or no available evidence citation",
                "trajectory": ["verify"],
            }
        return {"trajectory": ["verify"]}

    def _plan(self, state: AgentState) -> AgentState:
        plan = self.planner.plan(
            state["evidence"], Diagnosis.model_validate(state["diagnosis"])
        )
        self._record("plan", state, action=plan.action)
        return {"plan": plan.model_dump(mode="json"), "trajectory": ["plan"]}

    def _policy(self, state: AgentState) -> AgentState:
        decision = evaluate_policy(ActionPlan.model_validate(state["plan"]), state["evidence"])
        self._record("policy", state, allowed=decision.allowed)
        return {"policy": decision.model_dump(mode="json"), "trajectory": ["policy"]}

    def _approval(self, state: AgentState) -> AgentState:
        plan = ActionPlan.model_validate(state["plan"])
        response = interrupt(
            {
                "incident_id": plan.incident_id,
                "action": plan.action,
                "target_service": plan.target_service,
                "parameters": plan.parameters.compact(),
                "risk": plan.risk.value,
                "question": "Approve this simulated remediation?",
            }
        )
        decision = ApprovalDecision.model_validate(response)
        self._record("approval", state, approved=decision.approved)
        return {"approval": decision.model_dump(mode="json"), "trajectory": ["approval"]}

    def _execute(self, state: AgentState) -> AgentState:
        plan = ActionPlan.model_validate(state["plan"])
        try:
            result = self.executor.execute(
                plan,
                idempotent=True,
                inject_crash_after_commit=state.get("inject_crash", False),
                force_failure=state.get("force_action_failure", False),
                simulate_timeout=state.get("simulate_timeout", False),
            )
        except ToolTimeout as exc:
            self._record("execute", state, status="timeout")
            return {
                "terminal_status": "tool_timeout",
                "error": str(exc),
                "trajectory": ["execute"],
            }
        self._record(
            "execute", state, status=result.status, deduplicated=result.deduplicated
        )
        return {"execution": result.model_dump(mode="json"), "trajectory": ["execute"]}

    def _validate(self, state: AgentState) -> AgentState:
        result = ExecutionResult.model_validate(state["execution"])
        status = "resolved" if result.status == "completed" else "action_failed"
        self._record("validate", state, terminal_status=status)
        return {"terminal_status": status, "trajectory": ["validate"]}

    def _compensate(self, state: AgentState) -> AgentState:
        plan = ActionPlan.model_validate(state["plan"])
        execution = ExecutionResult.model_validate(state["execution"])
        result = self.executor.compensate(plan, execution.effect_id)
        self._record("compensate", state, status=result.status)
        return {
            "compensation": result.model_dump(mode="json"),
            "terminal_status": "compensated",
            "trajectory": ["compensate"],
        }

    def _close(self, state: AgentState) -> AgentState:
        status = state.get("terminal_status")
        if status is None:
            policy = PolicyDecision.model_validate(state["policy"])
            approval_payload = state.get("approval")
            if not policy.allowed:
                status = "blocked_policy"
            elif approval_payload and not ApprovalDecision.model_validate(approval_payload).approved:
                status = "rejected_by_operator"
            else:
                status = "closed_without_execution"
        self._record("close", state, terminal_status=status)
        return {"terminal_status": status, "trajectory": ["close"]}

    @staticmethod
    def _after_verify(state: AgentState) -> str:
        return "close" if state.get("terminal_status") else "plan"

    @staticmethod
    def _after_policy(state: AgentState) -> str:
        return "approval" if PolicyDecision.model_validate(state["policy"]).allowed else "close"

    @staticmethod
    def _after_approval(state: AgentState) -> str:
        approval = ApprovalDecision.model_validate(state["approval"])
        return "execute" if approval.approved else "close"

    @staticmethod
    def _after_execute(state: AgentState) -> str:
        return "close" if state.get("terminal_status") == "tool_timeout" else "validate"

    @staticmethod
    def _after_validate(state: AgentState) -> str:
        return "close" if state.get("terminal_status") == "resolved" else "compensate"

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("diagnose", self._diagnose)
        builder.add_node("verify", self._verify)
        builder.add_node("plan", self._plan)
        builder.add_node("policy", self._policy)
        builder.add_node("approval", self._approval)
        builder.add_node("execute", self._execute)
        builder.add_node("validate", self._validate)
        builder.add_node("compensate", self._compensate)
        builder.add_node("close", self._close)
        builder.add_edge(START, "diagnose")
        builder.add_edge("diagnose", "verify")
        builder.add_conditional_edges("verify", self._after_verify)
        builder.add_edge("plan", "policy")
        builder.add_conditional_edges("policy", self._after_policy)
        builder.add_conditional_edges("approval", self._after_approval)
        builder.add_conditional_edges("execute", self._after_execute)
        builder.add_conditional_edges("validate", self._after_validate)
        builder.add_edge("compensate", "close")
        builder.add_edge("close", END)
        return builder.compile(checkpointer=self.checkpointer)

    @staticmethod
    def _config(thread_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": thread_id}}

    def start(
        self,
        case: IncidentCase,
        thread_id: str,
        *,
        inject_crash: bool = False,
        simulate_timeout: bool = False,
    ) -> AgentState:
        return self.graph.invoke(
            {
                "evidence": case.public_view(),
                "force_action_failure": case.force_action_failure,
                "inject_crash": inject_crash,
                "simulate_timeout": simulate_timeout,
                "trajectory": [],
            },
            self._config(thread_id),
        )

    def resume_approval(
        self, thread_id: str, decision: ApprovalDecision
    ) -> AgentState:
        return self.graph.invoke(
            Command(resume=decision.model_dump(mode="json")), self._config(thread_id)
        )

    def recover_after_crash(self, thread_id: str) -> AgentState:
        return self.graph.invoke(None, self._config(thread_id))


def run_stateless_baseline(
    case: IncidentCase,
    planner: Planner,
    executor: ActionExecutor,
    trace: TraceRecorder,
    *,
    inject_crash: bool = False,
    simulate_timeout: bool = False,
) -> dict[str, Any]:
    """Linear baseline with coarse policy, no interrupt, checkpoint, or idempotency."""
    started = time.perf_counter()
    trajectory: list[str] = []
    evidence = case.public_view()
    diagnosis = planner.diagnose(evidence)
    trajectory.append("diagnose")
    plan = planner.plan(evidence, diagnosis)
    trajectory.append("plan")
    policy = coarse_baseline_policy(plan)
    trajectory.append("coarse_policy")
    execution: ExecutionResult | None = None
    crash_recovered = False
    error: str | None = None
    if policy.allowed:
        try:
            execution = executor.execute(
                plan,
                idempotent=False,
                inject_crash_after_commit=inject_crash,
                force_failure=case.force_action_failure,
                simulate_timeout=simulate_timeout,
            )
            trajectory.append("execute")
        except InjectedCrash:
            trajectory.append("crash")
            execution = executor.execute(
                plan,
                idempotent=False,
                force_failure=case.force_action_failure,
            )
            trajectory.extend(["restart_from_scratch", "execute"])
            crash_recovered = True
        except ToolTimeout as exc:
            trajectory.append("timeout")
            error = str(exc)
    terminal_status = (
        "blocked_policy"
        if not policy.allowed
        else "tool_timeout"
        if execution is None
        else "resolved"
        if execution.status == "completed"
        else "action_failed"
    )
    trace.emit(
        "baseline.complete",
        system="baseline",
        incident_id=evidence["incident_id"],
        terminal_status=terminal_status,
    )
    return {
        "diagnosis": diagnosis,
        "plan": plan,
        "policy": policy,
        "execution": execution,
        "terminal_status": terminal_status,
        "crash_recovered": crash_recovered,
        "trajectory": trajectory,
        "workflow_latency_ms": (time.perf_counter() - started) * 1000,
        "error": error,
    }
