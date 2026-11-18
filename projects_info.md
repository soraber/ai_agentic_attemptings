# AI Agentic Projects Information

Detailed implementation, evaluation, resource, and maintenance information for
the projects developed in this repository. The structure follows the project
documentation pattern used in `ai_project_artifacts`: portfolio summary,
repository map, methods, compute settings, results and judgment, future work, and
debugging notes.

> **Version:** ver 0.15: verified A100 SQL and LongMemEval comparisons<br>
> **Updated:** 2026-11-18 05:25 EST

## P0 Security Follow-Up

The CPU regression and full CPU/API notebook environments now have hash-locked
dependencies. The 2026-11-17 pip-audit scan reports no known advisories for these
locks after upgrading pytest to 9.0.3. This is a point-in-time dependency check,
not proof of application security. All five setup cells pass in a fresh Python
3.11 venv. macOS and offline Linux ARM64 checks pass 144 tests, with two Docker-only checks
handled separately. No API calls or new model-quality claims were made in this step.

Project 7 now verifies signed, short-lived access tokens against configured public
keys, issuer, audience, subject and client bindings. Permissions come from verified
identity and tool scopes, not model-selected sender fields. Approvals are bound to
that actor and survive restart. Eighteen new authentication tests include a real
MCP Streamable HTTP socket exchange. Deployment behind TLS and a real identity
provider, key rotation operations, and provider login are not claimed tested.

Notebook cells changed in this follow-up: Project 4 cells 2/9 (`P04-C01`, `P04-C08`);
Project 5 cells 2/9 (`P05-C01`, `P05-C08`); Project 6 cells 1/2/9/13
(`P06-C00`, `P06-C01`, `P06-C08`, `P06-C12`) plus new 14/15 (`P06-C13`, `P06-C14`);
Project 7 cells 1/2/9 (`P07-C00`, `P07-C01`, `P07-C08`); Project 8 cells 2/9
(`P08-C01`, `P08-C08`) plus new 12/13 (`P08-C11`, `P08-C12`). Setup no longer installs into the shared
interpreter or automatically pulls repository changes. Historical GPU locks have
new advisory findings and must not be reused for new runs; shared P0 remains open
until their replacements have passed GPU validation.
The sibling repository's approved LangGraph migration removes the unused
CrewAI/Chroma packages. MyPro has validated the patched inference lock with
the Project 5 matched model comparison.

Project 6's patched sandbox also passed both real-container integration tests
([new evidence](project6/output/runs/upgrade-v2/docker/20261117T165406957329Z/sandbox_validation.json)).
Its tag is `project6-test-runner:p0-20261117`, with a pinned Python base digest and
hash-verified pytest 9.0.3 dependencies. Historical sandbox results retain the old
image ID. The current macOS CPU suite passes 144 tests; both Docker tests are
additional, not counted as CPU passes. See [security setup](SECURITY_UPGRADE.md)
and [Project 7 HTTP boundary](project7/HTTP_AUTH.md) for execution details.

### Non-Training Follow-Up

| Project | New Local Work | Verification And Pending Experiments |
| --- | --- | --- |
| 4 | Main evaluation records versioned source/data/config hashes, packages, timing, and failures | 23 CPU tests; prior recovery/load evidence is unchanged. No new API run. |
| 5 | Isolated notebook setup and common v2 run manifest | 25 CPU tests. On the same 40-case holdout, Qwen3-4B improved governed value matches from 2/27 to 13/27. See the v2 results below. |
| 6 | Patched executor plus frozen SWE-bench Lite public/evaluator views and official prediction interface | 24 tests including two real Docker tests. SWE-bench 5.0.2 CLI preflight passed. Official scoring remains open because the stock evaluator requests `SYS_ADMIN`. [Procedure](project6/BENCHMARKS.md). |
| 7 | Authenticated HTTP, live binding revocation, model/tool/case deadlines, real MCP cancellation, correlated payload-free server traces, hostile tool-result controls | 43 CPU tests including shared preflight/provenance checks. Async model harness retains unknown-cost reservations. No new model-quality run; cancellation cannot undo a committed effect. |
| 8 | Gold-separated LongMemEval-S adapter, tokenizer-bounded contexts, per-case failure retention, optional notebook experiment | 31 CPU tests plus a six-case A100 pilot across temporal reasoning, updates, and abstention. See the v2 results below. |

All five main evaluation cells write new `upgrade-v2` outputs with
`run_manifest.json`. The manifests capture source-only notebook fingerprints,
configuration/dataset hashes, package versions, runtime, status, and observed
model metadata where available. They do not collect environment variables or
credentials. Actual API aliases are not asserted to be immutable model revisions.
Shared S4 stays open until a new end-to-end run verifies all usage/provenance fields.
Public benchmark preparation manifests contain hashes and IDs, not gold patches,
full histories, or credentials. Historical figures/PDFs are not regenerated from
these local checks.

### Project 5 Matched Local Model Comparison

The original notebook's cells 12-13 launched and verified a 910.66-second run on
one A100-SXM4-40GB. Both models used BF16, the same 40-case holdout, the same
schema retriever, a 500-token output cap and at most two repair attempts.

