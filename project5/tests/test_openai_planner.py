from __future__ import annotations

import json
from types import SimpleNamespace

from project5_agent.analyst import OpenAISQLPlanner
from project5_agent.config import Project5Config
from project5_agent.schemas import QueryPlan


class FakeResponses:
    def __init__(self, plan: QueryPlan):
        self.plan = plan
        self.prompt: dict[str, object] | None = None

    def parse(self, **kwargs):
        self.prompt = json.loads(kwargs["input"])
        return SimpleNamespace(
            output_parsed=self.plan,
            usage=SimpleNamespace(input_tokens=120, output_tokens=80),
        )


def test_openai_planner_records_usage_and_identifiers(project5_data) -> None:
    _, cases = project5_data
    case = next(case for case in cases if case.category == "benign")
    plan = QueryPlan(
        question_id=case.question_id,
        intent=case.category,
        selected_tables=["orders"],
        requested_regions=case.requested_regions,
        sql=case.gold_sql,
        rationale="Test plan.",
    )
    responses = FakeResponses(plan)
    planner = OpenAISQLPlanner(Project5Config(), SimpleNamespace(responses=responses))

    assert planner.plan(case) == plan
    assert responses.prompt["question_id"] == case.question_id
    assert responses.prompt["category"] == case.category
    assert planner.usage_summary() == {
        "model_calls": 1,
        "input_tokens": 120,
        "output_tokens": 80,
        "estimated_cost_usd": 0.0006,
    }
