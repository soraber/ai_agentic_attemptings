# AI Agentic Projects Information

Detailed implementation, evaluation, resource, and maintenance information for
the projects developed in this repository. The structure follows the project
documentation pattern used in `ai_project_artifacts`: portfolio summary,
repository map, methods, compute settings, results and judgment, future work, and
debugging notes.

> **Version:** ver 0.2: document Projects 5-8 execution scaffolds<br>
> **Updated:** 2026-08-03 00:01 EDT

## Portfolio Summary

| Project | Primary goal | Main comparison | Current result | Judgment |
| --- | --- | --- | --- | --- |
| 4. Durable Incident-Response Agent | Build a recoverable, approval-gated agent for simulated service incidents | Stateless linear loop vs. checkpointed LangGraph workflow | Preflight complete: 11 deterministic tests passed; final API evaluation has not run | The workflow mechanics, safety policy, idempotency, recovery, redaction, and report pipeline are ready; no model-quality claim should be made yet |
| 5. Governed Text-to-SQL Analyst | Answer analytics questions while enforcing database policy | One-shot SQL vs. schema-grounded governed repair | Preflight complete: 7 tests passed and the deterministic held-out dry run completed; final API evaluation has not run | SQL execution, policy, repair, PII, and report mechanics are ready; dry-run scores isolate controls rather than model quality |
| 6. Test-Driven Code-Repair Agent | Repair compact Python defects without accepting unsafe or overfit patches | One-shot patch vs. bounded test-driven repair loop | Preflight complete: 6 tests passed; pinned QuixBugs evaluation has not run | Repository mapping, patch constraints, hidden-test gating, rollback, and report mechanics are ready |
| 7. Secure Interoperable Agent Gateway | Preserve utility while blocking protocol-layer attacks | Undefended vs. defended A2A/MCP-style workflow | Preflight complete: 7 tests passed and the deterministic held-out dry run completed; optional structured policy review has not run | The local protocol controls block the included attacks without reducing benign success; this is not production security certification |
| 8. Long-Term Memory Agent | Retrieve useful cross-session facts while honoring corrections, conflicts, and deletion | Recent window vs. episodic vs. hybrid memory | Preflight complete: 7 tests passed and lifecycle fixtures completed; LoCoMo API QA has not run | Memory lifecycle mechanics are verified locally; final QA quality and context-cost claims require the notebook run |

## Repository Map

### Project 4 Files

| File | Purpose |
| --- | --- |
| [`project4/project4_durable_incident_response_agent.ipynb`](project4/project4_durable_incident_response_agent.ipynb) | Stable-cell Colab notebook covering setup, data, baseline, durable workflow, reliability tests, paired evaluation, error analysis, and export |
| [`project4/README.md`](project4/README.md) | Project scope, architecture, execution modes, quick start, outputs, and safety boundary |
| [`project4/RUNBOOK.md`](project4/RUNBOOK.md) | Cell-by-cell execution instructions, commands, secrets, budgets, failure injection, and output checks |
| [`project4/background/project4_background.md`](project4/background/project4_background.md) | Graduate-level explanation of durable execution, checkpointing, idempotency, HITL, retries, sagas, and observability |
| [`project4/config/default.json`](project4/config/default.json) | Seed, planner mode, model, call/token/cost budgets, split, repetitions, and fault-injection settings |
| [`project4/data/cache/project4_incidents.json`](project4/data/cache/project4_incidents.json) | Fixed benchmark containing 24 deterministic incidents across four simulated services |
| [`project4/data/cache/project4_incidents.sha256`](project4/data/cache/project4_incidents.sha256) | SHA-256 checksum protecting the committed benchmark from accidental changes |
| [`project4/src/project4_agent/`](project4/src/project4_agent/) | Typed schemas, dataset generation, planners, policy engine, SQLite simulator, durable graph, telemetry, and evaluation code |
| [`project4/tests/`](project4/tests/) | Deterministic tests for data isolation, planning, policy, idempotency, compensation, telemetry, and graph recovery |
| [`project4/tools/build_notebook.py`](project4/tools/build_notebook.py) | Rebuilds the notebook deterministically with stable cell IDs `P04-C00` through `P04-C10` |
| [`project4/tools/generate_incident_dataset.py`](project4/tools/generate_incident_dataset.py) | Reproduces the fixed incident benchmark and checksum |
| [`project4/tools/generate_report.py`](project4/tools/generate_report.py) | Generates measured charts, procedure diagram, and final PDF from saved result JSON |
| [`project4/tools/validate_project.py`](project4/tools/validate_project.py) | Checks structure, notebook cell order, dataset integrity, output contract, local paths, and key-shaped strings |
| [`project4/debug_log/project4_debug_log.md`](project4/debug_log/project4_debug_log.md) | Records material setup, validation, security, and PDF-generation issues and fixes |
| [`project4/output/`](project4/output/) | Reserved for measured summaries, traces, report assets, and final PDF; no placeholder results are committed |

