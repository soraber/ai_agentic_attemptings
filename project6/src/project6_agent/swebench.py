"""Frozen real-repository task preparation, separate from the final official harness."""
import json
import random
import re
from pathlib import Path

DATASET='princeton-nlp/SWE-bench_Lite'
REVISION='6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2'
SOURCE_HASHES={'dev':'8312f321838051849d2fa7c6ca071244733a3e90bb517ff6ca8186f722199b5c',
               'test':'7a21f37b8bc179c7db5beeb14e88ac538ba283455c776e6b2535bbfb6e3551b4'}
DEV_REPOS=('pylint-dev/astroid','marshmallow-code/marshmallow')
TEST_REPOS=('psf/requests','pallets/flask','pytest-dev/pytest','sphinx-doc/sphinx')
PUBLIC_FIELDS=('instance_id','repo','base_commit','problem_statement','version')


def public_view(row):
    value={key:row[key] for key in PUBLIC_FIELDS}
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',value['repo']):
        raise ValueError('Invalid repository name')
    if not re.fullmatch(r'[a-f0-9]{40}',value['base_commit']):
        raise ValueError('Immutable base commit required')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+',value['instance_id']) or not value['problem_statement'].strip():
        raise ValueError('Invalid task identifier or issue text')
    return value


def select_cases(rows, repositories, count, seed=2026):
    if count<1 or len({r['instance_id'] for r in rows})!=len(rows):
        raise ValueError('Invalid count or duplicate instances')
    rng=random.Random(seed)
    groups={repo:sorted([r for r in rows if r['repo']==repo],key=lambda r:r['instance_id']) for repo in repositories}
    for group in groups.values(): rng.shuffle(group)
    selected=[]
    while len(selected)<count:
        before=len(selected)
        for repo in sorted(groups):
            if groups[repo]: selected.append(groups[repo].pop())
            if len(selected)==count: break
        if before==len(selected): raise ValueError('Insufficient tasks in the preregistered repositories')
    for row in selected: public_view(row)
    return selected


def write_predictions(rows, expected_ids, path):
    expected=set(expected_ids)
    if len(rows)!=len(expected) or {r.get('instance_id') for r in rows}!=expected:
        raise ValueError('Predictions must include every frozen instance exactly once; retain empty failed patches')
    for row in rows:
        if set(row)!={'instance_id','model_name_or_path','model_patch'}:
            raise ValueError('Only official prediction fields are allowed; never export gold patches')
        if not all(isinstance(v,str) for v in row.values()) or len(row['model_patch'])>100000:
            raise ValueError('Invalid or oversized prediction')
    with Path(path).open('x') as handle:
        for row in rows: handle.write(json.dumps(row)+'\n')


def harness_command(python, sealed_dataset, predictions, run_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',run_id):
        raise ValueError('Use a unique, simple run ID for each frozen prediction set')
    return [str(python),'-m','swebench.harness.run_evaluation','--dataset_name',str(sealed_dataset),
            '--predictions_path',str(predictions),'--max_workers','1','--run_id',run_id]
