# SWE-bench Lite Preparation

Status: four development tasks and eight test tasks are frozen and schema-checked.
No model predictions or official harness evaluation have been run for this slice.
The existing QuixBugs measurements remain separate historical experiments.

## Inputs And Isolation

- Dataset: `princeton-nlp/SWE-bench_Lite`, revision
  `6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2`.
- Seed 2026; development repositories: astroid and marshmallow. Test repositories:
  requests, Flask, pytest, and Sphinx. Selection is round-robin after seeded shuffle.
- Planner input contains only issue text, repository, immutable base commit,
  instance ID, and version. Gold patches and evaluator tests are not planner input.
- Raw inputs stay in ignored `data/cache/`. The word `sealed` denotes evaluator-only
  handling, not encryption or a filesystem permission boundary. Never mount those
  files into the repair workspace. Model-generated patches require isolated execution.

The public [preparation manifest](output/runs/upgrade-v2/swebench_preparation/manifest.json)
records source and prepared-file hashes, selected IDs, base commits, and zero model calls.

## Reproduce Preparation

Use Python 3.11 in an isolated environment, from the repository root. The following
preparation-only libraries were used locally; they are not the official harness:

```sh
uv venv --python 3.11.17 .venv-benchmark
uv pip install --python .venv-benchmark/bin/python huggingface-hub==2.4.0 pyarrow==26.0.1
.venv-benchmark/bin/hf download princeton-nlp/SWE-bench_Lite --repo-type dataset --revision 6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2 --include 'data/dev-*.parquet' 'data/test-*.parquet' --local-dir project6/data/cache/benchmark-downloads
.venv-benchmark/bin/python project6/tools/prepare_swebench.py --data-dir project6/data/cache/benchmark-downloads/data --evidence project6/output/runs/upgrade-v2/swebench_preparation/manifest.json
```

The dataset is public and needs no token. Preparation checks the exact parquet
SHA256 values before parsing. Existing preparation directories/evidence are never
overwritten; inspect/reuse a matching saved manifest, or select new `--output` and
`--evidence` paths. The already-prepared local cache should not be downloaded again.
Notebook cells 14-15 (`P06-C13`, `P06-C14`) inspect only the public task view.

## Deferred Evaluation

The SWE-bench 5.0.2 evaluator CLI was installed in a separate hash-verified
Python 3.11 environment. The 94-package lock had zero reported advisories at
preflight. The CLI help ran successfully. Inspection of the installed evaluator
showed its Docker launch paths add `SYS_ADMIN`. Project 6's generated-patch
executor drops all capabilities, so the stock evaluator was held at preflight.
The Docker VM reported ARM64 and 7.75 GiB RAM. Official model scoring still needs
a separate evaluator that meets the isolation and resource requirements.

The compact patched sandbox regression rerun passed all 24 tests, including its
two real-container checks. These totals are for the existing regression suite.

1. Pin and audit the official SWE-bench harness separately. Its per-repository Docker
   images and test dependencies are much larger than the compact QuixBugs image;
   review disk, memory, architecture, and time budgets before building them.
2. Check out each public task's base commit in an isolated workspace. Give the
   planner the public issue and bounded repository context only. Select patches
   using development/public tests, with the same call, token, time, and attempt
   limits for each edit interface. Do not feed final evaluator failures back.
3. Freeze all predictions, including empty patches for failed attempts, using
   `project6_agent.swebench.write_predictions`. Required fields are `instance_id`,
   `model_name_or_path`, and `model_patch`; every frozen test ID must occur once.
4. In a separate evaluator environment, use `harness_command(...)` to construct
   the official `python -m swebench.harness.run_evaluation` command with the sealed
   dataset JSON, predictions JSONL, `--max_workers 1`, and a fresh unique run ID.
   This helper does not execute the command. Keep evaluator data outside planner
   mounts and do not reuse a cached run ID for changed predictions.
5. Report resolved count/total, execution and patch failures, calls/tokens/cost,
   elapsed time, exact model/harness/image revisions, and paired per-instance
   outcomes. Eight public tasks are a small diagnostic slice, not a leaderboard
   score or strong evidence of generalization; benchmark contamination is possible.

Sources: [SWE-bench Lite dataset](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite),
[official evaluation guide](https://www.swebench.com/SWE-bench/guides/evaluation/),
[official harness](https://github.com/SWE-bench/SWE-bench).
