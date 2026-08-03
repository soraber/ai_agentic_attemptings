# Project 6: Test-Driven Code-Repair Agent

A constrained coding-agent experiment comparing one-shot patches with a bounded
inspect, patch, test, reflect, accept-or-rollback loop on a pinned Python QuixBugs
subset.

## Status

Prepared for execution. Local fixture tests validate repository mapping, patch
policy, subprocess limits, hidden-test gating, and exact rollback without model
calls. Final QuixBugs results are absent.

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
