# Project 5 Debug Log

Record date, environment, exact `P05-CXX` cell, symptom, root cause, minimal fix,
verification, and preservation of prior user edits.

## 2026-08-02 - Initial Scaffold

- **Environment:** Local pre-execution workspace
- **Notebook cell:** `P05-C00` through `P05-C10`
- **Symptom:** None
- **Fix:** Created the governed text-to-SQL experiment package
- **Verification:** Static validation and deterministic tests accompany the commit
- **Preservation:** New project; no prior Project 5 files existed

## 2026-08-03 - Local API Execution

- **Environment:** Local macOS kernel with temporary isolated dependencies; OpenAI Responses API
- **Notebook cells:** `P05-C01`, `P05-C02`, and executed `P05-C03` through `P05-C10`
- **Symptom:** The first one-case smoke command could not import `project5_agent`; no API request was made
- **Root cause:** The smoke-test process omitted the project `src` directory from `PYTHONPATH`
- **Fix:** Added the source path for local execution, added a skip-install guard in `P05-C01`, enabled the measured run in `P05-C02`, and added bounded retries plus token/cost accounting
- **Verification:** Live smoke request succeeded; the final expanded suite passed 10 tests; 40 test questions completed with 50 model calls; report and privacy validation passed; rendered PDF had no visible clipping or overlap
- **Preservation:** Retained VS Code's existing `Python 3 (ipykernel)` metadata and changed no dataset-preparation logic

## 2026-08-03 - A100 Local Planner Extension

- **Environment:** Local CPU interface validation; A100 execution path prepared
- **Notebook cells:** `P05-C01`, `P05-C02`, `P05-C06`, `P05-C08`, `P05-C09`, and `P05-C10`
- **Symptom:** The completed experiment exercised API generation but did not demonstrate local GPU inference or dense schema linking
- **Root cause:** The initial scope prioritized governed execution and reproducible API evaluation
- **Fix:** Added normalized MiniLM schema retrieval, a shared BF16 Qwen2.5-Coder planner, isolated `output/gpu/` artifacts, and patch-only notebook updates
- **Verification:** Ten CPU-side tests and the structure/privacy validator pass; changed cells were reset while `P05-C03` and its output were preserved
- **Preservation:** Existing OpenAI metrics, traces, report, and all dataset-preparation content remain unchanged