## Project 4: Durable Incident-Response Agent

### Goal

Build a compact incident-response agent that diagnoses simulated microservice
failures, proposes a constrained remediation, pauses for human approval, survives
an injected crash, and resumes without repeating the side effect. The experiment
tests whether durable orchestration improves recovery and safety compared with a
stateless loop while exposing its latency and cost overhead.

### Methods

- Generated 24 deterministic incidents across `gateway`, `checkout`, `payments`,
  and `inventory`, with six root-cause archetypes per service.
- Represented evidence with Pydantic schemas for logs, metrics, trace spans,
  versions, dependencies, hidden root causes, remediations, and escalation labels.
- Kept gold labels out of the planner-facing `public_view()` and used a fixed
  eight-case development and sixteen-case held-out split.
- Implemented diagnose, verify, plan, policy, approval, execute, validate,
  compensate, and close nodes with LangGraph `StateGraph`.
- Used SQLite checkpointing and persistent thread IDs to resume an interrupted
  workflow under the same incident identity.
- Used LangGraph `interrupt()` and `Command(resume=...)` for approval-bound
  execution.
- Added a transactional SQLite execution ledger and stable idempotency keys. A
  crash is injected after the simulated effect commits but before acknowledgement.
- Added strict action, target, incident-identity, parameter, and approval checks;
  five adversarial plan forms exercise the policy boundary.
- Added saga-style idempotent compensation for an intentionally failed action.
- Added a deterministic planner for workflow isolation and an optional OpenAI
  Responses API planner with structured outputs, bounded retries, call limits,
  output-token limits, and estimated-cost limits.
- Froze each planner decision and replayed it into both systems so differences in
  reliability cannot be attributed to different model outputs.
- Recorded redacted JSONL traces and provided optional local OpenTelemetry setup.
- Generated reports only from saved measured JSON. The report tool rejects absent
  or placeholder summaries.

### Procedure

```text
incident evidence
      |
      v
diagnose -> verify -> plan -> policy gate -> approval interrupt
                                             |
                                      SQLite checkpoint
                                             |
                                             v
                                  execute -> validate
                                      |          |
                            idempotent replay    +-> compensate
                                      |                    |
                                      +--------------------+
                                                   |
                                                   v
                                                  close

Evaluation: root-cause/remediation accuracy, policy blocking, crash recovery,
duplicate effects, compensation, trajectory length, latency, tokens, and cost.
```

### Compute Resources, Time, and Key Settings

| Item | Configuration |
| --- | --- |
| Preflight compute | Local macOS CPU using an isolated Python 3.13 dependency directory; no GPU and no API key |
| Verified preflight time | Eleven tests completed in 0.17 seconds; one-repetition deterministic evaluator dry run completed in about 0.7 seconds |
| Intended complete runtime | Google Colab CPU; approximately 45-90 minutes for the API-backed experiment and artifact review |
| Dataset | 24 incidents, four services, six root causes per service, eight development cases, and sixteen held-out test cases |
| Dataset checksum | `46e6e39a2d328a4c8f120f311db9f0bc5b80e5c87360f8640124c8196e4337e6` |
| Evaluation design | Two repetitions and paired decisions; half of held-out cases receive a post-commit crash |
| Default API planner | `gpt-5.6-luna` with low reasoning effort; API mode is opt-in |
| API limits | Maximum 120 calls, 450 output tokens per structured call, two retries, and USD 5.00 estimated cost |
| Expected default API use | 64 structured calls: 16 cases x diagnosis and planning x two repetitions |
| Action boundary | Restart, rollback, scale, and open-ticket simulations writing only to local SQLite |

