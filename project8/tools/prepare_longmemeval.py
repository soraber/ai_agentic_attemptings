"""Prepare a frozen public benchmark slice; no model calls or raw data publication."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from project8_agent.longmemeval import DATASET, REVISION, SOURCE_SHA256, category, public_case, select_cases


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--per-type',type=int,default=2)
    parser.add_argument('--output',type=Path,default=ROOT/'data/cache/longmemeval-v2')
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    with args.input.open('rb') as handle: checksum=hashlib.file_digest(handle,'sha256').hexdigest()
    if checksum!=SOURCE_SHA256: raise ValueError('Expected the pinned cleaned S file, not oracle/modified data')
    rows=json.loads(args.input.read_text());selected=select_cases(rows,args.per_type)
    checked=[public_case(row) for row in selected]
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'selected.json').write_text(json.dumps(selected)+'\n')
    args.evidence.parent.mkdir(parents=True,exist_ok=True)
    with args.evidence.open('x') as handle:
        json.dump({'status':'prepared_and_schema_validated','dataset':DATASET,'revision':REVISION,
            'source_sha256':checksum,'source_examples':len(rows),'selected_ids':[r['question_id'] for r in selected],
            'strata':{name:sum(category(r)==name for r in selected) for name in set(category(r) for r in selected)},
            'selected_sha256':hashlib.sha256((args.output/'selected.json').read_bytes()).hexdigest(),
            'history_events':[len(public['events']) for public,gold in checked],
            'model_calls':0,'quality_result':None,'raw_data_committed':False},handle,indent=2)
    print({'source_examples':len(rows),'selected':len(selected),'model_calls':0})


if __name__=='__main__': main()