| Planner | Baseline Value Matches | Governed Value Matches | Model Calls | Governed p50 |
| --- | ---: | ---: | ---: | ---: |
| Qwen2.5-Coder-7B-Instruct | 5/27 | 2/27 | 84 | 11.61 s |
| Qwen3-4B-Instruct-2507 | 23/27 | 13/27 | 41 | 8.25 s |

Both planners had zero observed PII leaks on this fixture. The candidate's
governed result is ten more value matches than the earlier model. The gap
between its baseline and governed results remains a separate area to diagnose.
[Metrics snapshot](project5/output/runs/upgrade-v2/20261118T100123095228Z/metrics_snapshot.json).

### Project 8 LongMemEval-S Pilot

Cells 13-15 selected, launched, and verified the six-case comparison in 122.69
seconds on one A100-SXM4-40GB. All three retrievers used the same pinned
Qwen2.5-7B-Instruct answerer and 2,048-token context cap. Episodic and hybrid
retrieval both scored 0.3333 lexical F1 on the two knowledge-update cases.
The recent window scored zero. Every arm scored zero lexical F1 on the two
temporal cases and abstained correctly on both absence cases. The narrow pilot
checks integration and the saved hypotheses still need official semantic grading.
[Metrics snapshot](project8/output/runs/upgrade-v2/20261118T102213022610Z/metrics_snapshot.json).

## Upgrade Evidence

The sections below retain the historical experiments, not measurements of the
upgraded implementation. See [upgrade_plan.md](upgrade_plan.md) for exact notebook
cell changes, completed steps, and remaining work, and the [upgrade debug log](debug_log/upgrade_debug_log.md)
for implementation issues. No historical outputs were overwritten or pushed.

| Project | Implemented And Verified | New Evidence / Remaining Gate |
| --- | --- | --- |
| 4 | Parameter-bound expiring approvals; atomic idempotency; whole-workflow process restart; separate local action process with reconciliation before retry | 23 CPU tests. [New API run](project4/output/runs/upgrade-v1/openai/20261117T053319313741Z/project4_final_summary.json): root-cause accuracy 100%, remediation accuracy 65.6%; no durable duplicate effects. Only five durable crash trials actually executed, all recovered. Reviewer/actions remain simulated; no distributed exactly-once guarantee. |
| 5 | Physical authorized-row/PII-free snapshots, disabled external I/O, query timeout/row cap, introspected schema, bounded failed calls, final value scoring separate from exact hashes | 25 CPU tests; 22 then-current tests also passed on Colab. [New GPU run](project5/output/runs/upgrade-v1/local_gpu/20261117T064159242835Z/): no observed PII exposure, but weak planning. [Frozen-SQL value scoring](project5/output/runs/upgrade-v1/local_gpu/20261117T064159242835Z/value_scoring_v2/summary.json) matched 5/27 baseline vs 2/27 governed answerable cases. Three otherwise correct queries were blocked because model table metadata omitted nested references. Strict alias-sensitive hash scores remain 0%. |
| 6 | Generated code requires Docker; secrets/network restricted; hidden tests used once after selection; localization enters planner context; optional exact source edits and shared API budget | [Two real-container checks](project6/output/runs/upgrade-v1/docker/20261117T054654314647Z/sandbox_validation.json) passed. [API/Docker test run](project6/output/runs/upgrade-v1/openai/20261117T053902107808Z/project6_final_summary.json): one-shot 7/8 vs repair-loop 6/8. [Separate development comparison](project6/output/runs/upgrade-v1/development_edits/20261117T055338129249Z/development_summary.json): structured edits 4/4 versus unified diffs 2/4; not a new holdout score. |
| 7 | Real MCP v2.3 stdio server/client, trusted launch identity, persisted approvals and idempotency, strict API schema conversion, bounded model/tool loop | [Historical model-to-MCP run](project7/output/runs/upgrade-v1/model_mcp/20261117T054505255155Z/model_mcp_summary.json): two benign tasks passed; six synthetic attack cases with one heuristic adaptive escalation each produced no observed leaks/unauthorized effects. Small authored set, not general injection resistance. The later authenticated HTTP and lifecycle controls are independently tested above; production deployment remains pending. |
| 8 | Tombstones survive replay/cache-format changes; dependent caches are invalidated; source-bound consent; bounded neighboring turns; fresh/cached timing and retrieved/cited recall separated | 26 CPU tests; 23 then-current tests passed in Colab. [Same-answerer GPU ablation](project8/output/runs/upgrade-v1/local_gpu/20261117T064159242835Z/) is complete with 50 questions and 250 fresh calls. Dense episodic F1 0.1565 versus lexical 0.1159; paired interval includes zero. Authored lifecycle tests validate deletion behavior, not natural-language extraction quality or provider retention. |

The CPU checks run in an isolated Python 3.11 environment captured in
`requirements-upgrade-cpu.lock.txt`. Secret-free CI is added but has not been run
on GitHub. Model runs and fixture runs have separate directories and source-hash
manifests. No GPU result or model improvement is inferred from CPU tests. Projects 5/8
resolve model and embedding commits before loading; actual GPU environment locks,
timing, peak memory, and per-case scores accompany completed runs. The prepared
queue uses a separate inference environment because CrewAI's MCP 1.x requirement
conflicts with Project 7's tested MCP 2.x transport. Both GPU runs are complete,
and the A100 is idle. Historical reports/runbooks describe their
original stacks; consult the upgrade checklist for the new execution boundaries.
That earlier CPU run passed 107 tests. The current suite passes 144 with all
notebook syntax checks; two Docker-only checks are skipped there but pass separately.

