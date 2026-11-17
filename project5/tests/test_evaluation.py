from project5_agent.config import Project5Config
from project5_agent.evaluation import evaluate_project5
from project5_agent.analyst import LocalSQLPlanner
from types import SimpleNamespace


def test_timing_and_blocking_denominators_are_explicit(project5_data, tmp_path):
    database, cases = project5_data
    result = evaluate_project5(cases, database, Project5Config(), tmp_path / 'results')
    baseline = result['baseline']
    assert baseline['unsafe_policy_or_abstention_pct'] <= baseline['unsafe_block_rate_pct']
    assert baseline['end_to_end_p95_ms'] >= baseline['end_to_end_p50_ms']
    assert len(result['test_cases_sha256']) == 64
    assert 'initial planning' in result['latency_definition']


def test_model_parse_failures_are_counted_not_reported_as_policy_success(project5_data, tmp_path):
    database, cases = project5_data
    generator = SimpleNamespace(generate=lambda *args: 'not json')
    retriever = SimpleNamespace(retrieve=lambda *args: ['customers'])
    config = Project5Config(max_model_calls=1)
    planner = LocalSQLPlanner(config, generator=generator, retriever=retriever)
    result = evaluate_project5(cases, database, config, tmp_path / 'bad-model', planner)
    assert result['planner_usage']['model_calls'] == 1
    assert result['baseline']['planning_error_pct'] == 100
    assert result['governed']['unsafe_policy_or_abstention_pct'] == 0
