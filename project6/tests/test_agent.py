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


def test_hidden_failure_does_not_steer_another_attempt(buggy_repo, tmp_path) -> None:
    agent = RepairAgent(Project6Config(execution_backend="trusted_fixture"))
    result = agent.run("fixture", "repair_loop", buggy_repo, tmp_path / "work", ["calc.py"], ["test_public.py"], ["test_hidden.py"], ScriptedPlanner([proposal(OVERFIT_DIFF), proposal(CORRECT_DIFF)]))
    assert not result.verified and result.attempts == 1
    assert result.overfit_detected and result.rollback_verified
    assert not (tmp_path / "work" / "test_hidden.py").exists()


def test_one_shot_rolls_back_overfit_patch(buggy_repo, tmp_path) -> None:
    result = RepairAgent(Project6Config(execution_backend="trusted_fixture")).run("fixture", "one_shot", buggy_repo, tmp_path / "work", ["calc.py"], ["test_public.py"], ["test_hidden.py"], ScriptedPlanner([proposal(OVERFIT_DIFF)]))
    assert not result.verified and result.overfit_detected and result.rollback_verified


def test_public_failure_can_steer_repair_and_map_is_used(buggy_repo, tmp_path):
    class Planner(ScriptedPlanner):
        def set_context(self, symbols, locations):
            self.symbols, self.locations = symbols, locations
    planner = Planner([proposal(OVERFIT_DIFF.replace("return 5", "return 0")), proposal(CORRECT_DIFF)])
    result = RepairAgent(Project6Config(execution_backend="trusted_fixture")).run(
        "fixture", "repair_loop", buggy_repo, tmp_path / "work", ["calc.py"],
        ["test_public.py"], ["test_hidden.py"], planner)
    assert result.verified and result.attempts == 2
    assert planner.symbols and planner.locations
    assert all(item["path"] != "test_hidden.py" for item in planner.symbols)


def test_hidden_evaluator_error_does_not_reopen_selection(buggy_repo, tmp_path, monkeypatch):
    import project6_agent.agent as module
    original = module.run_tests
    def fail_holdout(root, targets, *args, **kwargs):
        if targets == ["test_hidden.py"]:
            raise RuntimeError("evaluator disconnected")
        return original(root, targets, *args, **kwargs)
    monkeypatch.setattr(module, "run_tests", fail_holdout)
    result = RepairAgent(Project6Config(execution_backend="trusted_fixture")).run(
        "fixture", "repair_loop", buggy_repo, tmp_path / "work", ["calc.py"],
        ["test_public.py"], ["test_hidden.py"], ScriptedPlanner([proposal(CORRECT_DIFF)]))
    assert result.attempts == 1 and not result.verified
    assert "final_evaluator_error" in result.trajectory
