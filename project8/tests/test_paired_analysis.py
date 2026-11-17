import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('paired', Path(__file__).parents[1] / 'tools/analyze_saved_ablation.py')
paired = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paired)


def rows(values):
    return [dict(sample_id=f'c{i // 2}', qa_index=i, question=str(i), gold=str(i), token_f1=v)
            for i, v in enumerate(values)]


def test_constant_paired_improvement():
    result = paired.paired_interval(rows([0, 0, 0, 0]), rows([1, 1, 1, 1]), 'token_f1', 100)
    assert result == dict(pairs=4, conversations=2, dense_minus_lexical=1.0, ci95=[1.0, 1.0])


def test_pairing_rejects_missing_or_duplicate_questions():
    with pytest.raises(ValueError):
        paired.paired_interval(rows([0, 1]), rows([0]), 'token_f1')
    with pytest.raises(ValueError):
        paired.paired_interval(rows([0]) * 2, rows([0]) * 2, 'token_f1')


def test_reproducible_intervals_and_reference_drift():
    a, b = rows([0, .5, 1, 0]), rows([.5, .5, 0, 1])
    assert paired.paired_interval(a, b, 'token_f1') == paired.paired_interval(a, b, 'token_f1')
    b[0]['gold'] = 'changed'
    with pytest.raises(ValueError):
        paired.paired_interval(a, b, 'token_f1')