### New Run Resources And Judgment

| Run | Resources And Settings | Observations And Limits |
| --- | --- | --- |
| Project 4 | Local Python 3.11 orchestration, OpenAI GPT-5.6 Luna, low reasoning, 2,048 maximum output tokens; 64 calls, 48,086 input/13,407 output tokens; 170.34 seconds; estimated $0.025706 | Frozen decisions shared between arms. Durable statuses: 11 resolved, seven operator-rejected, 14 evidence-verification blocks. Duplicate-effect cases: baseline 50%, durable 0%. Recovery denominators are 16 baseline and five durable, not a matched set of executed crashes. Workflow-only latency excludes the shared planner calls. |
| Project 5 | One Colab A100 40 GB, Python 3.11.17, Qwen2.5-Coder-7B in BF16; model revision `c03e6d358207e414f1eca0bb1891e29f1db0e242`; 84 calls, 39,433 input/12,298 output tokens; 516.39 seconds including setup, 410.55 seconds evaluator time; peak allocated memory about 14.37 GiB. Maximum 500 new tokens, 180 calls, two repairs, five retrieved schema tables | 40 held-out questions, 27 answerable and 13 unsafe/ambiguous. Result-value equivalence: 18.5% baseline vs 7.4% governed; this is a fixed-fixture check, not general SQL correctness. Intentional unsafe policy/abstention: 0% vs 38.5%; both arms had execution/repair errors on 55% of all cases. End-to-end p50/p95: 4.66/6.54 seconds baseline, 11.44/19.41 governed. Local GPU API charge is zero, not zero compute cost. |
| Project 6 | Local Docker Desktop 4.99.0 / Engine 29.9.3 on ARM64; each executor 1 CPU, 512 MiB RAM, 64-process cap, no network, read-only mount. GPT-5.6 Sol, low reasoning, 2,048 output tokens; 20 calls, 28,886 input/4,574 output tokens; 80.03 cumulative trial seconds; estimated $0.207024 | Eight public benchmark bugs, one-shot vs at most three attempts; arm order seeded/randomized. Final tests never feed back to the planner. One-shot outperformed the loop by one case; this sample does not establish general superiority. Public benchmark contamination is possible. The next experiment should test edit-format reliability on development bugs, then use a fresh evaluation set. |
| Project 7 | Local MCP SDK 2.3.0 stdio plus OpenAI GPT-5.6 Luna; five model turns per trial, bounded tools, 1,024 output tokens, $5 cap; 42 calls, 18,227 input/1,445 output tokens; median 3.57 seconds/trial; estimated $0.005379 | Two benign cases and six attack cases, each attack tried twice with a response-conditioned heuristic escalation. No hostile tool attempts, canary leaks, or unauthorized effects were observed. This validates the narrow path, not resistance to sophisticated/adaptive attackers. Gateway rejection is separately established by transport tests. Final-answer semantic quality is not independently graded. |
| Project 8 | One Colab A100 40 GB; Qwen2.5-7B-Instruct BF16, revision `a09a35458c702b33eeacc393d103063234e8bc28`; MiniLM revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. 401.02 seconds including setup, 14.38 GiB peak allocation; 250 calls plus 50 cache hits, 115,801 input/10,303 output tokens, $0 API charge. Greedy 300-token outputs, shared 300-call cap; recent window six events, retrieval five events including neighboring-turn expansion | Same answerer, prompt and decoding across lexical/dense arms, 25 questions from each of two conversations. Dense episodic exact match 6%, lexical 2%; two lexical JSON/validation failures remain in scores. Same-window cached outputs are not faster inference. Retrieval and citation recall are separate; lifecycle deletion compliance is a separate authored fixture, not a natural-language QA guarantee. |

Prices were checked on 2026-11-17 against the official
[Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna) and
[Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol) model pages.
Costs use uncached token rates and are estimates, not billing statements. The
four-development-bug edit comparison took 159.21 seconds and 12 calls, estimated
$0.097064. Structured edits used four calls; unified diffs used eight and failed
two cases with malformed patches. This diagnoses an interface weakness, not a
general repair-accuracy gain. Its saved source hashes are end-of-run snapshots;
the effective configuration is recorded separately. New
results do not overwrite historical figures or PDFs. No credentials were persisted
in these runs, and the MCP/test-container environments do not inherit API keys.

Project 4 also has [local deterministic load evidence](project4/output/runs/upgrade-v1/load/20261117T060455018600Z/load_summary.json):
32 requests at each concurrency of 1, 4, and 8, all resolved with exactly 32 effects
per condition. Worker-entry-to-completion p95 was 10.91, 35.83, and 87.90 ms;
throughput was approximately 105, 128, and 116 requests/s. This sub-second,
cold-initialization smoke test excludes model latency, human approval wait, and
pending executor-queue wait. It is not a serving-capacity estimate or evidence to
migrate storage. Per-node p50/p95 separates successful, interrupted, and failed spans.

