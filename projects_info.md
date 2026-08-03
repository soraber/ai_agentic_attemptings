# AI Agentic Projects Information

Detailed implementation, evaluation, resource, and maintenance information for
the projects developed in this repository. The structure follows the project
documentation pattern used in `ai_project_artifacts`: portfolio summary,
repository map, methods, compute settings, results and judgment, future work, and
debugging notes.

> **Version:** ver 0.1: document Project 4 pre-execution scaffold<br>
> **Updated:** 2026-08-02 23:07 EDT

## Portfolio Summary

| Project | Primary goal | Main comparison | Current result | Judgment |
| --- | --- | --- | --- | --- |
| 4. Durable Incident-Response Agent | Build a recoverable, approval-gated agent for simulated service incidents | Stateless linear loop vs. checkpointed LangGraph workflow | Preflight complete: 11 deterministic tests passed; final API evaluation has not run | The workflow mechanics, safety policy, idempotency, recovery, redaction, and report pipeline are ready; no model-quality claim should be made yet |

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

## Documentation Maintenance

The root [`README.md`](README.md) is a concise repository and portfolio summary.
Whenever its project-summary content changes, update the corresponding project
entry in this file in the same commit. Detailed methods, resources, settings,
results, judgments, figures, future optimization, and debug information belong
here rather than in the root README.
