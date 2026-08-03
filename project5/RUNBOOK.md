# Project 5 Execution Runbook

Use a fresh Google Colab A100 runtime for `local_gpu`; CPU is sufficient for
deterministic or OpenAI-backed execution. Run cells in order and do not enable a
model-backed evaluation until deterministic checks pass.

| Cell | Purpose |
| --- | --- |
| `P05-C00` | Scope, comparison, success criteria, and safety boundary |
| `P05-C01` | Clone once, install bounded dependencies, print CUDA/GPU status |
| `P05-C02` | Select `deterministic`, `openai`, or `local_gpu`; load a secret only for OpenAI |
| `P05-C03` | Reuse or generate the synthetic DuckDB and 50-question benchmark |
| `P05-C04` | Verify development/test split and hidden-label isolation |
| `P05-C05` | Run one-shot baseline smoke case |
| `P05-C06` | Run governed analyst and dense schema-retrieval smoke test |
| `P05-C07` | Run deterministic policy, repair, masking, and export tests |
| `P05-C08` | Run paired evaluation when `RUN_FULL_EVAL=True` |
| `P05-C09` | Inspect blocked, repaired, and failed representative cases |
| `P05-C10` | Generate measured charts/PDF and validate output contract |

## Colab Commands

```bash
python -m pip install --upgrade-strategy only-if-needed -r requirements-colab.txt
python -m pip install -e . --no-deps
python -m pip check
```

Unrelated preinstalled-package conflicts are displayed but do not abort the setup.
Project 5 import smoke tests do fail fast.

## Modes and Budgets

For the A100 comparison use:

```python
EVAL_BACKEND = "local_gpu"
RUN_FULL_EVAL = True
```

The local path loads `Qwen/Qwen2.5-Coder-7B-Instruct` once in BF16 and
`sentence-transformers/all-MiniLM-L6-v2` for normalized schema embeddings. It
writes only to `output/gpu/`. OpenAI mode retains the existing 180-call,
500-output-token, two-retry, USD 6 limits and writes to `output/`.

Model sources:

- https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct
- https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

## Governance Checks

- Parse one DuckDB statement with SQLGlot.
- Permit query expressions only; reject DDL, DML, commands, and external I/O.
- Enforce approved tables, regions, columns, and a maximum result limit.
- Deny direct `email` and `card_last4` selection for ordinary analyst scope.
- Run `EXPLAIN` before execution and use a read-only DuckDB connection.
- Mask residual PII defensively and require approval before file export.
- Treat database cell text as untrusted data, never as agent instructions.

## Output Contract

After execution, `output/` must contain final summary JSON, representative samples,
trace JSONL, report PDF, and four report assets. Run:

```bash
python tools/validate_project.py --require-results
```

For every notebook edit, record the exact `P05-CXX` cell in the debug log.