Interpretation changes: Project 5's old baseline used different data-access
boundaries and PII accounting; Project 6's old hidden tests influenced patch
selection; Project 7's old scores covered protocol-shaped fixtures; Project 8's
old API/local comparison changed both answerer and retrieval. These historical
values remain visible for traceability, not as controlled evidence for new code.

Project 5's value metric ignores column aliases but retains column positions,
duplicate rows, NULL values, and ordering requested by the reference query, using
numeric tolerances of 1e-6 absolute / 1e-9 relative. The original strict hashes
are retained. The corrected metric re-executes frozen SQL inside the same physical
tenant snapshot and never returns gold-query feedback to the model. Missing
`orders.region` columns and inconsistent nested-table metadata are model/interface
failures, not reasons to weaken data restrictions. Improve schema/contract use on
development questions, then reserve a fresh holdout for any next model comparison.

### Project 8 Matched Retrieval Results

Each row uses the same 50-question slice. F1 and recall are fractions; fresh
latency includes retrieval and generation, including the first dense index build.

| Retrieval / Memory | Exact Match | Token F1 | Retrieved Recall | Cited Recall | Fresh p50 / p95 Seconds |
| --- | --- | --- | --- | --- | --- |
| Lexical / recent window | 0% | 0.0022 | 0.0000 | 0.0000 | 0.899 / 1.947 |
| Lexical / episodic | 2% | 0.1159 | 0.2567 | 0.2367 | 1.307 / 2.377 |
| Dense / episodic | 6% | 0.1565 | 0.2717 | 0.2517 | 1.330 / 2.297 |
| Lexical / hybrid | 2% | 0.0830 | 0.2000 | 0.1800 | 1.311 / 2.345 |
| Dense / hybrid | 4% | 0.1193 | 0.2217 | 0.2017 | 1.226 / 2.314 |

The dense-arm recent-window control reuses 50 identical cached answers, so its
sub-millisecond latency is not shown as a serving improvement. Episodic abstentions
were 29/50 lexical and 27/50 dense; window abstained on 49/50. Lexical episodic and
hybrid each had one `ValueError`, retained as failed answers rather than excluded.

[Paired analysis](project8/output/runs/upgrade-v1/local_gpu/20261117T064159242835Z/paired_analysis_v1.json)
uses 2,000 within-conversation paired question resamples: dense-minus-lexical F1
is +0.0405, CI [-0.0330, 0.1206] for episodic, and +0.0363,
CI [-0.0197, 0.1040] for hybrid. These descriptive intervals condition on just
two conversations, do not establish generalization, and are not adjusted for
multiple comparisons. Neither establishes a reliable F1 gain. Low retrieved
recall is an important bottleneck; a larger independent temporal-memory set and
development-only retrieval/context experiments should precede deployment claims.

Reproduce the offline analysis with
`python project8/tools/analyze_saved_ablation.py <saved-run-directory>`.
The command refuses to overwrite an existing analysis; it never makes model calls
or changes the original results. The historical 80-question run is not a matched
baseline for this 50-question experiment.

## Historical Portfolio Summary

| Project | Primary goal | Main comparison | Current result | Judgment |
| --- | --- | --- | --- | --- |
| 4. Durable Incident-Response Agent | Build a recoverable, approval-gated agent for simulated service incidents | Stateless linear loop vs. checkpointed LangGraph workflow | Measured API run: 32 paired observations per system, 64 model calls, and 13 final local tests passed | The durable path preserved task quality, eliminated duplicate effects and unsafe allows, and recovered every executed crash, at roughly 10x workflow latency |
| 5. Governed Text-to-SQL Analyst | Answer analytics questions while enforcing database policy | One-shot SQL vs. schema-grounded governed repair | API: 40 held-out questions and 54 calls; A100: 40 questions and 91 local-model calls | API governance improved accuracy and safety; the local model retained zero PII leakage but did not produce correct result hashes, so it is a diagnostic comparison rather than the headline result |
| 6. Test-Driven Code-Repair Agent | Repair compact Python defects without accepting unsafe or overfit patches | One-shot patch vs. bounded test-driven repair loop | API: 8 defects per system and 18 calls; A100: 8 defects per system and 32 local-model calls | API feedback recovered one additional defect; the local model produced no accepted repair but rollback remained perfect, isolating proposal quality from harness safety |
| 7. Secure Interoperable Agent Gateway | Preserve utility while blocking protocol-layer attacks | Undefended vs. defended A2A/MCP-style workflow | Measured API run: 32 held-out cases, 32 review calls, and 8 final tests passed | The local controls eliminated included attacks without reducing benign utility; structured review was useful but correctly remained non-authoritative |
| 8. Long-Term Memory Agent | Retrieve useful cross-session facts while honoring corrections, conflicts, and deletion | Recent window vs. episodic vs. hybrid memory | API: 240 grounded answers; A100: 150 new local-model calls plus 90 cache hits; 12 tests passed | Episodic retrieval led both runs; the API lexical result exceeded the local dense result, while lifecycle controls and deletion compliance remained intact |

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
| [`project5/src/project5_agent/`](project5/src/project5_agent/) | DuckDB data, typed plans, SQLGlot policy, governed execution, paired evaluation, MiniLM schema retrieval, and a BF16 local planner |
| [`project5/tests/`](project5/tests/) | Dataset integrity, SQL policy, PII masking, repair, export approval, and paired-agent tests |
| [`project5/tools/`](project5/tools/) | Dataset, notebook, report, and structure/privacy generators and validators |
| [`project5/background/project5_background.md`](project5/background/project5_background.md) | Schema grounding, executable SQL evaluation, AST policy, repair, and governance concepts |
| [`project5/debug_log/project5_debug_log.md`](project5/debug_log/project5_debug_log.md) | Cell-specific preparation history |
| [`project5/output/`](project5/output/) | Measured API results and report plus the completed independent A100 comparison under `output/gpu/` |

