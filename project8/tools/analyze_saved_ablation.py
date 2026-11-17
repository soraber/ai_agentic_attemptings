"""Paired descriptive uncertainty for frozen same-answerer retrieval outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path


def paired_interval(lexical, dense, metric, resamples=2000, seed=2026):
    def keyed(rows):
        result = {(r['sample_id'], r['qa_index']): r for r in rows}
        if len(result) != len(rows):
            raise ValueError('Duplicate question within a system')
        return result

    left, right = keyed(lexical), keyed(dense)
    if not left or left.keys() != right.keys():
        raise ValueError('Paired evaluation requires identical nonempty questions')
    groups = defaultdict(list)
    for key in sorted(left):
        if (left[key]['question'], left[key]['gold']) != (right[key]['question'], right[key]['gold']):
            raise ValueError('Question/reference drift between retrieval arms')
        a, b = left[key][metric], right[key][metric]
        if a is None or b is None:
            continue
        groups[key[0]].append(float(b) - float(a))
    count = sum(map(len, groups.values()))
    if not count or resamples < 2:
        raise ValueError('Insufficient eligible pairs or resamples')
    rng = random.Random(seed)
    draws = sorted(sum(rng.choice(values) for values in groups.values() for _ in values) / count
                   for _ in range(resamples))

    def percentile(p):
        position = p * (len(draws) - 1)
        low = int(position)
        high = min(low + 1, len(draws) - 1)
        return draws[low] + (draws[high] - draws[low]) * (position - low)

    return {'pairs': count, 'conversations': len(groups),
            'dense_minus_lexical': statistics.fmean(v for values in groups.values() for v in values),
            'ci95': [percentile(.025), percentile(.975)]}


def analyze(run_dir, resamples=2000, seed=2026):
    files = {arm: run_dir / arm / 'project8_case_results.json' for arm in ('lexical', 'dense')}
    data = {arm: json.loads(path.read_text()) for arm, path in files.items()}
    comparisons = {}
    for system in ('window', 'episodic', 'hybrid'):
        selected = {arm: [r for r in rows if r['system'] == system] for arm, rows in data.items()}
        comparisons[system] = {
            metric: paired_interval(selected['lexical'], selected['dense'], metric, resamples, seed)
            for metric in ('token_f1', 'exact_match', 'retrieved_evidence_recall', 'cited_evidence_recall')
        }
    return {'analysis_version': 'paired-v1', 'resamples': resamples, 'seed': seed,
            'method': 'Paired question bootstrap within each fixed conversation; percentile 95% intervals.',
            'limitations': 'Conditional on two selected conversations, not new-conversation generalization. '
                           'Questions may remain dependent; intervals are descriptive and not corrected '
                           'for multiple comparisons. Generation failures stay in the answer scores. '
                           'Cached window outputs are paired identical controls, not a latency comparison.',
            'source_sha256': {arm: hashlib.sha256(path.read_bytes()).hexdigest() for arm, path in files.items()},
            'comparisons': comparisons}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    args = parser.parse_args()
    result = analyze(args.run_dir)
    destination = args.run_dir / 'paired_analysis_v1.json'
    with destination.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2))
