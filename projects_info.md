# AI Agentic Projects Information

Detailed implementation, evaluation, resource, and maintenance information for
the projects developed in this repository. The structure follows the project
documentation pattern used in `ai_project_artifacts`: portfolio summary,
repository map, methods, compute settings, results and judgment, future work, and
debugging notes.

> **Version:** ver 0.4: add measured Projects 5-8 evaluations<br>
> **Updated:** 2026-08-03 01:49 EDT

## Portfolio Summary

| Project | Primary goal | Main comparison | Current result | Judgment |
| --- | --- | --- | --- | --- |
| 4. Durable Incident-Response Agent | Build a recoverable, approval-gated agent for simulated service incidents | Stateless linear loop vs. checkpointed LangGraph workflow | Measured API run: 32 paired observations per system, 64 model calls, and 13 final local tests passed | The durable path preserved task quality, eliminated duplicate effects and unsafe allows, and recovered every executed crash, at roughly 10x workflow latency |
| 5. Governed Text-to-SQL Analyst | Answer analytics questions while enforcing database policy | One-shot SQL vs. schema-grounded governed repair | Measured API run: 40 held-out questions, 50 calls, and 10 final tests passed | Governance doubled result-hash accuracy, improved repair, and blocked unsafe cases, but absolute SQL accuracy remains a clear optimization target |
| 6. Test-Driven Code-Repair Agent | Repair compact Python defects without accepting unsafe or overfit patches | One-shot patch vs. bounded test-driven repair loop | Measured API run: 8 pinned defects per system, 18 calls, and 9 final tests passed | Iterative public-test feedback recovered one additional defect while hidden tests and exact rollback constrained acceptance |
| 7. Secure Interoperable Agent Gateway | Preserve utility while blocking protocol-layer attacks | Undefended vs. defended A2A/MCP-style workflow | Measured API run: 32 held-out cases, 32 review calls, and 8 final tests passed | The local controls eliminated included attacks without reducing benign utility; structured review was useful but correctly remained non-authoritative |
| 8. Long-Term Memory Agent | Retrieve useful cross-session facts while honoring corrections, conflicts, and deletion | Recent window vs. episodic vs. hybrid memory | Measured API run: 80 QA items across 3 systems, 240 cached calls, and 11 final tests passed | Episodic retrieval beat the current hybrid weighting; strict exact match exposed substantial retrieval/answer-quality headroom while lifecycle deletion stayed complete |

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
| [`project4/tests/`](project4/tests/) | Thirteen deterministic tests for data isolation, planning, strict schemas, policy, idempotency, compensation, telemetry, recovery, and metric aggregation |
| [`project4/tools/build_notebook.py`](project4/tools/build_notebook.py) | Rebuilds the notebook deterministically with stable cell IDs `P04-C00` through `P04-C10` |
| [`project4/tools/generate_incident_dataset.py`](project4/tools/generate_incident_dataset.py) | Reproduces the fixed incident benchmark and checksum |
| [`project4/tools/generate_report.py`](project4/tools/generate_report.py) | Generates measured charts, procedure diagram, and final PDF from saved result JSON |
| [`project4/tools/validate_project.py`](project4/tools/validate_project.py) | Checks structure, notebook cell order, dataset integrity, output contract, local paths, and key-shaped strings |
| [`project4/debug_log/project4_debug_log.md`](project4/debug_log/project4_debug_log.md) | Records material setup, validation, security, and PDF-generation issues and fixes |
| [`project4/output/`](project4/output/) | Measured per-case results, summary, representative samples, redacted traces, report assets, and final PDF from the completed API evaluation |

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
| Evaluation compute | Google Colab CPU, Python 3.12.13; no GPU required |
| Measured evaluation time | 178.67 seconds for the API-backed paired evaluation; report generation and validation completed afterward |
| Final verification | Thirteen local deterministic tests passed in 0.20 seconds; the notebook's pre-evaluation suite passed its then-current 12 tests in 0.86 seconds |
| Dataset | 24 incidents, four services, six root causes per service, eight development cases, and sixteen held-out test cases |
| Dataset checksum | `46e6e39a2d328a4c8f120f311db9f0bc5b80e5c87360f8640124c8196e4337e6` |
| Evaluation design | Two repetitions and paired decisions; half of held-out cases receive a post-commit crash |
| API planner | `gpt-5.6-luna` with low reasoning effort and strict Pydantic structured outputs |
| API limits | Maximum 120 calls, 450 output tokens per structured call, two retries, and USD 5.00 estimated cost |
| Measured API use | 64 structured calls, 48,171 input tokens, 13,298 output tokens, USD 0.127959 estimated cost |
| Action boundary | Restart, rollback, scale, and open-ticket simulations writing only to local SQLite |