### Project 6 Files

| File | Purpose |
| --- | --- |
| [`project6/project6_test_driven_code_repair.ipynb`](project6/project6_test_driven_code_repair.ipynb) | Stable cells `P06-C00` through `P06-C12` for pinned data, mapping, patching, tests, evaluation, export, and the optional development edit-interface comparison |
| [`project6/RUNBOOK.md`](project6/RUNBOOK.md) | QuixBugs preparation, execution modes, budgets, evidence checks, and troubleshooting |
| [`project6/data/quixbugs_manifest.json`](project6/data/quixbugs_manifest.json) | Twelve-case manifest pinned to one exact upstream commit |
| [`project6/src/project6_agent/`](project6/src/project6_agent/) | AST repository map, API and BF16 local patch planners, diff policy, subprocess runner, repair loop, rollback, and evaluation |
| [`project6/tests/`](project6/tests/) | Deterministic tests for mapping, path/line policy, timeout, hidden regression rejection, acceptance, and rollback |
| [`project6/tools/fetch_quixbugs.py`](project6/tools/fetch_quixbugs.py) | Download-once clone and pinned-revision verification |
| [`project6/tools/generate_report.py`](project6/tools/generate_report.py) | Generates measured repair charts, procedure diagram, and PDF |
| [`project6/tools/build_notebook.py`](project6/tools/build_notebook.py) | Rebuilds the notebook with stable cell IDs |
| [`project6/tools/validate_project.py`](project6/tools/validate_project.py) | Checks structure, notebook order, manifest pin, local paths, and key-shaped strings |
| [`project6/background/project6_background.md`](project6/background/project6_background.md) | Fault localization, constrained patches, feedback loops, hidden tests, and rollback concepts |
| [`project6/debug_log/project6_debug_log.md`](project6/debug_log/project6_debug_log.md) | Cell-specific preparation history |
| [`project6/output/`](project6/output/) | Measured API repair results and report plus the completed independent A100 comparison under `output/gpu/` |

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
| [`project8/src/project8_agent/`](project8/src/project8_agent/) | SQLite memory lifecycle, lexical and dense retrieval, LoCoMo conversion, cached API/local answerers, and evaluation |
| [`project8/tests/`](project8/tests/) | Memory ingestion, supersession, conflict, deletion, retrieval, lifecycle, and LoCoMo conversion tests |
| [`project8/tools/fetch_locomo.py`](project8/tools/fetch_locomo.py) | Download-once pinned LoCoMo subset preparation |
| [`project8/tools/generate_report.py`](project8/tools/generate_report.py) | Generates memory-quality/context charts, lifecycle diagram, and PDF |
| [`project8/tools/build_notebook.py`](project8/tools/build_notebook.py) | Rebuilds the notebook with stable cell IDs |
| [`project8/tools/validate_project.py`](project8/tools/validate_project.py) | Checks structure, notebook order, source pin, local paths, and key-shaped strings |
| [`project8/background/project8_background.md`](project8/background/project8_background.md) | Memory tiers, temporal retrieval, consolidation, conflicts, deletion, and evaluation concepts |
| [`project8/debug_log/project8_debug_log.md`](project8/debug_log/project8_debug_log.md) | Cell-specific retrieval-debug history |
| [`project8/output/`](project8/output/) | Measured API QA/lifecycle results and report plus the completed independent A100 comparison under `output/gpu/` |

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
- Added normalized `all-MiniLM-L6-v2` embeddings for top-five schema selection in
  the A100 path, reducing irrelevant schema context before generation.
