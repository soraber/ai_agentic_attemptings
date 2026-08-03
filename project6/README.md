# Project 6: Test-Driven Code-Repair Agent

A constrained coding-agent experiment comparing one-shot patches with a bounded
inspect, patch, test, reflect, accept-or-rollback loop on a pinned Python QuixBugs
subset.

## Status

The OpenAI-backed QuixBugs comparison has been executed and saved in `output/`.
An A100 comparison is prepared under `output/gpu/` with one shared local BF16 code
model; patch policy, public/hidden tests, and rollback remain unchanged.

## Architecture

```text
issue + failing trace -> AST repository map -> fault localization -> patch plan
       -> diff policy -> git apply --check -> public tests -> hidden tests
       -> accept
       -> failure summary -> retry (max 3) or rollback
```

## Key Files

| Path | Purpose |
| --- | --- |
| `project6_test_driven_code_repair.ipynb` | Stable-cell Colab workflow |
| `data/quixbugs_manifest.json` | Twelve cases pinned to an exact upstream commit |
| `src/project6_agent/` | Mapping, patch policy, sandbox runner, workspace, and repair loop |
| `tests/` | Deterministic fixture tests including hidden regression and rollback |
| `tools/fetch_quixbugs.py` | Download-once pinned source preparation |
| `tools/generate_report.py` | Measured repair charts and PDF |
| `RUNBOOK.md` | Execution, cells, budgets, and debugging |

Every case starts from a fresh worktree copy. The agent may modify only the
declared Python source file and never sees gold patches during planning.

Set `EVAL_BACKEND="local_gpu"` in `P06-C02` to use
`Qwen/Qwen2.5-Coder-7B-Instruct` on an A100 without API calls.
