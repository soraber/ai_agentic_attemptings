from __future__ import annotations

from project6_agent.agent import RepairAgent, ScriptedPlanner
from project6_agent.config import Project6Config
from project6_agent.schemas import PatchProposal


OVERFIT_DIFF = """--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return 5
"""

CORRECT_DIFF = OVERFIT_DIFF.replace("return 5", "return a + b")


def proposal(diff: str) -> PatchProposal:
    return PatchProposal(rationale="fixture repair", unified_diff=diff, targeted_paths=["calc.py"])


def test_repair_loop_rejects_overfit_then_accepts_general_fix(buggy_repo, tmp_path) -> None:
    agent = RepairAgent(Project6Config())
    result = agent.run("fixture", "repair_loop", buggy_repo, tmp_path / "work", ["calc.py"], ["test_public.py"], ["test_hidden.py"], ScriptedPlanner([proposal(OVERFIT_DIFF), proposal(CORRECT_DIFF)]))
    assert result.verified and result.attempts == 2
    assert result.overfit_detected and result.rollback_verified


def test_one_shot_rolls_back_overfit_patch(buggy_repo, tmp_path) -> None:
    result = RepairAgent(Project6Config()).run("fixture", "one_shot", buggy_repo, tmp_path / "work", ["calc.py"], ["test_public.py"], ["test_hidden.py"], ScriptedPlanner([proposal(OVERFIT_DIFF)]))
    assert not result.verified and result.overfit_detected and result.rollback_verified