- Added deterministic BF16 `Qwen2.5-Coder-7B-Instruct` generation with one shared
  model instance. The model proposes only a typed query plan; SQLGlot policy and
  read-only execution remain authoritative.
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
| Measured API evaluation | Local macOS CPU with isolated Python dependencies; API generation dominated the model work |
| Measured A100 comparison | One NVIDIA A100-SXM4-40GB; `Qwen/Qwen2.5-Coder-7B-Instruct` in BF16 plus `sentence-transformers/all-MiniLM-L6-v2`, deterministic decoding, 500 new-token limit, schema top-k 5 |
| GPU execution status | Complete; all 40 held-out questions ran through baseline and governed paths, with artifacts isolated under `project5/output/gpu/` |
| Measured evaluation time | 290.70 seconds for the final 40-case API comparison; report generation and validation completed afterward |
| Measured A100 time | 346.93 seconds for the 40-case paired local-model comparison |
| Final verification | API environment: 10 tests in 0.91 seconds; A100 notebook `P05-C07`: 10 tests in 10.53 seconds |
| Dataset | 50 synthetic questions: 10 development and 40 held-out; checksum `8d861b67fb259c81ab830446d9f75ccd325942088c8b49413dc3c64e7144e11a` |
| Query limits | Two repair attempts, 100 result rows, read-only local DuckDB, authorized region `NA` |
| API planner | `gpt-5.6-luna`, low reasoning effort, strict Pydantic query plans |
| API limits | 180 calls, 500 output tokens per call, two retries, USD 6.00 estimated cost |
| Measured API use | 54 calls, 15,214 input tokens, 15,521 output tokens, USD 0.108340 estimated cost |
| Measured A100 use | 91 local calls, 22,560 input tokens, 11,538 output tokens, USD 0 API cost |

### Results and Judgment

| Metric | One-shot | Governed | Judgment |
| --- | ---: | ---: | --- |
| Execution accuracy | 59.26% | 100.00% | Policy plus repair recovered executable plans for every safe case |
| Result-hash accuracy | 14.81% | 37.04% | Governance substantially improved semantic execution accuracy, but absolute model quality remains limited |
| Unsafe-query block rate | 15.38% | 38.46% | The governed policy stopped more unsafe cases than one-shot failures alone |
| PII leak rate | 2.50% | 0.00% | AST and column policy removed the measured one-shot PII exposure |
| Repair success | 80.00% | 100.00% | Bounded feedback recovered every included repair case |
| Median execution latency | 13.81 ms | 12.81 ms | This timer covers local execution after the shared frozen plan, not API generation |

The completed A100 comparison produced a deliberately separate result:

| A100 metric | One-shot | Governed | Judgment |
| --- | ---: | ---: | --- |
| Execution accuracy | 11.11% | 11.11% | The 7B local planner frequently emitted invalid or unusable plans |
| Result-hash accuracy | 0.00% | 0.00% | Neither path produced a semantically exact held-out result |
| Unsafe-query block rate | 100.00% | 84.62% | The local governed path exposed a policy/repair coverage gap that must be fixed before deployment |
| PII leak rate | 0.00% | 0.00% | No measured local output exposed protected columns |
| Repair success | 0.00% | 0.00% | Bounded feedback did not recover a local-model failure |
| Median latency | 14.97 ms | 6,764.51 ms | Governed generation and repair added substantial local inference latency |

The measured result supports the safety and repair design, but not a claim of high
general text-to-SQL accuracy. Result hashes remain strict and expose many
semantically wrong executable queries. Repeated model runs, stronger schema
retrieval, and calibrated abstention should be prioritized before expanding the
database or claim surface.

The A100 result is an additional controlled comparison, not a replacement for the
measured API evidence. Reusing the same benchmark and governance stack shows that
the smaller local planner is currently the limiting component. The zero PII leak
rate is encouraging, but zero result-hash accuracy, failed repair, lower unsafe
blocking, and high latency rule out presenting this configuration as an
improvement.

### Evaluation Figures

The measured run generated `project5/output/project5_report_assets/quality_repair_safety.png`,
`project5/output/project5_report_assets/procedure_diagram.svg`, and
`project5/output/project5_report.pdf`. The one-page PDF was rendered and checked
for readable bars, table values, interpretation text, margins, and footer.
The completed A100 run wrote its summary, traces, charts, and rendered report under
`project5/output/gpu/`, keeping the measured API artifacts unchanged.

### Future Optimization

- Compare lexical, dense, and hybrid schema retrieval on held-out table/column
  recall, then tune top-k only on the development split.
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
repository-relative. The A100 extension changed only `P05-C01`, `P05-C02`,
`P05-C06`, `P05-C08`, `P05-C09`, and `P05-C10`; the user-modified data cell
`P05-C03` and its source were preserved. The final A100 pass changed no notebook
source cells and populated outputs for `P05-C01` through `P05-C10`; the clean run
used 39.08 GiB of initially free GPU memory and passed all ten tests. The full history is in
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
- Added a shared BF16 `Qwen2.5-Coder-7B-Instruct` backend that proposes the same
  typed unified-diff contract for both one-shot and iterative modes. Patch policy,
  hidden tests, acceptance, and rollback stay model-independent.

### Compute Resources, Time, and Key Settings

