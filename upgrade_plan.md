# Upgrade Plan: Projects 4-8

> **Updated:** 2026-11-18 05:25 EST<br>
> **Version:** 1.7: verified A100 SQL and memory comparisons<br>
> **Status:** Implementation started; unchecked items are not completed or validated.

## Scope And Rules

The audit identified useful modern orchestration and policy methods, but several
security boundaries and evaluation procedures remain demonstration-level. Older
local models are secondary to these correctness and evidence issues.

- **P0:** Safety or evidence defects; address before customer exposure or new claims.
- **P1:** Reliable integration and independent controlled evaluation.
- **P2:** Optimization supported by measured errors, latency, and cost.
- Preserve existing results as historical runs. New code does not retroactively
  validate their claims; write new outputs to separately versioned run directories.
- Update the notebook and imported implementation together. Record exact changed
  notebook cell numbers/IDs; preserve unrelated user modifications and outputs.
- Stop and ask for help after three failed attempts on the same issue. Record
  attempts in the relevant debug log.
- No automatic commit or push. Update summary documentation only with verified
  status; keep detailed measured results in `projects_info.md` when new runs exist.

## Shared Checklist

- [x] **S1 / P0:** Capture changed-cell maps and preserve historical artifacts.
- [x] **S2 / P0:** Use isolated, locked, tested environments and security checks.
  In particular, Project 4's `langgraph-checkpoint-sqlite>=2,<4` permits known
  vulnerable releases; this is not proof the installed version is vulnerable.
  CPU/API locks now use distribution hashes and pass the advisory audit. All five
  notebook setup cells pass in a fresh isolated kernel environment; 144 CPU tests
  pass locally (two Docker-only tests are separate). Projects 5 and 8 completed
  on MyPro in the sibling project's hash-locked CUDA inference environment.
- [x] **S3 / P1:** Add deterministic CI regression checks and notebook validation.
- [ ] **S4 / P1:** Version prompts/models/datasets/caches and record paired task
  metrics, model versus harness failures, latency, tokens, and cost.
  Shared credential-free run manifests now wrap all five main evaluation cells,
  including failures, source/data/config hashes, packages, hardware, and runtime.
  New outputs use upgrade-v2. Three local metadata tests pass; completeness of
  observed model revisions/usage still requires the deferred end-to-end runs.
- [ ] **S5 / P2:** Benchmark newer small local models after schema/formatting
  failures are diagnosed. Retain structured Responses API paths already present.

## Project 5: Governed Text-To-SQL Analyst

**Evidence:** [Policy](project5/src/project5_agent/governance.py),
[execution and planners](project5/src/project5_agent/analyst.py),
[notebook](project5/project5_governed_text_to_sql.ipynb).

**Finding:** Region checks trust model-declared metadata rather than enforced
row access. Read-only DuckDB is not an I/O sandbox. The governed path hardcodes
`pii_leaked=False`; baseline leakage uses column names despite masking. Schema
retrieval provides table descriptions instead of full columns/types/relationships.

### Ordered Checklist

- [x] **P5-01 / P0:** Enforce authorized rows and PII exclusion independently of
  model declarations, using restricted relations or tenant-specific snapshots.
  Reject wildcard/alias/lineage bypasses and test mismatched region metadata.
- [x] **P5-02 / P0:** Disable external I/O and extension loading where supported;
  bound execution time, memory, and returned rows. Fail closed on missing controls.
- [x] **P5-03 / P0:** Replace hardcoded leakage accounting with an independent,
  consistently applied output audit and keep exposure versus masking distinct.
- [x] **P5-04 / P1:** Supply introspected authorized schema, column types, and
  join relationships; preserve clarification and bounded repair behavior.
- [x] **P5-05 / P1:** Update notebook safety preflight and run regression tests.
- [x] **P5-06 / P1:** Re-evaluate API/local models on held-out queries and bypass
  cases. Report semantic result correctness separately from SQL execution success.
  Completed for the local model and deterministic boundary controls; a fresh API
  model comparison remains a separate optional run, not implied by these results.
