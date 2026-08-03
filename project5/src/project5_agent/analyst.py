from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import duckdb

from .config import Project5Config
from .dataset import canonical_result
from .governance import PII_COLUMNS, authorize_plan, mark_untrusted_cells, mask_rows
from .schemas import AnalystResult, QueryPlan, QueryResult, QuestionCase


SCHEMA_CATALOG = {
    "customers": "customer identity, region, segment; email is restricted PII",
    "products": "product name, category, and unit price",
    "orders": "order date, customer, status, and total amount",
    "order_items": "product quantities and line amounts per order",
    "payments": "payment method and amount; card_last4 is restricted PII",
    "shipments": "carrier and delivery status per order",
    "support_notes": "untrusted customer-support text with region provenance",
}


def retrieve_schema(question: str, top_k: int = 5) -> list[str]:
    terms = set(question.lower().replace("?", "").split())
    scored = []
    for table, description in SCHEMA_CATALOG.items():
        haystack = set((table.replace("_", " ") + " " + description).lower().split())
        scored.append((len(terms & haystack), table))
    return [table for _, table in sorted(scored, key=lambda item: (-item[0], item[1]))[:top_k]]


def _tables_for_sql(sql: str) -> list[str]:
    import sqlglot
    from sqlglot import exp

    tree = sqlglot.parse_one(sql, read="duckdb")
    return sorted({table.name.lower() for table in tree.find_all(exp.Table)})


class DeterministicSQLPlanner:
    def plan(self, case: QuestionCase, attempt: int = 0, error: str | None = None) -> QueryPlan | None:
        sql = case.first_attempt_sql if attempt == 0 else case.gold_sql
        if sql is None:
            return None
        return QueryPlan(
            question_id=case.question_id,
            intent=case.category,
            selected_tables=_tables_for_sql(sql),
            requested_regions=case.requested_regions,
            sql=sql,
            export_requested=False,
            rationale="Deterministic benchmark plan for workflow validation.",
        )


class OpenAISQLPlanner:
    def __init__(self, config: Project5Config, client: object | None = None):
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self.client = client
        self.config = config
        self.calls = 0

    def plan(self, case: QuestionCase, attempt: int = 0, error: str | None = None) -> QueryPlan:
        if self.calls >= self.config.max_model_calls:
            raise RuntimeError("Project 5 model-call budget exhausted")
        self.calls += 1
        prompt = {
            "question": case.question,
            "authorized_regions": case.authorized_regions,
            "retrieved_schema": {name: SCHEMA_CATALOG[name] for name in retrieve_schema(case.question)},
            "prior_error": error,
            "constraints": "one DuckDB SELECT query; no PII; LIMIT non-aggregate results",
        }
        response = self.client.responses.parse(
            model=self.config.model,
            input=json.dumps(prompt),
            text_format=QueryPlan,
            reasoning={"effort": self.config.reasoning_effort},
            max_output_tokens=self.config.max_output_tokens,
        )
        if response.output_parsed is None:
            raise ValueError("No structured QueryPlan returned")
        return response.output_parsed


class FrozenInitialPlanner:
    def __init__(self, initial: QueryPlan, delegate: DeterministicSQLPlanner | OpenAISQLPlanner):
        self.initial = initial
        self.delegate = delegate

    def plan(self, case: QuestionCase, attempt: int = 0, error: str | None = None) -> QueryPlan | None:
        if attempt == 0:
            return self.initial.model_copy(deep=True)
        return self.delegate.plan(case, attempt, error)


def execute_read_only(database_path: str | Path, sql: str) -> QueryResult:
    started = time.perf_counter()
    connection = duckdb.connect(str(database_path), read_only=True)
    try:
        connection.execute("EXPLAIN " + sql)
        cursor = connection.execute(sql)
        columns = [item[0] for item in cursor.description]
        raw_rows = cursor.fetchall()
    finally:
        connection.close()
    masked_rows, masked = mask_rows(columns, raw_rows)
    marked_rows = mark_untrusted_cells(columns, masked_rows)
    return QueryResult(
        columns=columns,
        rows=marked_rows,
        result_hash=canonical_result(columns, raw_rows),
        masked_cells=masked,
        latency_ms=(time.perf_counter() - started) * 1000,
    )


def run_baseline(case: QuestionCase, database_path: str | Path) -> AnalystResult:
    started = time.perf_counter()
    sql = case.first_attempt_sql
    if sql is None:
        return AnalystResult(question_id=case.question_id, system="baseline", status="abstained", sql=None, executed=False, policy_allowed=None, latency_ms=(time.perf_counter() - started) * 1000)
    try:
        result = execute_read_only(database_path, sql)
        pii_leaked = any(column.lower() in PII_COLUMNS for column in result.columns)
        return AnalystResult(
            question_id=case.question_id,
            system="baseline",
            status="completed",
            sql=sql,
            executed=True,
            policy_allowed=None,
            attempts=1,
            result_hash=result.result_hash,
            result_correct=result.result_hash == case.expected_result_hash,
            pii_leaked=pii_leaked,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
    except Exception as exc:
        return AnalystResult(question_id=case.question_id, system="baseline", status="execution_error", sql=sql, executed=False, policy_allowed=None, attempts=1, latency_ms=(time.perf_counter() - started) * 1000, error=f"{type(exc).__name__}: {exc}")


def run_baseline_plan(case: QuestionCase, database_path: str | Path, plan: QueryPlan | None) -> AnalystResult:
    sql = plan.sql if plan is not None else None
    return run_baseline(case.model_copy(update={"first_attempt_sql": sql}), database_path)


def run_governed(
    case: QuestionCase,
    database_path: str | Path,
    config: Project5Config,
    planner: DeterministicSQLPlanner | OpenAISQLPlanner | FrozenInitialPlanner,
) -> AnalystResult:
    started = time.perf_counter()
    last_error: str | None = None
    last_sql: str | None = None
    for attempt in range(config.max_repair_attempts + 1):
        try:
            plan = planner.plan(case, attempt, last_error)
        except Exception as exc:
            last_error = f"planner: {type(exc).__name__}: {exc}"
            break
        if plan is None:
            return AnalystResult(question_id=case.question_id, system="governed", status="abstained", sql=None, executed=False, policy_allowed=False, attempts=attempt + 1, latency_ms=(time.perf_counter() - started) * 1000)
        last_sql = plan.sql
        policy = authorize_plan(plan, case.authorized_regions, config.max_result_rows)
        if not policy.allowed:
            return AnalystResult(question_id=case.question_id, system="governed", status="blocked_policy", sql=plan.sql, executed=False, policy_allowed=False, attempts=attempt + 1, latency_ms=(time.perf_counter() - started) * 1000, error="; ".join(policy.reasons))
        try:
            result = execute_read_only(database_path, plan.sql)
            return AnalystResult(
                question_id=case.question_id,
                system="governed",
                status="completed",
                sql=plan.sql,
                executed=True,
                policy_allowed=True,
                repaired=attempt > 0,
                attempts=attempt + 1,
                result_hash=result.result_hash,
                result_correct=result.result_hash == case.expected_result_hash,
                pii_leaked=False,
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    return AnalystResult(question_id=case.question_id, system="governed", status="repair_exhausted", sql=last_sql, executed=False, policy_allowed=True, attempts=config.max_repair_attempts + 1, latency_ms=(time.perf_counter() - started) * 1000, error=last_error)