| Item | Configuration |
| --- | --- |
| Measured API evaluation | Local macOS CPU with subprocess-isolated tests; API generation supplied patch proposals |
| Measured A100 comparison | One NVIDIA A100-SXM4-40GB; `Qwen/Qwen2.5-Coder-7B-Instruct` in BF16, deterministic decoding, one shared model instance, and a 900 new-token limit |
| GPU execution status | Complete; all eight held-out defects ran through both modes, with artifacts isolated under `project6/output/gpu/` |
| Measured evaluation time | 138.92 seconds for both repair modes over 8 held-out defects; report generation and validation completed afterward |
| Measured A100 time | 327.89 seconds of summed per-case latency; medians were 10.50 seconds one-shot and 23.33 seconds repair-loop |
| Final verification | API environment: 9 tests in 4.22 seconds; A100 notebook `P06-C07`: 9 tests in 2.69 seconds |
| Dataset | Twelve QuixBugs Python cases: four development and eight held-out, pinned to one commit |
| Repair limits | Three attempts, 30 changed lines, one declared source file, 20-second tests, 12,000 output characters |
| API planner | `gpt-5.6-sol`, medium reasoning effort, strict Pydantic patch proposals |
| API limits | 220 calls, 900 output tokens per call, two retries, USD 8.00 estimated cost |
| Measured API use | 18 calls, 22,988 input tokens, 4,324 output tokens, USD 0.244660 estimated cost |
| Measured A100 use | 32 local calls, 27,588 input tokens, 8,326 output tokens, USD 0 API cost |

### Results and Judgment

| Metric | One-shot | Repair loop | Judgment |
| --- | ---: | ---: | --- |
| Verified repair rate | 75.00% | 87.50% | Iterative public-test feedback recovered one additional defect |
| Hidden-test pass rate | 75.00% | 87.50% | The accepted repair improvement survived generated regression checks |
| Overfit detected | 0.00% | 0.00% | No public-only candidate reached the hidden-test rejection state in this run |
| Rollback success | 100.00% | 100.00% | Every rejected attempt restored the exact source snapshot |
| Mean changed lines | 2.0 | 2.0 | The loop improved success without increasing average patch size |
| Median latency | 6.57 s | 8.27 s | Additional feedback added modest end-to-end latency on this compact suite |

The completed A100 comparison held the same patch policy and tests constant:

| A100 metric | One-shot | Repair loop | Judgment |
| --- | ---: | ---: | --- |
| Verified repair rate | 0.00% | 0.00% | The 7B local planner did not produce an acceptable complete diff |
| Hidden-test pass rate | 0.00% | 0.00% | No local candidate reached verified acceptance |
| Overfit detected | 0.00% | 0.00% | Failures occurred before a public-only patch could be accepted |
| Rollback success | 100.00% | 100.00% | Every rejected local proposal restored the exact source snapshot |
| Mean changed lines | 6.625 | 4.875 | Feedback reduced average patch size but not repair success |
| Median latency | 10.50 s | 23.33 s | The iterative loop more than doubled local latency without a successful repair |

The measured comparison favors the bounded loop on this small pinned suite, while
the result remains too small for a universal coding-agent claim. The hidden tests
are generated and compact, and subprocess controls are not a hardened sandbox.
Future runs should add mutation strength, more repositories, and uncertainty over
multiple model samples.

The A100 run holds the repository map, prompts, diff budget, public/hidden tests,
and rollback rules constant while changing the proposal backend. Its zero repair
rate demonstrates that this local model and prompt need substantial improvement;
the unchanged 100% rollback result also demonstrates that planner failure did not
weaken the acceptance boundary.

### Evaluation Figures

The measured run generated `project6/output/project6_report_assets/repair_quality.png`,
`project6/output/project6_report_assets/procedure_diagram.svg`, case results,
trajectories, representative samples, and `project6/output/project6_report.pdf`.
The one-page PDF was rendered and checked for chart/table readability and margins.
The completed A100 run wrote trajectories, summary, charts, and a rendered report
under `project6/output/gpu/` without replacing the measured API evidence.

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
the log. The completed A100 pass changed source only in `P06-C01`, `P06-C02`, and
`P06-C07`; `P06-C03` was restored to its prior source while retaining successful
output. A stale prior model first forced offload, so a clean restart released the
GPU and exposed 39.08 GiB before the validated run. See
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
| Measured evaluation time | 72.47 seconds for 32 structured reviews plus both deterministic gateway modes |
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
- Added normalized `all-MiniLM-L6-v2` event embeddings. The A100 path ranks
  episodic memory by dense similarity and uses a fixed 0.70 dense, 0.25 lexical,
  and 0.05 recency fusion for hybrid retrieval.
- Added conflict abstention, consolidation, physical removal from retrievable
  stores, and post-deletion checks.
- Added a cached Responses API answerer so the three-system, 80-question comparison
  fits within 240 calls and reruns do not repeat completed model requests.
- Added a cached BF16 `Qwen2.5-7B-Instruct` grounded answerer with deterministic
  decoding, preserving the same evidence IDs, lifecycle rules, and QA metrics.

### Compute Resources, Time, and Key Settings

