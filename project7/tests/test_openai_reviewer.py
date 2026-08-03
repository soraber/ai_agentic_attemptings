from __future__ import annotations

from types import SimpleNamespace

from project7_agent.config import Project7Config
from project7_agent.dataset import generate_cases
from project7_agent.reviewers import OpenAIPolicyReviewer
from project7_agent.schemas import PolicyRecommendation


class FakeResponses:
    def parse(self, **kwargs):
        return SimpleNamespace(
            output_parsed=PolicyRecommendation(action="approve", rationale="Valid request."),
            usage=SimpleNamespace(input_tokens=300, output_tokens=100),
        )


def test_openai_reviewer_records_usage() -> None:
    case = next(case for case in generate_cases() if case.category == "benign")
    reviewer = OpenAIPolicyReviewer(
        Project7Config(),
        client=SimpleNamespace(responses=FakeResponses()),
    )

    assert reviewer.review(case).action == "approve"
    assert reviewer.usage_summary() == {
        "model_calls": 1,
        "input_tokens": 300,
        "output_tokens": 100,
        "estimated_cost_usd": 0.0009,
    }
