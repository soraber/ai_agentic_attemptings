import pytest

from project5_agent.analyst import execute_read_only, run_governed
from project5_agent.config import Project5Config
from project5_agent.execution import audit_output, describe_authorized_schema, query_snapshot, restricted_snapshot
from project5_agent.schemas import QueryPlan


def test_missing_tenant_filter_cannot_expand_rows(project5_data):
    database, cases = project5_data
    case = cases[0].model_copy(update={"authorized_regions": ["NA"]})
    class Planner:
        def plan(self, *args):
            return QueryPlan(question_id=case.question_id, intent="count", selected_tables=["orders"],
                             requested_regions=[], sql="SELECT COUNT(*) AS n FROM orders", rationale="test")
    result = run_governed(case, database, Project5Config(), Planner())
    assert result.executed
    assert execute_read_only(database, "SELECT COUNT(*) AS n FROM orders", ["NA"]).rows == [[24]]
    assert execute_read_only(database, "SELECT COUNT(*) AS n FROM customers WHERE region='EU'", ["NA"]).rows == [[0]]


@pytest.mark.parametrize("sql", [
    "SELECT email AS innocuous FROM customers LIMIT 1",
    "SELECT * FROM customers LIMIT 1",
    "SELECT content FROM read_text('/etc/passwd') LIMIT 1",
    "SELECT * FROM range(1000)",
    "ATTACH '/tmp/other.duckdb' AS other",
    "SELECT 1; SELECT 2",
])
def test_escape_and_pii_queries_fail(project5_data, sql):
    with pytest.raises(Exception):
        execute_read_only(project5_data[0], sql, ["NA"])


def test_empty_scope_and_row_budget_fail_closed(project5_data):
    with pytest.raises(PermissionError):
        execute_read_only(project5_data[0], "SELECT 1", [])
    with pytest.raises(RuntimeError, match="row budget"):
        execute_read_only(project5_data[0], "SELECT order_id FROM orders", ["NA"], max_rows=1)


def test_schema_and_audit_are_independent_of_output_aliases(project5_data):
    schema = describe_authorized_schema(project5_data[0], ["NA"])
    assert "email" not in schema["customers"] and "card_last4" not in schema["payments"]
    assert "total_amount DOUBLE" in schema["orders"]
    assert audit_output([[{"value": "customer01@example.invalid"}]])
    assert audit_output([["4321"]], {"4321"})
    assert not audit_output([[24, "NA"]])


def test_connection_is_locked_and_query_deadline_interrupts(project5_data):
    with restricted_snapshot(project5_data[0], ["NA"]) as (connection, _):
        assert connection.execute("SELECT current_setting('enable_external_access')").fetchone() == (False,)
        with pytest.raises(Exception):
            connection.execute("SET enable_external_access=true")
        with pytest.raises(Exception):
            query_snapshot(connection, "SELECT SUM(a.order_id*b.order_id*c.order_id*d.order_id*e.order_id) FROM orders a, orders b, orders c, orders d, orders e", 100, 0.001)
