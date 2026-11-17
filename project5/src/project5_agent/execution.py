from __future__ import annotations

import re
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb
import sqlglot
from sqlglot import exp


# Generated SQL sees only these physical tables, never the source database.
SAFE_COLUMNS = {
    "customers": "customer_id, region, segment",
    "products": "product_id, product_name, category, unit_price",
    "orders": "order_id, customer_id, order_date, total_amount, status",
    "order_items": "order_id, product_id, quantity, line_amount",
    "payments": "payment_id, order_id, method, amount",
    "shipments": "shipment_id, order_id, carrier, status",
    "support_notes": "note_id, customer_id, region, note_text",
}
REGIONS = {"NA", "EU", "APAC", "LATAM", "MEA"}
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def audit_output(rows: list, sensitive_values: set[str] | None = None) -> bool:
    """Audit values, not column aliases; strings in nested provenance count too."""
    if isinstance(rows, dict):
        return any(audit_output(value, sensitive_values) for value in rows.values())
    if isinstance(rows, (list, tuple)):
        return any(audit_output(value, sensitive_values) for value in rows)
    text = str(rows)
    return bool(EMAIL.search(text) or text in (sensitive_values or set()))


@contextmanager
def restricted_snapshot(
    database_path: str | Path, authorized_regions: list[str], max_snapshot_rows: int = 50000
) -> Iterator[tuple[duckdb.DuckDBPyConnection, set[str]]]:
    if not authorized_regions or not set(authorized_regions) <= REGIONS:
        raise PermissionError("A nonempty trusted region scope is required")
    scope = sorted(set(authorized_regions))
    placeholders = ",".join("?" for _ in scope)
    customer_scope = f"SELECT customer_id FROM customers WHERE region IN ({placeholders})"
    order_scope = f"SELECT order_id FROM orders WHERE customer_id IN ({customer_scope})"
    predicates = {
        "customers": f"region IN ({placeholders})",
        "products": None,
        "orders": f"customer_id IN ({customer_scope})",
        "order_items": f"order_id IN ({order_scope})",
        "payments": f"order_id IN ({order_scope})",
        "shipments": f"order_id IN ({order_scope})",
        "support_notes": f"region IN ({placeholders}) AND customer_id IN ({customer_scope})",
    }
    source = duckdb.connect(str(database_path), read_only=True)
    target = None
    try:
        target = duckdb.connect(":memory:", config={
            "enable_external_access": "false",
            "autoload_known_extensions": "false",
            "autoinstall_known_extensions": "false",
            "allow_unsigned_extensions": "false",
            "memory_limit": "512MB",
            "threads": "1",
            "max_temp_directory_size": "0B",
        })
        sensitive = {str(row[0]) for row in source.execute(
            "SELECT email FROM customers UNION ALL SELECT card_last4 FROM payments"
        ).fetchall() if row[0]}
        for table, columns in SAFE_COLUMNS.items():
            predicate = predicates[table]
            query = f"SELECT {columns} FROM {table}" + (f" WHERE {predicate}" if predicate else "")
            params = scope * (2 if table == "support_notes" else 1) if predicate else []
            cursor = source.execute(query, params)
            fields = ", ".join(f'"{item[0]}" {item[1]}' for item in cursor.description)
            rows = cursor.fetchmany(max_snapshot_rows + 1)
            if len(rows) > max_snapshot_rows:
                raise RuntimeError("Restricted snapshot row budget exceeded")
            target.execute(f"CREATE TABLE {table} ({fields})")
            # Free text is also audited before reaching the query engine/model.
            rows = [tuple("[REDACTED]" if audit_output(value, sensitive) else value
                          for value in row) for row in rows]
            if rows:
                marks = ",".join("?" for _ in cursor.description)
                target.executemany(f"INSERT INTO {table} VALUES ({marks})", rows)
        target.execute("SET lock_configuration = true")
        yield target, sensitive
    finally:
        source.close()
        if target is not None:
            target.close()


def validate_read_query(sql: str) -> None:
    statements = sqlglot.parse(sql, read="duckdb")
    if len(statements) != 1 or not isinstance(statements[0], exp.Query):
        raise PermissionError("Only one SELECT query is executable")
    for table in statements[0].find_all(exp.Table):
        if table.catalog or table.db or table.name.lower() not in SAFE_COLUMNS:
            raise PermissionError("Query references a relation outside the authorized snapshot")
    for star in statements[0].find_all(exp.Star):
        if not isinstance(star.parent, exp.Count):
            raise PermissionError("Explicit projected columns are required")


def query_snapshot(connection, sql: str, max_rows: int, timeout_seconds: float):
    validate_read_query(sql)
    expired = threading.Event()

    def interrupt():
        expired.set()
        connection.interrupt()

    timer = threading.Timer(timeout_seconds, interrupt)
    timer.daemon = True
    timer.start()
    try:
        cursor = connection.execute(sql)
        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchmany(max_rows + 1)
        if expired.is_set():
            raise TimeoutError("SQL execution deadline exceeded")
        if len(rows) > max_rows:
            raise RuntimeError("SQL result row budget exceeded")
        return columns, rows
    finally:
        timer.cancel()
        timer.join()


def describe_authorized_schema(database_path: str | Path, regions: list[str]) -> dict[str, str]:
    with restricted_snapshot(database_path, regions) as (connection, _):
        return {table: "; ".join(f"{row[0]} {row[1]}" for row in connection.execute(
            f"DESCRIBE {table}"
        ).fetchall()) for table in SAFE_COLUMNS}