### Preflight Results and Judgment

| Check or metric | Stateless baseline | Durable workflow | Judgment |
| --- | ---: | ---: | --- |
| Deterministic test suite | Included | Included | **11 of 11 tests passed** across shared components and both workflows |
| Post-commit crash recovery | 100% in the dry run | 100% in the dry run | Both restarted, but only the durable path preserved exactly one primary effect |
| Cases with duplicate primary effects | 50% in the one-repetition dry run | 0% in the one-repetition dry run | The injected crash affected half of cases; the baseline repeated effects while the ledger deduplicated replay |
| Adversarial plans blocked | 20% with the coarse action-name check | 100% with the strict policy | The strict policy rejected unknown actions, excessive scale, wrong versions, wrong targets, and external callbacks |
| Dataset integrity | Shared checksum verified | Shared checksum verified | Both systems receive the same committed benchmark |
| Privacy and structure validation | Shared validator passed | Shared validator passed | No plaintext key or absolute local user path was found in project content |

These are deterministic preflight observations, not the final Project 4 result.
The planner in the dry run was rule based, the result JSON was written only to a
temporary directory, and no OpenAI call was made. The preflight supports the
engineering claim that the implemented ledger and graph recover as designed. It
does not establish LLM diagnosis quality, production safety, or real-system
exactly-once execution.

Final judgment must wait for notebook cell `P04-C08` to run the held-out API-backed
comparison and cell `P04-C10` to persist and validate the report artifacts.

### Training and Evaluation Figures

No final figures are committed before execution. After a measured run, the report
pipeline will create:

- `project4/output/project4_report_assets/procedure_diagram.svg`
- `project4/output/project4_report_assets/quality_metrics.png`
- `project4/output/project4_report_assets/recovery_safety.png`
- `project4/output/project4_report_assets/latency_cost_tradeoff.png`
- `project4/output/project4_report.pdf`

The generator was dry-tested with temporary measured-format data. The resulting
two-page PDF was rendered page by page to verify its white background, RGB charts,
table readability, margins, and non-overlapping layout.

### Future Optimization

- Replace the simulated operator with a small blinded human review study and
  measure approval agreement, review time, and false approvals.
- Add concurrent duplicate-delivery and multi-process ledger tests, then compare
  SQLite with PostgreSQL advisory locks or a transactional outbox.
- Expand the benchmark with ambiguous evidence, simultaneous root causes, stale
  telemetry, partial dependency failures, and adversarial log content.
- Add calibrated abstention and escalation thresholds selected only on the
  development split.
- Compare structured single-call diagnosis/planning with the current two-call
  design under fixed accuracy, latency, and cost budgets.
- Add p50/p95 node-level spans, retry counts, checkpoint size, and recovery-time
  objectives to the final report.
- Test real sandbox adapters for Kubernetes or ticketing only behind scoped
  credentials, dry-run modes, policy enforcement, and separate approval.
- Repeat the API evaluation across multiple seeds or model snapshots and report
  paired confidence intervals.

### Debug Log Summary

| Issue | Root cause | Resolution |
| --- | --- | --- |
| Local compile-cache permission | System Python redirected bytecode outside the permitted workspace | Redirected bytecode to `/private/tmp` and used isolated Python 3.13 for tests |
| Privacy-validator false positives | Static fixtures looked like the secrets and paths they were designed to detect | Built test tokens and path roots from noncontiguous fragments while retaining runtime detection |
| Transparent PDF rendered black | ReportLab page transparency was interpreted inconsistently by the macOS renderer | Painted an explicit white background and added a restrained footer |
| Chart fills disappeared and limits overflowed | Embedded RGBA PNG behavior and an over-tall second-page layout | Flattened charts to RGB and resized the second-page figures into a verified two-page report |

The full cell-specific history remains in
[`project4/debug_log/project4_debug_log.md`](project4/debug_log/project4_debug_log.md).

## Repository Map: Projects 5-8

### Project 5 Files