### Results and Judgment

| Metric | Stateless baseline | Durable workflow | Judgment |
| --- | ---: | ---: | --- |
| Root-cause accuracy | 96.875% | 96.875% | Frozen paired decisions correctly isolate orchestration effects from planner variation |
| Remediation accuracy | 71.875% | 71.875% | The reliability layer does not improve model task quality by design |
| Controlled completion | 100% | 100% | Resolution, policy blocks, operator rejection, and compensation are treated explicitly |
| Executed-crash recovery | 100% (`n=16`) | 100% (`n=12`) | Four durable cases were rejected before execution; every workflow that reached the injected crash recovered |
| Cases with duplicate primary effects | 50% | 0% | The stateless restart repeated post-commit effects; the durable ledger deduplicated replay |
| Adversarial plans blocked | 20% | 100% | Strict typed policy reduced unsafe allows from 80% to 0% over 80 challenges |
| Mean workflow latency | 11.42 ms | 112.02 ms | Checkpointing, approval, validation, and recovery controls add roughly 10x orchestration latency |

The measured result supports the engineering claim: durable orchestration adds
stronger execution safety and replay correctness without changing the frozen
planner's diagnosis or remediation quality. The tradeoff is substantial local
workflow latency and more trajectory steps. No evaluated action failed, so the
compensation path remains verified by deterministic tests rather than the measured
held-out run. The tools and incidents are simulations; this is not a claim of
production exactly-once execution or universal model safety.

### Evaluation Figures

The completed measured run generated:

- `project4/output/project4_report_assets/procedure_diagram.svg`
- `project4/output/project4_report_assets/quality_metrics.png`
- `project4/output/project4_report_assets/recovery_safety.png`
- `project4/output/project4_report_assets/latency_cost_tradeoff.png`
- `project4/output/project4_report.pdf`

The two-page PDF was regenerated after correcting the executed-crash denominator,
then rendered page by page. Its white background, RGB charts, trial-count table,
margins, and non-overlapping layout were visually verified.

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
| Colab Secret timed out in VS Code | The extension lacks the Colab web UI secret-fetch channel | Added hidden `getpass` fallback; the key remained only in kernel memory |
| OpenAI rejected the action schema | An open parameter dictionary violated strict structured-output requirements | Replaced it with a closed typed model and added a schema regression test |
| Reused Colab clone stayed stale | Candidate selection bypassed the pull branch and Python cached old modules | Fast-forward every reused clone and evict only Project 4 modules before import |
| Crash recovery appeared as 75% | Operator-rejected cases were counted although execution and fault injection never occurred | Restricted the denominator to executed crash trials and exposed `n=16` versus `n=12` |

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
| [`project5/output/`](project5/output/) | Measured per-case results, summary, representative samples, traces, report assets, and final PDF |

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
| [`project6/output/`](project6/output/) | Measured repair results, trajectories, representative samples, report assets, and final PDF |

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
| [`project7/output/`](project7/output/) | Measured paired results, correlated traces, representative attacks, report assets, and final PDF |

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
| [`project8/output/`](project8/output/) | Measured QA/lifecycle results, evidence traces, representative samples, report assets, cache, and final PDF |

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
| Evaluation compute | Local macOS CPU with isolated Python dependencies; no GPU required |
| Measured evaluation time | 201.55 seconds for the 40-case API comparison; report generation and validation completed afterward |
| Final verification | 10 deterministic tests passed in 0.91 seconds, including local-model fallback contracts |
| Dataset | 50 synthetic questions: 10 development and 40 held-out; checksum `8d861b67fb259c81ab830446d9f75ccd325942088c8b49413dc3c64e7144e11a` |
| Query limits | Two repair attempts, 100 result rows, read-only local DuckDB, authorized region `NA` |
| API planner | `gpt-5.6-luna`, low reasoning effort, strict Pydantic query plans |
| API limits | 180 calls, 500 output tokens per call, two retries, USD 6.00 estimated cost |
| Measured API use | 50 calls, 13,634 input tokens, 13,665 output tokens, USD 0.095624 estimated cost |

