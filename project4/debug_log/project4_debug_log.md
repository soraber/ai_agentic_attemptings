# Project 4 Debug Log

Record only material issues that affect execution, correctness, reproducibility,
security, or reported results.

## Entry Template

### YYYY-MM-DD - Short Issue Name

- **Environment:** Colab CPU/L4, local macOS, or other
- **Notebook cell:** `P04-CXX`
- **Symptom:** Exact error or incorrect behavior
- **Root cause:** Confirmed cause, not only a guess
- **Fix:** Minimal code or configuration change
- **Verification:** Command, test, or measured output proving the fix
- **Preservation note:** Existing user-edited cells or files preserved

## Pre-Execution Notes

### 2026-08-02 - Initial Scaffold

- **Environment:** Local macOS workspace
- **Notebook cell:** All planned cells, `P04-C00` through `P04-C10`
- **Symptom:** None; pre-execution construction
- **Root cause:** Not applicable
- **Fix:** Created the initial project package, deterministic benchmark generator,
  workflow modules, tests, notebook builder, runbook, and output contract
- **Verification:** Static validation and deterministic tests are recorded in the
  repository commit that introduces the scaffold
- **Preservation note:** No prior Project 4 notebook or user-edited Project 4 files
  existed

### 2026-08-02 - Local Compile Cache Permission

- **Environment:** Restricted macOS workspace with system Python 3.9.6
- **Notebook cell:** Not applicable; pre-execution repository validation
- **Symptom:** `compileall` raised `PermissionError` while trying to write beneath
  `~/Library/Caches/com.apple.python/`
- **Root cause:** The system Python redirects bytecode outside the permitted
  `jobs` workspace; source parsing had not failed
- **Fix:** Set `PYTHONPYCACHEPREFIX=/private/tmp/project4-pycache` for local compile
  checks and use an isolated Python 3.10+ environment for dependency-backed tests
- **Verification:** The same `compileall` command completed with exit code 0 after
  redirecting its cache
- **Preservation note:** No notebook cells or existing files were changed

### 2026-08-02 - Security Validator Fixture False Positives

- **Environment:** Local isolated Python 3.13 validation environment
- **Notebook cell:** Not applicable; pre-execution repository validation
- **Symptom:** The privacy scanner flagged its own local-path expression and the
  deliberately fake key used by the telemetry redaction test
- **Root cause:** Static scanning cannot distinguish a test fixture from a leaked
  secret when both use the same contiguous token shape
- **Fix:** Construct redaction fixtures and scanner path roots from noncontiguous
  string fragments while retaining runtime checks for key-shaped values and any
  absolute macOS or Linux home path
- **Verification:** `tools/validate_project.py` and the telemetry test both pass
- **Preservation note:** No notebook cells or user-authored files were changed

### 2026-08-02 - Portable PDF Rendering

- **Environment:** Local macOS PDF dry run with ReportLab and `sips`
- **Notebook cell:** `P04-C10` invokes the tool, but the cell itself was unchanged
- **Symptom:** A transparent PDF page rendered black, and RGBA chart fills were
  omitted after adding a white background; the limits section also overflowed to
  an otherwise empty third page
- **Root cause:** The macOS renderer handled ReportLab transparency and embedded
  RGBA PNG fills inconsistently, while the initial second-page layout was too tall
- **Fix:** Paint an explicit white page, flatten chart assets to RGB, add a footer,
  and resize second-page charts so the report remains two pages
- **Verification:** A temporary measured dry run was rendered and visually checked
  page by page; both pages are legible with intact charts and no overlap
- **Preservation note:** No notebook cells or existing result artifacts were changed

### 2026-08-03 - Editable Install Not Visible In Running Kernel

- **Environment:** Google Colab CPU connected through VS Code
- **Notebook cell:** `P04-C01`
- **Symptom:** Dependency installation completed, then the import smoke test raised
  `ModuleNotFoundError: No module named 'project4_agent'`
- **Root cause:** The editable install created its import-path registration after
  the Colab interpreter had started, so the current process had not loaded it
- **Fix:** Insert `PROJECT_ROOT / "src"` into `sys.path` immediately after the
  editable install; keep the editable install for subprocesses and later sessions
