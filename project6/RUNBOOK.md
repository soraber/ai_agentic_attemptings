# Project 6 Execution Runbook

Use a Docker-enabled host for generated-code evaluation. CPU plus the OpenAI API
is sufficient; standard Colab alone does not supply the required isolated executor.
Never switch to trusted-fixture execution for model-generated code.

| Cell | Purpose |
| --- | --- |
| `P06-C00` | Scope, threat boundary, comparison, and metrics |
| `P06-C01` | Clone/install/import smoke test and print CUDA/GPU status |
| `P06-C02` | Select `openai` or `local_gpu`; load a secret only for OpenAI |
| `P06-C03` | Download pinned QuixBugs once and verify commit |
| `P06-C04` | Load 4 development and 8 held-out cases |
| `P06-C05` | One-shot fixture repair smoke test |
| `P06-C06` | Bounded repair loop with test feedback and rollback |
| `P06-C07` | Patch-policy, timeout, hidden-test, and rollback tests |
| `P06-C08` | Paired held-out evaluation when enabled |
| `P06-C09` | Patch and failure analysis |
| `P06-C10` | Measured report generation and validation |
| `P06-C11` | Development-only edit-interface comparison scope |
| `P06-C12` | Optional four-development-bug comparison; no final-test rerun |

## Docker Preflight

From the project directory, with Docker running:

```bash
docker build -f tools/Dockerfile.sandbox -t project6-test-runner:upgrade-v1 tools
PROJECT6_DOCKER_TESTS=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_docker_integration.py -q -p no:cacheprovider
```

Use the isolated project environment captured by the upgrade dependency snapshot.
If Docker Desktop reports a missing bind path after pytest recreates a temporary
directory, rerun with a new `--basetemp` path inside the workspace, not with broader
filesystem permissions. Docker Desktop's CLI and credential helper must be on PATH.

## Safety Limits

- Only paths listed by the benchmark case may change.
- Unified diffs must pass `git apply --check` and a 30 changed-line budget.
- Tests run in a non-root Docker container with no network, read-only root and
  workspace, dropped capabilities, no-new-privileges, 512 MiB memory, one CPU,
  64 processes, a bounded temporary filesystem, timeout and output limits.
- A maximum of three patches may be attempted.
- Public tests guide selection; hidden tests run once afterward in separate staging
  and never feed back to the planner. Infrastructure errors do not reopen selection.
- Failed candidates are rolled back byte-for-byte.

API mode is opt-in and limited to 220 calls, 900 output tokens per patch by default,
three attempts per bug, and USD 8 estimated cost shared across all API planners.
Failed calls count and retain a conservative cost reservation. Record every notebook edit by
`P06-CXX` in the debug log.

On a GPU host that also supports Docker, set `EVAL_BACKEND="local_gpu"`.
One shared `Qwen/Qwen2.5-Coder-7B-Instruct` instance serves all cases
in BF16. New artifacts go to `output/runs/upgrade-v1/`; the
model only proposes diffs and cannot bypass the path allowlist, line budget,
`git apply --check`, tests, or rollback.

## Structured Edits

Cell 13 (`P06-C12`) is disabled by default. Enable `RUN_EDIT_FORMAT_DEVELOPMENT`
only after setup/config/data/tests and hidden API authentication. It compares both
edit interfaces on four development bugs, at most three attempts each, with a $2
aggregate cap and 2,048 output tokens. Results remain explicitly development-only.

To select structured edits for a separately versioned API experiment, before cell 9:

```python
config = config.model_copy(update={"edit_format": "structured_edits"})
```

Exact anchors must be unique and non-overlapping in the original source. The
harness validates syntax and generates the unified diff; the same path/line/sandbox
checks still apply. Structured edits are currently API-only. Do not treat rerunning
the diagnosed test set as a fresh blind holdout.

[Model source](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)
