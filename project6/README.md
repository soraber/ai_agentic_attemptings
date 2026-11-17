# Project 6: Test-Driven Code-Repair Agent

A constrained coding-agent experiment comparing one-shot patches with a bounded
inspect, patch, test, reflect, accept-or-rollback loop on a pinned Python QuixBugs
subset.

## Status

The upgraded Docker-backed test run verified 7/8 bugs with one-shot and 6/8 with
the repair loop. Malformed model-written diffs caused failures. A separate
four-development-bug comparison reached 4/4 with structured source replacements
versus 2/4 with unified diffs. This is development evidence, not a new holdout score.
See [current evidence](../projects_info.md#upgrade-evidence) and [runbook](RUNBOOK.md).

Historical comparisons are retained: the API repair loop in `output/` reached 87.5%
verified repair on eight held-out defects. The A100 Qwen comparison in
`output/gpu/` reached 0% verified repair in both modes but preserved 100% rollback;
those old runs fed hidden-test feedback into selection and are not blind holdout estimates.

## Architecture

```text
issue + failing trace -> AST repository map -> fault localization -> patch plan
       -> exact edits or diff -> policy -> git apply --check -> public tests
                                                  failure -> rollback/retry (max 3)
                                                  success -> final hidden tests once
                                                               -> accept or reject/rollback
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
| `src/project6_agent/structured_edits.py` | Unique source anchors and harness-generated diffs |
| `src/project6_agent/edit_comparison.py` | Development-only edit-interface comparison |
| `tools/Dockerfile.sandbox` | Non-root, pinned-pytest executor image |
| `RUNBOOK.md` | Execution, cells, budgets, and debugging |

Every case starts from a fresh worktree copy. The agent may modify only the
declared Python source file and never sees gold patches during planning.

Set `EVAL_BACKEND="local_gpu"` in `P06-C02` to use
`Qwen/Qwen2.5-Coder-7B-Instruct` without API calls only on a GPU host that also
supports the required Docker isolation. Standard Colab alone is insufficient.
