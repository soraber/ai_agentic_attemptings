from __future__ import annotations

import json,shutil
from pathlib import Path


HIDDEN_ASSERTIONS={
    "bitcount":"assert bitcount(0)==0\nassert bitcount(2**20-1)==20",
    "bucketsort":"assert bucketsort([3,1,3,0],4)==[0,1,3,3]",
    "find_first_in_sorted":"assert find_first_in_sorted([1,2,2,2,4],2)==1\nassert find_first_in_sorted([],2)==-1",
    "flatten":"assert list(flatten([1,[2,[3]],4]))==[1,2,3,4]",
    "gcd":"assert gcd(48,18)==6\nassert gcd(7,0)==7",
    "get_factors":"assert get_factors(12)==[2,2,3]\nassert get_factors(1)==[]",
    "hanoi":"assert hanoi(2)==[(1,2),(1,3),(2,3)]",
    "is_valid_parenthesization":"assert is_valid_parenthesization('(())')\nassert not is_valid_parenthesization('(()')",
    "levenshtein":"assert levenshtein('kitten','sitting')==3\nassert levenshtein('', 'abc')==3",
    "lis":"assert lis([3,1,2,5,4])==3\nassert lis([])==0",
    "mergesort":"assert mergesort([3,1,2,1])==[1,1,2,3]",
    "quicksort":"assert quicksort([3,1,3,2])==[1,2,3,3]",
}


def prepare_case(quixbugs_root:str|Path,case:dict,destination:str|Path)->dict[str,object]:
    source=Path(quixbugs_root); destination=Path(destination)
    if destination.exists(): shutil.rmtree(destination)
    (destination/"python_programs").mkdir(parents=True); (destination/"python_testcases").mkdir(); (destination/"json_testcases").mkdir()
    algorithm=case["bug_id"]
    for relative in ["conftest.py",case["source"],case["public_test"],"python_testcases/load_testdata.py",f"json_testcases/{algorithm}.json"]:
        target=destination/relative; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source/relative,target)
    hidden=destination/f"test_hidden_{algorithm}.py"
    hidden.write_text(f"from python_programs.{algorithm} import {algorithm}\n\ndef test_hidden_regressions():\n    " + HIDDEN_ASSERTIONS[algorithm].replace("\n","\n    ") + "\n",encoding="utf-8")
    return {"root":destination,"source":case["source"],"public_tests":[case["public_test"]],"hidden_tests":[hidden.name]}


def load_manifest(path:str|Path)->dict: return json.loads(Path(path).read_text())
