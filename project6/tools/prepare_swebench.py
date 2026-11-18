"""Prepare public planner tasks and isolated gold evaluator input, without model calls."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from project6_agent.swebench import DATASET,REVISION,SOURCE_HASHES,DEV_REPOS,TEST_REPOS,public_view,select_cases


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'data/cache/swebench-v2')
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    import pyarrow.parquet as pq
    selected={}
    for split,repos,count in [('dev',DEV_REPOS,4),('test',TEST_REPOS,8)]:
        path=args.data_dir/f'{split}-00000-of-00001.parquet'
        with path.open('rb') as handle: actual=hashlib.file_digest(handle,'sha256').hexdigest()
        if actual!=SOURCE_HASHES[split]: raise ValueError('Dataset source checksum mismatch')
        selected[split]=select_cases(pq.read_table(path).to_pylist(),repos,count)
    if {r['instance_id'] for r in selected['dev']} & {r['instance_id'] for r in selected['test']}:
        raise ValueError('Development/test overlap')
    args.output.mkdir(parents=True,exist_ok=False)
    hashes={}
    for split,rows in selected.items():
        for kind,payload in [('public',[public_view(row) for row in rows]),('sealed_evaluator',rows)]:
            name=f'{split}_{kind}.json'; path=args.output/name
            path.write_text(json.dumps(payload,indent=2)+'\n')
            hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    args.evidence.parent.mkdir(parents=True,exist_ok=True)
    with args.evidence.open('x') as handle:
        json.dump({'status':'prepared_only','dataset':DATASET,'revision':REVISION,'source_sha256':SOURCE_HASHES,
            'task_ids':{split:[row['instance_id'] for row in rows] for split,rows in selected.items()},
            'base_commits':{row['instance_id']:row['base_commit'] for rows in selected.values() for row in rows},
            'input_sha256':hashes,'model_calls':0,'official_harness_executed':False,
            'limits':'Public benchmark may be contaminated; no correctness or model-comparison result yet.'},handle,indent=2)
    print({split:len(rows) for split,rows in selected.items()})


if __name__=='__main__':main()
