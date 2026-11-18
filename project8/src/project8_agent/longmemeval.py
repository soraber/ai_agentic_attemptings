"""LongMemEval-S adapter: gold labels never enter retrieval or generation inputs."""
import hashlib
import json
import random
import statistics
import time
from pathlib import Path

from .evaluation import token_f1

DATASET = 'xiaowu0162/longmemeval-cleaned'
REVISION = '98d7416c24c778c2fee6e6f3006e7a073259d48f'
SOURCE_SHA256 = 'd6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442'
TARGET_TYPES = ('temporal-reasoning', 'knowledge-update', 'abstention')


def category(row):
    return 'abstention' if row['question_id'].endswith('_abs') else row['question_type']


def select_cases(rows, per_type=2, seed=2026):
    if type(per_type) is not int or per_type < 1:
        raise ValueError('per_type must be positive')
    if len({row['question_id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate question IDs')
    rng = random.Random(seed)
    selected = []
    for name in TARGET_TYPES:
        pool = sorted((r for r in rows if category(r)==name), key=lambda r:r['question_id'])
        if len(pool)<per_type:
            raise ValueError(f'Not enough cases in {name}')
        selected.extend(rng.sample(pool,per_type))
    return selected


def public_case(row):
    sessions, ids, dates = row['haystack_sessions'], row['haystack_session_ids'], row['haystack_dates']
    if not sessions or not len(sessions)==len(ids)==len(dates) or len(set(ids))!=len(ids):
        raise ValueError('Malformed or duplicate history sessions')
    events = []
    mapping = {}
    support_events = set()
    for session, identifier, date in zip(sessions,ids,dates):
        opaque = 's-'+hashlib.sha256((row['question_id']+'\0'+identifier).encode()).hexdigest()[:20]
        mapping[identifier] = opaque
        for index, turn in enumerate(session):
            if turn.get('role') not in {'user','assistant'} or not isinstance(turn.get('content'),str):
                raise ValueError('Unexpected history turn')
            event_id = f'{opaque}-t{index}'
            events.append({'event_id':event_id, 'session':opaque, 'timestamp':date,
                           'speaker':turn['role'], 'text':turn['content']})
            if turn.get('has_answer') is True:
                support_events.add(event_id)
    if any(identifier not in mapping for identifier in row['answer_session_ids']):
        raise ValueError('Gold evidence references an absent session')
    public = {'sample_id':hashlib.sha256(row['question_id'].encode()).hexdigest()[:24],
              'question':f"As of {row['question_date']}: {row['question']}", 'events':events}
    gold = {'question_id':row['question_id'], 'category':category(row), 'answer':str(row['answer']),
            'answerable':category(row)!='abstention',
            'session_ids':{mapping[key] for key in row['answer_session_ids']}, 'event_ids':support_events}
    return public, gold


def bounded_context(events, anchors, count_tokens, token_budget):
    by_id = {event['event_id']:event for event in events}
    selected, seen = [], set()
    for anchor in anchors:
        identifier = anchor.get('event_id')
        if identifier not in by_id or anchor != by_id[identifier]:
            raise ValueError('Retriever returned unknown or modified evidence')
        if identifier in seen:
            continue
        candidate = selected+[by_id[identifier]]
        count = count_tokens(candidate)
        if type(count) is not int or count < 0:
            raise ValueError('Tokenizer must return a nonnegative integer')
        if count <= token_budget:
            selected = candidate
            seen.add(identifier)
    return selected


def evaluate(rows, answerer, retrievers, count_tokens, tokenizer_id, output_dir, token_budget=2048, seed=2026):
    if not tokenizer_id or token_budget<1 or not retrievers:
        raise ValueError('A named tokenizer, positive context budget, and retrieval arms are required')
    if not rows or len({row['question_id'] for row in rows})!=len(rows):
        raise ValueError('A nonempty, unique question set is required')
    if any(not name.replace('_','').isalnum() for name in retrievers):
        raise ValueError('Unsafe system identifier')
    output=Path(output_dir); output.mkdir(parents=True,exist_ok=False)
    records=[]; rng=random.Random(seed)
    for row in rows:
        public,gold=public_case(row)
        names=list(retrievers);rng.shuffle(names)
        for name in names:
            started=time.perf_counter(); error=None; answer=None; context=[]
            try:
                anchors=retrievers[name](public['events'],public['question'])
                context=bounded_context(public['events'],anchors,count_tokens,token_budget)
                candidate=answerer.answer(public['sample_id'],public['question'],name,context)
                if not isinstance(getattr(candidate,'answer',None),str) or type(getattr(candidate,'abstained',None)) is not bool:
                    raise ValueError('Answerer must return text and an explicit boolean abstention')
                if not candidate.answer.strip() and not candidate.abstained:
                    raise ValueError('Empty answer without explicit abstention')
                answer=candidate
            except Exception as exc:
                error=type(exc).__name__
            predicted='' if answer is None else answer.answer
            abstained=bool(answer is not None and answer.abstained)
            selected_sessions={item['session'] for item in context}
            selected_events={item['event_id'] for item in context}
            records.append({'question_id':gold['question_id'],'category':gold['category'],'system':name,
                'answer':predicted,'abstained':abstained,'error':error,
                'token_f1_proxy':(token_f1(predicted,gold['answer']) if not error else 0.0) if gold['answerable'] else None,
                'abstention_correct':float(abstained and not error) if not gold['answerable'] else None,
                'session_recall':len(selected_sessions&gold['session_ids'])/len(gold['session_ids']) if gold['session_ids'] else None,
                'retrieved_event_recall':len(selected_events&gold['event_ids'])/len(gold['event_ids']) if gold['event_ids'] else None,
                'context_tokens':count_tokens(context),'seconds':time.perf_counter()-started})
    summaries={}
    for name in retrievers:
        summaries[name]={}
        for kind in TARGET_TYPES:
            selected=[row for row in records if row['system']==name and row['category']==kind]
            summaries[name][kind]={'count':len(selected),'errors':sum(row['error'] is not None for row in selected)}
            for metric in ('token_f1_proxy','abstention_correct','session_recall','retrieved_event_recall'):
                values=[row[metric] for row in selected if row[metric] is not None]
                summaries[name][kind][metric]=statistics.fmean(values) if values else None
        predictions=[{'question_id':r['question_id'],'hypothesis':(
                         '' if r['error'] else r['answer'] or 'Insufficient evidence to answer.')}
                     for r in records if r['system']==name]
        (output/f'{name}_hypotheses.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in predictions))
    result={'version':'longmemeval-s-v1','dataset':DATASET,'revision':REVISION,'seed':seed,
        'question_ids':[r['question_id'] for r in rows],'tokenizer':tokenizer_id,'context_token_budget':token_budget,
        'summary':summaries,'official_semantic_accuracy':None,
        'official_scoring_rule':'Join grader outputs to per_case.json; any non-null error scores zero, including abstention tasks',
        'scope':'same-answerer retrieval comparison; lexical F1 is a proxy, not official LongMemEval accuracy'}
    (output/'per_case.json').write_text(json.dumps(records,indent=2)+'\n')
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