| File | Purpose |
| --- | --- |
| [`project5/project5_governed_text_to_sql.ipynb`](project5/project5_governed_text_to_sql.ipynb) | Stable cells `P05-C00` through `P05-C10` for setup, data, baseline, governed agent, evaluation, and export |
| [`project5/RUNBOOK.md`](project5/RUNBOOK.md) | Cell-by-cell commands, secrets, execution modes, budgets, and troubleshooting |
| [`project5/config/default.json`](project5/config/default.json) | Split, planner, governance, repair, row, call, token, retry, and cost limits |
| [`project5/data/cache/project5_questions.json`](project5/data/cache/project5_questions.json) | Fixed 50-question synthetic e-commerce benchmark |
| [`project5/src/project5_agent/`](project5/src/project5_agent/) | DuckDB data, typed plans, SQLGlot policy, planners, governed execution, and paired evaluation |
| [`project5/tests/`](project5/tests/) | Dataset integrity, SQL policy, PII masking, repair, export approval, and paired-agent tests |
| [`project5/tools/`](project5/tools/) | Dataset, notebook, report, and structure/privacy generators and validators |
| [`project5/background/project5_background.md`](project5/background/project5_background.md) | Schema grounding, executable SQL evaluation, AST policy, repair, and governance concepts |
| [`project5/debug_log/project5_debug_log.md`](project5/debug_log/project5_debug_log.md) | Cell-specific preparation history |
| [`project5/output/`](project5/output/) | Reserved for measured summaries, samples, traces, report assets, and PDF |

### Project 6 Files

| File | Purpose |
| --- | --- |
| [`project6/project6_test_driven_code_repair.ipynb`](project6/project6_test_driven_code_repair.ipynb) | Stable cells `P06-C00` through `P06-C10` for pinned data, mapping, patching, tests, evaluation, and export |
| [`project6/RUNBOOK.md`](project6/RUNBOOK.md) | QuixBugs preparation, execution modes, budgets, evidence checks, and troubleshooting |
| [`project6/data/quixbugs_manifest.json`](project6/data/quixbugs_manifest.json) | Twelve-case manifest pinned to one exact upstream commit |
| [`project6/src/project6_agent/`](project6/src/project6_agent/) | AST repository map, OpenAI patch planner, diff policy, subprocess runner, repair loop, rollback, and evaluation |
| [`project6/tests/`](project6/tests/) | Deterministic tests for mapping, path/line policy, timeout, hidden regression rejection, acceptance, and rollback |
| [`project6/tools/fetch_quixbugs.py`](project6/tools/fetch_quixbugs.py) | Download-once clone and pinned-revision verification |
| [`project6/tools/generate_report.py`](project6/tools/generate_report.py) | Generates measured repair charts, procedure diagram, and PDF |
| [`project6/tools/build_notebook.py`](project6/tools/build_notebook.py) | Rebuilds the notebook with stable cell IDs |
| [`project6/tools/validate_project.py`](project6/tools/validate_project.py) | Checks structure, notebook order, manifest pin, local paths, and key-shaped strings |
| [`project6/background/project6_background.md`](project6/background/project6_background.md) | Fault localization, constrained patches, feedback loops, hidden tests, and rollback concepts |
| [`project6/debug_log/project6_debug_log.md`](project6/debug_log/project6_debug_log.md) | Cell-specific preparation history |
| [`project6/output/`](project6/output/) | Reserved for measured repair summaries, patches, traces, matrix, report assets, and PDF |

### Project 7 Files

| File | Purpose |
| --- | --- |
| [`project7/project7_secure_agent_gateway.ipynb`](project7/project7_secure_agent_gateway.ipynb) | Stable cells `P07-C00` through `P07-C10` for contracts, defenses, attacks, comparison, and export |
| [`project7/RUNBOOK.md`](project7/RUNBOOK.md) | Commands, protocol boundary, execution modes, budgets, and troubleshooting |
| [`project7/data/cache/project7_cases.json`](project7/data/cache/project7_cases.json) | Fixed 40-case benign and attack benchmark |
| [`project7/src/project7_agent/`](project7/src/project7_agent/) | Agent Cards, A2A task envelopes, MCP-style tools, policy gateway, traces, and paired evaluation |
| [`project7/tests/`](project7/tests/) | Contract, scope, taint, metadata, redaction, idempotency, and benchmark tests |
| [`project7/tools/`](project7/tools/) | Dataset, notebook, report, and structure/privacy generators and validators |
| [`project7/background/project7_background.md`](project7/background/project7_background.md) | Protocol roles, trust boundaries, least privilege, taint, pinning, and idempotency concepts |
| [`project7/debug_log/project7_debug_log.md`](project7/debug_log/project7_debug_log.md) | Cell-specific data and report-layout issue history |
| [`project7/output/`](project7/output/) | Reserved for measured summaries, correlated traces, attack matrix, diagrams, and PDF |

