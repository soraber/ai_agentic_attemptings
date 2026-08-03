# Project 5: Governed Text-to-SQL Analyst

A controlled comparison between one-shot SQL generation and a governed analytics
agent with schema retrieval, SQL AST validation, row/column policy, bounded repair,
PII masking, read-only execution, and export approval.

## Status

Prepared for execution. Deterministic policy and database tests may run without an
API key; final model-backed results are intentionally absent.

## Architecture

```text
question -> schema retrieval -> typed query plan -> SQLGlot AST policy
                                                     |
                              blocked <--------------+
                                                     |
                                                     v
                                          EXPLAIN -> read-only query
                                                     |
                                        error -> bounded repair
                                                     |
                                             mask PII -> approve export
```

## Repository Map

| Path | Purpose |
| --- | --- |
| `project5_governed_text_to_sql.ipynb` | Stable-cell Colab experiment |
| `RUNBOOK.md` | Commands, cells, secrets, budgets, and troubleshooting |
| `config/default.json` | Data split, governance, model, and budget settings |
| `data/cache/project5_questions.json` | Fixed 50-question benchmark |
| `src/project5_agent/` | Database, schemas, governance, analyst, and evaluation |
| `tests/` | Dataset, AST policy, repair, masking, and export tests |
| `tools/` | Dataset, notebook, report, and validation utilities |
| `background/project5_background.md` | Text-to-SQL and governance concepts |
| `debug_log/project5_debug_log.md` | Cell-specific issue history |
| `output/` | Measured summaries, samples, traces, charts, and PDF |

## Quick Start

```bash
python -m pip install -r requirements-colab.txt
python -m pip install -e . --no-deps
python tools/generate_dataset.py
pytest -q
python tools/validate_project.py
```

All data is synthetic. Execution is restricted to a local read-only DuckDB file;
no external database, warehouse, or export destination is contacted.
