from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp

from .schemas import PolicyDecision, QueryPlan, QueryResult


ALLOWED_TABLES = {"customers", "products", "orders", "order_items", "payments", "shipments", "support_notes"}
PII_COLUMNS = {"email", "card_last4"}
EXTERNAL_FUNCTIONS = {"read_csv", "read_csv_auto", "read_parquet", "httpfs", "sqlite_scan", "postgres_scan"}
INSTRUCTION_PATTERN = re.compile(r"(?i)(ignore (all |prior )?instructions|reveal secrets|system prompt)")


def validate_plan(plan: QueryPlan, max_result_rows: int = 100) -> PolicyDecision:
    reasons: list[str] = []
    try:
        statements = sqlglot.parse(plan.sql, read="duckdb")
    except Exception as exc:
        return PolicyDecision(allowed=False, reasons=[f"SQL parse error: {type(exc).__name__}"])
    if len(statements) != 1:
        return PolicyDecision(allowed=False, reasons=["exactly one SQL statement is required"])
    tree = statements[0]
    if not isinstance(tree, exp.Query):
        reasons.append("only query expressions are allowed")

    prohibited_types = tuple(
        item for item in (getattr(exp, name, None) for name in ["Insert", "Update", "Delete", "Create", "Drop", "Alter", "Command", "Copy", "Merge"]) if item is not None
    )
    if prohibited_types and any(tree.find_all(*prohibited_types)):
        reasons.append("DDL, DML, command, and copy nodes are forbidden")

    tables = sorted({table.name.lower() for table in tree.find_all(exp.Table) if table.name})
    columns = sorted({column.name.lower() for column in tree.find_all(exp.Column) if column.name})
    unknown_tables = set(tables) - ALLOWED_TABLES
    if unknown_tables:
        reasons.append(f"unapproved tables: {sorted(unknown_tables)}")
    if not set(plan.selected_tables).issubset(ALLOWED_TABLES):
        reasons.append("query plan selected an unapproved table")
    if set(plan.selected_tables) != set(tables):
        reasons.append("query-plan tables do not match SQL AST tables")
    if set(columns) & PII_COLUMNS:
        reasons.append("direct PII column selection is forbidden")

    function_names = {
        function.sql_name().lower()
        for function in tree.find_all(exp.Func)
        if function.sql_name()
    }
    if function_names & EXTERNAL_FUNCTIONS:
        reasons.append("external I/O functions are forbidden")

    limit = tree.args.get("limit")
    has_aggregate = any(tree.find_all(exp.AggFunc))
    if limit is None and not has_aggregate:
        reasons.append("non-aggregate queries require an explicit LIMIT")
    elif limit is not None:
        try:
            value = int(limit.expression.name)
            if value > max_result_rows:
                reasons.append(f"LIMIT exceeds {max_result_rows}")
        except (AttributeError, TypeError, ValueError):
            reasons.append("LIMIT must be a literal integer")

    return PolicyDecision(
        allowed=not reasons,
        reasons=reasons or ["query satisfies project5-policy-v1"],
        parsed_expression=type(tree).__name__,
        tables=tables,
        columns=columns,
    )


def authorize_plan(
    plan: QueryPlan, authorized_regions: list[str], max_result_rows: int = 100
) -> PolicyDecision:
    decision = validate_plan(plan, max_result_rows=max_result_rows)
    reasons = list(decision.reasons if not decision.allowed else [])
    unauthorized = set(plan.requested_regions) - set(authorized_regions)
    if unauthorized:
        reasons.append(f"unauthorized regions: {sorted(unauthorized)}")
    return decision.model_copy(
        update={
            "allowed": not reasons,
            "reasons": reasons or ["query satisfies project5-policy-v1"],
        }
    )


def mask_rows(columns: list[str], rows: list[tuple[Any, ...]]) -> tuple[list[list[Any]], int]:
    masked = 0
    output: list[list[Any]] = []
    for row in rows:
        values: list[Any] = []
        for column, value in zip(columns, row):
            if column.lower() in PII_COLUMNS and value is not None:
                values.append("[MASKED]")
                masked += 1
            else:
                values.append(value)
        output.append(values)
    return output, masked


def mark_untrusted_cells(columns: list[str], rows: list[list[Any]]) -> list[list[Any]]:
    output: list[list[Any]] = []
    for row in rows:
        values = []
        for column, value in zip(columns, row):
            if column.lower().endswith("note_text") and isinstance(value, str) and INSTRUCTION_PATTERN.search(value):
                values.append({"provenance": "untrusted_database_text", "value": value})
            else:
                values.append(value)
        output.append(values)
    return output


def export_json(result: QueryResult, destination: str | Path, root: str | Path, approved: bool) -> Path:
    if not approved:
        raise PermissionError("result export requires explicit approval")
    root = Path(root).resolve()
    destination = Path(destination).resolve()
    if destination != root and root not in destination.parents:
        raise PermissionError("export destination escapes the approved root")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    return destination