### Project 8 Files

| File | Purpose |
| --- | --- |
| [`project8/project8_long_term_memory.ipynb`](project8/project8_long_term_memory.ipynb) | Stable cells `P08-C00` through `P08-C10` for data, stores, retrieval, lifecycle tests, QA, and export |
| [`project8/RUNBOOK.md`](project8/RUNBOOK.md) | LoCoMo preparation, secrets, execution modes, budgets, evidence checks, and troubleshooting |
| [`project8/data/locomo_selection.json`](project8/data/locomo_selection.json) | Auditable LoCoMo source revision and two-conversation, 80-QA selection |
| [`project8/data/lifecycle_cases.json`](project8/data/lifecycle_cases.json) | Deterministic correction, conflict, supersession, and deletion fixtures |
| [`project8/src/project8_agent/`](project8/src/project8_agent/) | SQLite memory lifecycle, recent/episodic/hybrid retrieval, LoCoMo conversion, cached answerer, and evaluation |
| [`project8/tests/`](project8/tests/) | Memory ingestion, supersession, conflict, deletion, retrieval, lifecycle, and LoCoMo conversion tests |
| [`project8/tools/fetch_locomo.py`](project8/tools/fetch_locomo.py) | Download-once pinned LoCoMo subset preparation |
| [`project8/tools/generate_report.py`](project8/tools/generate_report.py) | Generates memory-quality/context charts, lifecycle diagram, and PDF |
| [`project8/tools/build_notebook.py`](project8/tools/build_notebook.py) | Rebuilds the notebook with stable cell IDs |
| [`project8/tools/validate_project.py`](project8/tools/validate_project.py) | Checks structure, notebook order, source pin, local paths, and key-shaped strings |
| [`project8/background/project8_background.md`](project8/background/project8_background.md) | Memory tiers, temporal retrieval, consolidation, conflicts, deletion, and evaluation concepts |
| [`project8/debug_log/project8_debug_log.md`](project8/debug_log/project8_debug_log.md) | Cell-specific retrieval-debug history |
| [`project8/output/`](project8/output/) | Reserved for measured summaries, evidence, traces, report assets, and PDF |

## Project 5: Governed Text-to-SQL Analyst

### Goal

Build a natural-language analytics agent that can answer questions over a local
e-commerce database while enforcing read-only execution, region and column policy,
row limits, PII masking, bounded repair, and approval before export.

### Methods

- Generated a deterministic seven-table DuckDB snapshot and 50 typed questions,
  including benign analytics, invalid SQL, PII, unauthorized-region, ambiguity,
  oversized-result, and stored-instruction cases.
- Kept ten cases for development and 40 for held-out evaluation; expected result
  hashes are computed against the fixed snapshot.
- Retrieved relevant schema descriptions and required a Pydantic query plan before
  execution.
- Parsed SQL with SQLGlot and traversed the AST to allow only bounded `SELECT`
  queries over approved tables and columns.
- Used a read-only DuckDB connection, `EXPLAIN`, deterministic result hashing, PII
  masking, and explicit export approval.
- Compared a frozen one-shot plan with the same plan passed through policy and a
  maximum two-attempt repair loop. API and deterministic planners share this paired
  evaluation path.
- Recorded per-case policy, repair, execution, result-hash, latency, and leakage
  outcomes; reports reject placeholder summaries.

### Compute Resources, Time, and Key Settings

