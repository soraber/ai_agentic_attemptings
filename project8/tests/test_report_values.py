import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("report", Path(__file__).parents[1] / "tools/generate_report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def test_report_handles_lifecycle_and_does_not_assume_winner():
    summary = {"result_status": "measured"}
    for name, score in zip(report.SYSTEMS, [.1, .2, .9]):
        summary[name] = {"mean_token_f1": score, "mean_context_words": 12}
    scores, words, interpretation = report.report_values(summary)
    assert scores == [10, 20, 90]
    assert words == [12, 12, 12]
    assert "Hybrid (90.0%)" in interpretation
    assert "deterministic lifecycle fixture" in interpretation