- [x] **P5-07 / P2:** Compare newer local models under equal budgets after the
  zero-correct-result local baseline's schema/formatting failures are understood.
  MyPro run `20261118T100123095228Z` verified a matched 40-case holdout and
  equal settings apart from the model. Governed result-value matches increased
  from 2/27 to 13/27 with Qwen3-4B-Instruct-2507, and model calls fell from
  84 to 41. Both models recorded zero observed PII leakage on this suite.

**Acceptance:** Incorrect metadata cannot expand access; restricted data never
reaches the planner/output; leak metrics come from observations, not assumptions.

## Project 6: Test-Driven Code-Repair Agent

**Evidence:** [Runner](project6/src/project6_agent/runner.py),
[repair loop](project6/src/project6_agent/agent.py),
[notebook](project6/project6_test_driven_code_repair.ipynb).

**Finding:** Resource-limited subprocesses inherit the parent environment and do
not isolate filesystem/network access. Hidden-test failure feeds back into repair,
so those tests are not a blind final holdout. Repository-map/localization results
are computed without being incorporated into planner context.

### Ordered Checklist

- [x] **P6-01 / P0:** Default generated-code execution to an isolated backend
  with no secrets, no network, restricted mounts, and CPU/memory/process limits.
  Fail closed when unavailable; allow trusted-fixture mode only explicitly.
- [x] **P6-02 / P0:** Select patches using public/development tests only; run
  final hidden evaluation once without returning its feedback to the planner.
  Keep hidden test material outside the repair workspace until final evaluation.
- [x] **P6-03 / P1:** Feed repository mapping and fault locations into the repair
  context, with bounded context and allowed-path validation.
- [x] **P6-04 / P1:** Update notebook preflight and test isolation command
  construction, timeout/output handling, hidden-test separation, and rollback.
- [x] **P6-05 / P1:** Execute a sandbox integration test and independently score
  final candidates. Do not substitute mocked runner tests for real isolation tests.
- [ ] **P6-06 / P2:** Expand beyond eight compact bugs to a manageable real-repo
  benchmark subset; compare models/edit interfaces under a matched attempt budget.
  Partial: development-only structured-edit comparison is implemented and measured
  (4/4 vs 2/4 verified). Four SWE-bench Lite development tasks and eight test tasks
  are now frozen, with public planner views separated from evaluator gold and
  official prediction/harness interfaces tested. Real-repository repair, official
  container scoring, and matched model comparisons remain pending; see BENCHMARKS.md.
  SWE-bench 5.0.2's isolated, audited CLI preflight passed. Its stock executor
  adds `SYS_ADMIN`, so it was held at preflight for generated patches.

**Acceptance:** No ambient credential inheritance or unrestricted host access;
held-out evaluation cannot steer patch selection; accepted patches have real tests.

## Project 7: Secure Interoperable Agent Gateway

**Evidence:** [Gateway](project7/src/project7_agent/gateway.py),
[contracts](project7/src/project7_agent/contracts.py),
[notebook](project7/project7_secure_agent_gateway.ipynb).

**Finding:** In-process protocol-shaped objects do not demonstrate MCP/A2A
interoperability. Benchmark category labels affect gateway behavior, and fixed
canary/keyword controls are not evidence of general injection resistance. Recipient
names must not serve as authenticated identity; the model review is advisory.

### Ordered Checklist

- [x] **P7-01 / P0:** Remove benchmark-label-dependent decision logic; separate
  evaluator gold labels from runtime requests and mark fixture-only metrics.
- [x] **P7-02 / P0:** Bind policy to an authenticated principal rather than a
  caller-selected recipient/card. Persist idempotency across gateway restarts.
  Verified signed JWT issuer/audience/expiry/client/subject binding, per-tool
  scopes, actor-bound approvals, and restart deduplication through real MCP
  Streamable HTTP. Production identity-provider login and TLS deployment remain
  outside this local resource-server test; stdio retains trusted launch identity.
- [x] **P7-03 / P1:** Implement and test a real MCP client/server with a supported
  SDK/transport and versioned tool contracts. Use A2A only for genuine cross-service
  task handoff; do not imply it is implemented by a similar JSON envelope.