| Item | Configuration |
| --- | --- |
| Verified preflight | Local macOS CPU; 7 tests passed in 0.82 seconds and a deterministic 40-case dry run completed in 0.44 seconds |
| Intended complete runtime | Google Colab CPU, approximately 60-120 minutes |
| Dataset | 50 synthetic questions: 10 development and 40 held-out; checksum `8d861b67fb259c81ab830446d9f75ccd325942088c8b49413dc3c64e7144e11a` |
| Query limits | Two repair attempts, 100 result rows, read-only local DuckDB, authorized region `NA` |
| Default API planner | `gpt-5.6-luna`, low reasoning effort, API mode opt-in |
| API limits | 180 calls, 500 output tokens per call, two retries, USD 6.00 estimated cost |

### Preflight Results and Judgment

| Metric | One-shot deterministic dry run | Governed deterministic dry run |
| --- | ---: | ---: |
| Result-hash accuracy | 81.48% | 100.00% |
| Unsafe-query block rate | 23.08% | 100.00% |
| PII leak rate | 12.50% | 0.00% |
| Repair success | 0.00% | 100.00% |

These temporary dry-run values verify the benchmark and control logic using the
rule-based planner. They are not committed result artifacts and do not establish
model-backed text-to-SQL quality. Final judgment requires `P05-C08` in API mode.

### Training and Evaluation Figures

No final figures are committed before execution. The dry-tested report pipeline
creates `quality_repair_safety.png`, `procedure_diagram.svg`, and
`project5_report.pdf` from a measured summary. Its rendered page was visually
checked for readable charts, tables, margins, and footer placement.

### Future Optimization

- Replace lexical schema retrieval with evaluated embedding or hybrid retrieval.
- Add dialect variation, multi-hop joins, nested queries, null semantics, and
  larger database snapshots.
- Evaluate constrained decoding or grammar-guided SQL generation against repair.
- Add calibrated abstention for ambiguous questions and a blinded human approval
  study for exports.
- Run repeated model-backed evaluations and paired confidence intervals.

### Debug Log Summary

Project 5 was created as a new workspace and required no material debugging beyond
the shared test, notebook, privacy, and report verification pass. The full history
is in [`project5/debug_log/project5_debug_log.md`](project5/debug_log/project5_debug_log.md).

## Project 6: Test-Driven Code-Repair Agent

### Goal

Build a coding agent that maps a small Python repository, proposes a constrained
patch, runs public and generated hidden tests, accepts only verified repairs, and
restores the exact starting state after every rejected attempt.

### Methods

- Pinned QuixBugs to commit `4257f44b0ff1181dedaedee6a447e133219fcebf`
  and selected four development plus eight held-out Python defects.
- Built an AST repository map of symbols, imports, docstrings, and tests for fault
  localization without exposing gold patches.
- Required structured unified diffs, a source-path allowlist, successful
  `git apply --check`, and a 30-changed-line budget.
- Ran tests in a bounded subprocess with a 20-second timeout and capped output.
- Used public-test feedback for at most three attempts, then ran hidden generated
  assertions without returning their details to the planner.
- Accepted only patches passing syntax, policy, public, and hidden checks; all
  failed attempts restore an exact source snapshot.
- Added a Responses API patch planner and deterministic fixtures for mapping,
  overfitting rejection, correct-patch acceptance, timeout, and rollback.

### Compute Resources, Time, and Key Settings

| Item | Configuration |
| --- | --- |
| Verified preflight | Local macOS CPU; 6 tests passed in 6.17 seconds |
| Intended complete runtime | Google Colab CPU, approximately 90-180 minutes |
| Dataset | Twelve QuixBugs Python cases: four development and eight held-out, pinned to one commit |
| Repair limits | Three attempts, 30 changed lines, one declared source file, 20-second tests, 12,000 output characters |
| Default API planner | `gpt-5.6-sol`, medium reasoning effort, API mode opt-in |
| API limits | 220 calls, 900 output tokens per call, USD 8.00 estimated cost |

### Preflight Results and Judgment

All six deterministic tests pass. They verify AST mapping, traversal and line-budget
rejection, patch apply/rollback, test timeout, rejection of a public-test-only
overfit patch, and acceptance of a patch that passes hidden assertions. The report
generator also produced a readable temporary measured-format PDF.

