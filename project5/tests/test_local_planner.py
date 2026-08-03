from project5_agent.analyst import LocalSQLPlanner
from project5_agent.config import Project5Config
from project5_agent.local_models import extract_json_object


class FakeRetriever:
    def retrieve(self, question, top_k):
        assert question and top_k == 5
        return ["orders", "customers"]


class FakeGenerator:
    def generate(self, system, payload, max_new_tokens):
        assert "text-to-SQL" in system
        assert set(payload["retrieved_schema"]) == {"orders", "customers"}
        assert max_new_tokens == 500
        return """```json
        {"question_id":"wrong","intent":"analytics","selected_tables":["orders"],
        "requested_regions":["NA"],"sql":"SELECT COUNT(*) AS n FROM orders",
        "export_requested":false,"rationale":"Count orders."}
        ```"""


def test_extract_json_object_ignores_fences():
    assert extract_json_object("prefix {\"value\": 3} suffix") == {"value": 3}


def test_local_planner_uses_dense_retrieval_and_enforces_case_id(project5_data):
    _, cases = project5_data
    case = next(item for item in cases if item.category == "benign")
    planner = LocalSQLPlanner(Project5Config(), FakeGenerator(), FakeRetriever())
    plan = planner.plan(case)
    assert plan.question_id == case.question_id
    assert plan.selected_tables == ["orders"]
    assert planner.calls == 1
