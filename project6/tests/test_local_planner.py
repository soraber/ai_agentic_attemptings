from project6_agent.config import Project6Config
from project6_agent.planners import LocalPatchPlanner, extract_json_object


class FakeBackend:
    def generate(self, payload):
        assert payload["allowed_path"] == "python_programs/gcd.py"
        return """result:
        {"rationale":"Fix the base case.",
         "unified_diff":"--- a/python_programs/gcd.py\\n+++ b/python_programs/gcd.py\\n@@ -1 +1 @@\\n-return b\\n+return a\\n",
         "targeted_paths":["python_programs/gcd.py"]}"""


def test_extract_json_object_handles_prefixed_output():
    assert extract_json_object("answer {\"rationale\": \"ok\"}") == {"rationale": "ok"}


def test_local_patch_planner_parses_structured_diff(tmp_path):
    source = tmp_path / "gcd.py"
    source.write_text("return b\n", encoding="utf-8")
    planner = LocalPatchPlanner(
        Project6Config(),
        source,
        "gcd",
        "python_programs/gcd.py",
        FakeBackend(),
    )
    proposal = planner.propose("assertion failed", 0)
    assert proposal.targeted_paths == ["python_programs/gcd.py"]
    assert "+return a" in proposal.unified_diff
    assert planner.calls == 1