No QuixBugs repair rate is claimed yet. Final one-shot and repair-loop comparison
requires fetching the pinned repository and running notebook cell `P06-C08` with
an API key.

### Training and Evaluation Figures

The measured run will create a repair-quality chart, procedure diagram, bug matrix,
representative patches, trajectories, and `project6_report.pdf`. No placeholder
performance figure is committed.

### Future Optimization

- Add coverage and spectrum-based fault localization under the same token budget.
- Compare unified diffs with structured edit operations and constrained decoding.
- Run tests in a hardened container with network, process, filesystem, and memory
  isolation.
- Add mutation testing and property-based hidden tests to reduce overfitting.
- Expand to dependency-heavy repositories and report environment failures
  separately from agent failures.

### Debug Log Summary

Project 6 was created as a new pinned workspace. The preflight specifically tested
the most failure-prone boundaries: hidden-test information isolation, subprocess
timeout, failed-patch rollback, and exact source restoration. See
[`project6/debug_log/project6_debug_log.md`](project6/debug_log/project6_debug_log.md).

## Project 7: Secure Interoperable Agent Gateway

### Goal

Build a local requester/reviewer workflow that uses A2A-style task envelopes and
MCP-style tools while defending against unauthorized delegation, indirect prompt
injection, poisoned metadata, duplicate delivery, schema violations, and canary
exfiltration.

### Methods

- Generated 40 deterministic procurement cases in eight categories, with eight
  development and 32 held-out cases.
- Defined Agent Cards, versioned task envelopes, typed JSON Schema tool contracts,
  contract digests, artifacts, statuses, and correlation IDs.
- Compared an undefended workflow with scope enforcement, schema and metadata
  pinning, provenance/taint tracking, policy checks, approval, redaction, and an
  idempotent side-effect ledger.
- Propagated correlated trace events across delegation, policy search, review,
  approval, rejection, redaction, retry, and result production.
- Used only synthetic credentials, records, and canaries; no network service or
  production identity provider is contacted.
- Added an optional structured model recommendation, scored once per held-out case
  and frozen across both systems; it cannot authorize or execute a tool.

### Compute Resources, Time, and Key Settings

| Item | Configuration |
| --- | --- |
| Verified preflight | Local macOS CPU; 7 tests passed in 0.09 seconds and a deterministic 32-case dry run completed in 0.04 seconds |
| Intended complete runtime | Google Colab CPU, approximately 60-120 minutes |
| Dataset | 40 cases: eight development and 32 held-out; checksum `b86768acd310ca836fe6b370f5babc6989200b2879bbea6eb622409c2e5e5927` |
| Protocol controls | Agent-specific scopes, schema and metadata pinning, taint, redaction, approval, idempotency, and trace correlation |
| Optional API review | `gpt-5.6-luna`, low reasoning effort; one recommendation per held-out case, scored but non-authoritative |
| API limits | 160 calls, 500 output tokens per call, two retries, USD 6.00 estimated cost; expected evaluation use is 32 calls |

### Preflight Results and Judgment

| Metric | Undefended dry run | Defended dry run |
| --- | ---: | ---: |
| Benign success | 100.00% | 100.00% |
| Attack success | 85.19% | 0.00% |
| Secret leakage | 11.11% | 0.00% |
| Unsafe writes | 62.96% | 0.00% |
| Duplicate-effect cases | 9.38% | 0.00% |
| Complete traces | 100.00% | 100.00% |

The deterministic result verifies the implemented controls against this synthetic
threat suite. It does not evaluate internet transport, production authorization,
cryptographic identity, or every adaptive prompt-injection strategy.

### Training and Evaluation Figures

The dry-tested pipeline creates `attack_benign_matrix.png`,
`procedure_diagram.svg`, and `project7_report.pdf`. Visual inspection caught and
fixed a title/subtitle collision before this scaffold was committed.

### Future Optimization

- Bind messages to signed identities, nonces, expiry, and replay-resistant tokens.
- Add real MCP and A2A transports behind the same policy interface and test version
  negotiation and partial failures.
- Expand red-team cases with adaptive multi-turn attacks and tool-result poisoning.
- Measure serialization, tracing, and policy overhead separately at p50 and p95.
- Add formal information-flow labels and property-based protocol fuzzing.