- [x] **P7-04 / P1:** Connect an actual tool-using model to the boundary and
  evaluate held-out/adaptive injections, exfiltration attempts, and benign tasks.
  Completed for a small authored set and one heuristic adaptive escalation;
  broad/adversarial robustness and independent final-answer grading remain unmeasured.
- [x] **P7-05 / P1:** Update notebook and run independent policy/protocol tests.
- [x] **P7-06 / P2:** Add end-to-end cancellation, timeouts, correlated traces,
  permission changes, and malicious tool-result tests.
  Real stdio cancellation/deadline tests, correlated client/server spans, live
  binding revocation, async model deadlines, and hostile tool-result controls
  pass. Cancellation is cooperative and does not undo committed effects or
  guarantee provider-side cancellation. These are authored control tests, not
  general injection-resistance measurements or a production key-rotation service.

**Acceptance:** Safety does not depend on knowing the attack category; identities
are verified; real interoperability and model-injection resistance have separate tests.

## Project 4: Durable Incident-Response Agent

**Evidence:** [Workflow](project4/src/project4_agent/workflow.py),
[simulator](project4/src/project4_agent/simulator.py),
[notebook](project4/project4_durable_incident_response_agent.ipynb).

**Finding:** LangGraph checkpoints, interrupts, idempotency, and compensation remain
appropriate. Same-database simulated effects do not establish safe distributed
execution. Approval is simulated; evidence checks largely verify reference IDs.

### Ordered Checklist

- [x] **P4-01 / P0:** Exclude known-vulnerable checkpointer versions, test the
  resolved version, and document the simulator versus production boundary.
- [x] **P4-02 / P1:** Strengthen concurrent duplicate-delivery tests and atomic
  ledger behavior; retain the existing frozen paired planner comparison.
- [x] **P4-03 / P1:** Add a separate sandbox service and real process-kill/restart
  tests, including unknown remote outcomes and reconciliation before retry.
- [x] **P4-04 / P1:** Bind approval to incident, action, parameters, reviewer,
  and expiry; revalidate authorization after resuming a paused workflow.
- [x] **P4-05 / P1:** Update notebook, run recovery/safety tests, and report
  executed-crash denominators, duplicate effects, and compensation evidence.
- [x] **P4-06 / P2:** Add node-level p50/p95 traces and load tests; migrate storage
  only if concurrency or deployment needs justify it.
  Short local deterministic loads at concurrency 1/4/8 are measured; no serving
  capacity or storage-migration conclusion is drawn from these small runs.

**Acceptance:** Recovery survives a real process restart, approved parameters
cannot drift, and no distributed exactly-once guarantee is inferred from SQLite tests.

## Project 8: Long-Term Memory Agent

**Evidence:** [Memory lifecycle](project8/src/project8_agent/memory.py),
[LoCoMo evaluation](project8/src/project8_agent/locomo.py),
[notebook](project8/project8_long_term_memory.ipynb).

**Finding:** Lifecycle extraction expects `FACT`/`CORRECT` annotations. Tombstones
are not consulted by ingestion, so deleted events can reappear. API versus local
comparisons change answerer and retriever simultaneously. Evidence recall uses
generated citations, and reported context tokens are whitespace-word counts.

### Ordered Checklist

- [x] **P8-01 / P0:** Enforce tombstones during replay/reingestion and test
  deletion after corrections, duplicates, and consolidation.
- [x] **P8-02 / P0:** Separate retrieved-evidence recall from cited-evidence recall;
  label word counts correctly or use the actual tokenizer. Version answer caches
  with prompt/decoding settings as well as context and model.
- [x] **P8-03 / P1:** Add validated natural-language fact extraction with source
  provenance, temporal updates/conflict handling, and explicit retention consent.
- [x] **P8-04 / P1:** Propagate deletion to cached answers and derived indexes;
  test that a deleted fact is not recoverable through alternate retrieval paths.
- [x] **P8-05 / P1:** Update notebook and run same-answerer retrieval ablations
  with neighboring-turn context and separate lifecycle versus QA evaluation.
