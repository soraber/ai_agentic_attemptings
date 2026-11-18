import json
import pytest
from project6_agent.swebench import harness_command, public_view, select_cases, write_predictions


def case(identifier='repo__project-1'):
    return {'instance_id':identifier,'repo':'repo/project','base_commit':'a'*40,'problem_statement':'Fix the public issue',
            'version':'1','patch':'gold-secret','test_patch':'hidden-assertions','hints_text':'hidden hint',
            'FAIL_TO_PASS':['test_gold'],'PASS_TO_PASS':['test_old']}


def test_public_context_excludes_all_oracle_material():
    public=public_view(case())
    assert set(public)=={'instance_id','repo','base_commit','problem_statement','version'}
    assert 'gold-secret' not in json.dumps(public)
    with pytest.raises(ValueError):public_view({**case(),'base_commit':'main'})


def test_selection_and_frozen_predictions_include_failed_cases(tmp_path):
    rows=[case(f'repo__project-{i}') for i in range(3)]
    assert select_cases(rows,['repo/project'],2)==select_cases(rows,['repo/project'],2)
    ids=[r['instance_id'] for r in rows]
    predictions=[{'instance_id':i,'model_name_or_path':'fixture','model_patch':''} for i in ids]
    write_predictions(predictions,ids,tmp_path/'predictions.jsonl')
    assert len((tmp_path/'predictions.jsonl').read_text().splitlines())==3
    with pytest.raises(ValueError):write_predictions(predictions[:1],ids,tmp_path/'bad.jsonl')
    with pytest.raises(ValueError):write_predictions([{**p,'patch':'gold'} for p in predictions],ids,tmp_path/'bad.jsonl')


def test_official_harness_uses_frozen_local_dataset_and_no_shell():
    command=harness_command('python','sealed.json','predictions.jsonl','new_run_1')
    assert command[1:3]==['-m','swebench.harness.run_evaluation']
    assert command[command.index('--dataset_name')+1]=='sealed.json'
    assert command[command.index('--max_workers')+1]=='1'
    with pytest.raises(ValueError):harness_command('python','sealed.json','p.jsonl','bad; command')
