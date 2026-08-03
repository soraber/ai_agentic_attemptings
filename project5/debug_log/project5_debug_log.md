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
- **Verification:** Live smoke request succeeded; the final expanded suite passed 10 tests; the reconciled 40-question run completed with 54 model calls; report and privacy validation passed; rendered PDF had no visible clipping or overlap
- **Preservation:** Retained VS Code's existing `Python 3 (ipykernel)` metadata and changed no dataset-preparation logic

## 2026-08-03 - A100 Local Planner Extension

- **Environment:** Local CPU interface validation; A100 execution path prepared
- **Notebook cells:** `P05-C01`, `P05-C02`, `P05-C06`, `P05-C08`, `P05-C09`, and `P05-C10`
- **Symptom:** The completed experiment exercised API generation but did not demonstrate local GPU inference or dense schema linking
- **Root cause:** The initial scope prioritized governed execution and reproducible API evaluation
- **Fix:** Added normalized MiniLM schema retrieval, a shared BF16 Qwen2.5-Coder planner, isolated `output/gpu/` artifacts, and patch-only notebook updates
- **Verification:** Ten CPU-side tests and the structure/privacy validator pass; changed cells were reset while `P05-C03` and its output were preserved
- **Preservation:** Existing OpenAI metrics, traces, report, and all dataset-preparation content remain unchanged

## 2026-08-03 - Colab A100 Runtime Disconnection

- **Environment:** VS Code 2025.9.1 with the Google Colab extension; requested A100 runtime
- **Notebook cells:** `P05-C01`, `P05-C02`, and `P05-C07`
- **Symptom:** A first A100 kernel stayed busy after `pytest`; a replacement A100 server was removed immediately after Python selection and the notebook returned to `Select Kernel`
- **Root cause:** The first run used an already-open stale notebook buffer with an unbounded test cell; the replacement failure occurred in the VS Code/Colab remote-server lifecycle before any notebook code executed
- **Fix:** `P05-C01` now fast-forwards an existing Colab clone, `P05-C02` selects the isolated `local_gpu` backend, and `P05-C07` disables third-party pytest plugin autoload and enforces a 120-second timeout
- **Verification:** The earlier A100 smoke execution confirmed `NVIDIA A100-SXM4-40GB` and MiniLM schema retrieval; the complete local-GPU evaluation did not run because the replacement server disconnected
- **Preservation:** `P05-C03` dataset preparation and the complete OpenAI evaluation artifacts were not changed; remote debugging stopped after the user-defined 10-minute limit

## 2026-08-03 - Completed Colab A100 Evaluation

- **Environment:** Clean Colab A100-SXM4-40GB runtime; Qwen2.5-Coder-7B-Instruct and MiniLM
- **Notebook cells:** No source cells changed in this final pass; outputs were populated for `P05-C01` through `P05-C10`
- **Symptom:** The earlier A100 attempt had left an unusable remote-kernel state; Hugging Face also warned that the Colab secret channel was unavailable from VS Code
- **Root cause:** The first issue was remote kernel lifecycle state. The token warning was non-blocking because both selected Hugging Face models are public
- **Fix:** Reconnected to a clean A100 runtime, retained the bounded isolated test cell, and ran the complete notebook with artifacts exported separately
- **Verification:** `P05-C07` passed 10 tests in 10.53 seconds; 40 held-out questions completed in 346.93 seconds with 91 local calls; report generation and artifact checks passed
- **Measured result:** Governed result-hash accuracy 0%, unsafe blocking 84.62%, PII leakage 0%, and median governed latency 6,764.51 ms; the negative comparison is retained rather than promoted over the API result
- **Preservation:** `P05-C03` source and all existing API artifacts remained unchanged; the A100 outputs live only under `output/gpu/`