### Results and Judgment

| Metric | One-shot | Governed | Judgment |
| --- | ---: | ---: | --- |
| Execution accuracy | 70.37% | 100.00% | Policy plus repair recovered executable plans for every safe case |
| Result-hash accuracy | 18.52% | 37.04% | Governance doubled semantic execution accuracy, but absolute model quality remains limited |
| Unsafe-query block rate | 0.00% | 38.46% | The policy stopped a meaningful subset that one-shot execution would allow |
| PII leak rate | 0.00% | 0.00% | Neither measured path emitted a PII column in this model run |
| Repair success | 80.00% | 100.00% | Bounded feedback recovered every included repair case |
| Median execution latency | 15.85 ms | 12.22 ms | This timer covers local execution after the shared frozen plan, not API generation |

The measured result supports the safety and repair design, but not a claim of high
general text-to-SQL accuracy. Result hashes remain strict and expose many
semantically wrong executable queries. Repeated model runs, stronger schema
retrieval, and calibrated abstention should be prioritized before expanding the
database or claim surface.

### Evaluation Figures

The measured run generated `project5/output/project5_report_assets/quality_repair_safety.png`,
`project5/output/project5_report_assets/procedure_diagram.svg`, and
`project5/output/project5_report.pdf`. The one-page PDF was rendered and checked
for readable bars, table values, interpretation text, margins, and footer.

### Future Optimization

- Replace lexical schema retrieval with evaluated embedding or hybrid retrieval.
- Add dialect variation, multi-hop joins, nested queries, null semantics, and
  larger database snapshots.
- Evaluate constrained decoding or grammar-guided SQL generation against repair.
- Add calibrated abstention for ambiguous questions and a blinded human approval
  study for exports.
- Run repeated model-backed evaluations and paired confidence intervals.

### Debug Log Summary

The first smoke command omitted the local source path and made no API call. The
corrected smoke test passed, after which retries, token/cost accounting, and a
local skip-install path supported the full run. Saved notebook paths were made
repository-relative. The full history is in
[`project5/debug_log/project5_debug_log.md`](project5/debug_log/project5_debug_log.md).

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
| Evaluation compute | Local macOS CPU with subprocess-isolated tests; no GPU required |
| Measured evaluation time | 114.63 seconds for both repair modes over 8 held-out defects; report generation and validation completed afterward |
| Final verification | 9 deterministic tests passed in 4.22 seconds, including local patch-planner contracts |
| Dataset | Twelve QuixBugs Python cases: four development and eight held-out, pinned to one commit |
| Repair limits | Three attempts, 30 changed lines, one declared source file, 20-second tests, 12,000 output characters |
| API planner | `gpt-5.6-sol`, medium reasoning effort, strict Pydantic patch proposals |
| API limits | 220 calls, 900 output tokens per call, two retries, USD 8.00 estimated cost |
| Measured API use | 18 calls, 22,988 input tokens, 4,436 output tokens, USD 0.248020 estimated cost |

### Results and Judgment

