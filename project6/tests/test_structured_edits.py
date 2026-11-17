from types import SimpleNamespace

import pytest

from project6_agent.config import Project6Config
from project6_agent.patching import apply_unified_diff
from project6_agent.structured_edits import OpenAIStructuredEditPlanner, SourceEdit, StructuredEdits, to_patch


def proposal(old, new):
    return StructuredEdits(rationale="Repair arithmetic", edits=[SourceEdit(old=old, new=new)])


@pytest.mark.parametrize("ending", ["\n", ""])
def test_generated_diff_is_accepted_by_git(tmp_path, ending):
    source = "def add(a, b):\n    return a - b" + ending
    (tmp_path / "calc.py").write_text(source)
    patch = to_patch(source, proposal("a - b", "a + b"), "calc.py", 10)
    apply_unified_diff(tmp_path, patch.unified_diff)
    assert (tmp_path / "calc.py").read_text() == source.replace("a - b", "a + b")


def test_rejects_missing_ambiguous_overlapping_and_unsafe_edits():
    with pytest.raises(ValueError, match="exactly once"):
        to_patch("x=1\ny=1\n", proposal("1", "2"), "a.py", 10)
    with pytest.raises(ValueError, match="exactly once"):
        to_patch("x=1\n", proposal("missing", "2"), "a.py", 10)
    overlapping = StructuredEdits(rationale="x", edits=[SourceEdit(old="x=1", new="x=2"), SourceEdit(old="1", new="3")])
    with pytest.raises(ValueError, match="Overlapping"):
        to_patch("x=1\n", overlapping, "a.py", 10)
    with pytest.raises(PermissionError):
        to_patch("x=1\n", proposal("1", "2"), "../a.py", 10)
    with pytest.raises(SyntaxError):
        to_patch("x=1\n", proposal("1", "("), "a.py", 10)
    with pytest.raises(PermissionError, match="budget"):
        to_patch("x=1\n", proposal("1", "2"), "a.py", 1)


def test_planner_records_usage_and_returns_harness_generated_diff(tmp_path):
    source = tmp_path / "calc.py"
    source.write_text("x=1\n")
    def parse(**kwargs):
        assert kwargs["text_format"] is StructuredEdits
        return SimpleNamespace(output_parsed=proposal("1", "2"),
                               usage=SimpleNamespace(input_tokens=100, output_tokens=50))
    planner = OpenAIStructuredEditPlanner(Project6Config(), source, "calc", "calc.py",
                                         client=SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    patch = planner.propose("assertion failed", 0)
    assert patch.unified_diff.startswith("--- a/calc.py\n+++ b/calc.py\n@@")
    assert planner.calls == 1 and planner.input_tokens == 100
