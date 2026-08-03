# Project 6 Debug Log

Record date, environment, exact `P06-CXX` cell, symptom, root cause, minimal fix,
verification, and preservation notes.

## 2026-08-02 - Initial Scaffold

- **Environment:** Local pre-execution workspace
- **Notebook cell:** `P06-C00` through `P06-C10`
- **Symptom:** None
- **Fix:** Created pinned manifest, constrained repair harness, tests, and tools
- **Verification:** Static validation and deterministic tests accompany the commit

## 2026-08-03 - API Preflight and Notebook Execution

- **Environment:** Local macOS kernel with pinned QuixBugs commit and OpenAI Responses API
- **Notebook cells:** `P06-C01`, `P06-C02`, `P06-C03`, and `P06-C08`
- **Symptom:** Preflight found an absolute-path prompt/policy mismatch; the first notebook run then stopped in `P06-C03` with an unterminated string literal
- **Root cause:** The planner reused the absolute source path as the diff allowlist path, and the scaffold omitted the closing quote in the QuixBugs root assignment
- **Fix:** Added a separate relative `allowed_path`, bounded retries and usage accounting, a local skip-install path, measured-run controls, and the missing quote
- **Verification:** The final expanded suite passed 9 tests and a live allowlisted-diff smoke request; all 8 held-out bugs completed in both modes with 18 measured model calls; report/privacy validation passed; rendered PDF retained a 79-pixel top margin with no clipping or overlap
- **Preservation:** No prior user-authored Project 6 logic was overwritten

## 2026-08-03 - A100 Local Code-Model Extension

- **Environment:** Local CPU interface validation; A100 execution path prepared
- **Notebook cells:** `P06-C01`, `P06-C02`, `P06-C08`, `P06-C09`, and `P06-C10`
- **Symptom:** Repair quality was measured only with a hosted planner, leaving local code-model behavior untested
- **Root cause:** The initial implementation isolated the repair harness before adding a reusable GPU backend
- **Fix:** Added one shared BF16 Qwen2.5-Coder backend, typed local patch parsing, separate GPU outputs, and patch-only notebook updates
- **Verification:** Nine tests pass, including local-output parsing; the pinned QuixBugs download cell and prior measured artifacts were preserved
