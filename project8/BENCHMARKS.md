# LongMemEval-S Preparation

Status: MyPro completed the six-case, three-arm pilot with no execution errors.
The slice contains two cases each for temporal reasoning, knowledge updates, and
abstention. The run used one pinned Qwen2.5-7B-Instruct answerer. See the
[metrics snapshot](output/runs/upgrade-v2/20261118T102213022610Z/metrics_snapshot.json).
Official semantic grading remains open.

## Frozen Input

Dataset `xiaowu0162/longmemeval-cleaned`, revision
`98d7416c24c778c2fee6e6f3006e7a073259d48f`, file
`longmemeval_s_cleaned.json`. The source has 500 cases. Its SHA256 is
`d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442`.
This uses the full S histories, not the oracle evidence-only variant and not V2.

The adapter removes `has_answer`, answer labels, and question categories from
retrieval/generation inputs. It hashes informative session/question IDs so an
`_abs` suffix cannot reveal abstention gold. Role, date, and actual history text
remain available. Gold evidence IDs are consulted only after retrieval for scoring.
The [manifest](output/runs/upgrade-v2/longmemeval_preparation/manifest.json) records
selected IDs, stratum counts, source/subset hashes, history sizes, and zero model calls.

## Reproduce Preparation

From the repository root, use an isolated Python 3.11 environment. The download
library is pinned; no GPU is needed. Install the existing CPU lock for imports.

```sh
uv venv --python 3.11.17 .venv-benchmark
uv pip install --python .venv-benchmark/bin/python --require-hashes -r requirements-upgrade-cpu.hashes.txt
uv pip install --python .venv-benchmark/bin/python huggingface-hub==2.4.0
.venv-benchmark/bin/hf download xiaowu0162/longmemeval-cleaned longmemeval_s_cleaned.json --repo-type dataset --revision 98d7416c24c778c2fee6e6f3006e7a073259d48f --local-dir project8/data/cache/benchmark-downloads
.venv-benchmark/bin/python project8/tools/prepare_longmemeval.py --input project8/data/cache/benchmark-downloads/longmemeval_s_cleaned.json --per-type 2 --evidence project8/output/runs/upgrade-v2/longmemeval_preparation/manifest.json
```

Public access needs no token. The roughly 277 MB download and prepared raw subset
are ignored by git. Reuse the already-prepared local cache. The preparation command
refuses existing outputs; use distinct `--output`/`--evidence` paths for a separate
selection, and never adjust a frozen evaluation slice after seeing model results.

## Matched Evaluation

Notebook cell 13 (`P08-C12`) checks the opt-in `PORTFOLIO_LONGMEMEVAL=1` switch.
Cells 14-15 launch and check the run in the patched environment. The run used
one answerer and its actual tokenizer for recent-window, lexical episodic,
and lexical-plus-recency retrieval. The cell uses a 2,048-token context limit, identical
answerer settings, randomized arm order, and versioned run manifests. Unknown or
modified retrieved events fail validation. The adapter retains failed cases.

Results separate temporal/update lexical F1 proxies, abstention correctness,
retrieved session/event recall, context tokens, and latency. Lexical F1 is not
official LongMemEval accuracy. Official-format hypotheses are exported, but
semantic grading is a separate, unexecuted step with its own model/cost budget.
Join any future grader outputs to `per_case.json`: any generation or retrieval
error must score zero, even if a judge interprets empty text as abstention.

Six cases exercise the integration, not statistical significance. Before making
an optimization claim, freeze a larger balanced sample, compare paired outcomes
with uncertainty, and hold the answerer/context/generation budgets constant. Add
reranking only as a separate arm; do not attribute an answer-model change to memory.

Sources: [LongMemEval implementation and protocol](https://github.com/xiaowu0162/LongMemEval),
[cleaned dataset](https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned).
