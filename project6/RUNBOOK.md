# Project 6 Execution Runbook

Use a fresh Colab A100 runtime for the local model comparison. CPU is sufficient
for deterministic tests and the preserved OpenAI-backed workflow.

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

## Safety Limits

- Only paths listed by the benchmark case may change.
- Unified diffs must pass `git apply --check` and a 30 changed-line budget.
- Tests run in subprocesses with timeout, output truncation, and best-effort Unix
  CPU/address-space limits.
- A maximum of three patches may be attempted.
- Public and hidden tests must pass before acceptance.
- Failed candidates are rolled back byte-for-byte.

API mode is opt-in and limited to 220 calls, 900 output tokens per patch, three
attempts per bug, and USD 8 estimated cost. Record every notebook edit by
`P06-CXX` in the debug log.

For the A100 path set `EVAL_BACKEND="local_gpu"` and run `P06-C01` through
`P06-C10`. One shared `Qwen/Qwen2.5-Coder-7B-Instruct` instance serves all cases
in BF16, avoiding repeated model loads. GPU artifacts go to `output/gpu/`; the
model only proposes diffs and cannot bypass the path allowlist, line budget,
`git apply --check`, tests, or rollback.

Model source: https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct
