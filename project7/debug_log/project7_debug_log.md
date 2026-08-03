# Project 7 Debug Log

Record date, environment, exact `P07-CXX` cell, symptom, root cause, minimal fix,
verification, and preservation notes.

## 2026-08-02 - Initial Scaffold

- **Environment:** Local pre-execution workspace
- **Notebook cell:** `P07-C00` through `P07-C10`
- **Symptom:** None
- **Fix:** Created local A2A/MCP contracts, security gateway, benchmark, and tests

## 2026-08-02 - Synthetic ID Matched Secret Scanner

- **Environment:** Local pre-execution validation
- **Notebook cell:** `P07-C03` consumes the data; the cell itself was unchanged
- **Symptom:** Privacy validation flagged generated task IDs for secret-exfiltration cases
- **Root cause:** The final `k` in `task` plus `-secret...` formed a key-shaped `sk-` substring
- **Fix:** Changed the synthetic task-ID prefix from `task-` to `a2a-` and regenerated the benchmark checksum
- **Verification:** Privacy validation and all deterministic tests pass

## 2026-08-02 - Report Title Collision

- **Environment:** Local measured-format report dry run
- **Notebook cell:** None; only `tools/generate_report.py` changed
- **Symptom:** The long Project 7 title overlapped the report subtitle
- **Root cause:** The default ReportLab title and heading styles did not reserve reliable vertical spacing for this title length
- **Fix:** Added explicit title and subtitle styles with stable leading and spacing
- **Verification:** Regenerated the PDF and visually inspected the rendered page

## 2026-08-02 - API Mode Was Not Connected To Evaluation

- **Environment:** Final pre-execution consistency review
- **Notebook cell:** `P07-C08`
- **Symptom:** `RUN_API_EVAL` loaded a secret but did not affect the evaluation path
- **Root cause:** Protocol controls were implemented first and the optional language-review layer had not been connected
- **Fix:** Added a structured policy reviewer, scored one frozen recommendation per held-out case, and kept deterministic gateway policy authoritative
- **Verification:** Rebuilt the notebook; a deterministic reviewer test verifies 32 recommendations are scored without enabling unsafe writes

## 2026-08-03 - Measured API Evaluation

- **Environment:** Local macOS kernel with temporary isolated dependencies; OpenAI Responses API
- **Notebook cells:** `P07-C01` and `P07-C02`; executed `P07-C03` through `P07-C10`
- **Symptom:** The first deterministic test run failed because an exact expected summary did not include the new token/cost telemetry fields
- **Root cause:** Reviewer accounting intentionally expanded the evaluation result contract
- **Fix:** Added bounded retries and measured usage, updated the contract assertion, added the local skip-install path, and enabled the measured flags
- **Verification:** Eight tests passed; live attack-case review rejected the malicious document; all 32 held-out cases completed with 32 model calls; report/privacy validation passed; rendered PDF had no clipping or overlap
- **Preservation:** Dataset generation and deterministic gateway authorization logic were unchanged

## 2026-08-03 - Final Artifact Verification

- **Environment:** Local artifact and notebook review; no GPU execution requested by the implementation
- **Notebook cells:** No Project 7 notebook cells changed
- **Symptom:** Projects 5, 6, and 8 had explicit local-GPU backends, while Project 7 did not expose an equivalent A100 mode
- **Root cause:** Project 7's core experiment is protocol policy and local side-effect control; its only model component is a bounded, non-authoritative API reviewer, so a GPU run would not be a like-for-like backend switch
- **Fix:** Preserved the completed measured API evaluation instead of adding an unplanned local reviewer during finalization
- **Verification:** Existing artifacts report 32 held-out cases, 0% defended attack success, 100% benign success, 100% trace completeness, 84.375% reviewer accuracy, and 72.47 seconds runtime; the final PDF renders cleanly
- **Preservation:** No source, notebook, data, or measured output was modified
