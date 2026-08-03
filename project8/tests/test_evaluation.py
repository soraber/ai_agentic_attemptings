from pathlib import Path
from project8_agent.evaluation import evaluate_lifecycle


def test_three_system_evaluation_and_deletion(tmp_path):
    fixture=Path(__file__).parents[1]/"data/lifecycle_cases.json"; summary=evaluate_lifecycle(fixture,tmp_path/"memory.sqlite",tmp_path/"output")
    assert summary["deletion_compliance_pct"]==100
    assert summary["hybrid"]["exact_match_pct"]>=summary["window"]["exact_match_pct"]
    assert (tmp_path/"output/project8_traces.jsonl").exists()
