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
