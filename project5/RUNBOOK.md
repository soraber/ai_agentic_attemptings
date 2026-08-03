# Project 5 Execution Runbook

Use a fresh Google Colab CPU runtime. Run cells in order and keep API evaluation
disabled until deterministic checks pass.

| Cell | Purpose |
| --- | --- |
| `P05-C00` | Scope, comparison, success criteria, and safety boundary |
| `P05-C01` | Clone once, install bounded dependencies, import smoke test |
| `P05-C02` | Load config and optional `OPENAI_API_KEY` without printing it |
| `P05-C03` | Reuse or generate the synthetic DuckDB and 50-question benchmark |
| `P05-C04` | Verify development/test split and hidden-label isolation |
| `P05-C05` | Run one-shot baseline smoke case |
| `P05-C06` | Run governed analyst with AST policy and repair |
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

Start with:

```python
RUN_API_EVAL = False
RUN_FULL_EVAL = False
```

After `P05-C07` passes, enable full deterministic evaluation. API mode uses the
Responses API and must remain within 180 calls, 500 output tokens per call, two
retries, and USD 6 estimated cost.

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
