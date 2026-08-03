from __future__ import annotations

import json
from types import SimpleNamespace

from project6_agent.config import Project6Config
from project6_agent.planners import OpenAIPatchPlanner
from project6_agent.schemas import PatchProposal


class FakeResponses:
    def __init__(self, proposal: PatchProposal):
        self.proposal = proposal
        self.prompt: dict[str, object] | None = None

    def parse(self, **kwargs):
        self.prompt = json.loads(kwargs["input"])
        return SimpleNamespace(
            output_parsed=self.proposal,
            usage=SimpleNamespace(input_tokens=500, output_tokens=200),
        )


def test_openai_planner_uses_relative_allowlisted_path_and_records_usage(tmp_path) -> None:
    source = tmp_path / "python_programs" / "calc.py"
    source.parent.mkdir()
    source.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    proposal = PatchProposal(
        rationale="Use addition.",
        unified_diff="--- a/python_programs/calc.py\n+++ b/python_programs/calc.py\n@@ -1,2 +1,2 @@\n def add(a, b):\n-    return a - b\n+    return a + b\n",
        targeted_paths=["python_programs/calc.py"],
    )
    responses = FakeResponses(proposal)
    planner = OpenAIPatchPlanner(
        Project6Config(),
        source,
        "calc",
        allowed_path="python_programs/calc.py",
        client=SimpleNamespace(responses=responses),
    )

    assert planner.propose("assertion failed", 0) == proposal
    assert responses.prompt["allowed_path"] == "python_programs/calc.py"
    assert planner.usage_summary() == {
        "model_calls": 1,
        "input_tokens": 500,
        "output_tokens": 200,
        "estimated_cost_usd": 0.0085,
    }