- [ ] **P8-06 / P2:** Add LongMemEval tasks for temporal reasoning, knowledge
  updates, and abstention; adopt reranking only if matched-budget results improve.
  The pinned cleaned S file is validated, with six balanced tasks prepared, gold
  fields removed from planner inputs, true-tokenizer context budgeting, failure
  retention, and five adapter tests. The six-case A100 run completed with zero
  errors across three arms in 122.69 s. Episodic and hybrid tied at 0.3333 lexical
  F1 on the two update tasks versus 0 for the recent window. All arms abstained
  correctly on both abstention tasks. Official semantic grading, larger-sample
  uncertainty, and reranking comparisons remain open. See project8/BENCHMARKS.md.

## Current Follow-Up Cells

| Project | Changed Cells (1-Based) | Purpose |
| --- | --- | --- |
| 4 | 2 `P04-C01`, 9 `P04-C08` | Isolated setup and versioned run provenance |
| 5 | 2 `P05-C01`, 9 `P05-C08` | Isolated setup and versioned run provenance; data cell unchanged |
| 6 | 1 `P06-C00`, 2 `P06-C01`, 9 `P06-C08`, 13 `P06-C12`; added 14 `P06-C13`, 15 `P06-C14` | Patched sandbox, provenance, v2 development output, frozen real-repo preparation |
| 7 | 1 `P07-C00`, 2 `P07-C01`, 9 `P07-C08` | Authenticated boundary, isolated setup, async bounded model calls and provenance |
| 8 | 2 `P08-C01`, 9 `P08-C08`; added 12 `P08-C11`, 13 `P08-C12` | Isolated setup, provenance, opt-in LongMemEval adapter; data cell unchanged |

Project 5 cells 12-13 launch and check the matched local model runs in the
isolated CUDA environment. Project 8 cells 13-15 select, launch, and check the
LongMemEval run. The checks use the same original notebook datasets and use
no paid API services. Historical output directories retain their original versions.

**Acceptance:** Deleted facts stay deleted; lifecycle fixtures are not presented
as natural-language memory quality; retriever effects are isolated from model changes.

## Overall Execution Order

1. Shared environment/preflight work and Project 5/6 safety defects.
2. Project 7 policy/evaluation boundary and real protocol integration.
3. Project 8 deletion/metric corrections and Project 4 recovery/approval tests.
4. Notebook integration and deterministic regression suites for all projects.
5. Real sandbox, protocol, and API/GPU evaluations where runtimes are available.
6. Model refreshes and performance optimization after evidence is trustworthy.

## Primary References

