import json
from types import SimpleNamespace

import pytest
from project8_agent.longmemeval import bounded_context, evaluate, public_case, select_cases


def fixture(kind='temporal-reasoning',identifier='q1'):
    return {'question_id':identifier,'question_type':kind,'question':'What changed?',
        'question_date':'2026/01/02','answer':'blue','haystack_session_ids':['answer_session'],
        'haystack_dates':['2026/01/01'],'haystack_sessions':[[{'role':'user','content':'It is blue.','has_answer':True}]],
        'answer_session_ids':['answer_session']}


def test_gold_fields_and_informative_ids_do_not_reach_retriever():
    public,gold=public_case(fixture())
    raw=json.dumps(public)
    assert all(key not in raw for key in ['has_answer','answer_session','question_type'])
    assert public['events'][0]['text']=='It is blue.' and gold['event_ids']
    absent,_=public_case(fixture(identifier='q1_abs'))
    assert not absent['sample_id'].endswith('_abs')


def test_context_budget_and_evidence_tampering():
    public,_=public_case(fixture());events=public['events']
    assert bounded_context(events,events,lambda rows:len(rows)*10,5)==[]
    with pytest.raises(ValueError,match='modified'):
        bounded_context(events,[{**events[0],'text':'injected'}],lambda rows:10,100)


def test_balanced_selection_is_reproducible_and_explicit():
    rows=[fixture(),fixture('knowledge-update','q2'),fixture(identifier='q3_abs')]
    assert select_cases(rows,1)==select_cases(rows,1)
    with pytest.raises(ValueError):select_cases(rows,2)


def test_real_adapter_loop_keeps_errors_and_separates_proxy_from_official(tmp_path):
    rows=[fixture(),fixture('knowledge-update','q2'),fixture(identifier='q3_abs')]
    class Answerer:
        def answer(self,sample_id,question,system,context):
            assert 'has_answer' not in json.dumps(context)
            if system=='failed':raise ValueError('authored failure')
            return SimpleNamespace(answer='blue',abstained=False)
    result=evaluate(rows,Answerer(),{'ok':lambda events,q:events,'failed':lambda events,q:events},
        lambda context:len(json.dumps(context).split()),'authored-test-counter-not-a-model-tokenizer',tmp_path/'run')
    assert result['official_semantic_accuracy'] is None
    assert result['summary']['failed']['knowledge-update']['errors']==1
    assert result['summary']['ok']['abstention']['abstention_correct']==0
    assert len((tmp_path/'run/ok_hypotheses.jsonl').read_text().splitlines())==3
    assert all(json.loads(line)['hypothesis']=='' for line in (tmp_path/'run/failed_hypotheses.jsonl').read_text().splitlines())


def test_malformed_answer_is_retained_as_failure(tmp_path):
    class Answerer:
        def answer(self,*args):return SimpleNamespace(answer='',abstained='false')
    result=evaluate([fixture(identifier='q_abs')],Answerer(),{'arm':lambda events,q:events},
        lambda rows:len(rows),'test-counter',tmp_path/'run')
    assert result['summary']['arm']['abstention']['errors']==1
    assert result['summary']['arm']['abstention']['abstention_correct']==0