### Debug Log Summary

The synthetic task-ID prefix accidentally formed a key-shaped substring and was
changed before committing the benchmark. A report dry run also exposed overlapping
heading styles; explicit leading and spacing fixed the rendered PDF. Details are in
[`project7/debug_log/project7_debug_log.md`](project7/debug_log/project7_debug_log.md).

## Project 8: Long-Term Memory Agent

### Goal

Build a multi-session assistant that distinguishes recent context, episodic events,
and semantic/temporal facts while supporting corrections, conflicts, supersession,
consolidation, evidence retrieval, abstention, and verifiable deletion.

### Methods

- Pinned LoCoMo to commit `3eb6f2c585f5e1699204e3c3bdf7adc5c28cb376`
  and selected two conversations with 40 QA items each.
- Added deterministic lifecycle fixtures because benchmark QA alone does not cover
  correction, conflict, supersession, and deletion semantics.
- Stored immutable timestamped events, normalized facts, supersession links,
  conflict status, and deletion tombstones in SQLite.
- Implemented recent-window, lexical episodic, and hybrid episodic-plus-semantic
  retrieval with evidence IDs and compact context accounting.
- Added conflict abstention, consolidation, physical removal from retrievable
  stores, and post-deletion checks.
- Added a cached Responses API answerer so the three-system, 80-question comparison
  fits within 240 calls and reruns do not repeat completed model requests.

### Compute Resources, Time, and Key Settings

| Item | Configuration |
| --- | --- |
| Verified preflight | Local macOS CPU; 7 tests passed in 0.04 seconds; deterministic lifecycle evaluation also completed in under one second |
| Intended complete runtime | Google Colab CPU or L4, approximately 90-180 minutes |
| Dataset | LoCoMo samples 0 and 1, 40 QA per sample, plus deterministic lifecycle fixtures |
| Memory settings | Working window 6 events, episodic top-k 5, SQLite facts/events/tombstones, evidence-cited retrieval |
| Default API answerer | `gpt-5.6-luna`, low reasoning effort, API mode opt-in |
| API limits | 300 calls, 500 output tokens per call, two retries, USD 8.00 estimated cost; expected QA use is 240 calls |

### Preflight Results and Judgment

| Metric | Recent window | Episodic | Hybrid |
| --- | ---: | ---: | ---: |
| Lifecycle exact match | 75.00% | 75.00% | 100.00% |
| Mean context tokens | 12.0 | 2.5 | 2.5 |
| Deletion compliance | 100.00% | 100.00% | 100.00% |

The lifecycle dry run confirms that the hybrid store resolves the included
correction/conflict cases and that deletion removes retrievable events and facts
while preserving an audit tombstone. These small fixtures are engineering checks,
not the final LoCoMo QA result. Final quality, evidence recall, and context-cost
claims require API-backed cell `P08-C08`.

### Training and Evaluation Figures

The dry-tested report creates `quality_context_tradeoff.png`,
`procedure_diagram.svg`, and `project8_report.pdf`. The rendered page was inspected
for legible axes, table layout, deletion statement, limitations, and footer.

### Future Optimization

- Replace lexical retrieval with a versioned embedding index and compare hybrid
  fusion methods under fixed context budgets.
- Add learned memory extraction with calibrated confidence and provenance.
- Evaluate temporal interval queries, entity aliases, and multi-fact reasoning.
- Test cryptographic deletion receipts and provider/index deletion semantics.
- Tune retrieval only on a development split and report confidence intervals over
  conversations and QA categories.

### Debug Log Summary

Initial lexical overlap over-weighted a pronoun and did not normalize a simple
past-tense verb, causing the wrong event to rank first. A fixed stopword list and
minimal suffix normalization corrected the retrieval test without changing notebook
cells. See [`project8/debug_log/project8_debug_log.md`](project8/debug_log/project8_debug_log.md).

## Documentation Maintenance

The root [`README.md`](README.md) is a concise repository and portfolio summary.
Whenever its project-summary content changes, update the corresponding project
entry in this file in the same commit. Detailed methods, resources, settings,
results, judgments, figures, future optimization, and debug information belong
here rather than in the root README.
