"""Re-evaluate frozen SQL values in the restricted DB; make no model calls."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from project5_agent.dataset import build_database, generate_benchmark
from project5_agent.evaluation import _summary
from project5_agent.semantic_scoring import grade_saved_queries


def rescore(source, work_dir):
    original = json.loads((source / 'project5_final_summary.json').read_text())
    rows = json.loads((source / 'project5_case_results.json').read_text())
    work_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='p5-values-', dir=work_dir) as temporary:
        database = build_database(Path(temporary) / 'fixture.duckdb', original['config']['seed'])
        cases = [case for case in generate_benchmark(database, original['config']['seed']) if case.split == 'test']
        checksum = hashlib.sha256(json.dumps([case.model_dump(mode='json') for case in cases], sort_keys=True).encode()).hexdigest()
        if checksum != original['test_cases_sha256']:
            raise ValueError('Regenerated fixture does not match saved benchmark')
        scored = grade_saved_queries(rows, cases, database)
    out = source / 'value_scoring_v2'
    out.mkdir(exist_ok=False)
    by_id = {case.question_id: case for case in cases}
    summary = {'status': 'complete', 'model_calls': 0,
        'parent_records_sha256': hashlib.sha256((source / 'project5_case_results.json').read_bytes()).hexdigest(),
        'test_cases_sha256': checksum,
        'metric_source_sha256': hashlib.sha256((Path(__file__).parents[1] / 'src/project5_agent/semantic_scoring.py').read_bytes()).hexdigest(),
        'metric_definition': 'Aliases ignored; column positions, duplicates, NULLs and gold ORDER BY retained; numeric abs tolerance 1e-6, relative 1e-9. Fixed-fixture equivalence, not general query correctness. No feedback reaches the planner.',
        **{system: _summary([r for r in scored if r['system'] == system], by_id) for system in ['baseline', 'governed']}}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2))
    (out / 'per_case.json').write_text(json.dumps(scored, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--work-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(rescore(args.source, args.work_dir), indent=2))