| Metric | One-shot | Repair loop | Judgment |
| --- | ---: | ---: | --- |
| Verified repair rate | 75.00% | 87.50% | Iterative public-test feedback recovered one additional defect |
| Hidden-test pass rate | 75.00% | 87.50% | The accepted repair improvement survived generated regression checks |
| Overfit detected | 0.00% | 0.00% | No public-only candidate reached the hidden-test rejection state in this run |
| Rollback success | 100.00% | 100.00% | Every rejected attempt restored the exact source snapshot |
| Mean changed lines | 2.0 | 2.0 | The loop improved success without increasing average patch size |
| Median latency | 5.07 s | 5.98 s | Additional feedback added modest end-to-end latency on this compact suite |

The measured comparison favors the bounded loop on this small pinned suite, while
the result remains too small for a universal coding-agent claim. The hidden tests
are generated and compact, and subprocess controls are not a hardened sandbox.
Future runs should add mutation strength, more repositories, and uncertainty over
multiple model samples.

### Evaluation Figures

The measured run generated `project6/output/project6_report_assets/repair_quality.png`,
`project6/output/project6_report_assets/procedure_diagram.svg`, case results,
trajectories, representative samples, and `project6/output/project6_report.pdf`.
The one-page PDF was rendered and checked for chart/table readability and margins.

### Future Optimization

- Add coverage and spectrum-based fault localization under the same token budget.
- Compare unified diffs with structured edit operations and constrained decoding.
- Run tests in a hardened container with network, process, filesystem, and memory
  isolation.
- Add mutation testing and property-based hidden tests to reduce overfitting.
- Expand to dependency-heavy repositories and report environment failures
  separately from agent failures.

### Debug Log Summary

Preflight found that the prompt supplied an absolute patch path while policy
accepted only the relative manifest path; those concerns are now separate. The
first notebook run also exposed a missing quote in `P06-C03`, before benchmark API
calls. Both fixes, plus usage accounting and report validation, are recorded in
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
| Evaluation compute | Local macOS CPU; no GPU required |
| Measured evaluation time | 72.78 seconds for 32 structured reviews plus both deterministic gateway modes |
| Final verification | 8 deterministic tests passed in 0.08 seconds |
| Dataset | 40 cases: eight development and 32 held-out; checksum `b86768acd310ca836fe6b370f5babc6989200b2879bbea6eb622409c2e5e5927` |
| Protocol controls | Agent-specific scopes, schema and metadata pinning, taint, redaction, approval, idempotency, and trace correlation |
| API review | `gpt-5.6-luna`, low reasoning effort; one recommendation per held-out case, scored but non-authoritative |
| API limits | 160 calls, 500 output tokens per call, two retries, USD 6.00 estimated cost |
| Measured API use | 32 calls, 6,865 input tokens, 3,701 output tokens, USD 0.029071 estimated cost |

### Results and Judgment

| Metric | Undefended | Defended | Judgment |
| --- | ---: | ---: | --- |
| Benign success | 100.00% | 100.00% | Included defenses preserved measured utility |
| Attack success | 85.19% | 0.00% | Policy enforcement blocked every included attack path |
| Secret leakage | 11.11% | 0.00% | Provenance and redaction prevented canary disclosure |
| Unsafe writes | 62.96% | 0.00% | Scope, schema, approval, and policy gates prevented unauthorized effects |
| Duplicate-effect cases | 9.38% | 0.00% | Idempotency removed repeated effects from duplicate delivery |
| Complete traces | 100.00% | 100.00% | Correlation and trace coverage were preserved in both modes |
| Policy-review accuracy | - | 84.38% | The model recommendation is informative but not reliable enough to authorize tools |

The measured result supports the control design against this synthetic threat
suite and also supports keeping model review non-authoritative. It does not test
internet transport, cryptographic identity, production authorization, or every
adaptive prompt-injection strategy.

### Evaluation Figures

The measured run generated `project7/output/project7_report_assets/attack_benign_matrix.png`,
`project7/output/project7_report_assets/procedure_diagram.svg`, correlated traces,
representative attacks, and `project7/output/project7_report.pdf`. The one-page PDF
was rendered and checked for readable charts, policy-review text, limits, and footer.

### Future Optimization

