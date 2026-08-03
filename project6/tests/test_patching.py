from __future__ import annotations

from project6_agent.patching import RepairWorkspace, apply_unified_diff, validate_unified_diff


CORRECT_DIFF = """--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""


def test_diff_policy_and_exact_rollback(buggy_repo, tmp_path) -> None:
    decision = validate_unified_diff(CORRECT_DIFF, ["calc.py"], 10)
    assert decision.allowed and decision.changed_lines == 2
    workspace = RepairWorkspace(buggy_repo, tmp_path / "work")
    apply_unified_diff(workspace.destination, CORRECT_DIFF)
    assert workspace.changed_paths() == ["calc.py"]
    assert workspace.rollback() and not workspace.changed_paths()


def test_diff_policy_blocks_traversal_and_line_budget() -> None:
    traversal = CORRECT_DIFF.replace("a/calc.py", "a/../outside.py").replace("b/calc.py", "b/../outside.py")
    assert not validate_unified_diff(traversal, ["calc.py"], 10).allowed
    assert not validate_unified_diff(CORRECT_DIFF, ["calc.py"], 1).allowed