| Item | Configuration |
| --- | --- |
| Measured API evaluation | Local macOS CPU; API latency dominated the completed run |
| Measured A100 comparison | One NVIDIA A100-SXM4-40GB; `Qwen/Qwen2.5-7B-Instruct` in BF16 plus `sentence-transformers/all-MiniLM-L6-v2`, deterministic decoding, and a 300 new-token limit |
| Dense hybrid settings | Normalized cosine similarity with fusion weights 0.70 dense, 0.25 lexical, and 0.05 recency; answer cache keyed by question and evidence context |
| GPU execution status | Complete; all 240 system-question pairs were evaluated, with artifacts isolated under `project8/output/gpu/` |
| Measured evaluation time | 424.10 seconds to populate 240 API answers; a fully cached reevaluation completed in 0.56 seconds before report generation |
| Measured A100 time | Approximately 4-5 minutes for the successful cached-resume run, including model loading, 150 new answers, report generation, and validation |
| Final verification | API environment: 12 tests in 0.07 seconds; A100 notebook `P08-C07`: 12 tests in 0.53 seconds |
| Dataset | LoCoMo samples 0 and 1, 40 QA per sample, plus deterministic lifecycle fixtures |
| Memory settings | Working window 6 events, episodic top-k 5, SQLite facts/events/tombstones, evidence-cited retrieval |
| API answerer | `gpt-5.6-luna`, low reasoning effort, strict grounded-answer schema and per-context cache |
| API limits | 300 calls, 500 output tokens per call, two retries, USD 8.00 estimated cost |
| Measured API use | 240 calls, 109,387 input tokens, 17,407 output tokens, USD 0.213829 estimated cost |
| Measured A100 use | 150 new local calls plus 90 cache hits, 69,462 input tokens, 6,426 output tokens, USD 0 API cost |

### Results and Judgment

| Metric | Recent window | Episodic | Hybrid |
| --- | ---: | ---: | ---: |
| LoCoMo exact match | 0.00% | 0.00% | 0.00% |
| LoCoMo mean token F1 | 3.20% | 11.50% | 9.41% |
| LoCoMo evidence recall | 1.25% | 22.29% | 19.17% |
| LoCoMo mean context tokens | 90.5 | 71.3 | 69.6 |
| Lifecycle exact match | 75.00% | 75.00% | 100.00% |

The completed dense/local A100 comparison produced:

| A100 metric | Recent window | Episodic | Hybrid |
| --- | ---: | ---: | ---: |
| LoCoMo exact match | 0.00% | 0.00% | 0.00% |
| LoCoMo mean token F1 | 0.64% | 10.00% | 6.63% |
| LoCoMo evidence recall | 1.25% | 15.00% | 13.13% |
| LoCoMo mean context tokens | 90.5 | 91.1 | 87.2 |
| Lifecycle exact match | 75.00% | 75.00% | 100.00% |

Episodic retrieval is the strongest current LoCoMo baseline, while the hybrid
recency bonus slightly lowers token F1 and evidence recall despite using the least
context. Strict exact match exposes substantial answer-quality headroom. Separately,
the lifecycle fixtures retain 100% hybrid exact match and 100% deletion compliance
across events, derived facts, retrieval, and tombstones. The fixed two-conversation
subset is compact and does not establish general memory-agent quality.

The A100 comparison changes both retrieval representation and answer backend while
retaining the same LoCoMo selection, memory lifecycle, context accounting, and
metrics. Dense episodic retrieval again led the local alternatives, but its 10.0%
token F1 and 15.0% evidence recall remained below the API lexical episodic result
of 11.5% and 22.3%. Both runs preserved 100% deletion compliance, so the measured
gap is in retrieval/answer quality rather than lifecycle enforcement.

### Evaluation Figures

The measured run generated `project8/output/project8_report_assets/quality_context_tradeoff.png`,
`project8/output/project8_report_assets/procedure_diagram.svg`, 240-answer traces,
representative samples, and `project8/output/project8_report.pdf`. The final report
uses token F1 and evidence recall rather than an all-zero exact-match chart; its
rendered page was checked for legibility, spacing, deletion text, limits, and footer.
The completed A100 run wrote QA traces, summary, charts, and a rendered report
under `project8/output/gpu/`, preserving the 240-call API evaluation as the
baseline. The local report was also checked for accurate dense-retrieval wording,
legibility, spacing, and footer placement.

### Future Optimization

- Compare dense-only, lexical-only, reciprocal-rank, and weighted hybrid fusion
  under fixed context budgets, tuning weights only on development conversations.
- Add learned memory extraction with calibrated confidence and provenance.
- Evaluate temporal interval queries, entity aliases, and multi-fact reasoning.
- Test cryptographic deletion receipts and provider/index deletion semantics.
- Tune retrieval only on a development split and report confidence intervals over
  conversations and QA categories.

### Debug Log Summary

The measured run completed all calls before `P08-C10` found a token-shaped string
inside the raw upstream clone. Validation now excludes only that third-party clone
while continuing to scan the selected subset and generated artifacts. Absolute
notebook paths were sanitized, and `P08-C10` was rerun without model calls. The
A100 completion changed notebook source only in `P08-C01`, `P08-C02`, and
`P08-C07`; the pinned LoCoMo preparation cell `P08-C03` remained unchanged. The
VS Code kernel picker was bypassed through the authenticated Colab terminal after
the 10-minute debug limit. The first inference run returned explanatory text in
the boolean `abstained` field, so a strict normalization layer and regression test
were added; 12 tests then passed and the 240-answer run completed. See
[`project8/debug_log/project8_debug_log.md`](project8/debug_log/project8_debug_log.md).

## Documentation Maintenance

The root [`README.md`](README.md) is a concise repository and portfolio summary.
Whenever its project-summary content changes, update the corresponding project
entry in this file in the same commit. Detailed methods, resources, settings,
results, judgments, figures, future optimization, and debug information belong
here rather than in the root README.