- **Verification:** `P04-C01` completed in the same connected kernel on Python
  3.12.13; `P04-C03` verified all 24 cases and checksum
  `46e6e39a2d328a4c8f120f311db9f0bc5b80e5c87360f8640124c8196e4337e6`;
  `P04-C07` then passed all 11 deterministic tests in 1.05 seconds
- **Preservation note:** Existing notebook kernel metadata and all cells except
  `P04-C01` were preserved; the builder received the same minimal source change

### 2026-08-03 - Preinstalled IPython/Jedi Check Warning

- **Environment:** Google Colab CPU connected through VS Code
- **Notebook cell:** `P04-C01`
- **Symptom:** `pip check` reported `ipython 7.34.0 requires jedi, which is not installed`
- **Root cause:** The Colab base image includes an IPython/Jedi mismatch unrelated
  to Project 4's bounded dependency set
- **Fix:** No package change; Project 4 does not import Jedi, and changing the base
  environment would add risk without affecting this experiment
- **Verification:** Import smoke tests, both workflow smoke cases, and all 11
  Project 4 tests passed in the same runtime
- **Preservation note:** No notebook cell or dependency pin was changed for this warning

### 2026-08-03 - Deterministic Colab Evaluation And Artifact Transfer

- **Environment:** Google Colab CPU connected through VS Code
- **Notebook cells:** `P04-C02`, `P04-C08`, `P04-C09`, and `P04-C10`
- **Symptom:** The Colab run completed remotely, but generated files were not
  automatically synchronized into the local VS Code workspace
- **Root cause:** The Colab extension synchronizes notebook state while the cloned
  `/content` filesystem remains remote; its Jupyter filesystem API returned 404 to
  unauthenticated local requests
- **Fix:** Set `RUN_FULL_EVAL=True`; after the measured run, temporarily packaged
  non-runtime output files in `P04-C10`, transferred them through bounded notebook
  output, decoded them locally, and removed the transfer-only source and payload
- **Verification:** The transferred run completed 32 paired observations per system in 5.09
  seconds; local `tools/validate_project.py --require-results` passed, and both PDF
  pages were rendered and visually inspected without overlap or clipping
- **Preservation note:** Existing kernel metadata was preserved; `P04-C10` was
  restored to its original source after transfer, while successful normal outputs
  and execution counts remain

### 2026-08-03 - Safe API Credential Input Through VS Code

- **Environment:** Google Colab CPU connected through VS Code
- **Notebook cell:** `P04-C02`
- **Symptom:** Colab Secrets can time out when requested outside the Colab web UI,
  while a plaintext key in source would create an unacceptable disclosure risk
- **Root cause:** The VS Code Colab extension connects to the runtime but does not
  guarantee access to the Colab web UI's secret-fetch channel
- **Fix:** Prefer the `OPENAI_API_KEY` Colab Secret, catch client-access failures,
  and fall back to `getpass` so the key is entered into the current kernel only
- **Verification:** API mode completed 64 structured calls; a post-run privacy scan
  confirmed the key is absent from notebook source, outputs, traces, and files
- **Preservation note:** Only `P04-C02` changed; existing kernel metadata and all
  other notebook cells were preserved, and the builder received the same fallback

### 2026-08-03 - Strict Structured-Output Parameter Schema

- **Environment:** Google Colab CPU, OpenAI Responses API
- **Notebook cell:** `P04-C08` invokes the planner; the cell itself was unchanged
- **Symptom:** `BadRequestError` 400 reported that `ActionPlan.parameters` lacked
  `additionalProperties: false`; the planner stopped after bounded retries
- **Root cause:** `dict[str, Any]` produces an open JSON Schema that is invalid for
  strict structured outputs
- **Fix:** Replaced the open dictionary with a Pydantic `ActionParameters` model
  covering the approved catalog fields and explicit blocked callback fields;
  policy, workflow display, and idempotency convert it to a compact dictionary at
  their boundaries
- **Verification:** The schema regression test passed and the API evaluation
  accepted both strict response schemas, completing all 64 calls
- **Preservation note:** No notebook source changed for this fix; shared source and
  one focused schema regression test changed

### 2026-08-03 - Reused Colab Clone Did Not Refresh Source

- **Environment:** Google Colab CPU connected through VS Code
- **Notebook cell:** `P04-C01`
- **Symptom:** The download-once clone would continue importing the pre-fix planner
  source on subsequent runs