- [SQLite checkpointer advisory](https://github.com/langchain-ai/langgraph/security/advisories/GHSA-9rwj-6rc7-p77c):
  versions before 3.0.1 affected; resolve and audit current dependencies rather
  than assuming that this historical patch floor guarantees complete security.
- [DuckDB security](https://duckdb.org/docs/2.0/operations_manual/securing_duckdb/overview).
- [MCP transports](https://modelcontextprotocol.io/specification/latest/basic/transports).
- [A2A specification](https://a2a-protocol.org/latest/specification/).
- [AgentDojo](https://github.com/ethz-spylab/agentdojo).
- [SWE-bench](https://github.com/SWE-bench/SWE-bench).
- [LongMemEval](https://github.com/xiaowu0162/LongMemEval).
- [vLLM structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/).
- [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) and
  [Qwen3 embedding/reranking](https://github.com/QwenLM/Qwen3-Embedding): benchmark
  candidates, not promised improvements or drop-in replacements.

## Implementation Record

New model evaluations have run for Projects 4-8 in versioned directories.
Completed checks do not imply that unchecked deployment/GPU steps are complete.

| Project | Verification So Far | Notebook Cells Changed (1-Based) |
| --- | --- | --- |
| 5 | 25 deterministic tests, completed 40-query GPU comparison, frozen-SQL value rescoring | 1 `P05-C00`, 7 `P05-C06`, 9-11 `P05-C08` through `P05-C10`; cell 1 also documents strict-hash versus value metrics |
| 6 | Real Docker checks, eight-bug API test run, and separate development edit comparison | 1 `P06-C00`, 9-11 `P06-C08` through `P06-C10`; added 12-13 `P06-C11`, `P06-C12` |
| 7 | Real SDK v2.3 stdio, server restart, strict function schemas, and actual model-to-MCP run | 1 `P07-C00`, 7 `P07-C06`, 9-11 `P07-C08` through `P07-C10`; cell 9 now runs the live tool loop in API mode |
| 4 | 23 tests passed, including whole-workflow death/restart, separate action-process reconciliation and node timing | 1 `P04-C00`, 8-11 `P04-C07` through `P04-C10` |
| 8 | 26 CPU tests; completed 50-question matched retrieval ablation, plus frozen-output paired uncertainty | 1 `P08-C00`, 7 `P08-C06`, 9-11 `P08-C08` through `P08-C10`; no further notebook edits for offline analysis |

Project 4 still uses a simulated reviewer and synthetic actions. Its process-separated
service tests real lost acknowledgements and reconciliation, not network identity or
OS-level isolation. Project 7 binds the
local stdio process to a trusted launch identity; authenticated remote service
deployment remains pending. Project 8 invalidates its implemented caches/indexes,
not third-party backups or provider retention. Historical summaries are unchanged.

The CPU dependency snapshot and secret-free CI workflow are added, but Linux CI
has not run and no push was made. Project 8's new local ablation samples up to
50 QA items under the existing 300-call cap (two retrievers x three systems);
it does not silently increase the budget or compare this subset to the historical
80-question result as a matched experiment. Usage is measured incrementally per arm.
The report generator now derives the winning/tied system from data, handles lifecycle
summaries, labels context words correctly, and avoids a fixed 30% chart ceiling.

Project 8's natural-language API extraction interface is typed and bounded, and
ingestion validates consent/source binding before storage. Exact quotes are
provenance checks, not proof of entailment. Corrections require trusted-controller
authorization; provider-backed extraction quality is not measured by mock tests.

New authored deterministic runs for Projects 4, 5, 7, and 8 are saved under their
`output/runs/upgrade-v1/deterministic/` folders and summarized in `projects_info.md`.

Project 5 now records shared initial planning time in each arm's end-to-end latency,
and separates policy/abstention from failures that merely prevented execution.
Failed local generations count against the model-call budget. Projects 5/8 pin model
and embedding revisions when loading them. Project 8 bounds adjacent-turn expansion
by the same event limit for both retrievers, separates fresh/cached timing, records
per-case generation errors, and preserves deletion markers across cache-format changes.

Docker Desktop is installed and the two real-container boundary tests pass.
New API runs show limits as well as successes: Project 4 remediation accuracy is
65.6% despite perfect root-cause identification; Project 6 one-shot verified 7/8
bugs versus 6/8 for the loop; Project 7 observed no leak/unsafe effect in six
synthetic attack cases with one adaptive escalation each. These are not production
claims. Details and settings are in `projects_info.md`. The full CPU rerun passes
107 tests and all notebook syntax checks; two Docker-only tests skipped there were
executed and passed separately. Projects 5/8 completed their GPU runs and the
A100 is idle. Project 5's strict result-hash accuracy is 0%,
but separately rescored fixed-fixture value equivalence is 5/27 baseline and
2/27 governed. This exposes both alias-sensitive grading and actual schema/metadata
failures. The revised metric never feeds reference SQL back into planner repair.

Project 8 used 250 fresh model calls and 50 cached window controls, within the
300-call cap. Dense episodic F1 was 0.1565 versus lexical 0.1159, but its paired
95% delta interval [-0.0330, 0.1206] includes zero. Both lexical generation failures
remain in answer scores. Retrieval recall, citation recall, fresh/cached timings,
and authored lifecycle checks are reported independently. The analysis conditions
on only two conversations; no general memory-quality improvement is established.

Remaining unchecked work includes a complete cross-platform dependency/security
audit and uniform run metadata, newer-model comparisons, a fresh real-repository
code benchmark, authenticated remote gateway deployment, and LongMemEval. These
are not silently marked complete by the successful local evaluation round.

See [upgrade debugging record](debug_log/upgrade_debug_log.md).
