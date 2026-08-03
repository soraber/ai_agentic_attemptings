from __future__ import annotations

from project5_agent.governance import authorize_plan, export_json, mask_rows, validate_plan
from project5_agent.schemas import QueryPlan, QueryResult


def _plan(sql: str, tables: list[str], regions: list[str] | None = None) -> QueryPlan:
    return QueryPlan(question_id="test", intent="test", selected_tables=tables, requested_regions=regions or [], sql=sql, rationale="test")


def test_ast_policy_blocks_write_pii_external_io_and_excessive_limit() -> None:
    attacks = [
        _plan("DROP TABLE orders", []),
        _plan("SELECT email FROM customers LIMIT 5", ["customers"]),
        _plan("SELECT * FROM read_csv('/tmp/x.csv') LIMIT 5", []),
        _plan("SELECT product_name FROM products LIMIT 1000", ["products"]),
    ]
    assert not any(validate_plan(plan).allowed for plan in attacks)


def test_row_policy_binds_requested_region() -> None:
    plan = _plan("SELECT COUNT(*) FROM orders", ["orders"], ["EU"])
    assert not authorize_plan(plan, ["NA"]).allowed


def test_mask_and_export_approval(tmp_path) -> None:
    rows, count = mask_rows(["email", "value"], [("a@example.invalid", 3)])
    assert rows == [["[MASKED]", 3]] and count == 1
    result = QueryResult(columns=["value"], rows=[[3]], result_hash="x", latency_ms=0)
    destination = tmp_path / "approved" / "result.json"
    try:
        export_json(result, destination, tmp_path / "approved", approved=False)
        raise AssertionError("unapproved export succeeded")
    except PermissionError:
        pass
    assert export_json(result, destination, tmp_path / "approved", approved=True).exists()