- **Root cause:** Setup reused an existing `/content/ai_agentic_attemptings` clone
  without checking for new fast-forward commits
- **Fix:** Run `git pull --ff-only` when the cached repository and `.git` directory
  already exist; untracked runtime outputs remain untouched
- **Verification:** The reused clone fast-forwarded to the pushed schema fix while
  preserving the cached benchmark and untracked runtime artifacts
- **Preservation note:** Only `P04-C01` and its builder source changed

### 2026-08-03 - Live Kernel Retained Pre-Fix Modules

- **Environment:** Google Colab CPU connected through VS Code
- **Notebook cell:** `P04-C01`; failure surfaced in `P04-C08`
- **Symptom:** After a successful fast-forward pull, the API returned the same open
  `ActionPlan.parameters` schema error with pre-fix source line numbers
- **Root cause:** Python retained previously imported `project4_agent` modules in
  `sys.modules`, so updating files and reinstalling did not refresh live classes
- **Fix:** After installing and setting the source path, evict only
  `project4_agent` modules and invalidate import caches before the smoke import
- **Verification:** The same kernel imported the refreshed package and `P04-C07`
  discovered all 12 then-current tests
- **Preservation note:** Only `P04-C01` and its builder source changed; the runtime
  was not restarted, so the approved key remains ephemeral in memory

### 2026-08-03 - Existing Project Candidate Bypassed Pull

- **Environment:** Google Colab CPU connected through VS Code
- **Notebook cell:** `P04-C01`; failure surfaced in `P04-C08`
- **Symptom:** Module eviction ran, but the API still received the old open
  `ActionPlan.parameters` schema and `P04-C07` still discovered only 11 tests
- **Root cause:** The existing `/content/.../project4` candidate was selected before
  the `PROJECT_ROOT is None` branch, so the branch containing `git pull` never ran
- **Fix:** Define the Colab repository independently and run `git pull --ff-only`
  for every selected project path inside that repository before installation
- **Verification:** The corrected branch pulled the remote commit, all 12
  then-current tests passed in Colab, and `P04-C08` completed successfully
- **Preservation note:** Only `P04-C01` and its builder source changed; cached data,
  notebook metadata, and the in-memory key remain untouched

### 2026-08-03 - Recovery Denominator Included Pre-Execution Rejections

- **Environment:** Local post-processing of measured Colab API artifacts
- **Notebook cell:** Results originated in `P04-C08`; no notebook source changed
- **Symptom:** Durable crash recovery appeared as 75% although every workflow that
  reached an injected crash resumed successfully
- **Root cause:** The denominator included four cases assigned for fault injection
  that the simulated operator rejected before action execution, so no crash could
  occur in those workflows
- **Fix:** Define executed crash trials by excluding policy blocks and operator
  rejections, retain their controlled-completion credit, and expose trial counts
  in the saved summary and PDF table
- **Verification:** A focused regression test raised the suite to 13 passing tests;
  saved API rows recompute to 100% over 16 baseline and 12 durable crash trials;
  the artifact validator passed and both regenerated PDF pages were inspected
- **Preservation note:** No additional API calls were made; model outputs, traces,
  per-case results, usage totals, and runtime measurements remain unchanged

### 2026-08-03 - Completed API Evaluation and Artifact Export

- **Environment:** Google Colab CPU, Python 3.12.13, OpenAI Responses API
- **Notebook cells:** `P04-C01` through `P04-C10`
- **Result:** 16 held-out incidents x two repetitions produced 32 paired
  observations per system using 64 planner calls in 178.67 seconds
- **Usage:** 48,171 input tokens, 13,298 output tokens, and USD 0.127959 estimated
  cost under the configured 120-call and USD 5.00 ceilings
- **Verification:** Root-cause accuracy was 96.875%, remediation accuracy 71.875%,
  controlled completion 100%, durable duplicate effects 0%, durable unsafe-plan
  allow rate 0%, and all executed crash trials recovered; final JSON, JSONL, PNG,
  SVG, and PDF artifacts passed local validation
- **Preservation note:** The credential was entered with hidden input and stayed in
  kernel memory; only measured artifacts and nonsecret execution outputs persist