- Bind messages to signed identities, nonces, expiry, and replay-resistant tokens.
- Add real MCP and A2A transports behind the same policy interface and test version
  negotiation and partial failures.
- Expand red-team cases with adaptive multi-turn attacks and tool-result poisoning.
- Measure serialization, tracing, and policy overhead separately at p50 and p95.
- Add formal information-flow labels and property-based protocol fuzzing.

### Debug Log Summary

Earlier preflight corrected a synthetic key-shaped task ID and report heading
spacing. The measured run added retry and usage telemetry; one exact contract test
needed the new fields added to its expected summary. Details are in
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
| Evaluation compute | Local macOS CPU; no GPU required because API latency dominated |
| Measured evaluation time | 424.10 seconds for 80 QA items across 3 retrieval systems; report generation and validation completed afterward |
| Final verification | 11 deterministic tests passed in 0.07 seconds, including local embedding/answerer contracts; lifecycle evaluation completed in under one second |
| Dataset | LoCoMo samples 0 and 1, 40 QA per sample, plus deterministic lifecycle fixtures |
| Memory settings | Working window 6 events, episodic top-k 5, SQLite facts/events/tombstones, evidence-cited retrieval |
| API answerer | `gpt-5.6-luna`, low reasoning effort, strict grounded-answer schema and per-context cache |
| API limits | 300 calls, 500 output tokens per call, two retries, USD 8.00 estimated cost |
| Measured API use | 240 calls, 109,387 input tokens, 17,407 output tokens, USD 0.213829 estimated cost |

### Results and Judgment

| Metric | Recent window | Episodic | Hybrid |
| --- | ---: | ---: | ---: |
| LoCoMo exact match | 0.00% | 0.00% | 0.00% |
| LoCoMo mean token F1 | 3.20% | 11.50% | 9.41% |
| LoCoMo evidence recall | 1.25% | 22.29% | 19.17% |
| LoCoMo mean context tokens | 90.5 | 71.3 | 69.6 |
| Lifecycle exact match | 75.00% | 75.00% | 100.00% |

Episodic retrieval is the strongest current LoCoMo baseline, while the hybrid
recency bonus slightly lowers token F1 and evidence recall despite using the least
context. Strict exact match exposes substantial answer-quality headroom. Separately,
the lifecycle fixtures retain 100% hybrid exact match and 100% deletion compliance
across events, derived facts, retrieval, and tombstones. The fixed two-conversation
subset is compact and does not establish general memory-agent quality.

### Evaluation Figures

The measured run generated `project8/output/project8_report_assets/quality_context_tradeoff.png`,
`project8/output/project8_report_assets/procedure_diagram.svg`, 240-answer traces,
representative samples, and `project8/output/project8_report.pdf`. The final report
uses token F1 and evidence recall rather than an all-zero exact-match chart; its
rendered page was checked for legibility, spacing, deletion text, limits, and footer.

### Future Optimization

- Replace lexical retrieval with a versioned embedding index and compare hybrid
  fusion methods under fixed context budgets.
- Add learned memory extraction with calibrated confidence and provenance.
- Evaluate temporal interval queries, entity aliases, and multi-fact reasoning.
- Test cryptographic deletion receipts and provider/index deletion semantics.
- Tune retrieval only on a development split and report confidence intervals over
  conversations and QA categories.

### Debug Log Summary

The measured run completed all calls before `P08-C10` found a token-shaped string
inside the raw upstream clone. Validation now excludes only that third-party clone
while continuing to scan the selected subset and generated artifacts. Absolute
notebook paths were sanitized, and `P08-C10` was rerun without model calls. See
[`project8/debug_log/project8_debug_log.md`](project8/debug_log/project8_debug_log.md).

## Documentation Maintenance

The root [`README.md`](README.md) is a concise repository and portfolio summary.
Whenever its project-summary content changes, update the corresponding project
entry in this file in the same commit. Detailed methods, resources, settings,
results, judgments, figures, future optimization, and debug information belong
here rather than in the root README.
