# Upgrade Debug Log

> **Updated:** 2026-11-17 02:35 EST<br>
> **Scope:** Prioritized upgrades and separately versioned measured runs; no push.

## Final Round Status

- Projects 5/8 completed the resumed GPU queue; the observed suite exit was 0
  and A100 utilization returned to 0%. Runtime evidence was exported and imported
  with hash, path, size, and credential-pattern checks. Earlier failed runs remain.
- Project 8 finished at 07:10:26 UTC in 401.02 seconds. The lock screen prevented
  observing it promptly, not remote execution. After the UI became available,
  only read-only progress/inventory and safe export cells were executed.
- Same-answerer lexical/dense comparison: 50 questions, 250 fresh calls, 50 cached
  recent-window controls. Lexical episodic/hybrid each produced one `ValueError`
  on the same question; both failures remain in the scores. No retry or model
  tuning used these held-out outcomes.
- Dense episodic F1 0.1565 versus lexical 0.1159; a frozen-output, 2,000-resample
  paired analysis gives delta CI [-0.0330, 0.1206]. It is conditional on the two
  selected conversations, not a general performance guarantee. Recent-window
  cache latency and authored deletion compliance are not QA improvements.
- Added `project8/tools/analyze_saved_ablation.py` and three regression tests;
  included the helper in future GPU bundles because its tests import it. No
  additional project notebook cell was edited for this offline analysis.
- Latest CPU total: 107 passed; all notebook syntax checks pass. Two Docker-only
  tests skip in the CPU suite and passed separately in real containers. Project 8
  has 26 local tests; its executed Colab snapshot ran the then-current 23.
- README, detailed project information, and checklist now report completed runs
  without claiming all remaining research/deployment work is finished. Historical
  figures/PDFs, source manifests, and raw model results were not overwritten.

## Issue History

| Issue | Attempts / Diagnosis | Resolution / Status |
| --- | --- | --- |
| uv could not use the global cache | One failed cache access under sandbox permissions | Created the isolated environment and cache inside the jobs workspace. No global environment changed. |
| PyPI download failed in sandbox | Initial command exhausted its internal network retries | Requested network approval; approved download succeeded with automatic HTTP retries disabled. |
| Docker executable missing | Discovery check found no Docker runtime | User authorized installation; official Docker Desktop 4.99.0 installed, signature verified outside the restricted signing subsystem, engine 29.9.3 confirmed running. User completed sign-in. |
| Docker image build could not find credential helper | First build failed before image download | Include Docker's resource bin directory in this process's PATH; second build succeeded. No shell profile changed. |
| Container network test assumed only loopback appears in sysfs | First real-container test failed on down tunnel devices | Assert absence of non-loopback routes and failed external connection instead; retain --network=none. |
| Docker Desktop cached a removed/recreated pytest bind path | One subsequent run could not mount the reused test directory | Use a fresh test directory; both real-container integration tests pass. No boundary was weakened. |
| MCP tool schemas were rejected by strict OpenAI function calling | First model-backed attempt returned BadRequestError before tool execution | MCP omitted additionalProperties. Add false to a copied, reviewed scalar schema; reject optionality/type drift. New regression test and subsequent model run pass. |
| Reviewer unit test assumed the old token prices | One full-suite failure after verified price update | Update expected cost from the explicit 0.20/1.20 USD-per-million settings; historical costs stay unchanged. |
| Model-generated unified diffs were malformed | Project 6 retained three failed case/arm outcomes after bounded attempts | User approved development-only structured-edit testing. Four development bugs: structured edits 4/4 in four calls, unified diffs 2/4 in eight calls. Saved final-test scores unchanged. |
| Per-planner API caps could reset between repair cases | Code review during edit-interface work | Add a shared, lock-protected experiment budget with conservative reservations for failed calls; notebook cell 9 uses the shared budget. |
| Approval pauses were classified as timing errors | First new load-test assertion showed GraphInterrupt subclasses Exception | Classify GraphInterrupt explicitly as interrupted; second focused suite passed. Preserve the diagnostic load run and save a fresh corrected run. |
| Pytest temporary parent absent | One test invocation failed before fixtures could run | Created a workspace-local temporary parent and reran. |
| MCP SQLite thread ownership | First real transport run used a connection from the wrong thread | Open/close a connection inside each SDK worker-thread invocation. |
| MCP response had no structured content | One remaining failure after thread fix | Added explicit Pydantic response models and structured-output annotations; real transport test then passed. |
| SQL access trusted model metadata | Audit finding, not a failed test | Execute both systems against physical tenant-filtered, PII-free snapshots; prevent external I/O and lock settings. |
| Hidden test feedback guided code repair | Audit finding | Select using public tests, run the final hidden evaluation once in a separate evaluation workspace, and never feed it back to the planner. |
| Duplicate execution race | Audit finding | Recheck idempotency under the same SQLite write transaction; bind ledger entries to action parameters. Concurrent-delivery test passes. |
| Deleted memory could return | Audit finding | Consult persistent tombstones during ingestion; make repeated event ingestion idempotent; invalidate dependent answer caches and in-memory embeddings. |
| Final evaluator error could reopen patch selection | Additional review | Stop after candidate selection even if the evaluator infrastructure fails. One new test exposed a missing required result field; fixed on the next attempt. |
| Repair destination could contain the source | Additional review | Reject equal, nested, and ancestor destinations before removing any workspace. Regression test preserves a sentinel source file. |
| Two Project 8 retrievers could exceed the existing call cap | Additional review | Bound the shared subset before generation, enforce failed-attempt accounting, and measure per-arm usage deltas. |
| Report assumed episodic retrieval wins and expected token fields | Additional review | Derive interpretation from actual scores, handle lifecycle summaries, and use context words. Unit-tested report inputs; no historical report regenerated. |
| Cache-format invalidation could discard deletion markers | Additional review | Preserve tombstones independently of answer-entry compatibility; regression test passes. |
| SQL initial planning latency was omitted | Additional review | Charge the same measured frozen-plan latency to both end-to-end arms, while retaining the legacy post-plan metric. |
| A failed SQL planner could look like a successful safety block | Additional review | Keep model/parse errors distinct from policy rejection and abstention; count failed generations against the call cap. |
| Cached memory answers distorted latency interpretation | Additional review | Report cached and fresh latency separately and record usage/errors per case. Neighbor expansion is bounded and tested. |
| CrewAI and Project 7 require incompatible MCP major versions | Dependency inspection | Use separate isolated environments. Do not downgrade the tested MCP 2.3.0 service to install CrewAI. |
| GPU control became unavailable when the Mac locked | One UI observation in the companion runtime | Asked the user to unlock; do not restart the running Project 1 training or claim pending evaluations completed. |

## Verification

- Project 5: 22 tests passed; model-backed SQL evaluation not rerun.
- Project 6: 19 core tests and two separately executed real-container integration checks passed.
- Project 7: 14 tests cover real MCP client/server discovery, strict API schema conversion, malformed
  argument rejection, operator-approved synthetic effect, and restart deduplication.
- Project 4: 21 tests passed, including eight concurrent deliveries, parameter-bound
  approval rejection, whole-workflow process restart, and separate action-process reconciliation.
  Its expanded focused suite now passes 23 tests, including node timing and concurrent load.
- Project 8: 23 tests passed, including deletion persistence, event idempotency,
  consent/provenance, cache fingerprints, neighboring context, and derived-store invalidation.
- Full regression rerun: 101 passed, two Docker-only skips, all notebook syntax
  checks passed. The two skipped checks were executed and passed separately with Docker.

## New Measured Runs

- Project 4: 64 OpenAI calls; 16 incidents x two repetitions; root-cause accuracy
  100%, remediation accuracy 65.625%. Durable observed crash recovery 5/5 and no
  duplicate effects, versus baseline 16/16 and 50% duplicate-effect cases. Crash
  denominators differ because authorization/evidence checks stop some executions.
  Fourteen durable cases stopped at evidence verification and seven were rejected
  by the simulated operator. Total run 170.34 seconds; estimated token cost $0.025706.
- Project 6: real Docker, eight test defects per arm, one final hidden evaluation
  per selected candidate. One-shot 7/8 verified; repair loop 6/8. All failures were
  malformed patches; rollback 100%. Twenty API calls, estimated $0.207024.
  The loop did not improve accuracy in this small run.
- Project 7: real model-to-MCP function calls across two benign cases and six
  synthetic attack cases, with one response-conditioned heuristic escalation per
  attack. Forty-two API calls; no observed canary leakage or unauthorized effects,
  both benign tasks succeeded. This small set is not general injection robustness.
  Estimated token cost $0.005379; first schema-rejected run is retained separately.
- Project 1 training continues on the A100; Projects 5/8 are queued behind the
  training and the earlier GPU evaluations. Credentials remained in memory, not
  in either repository or MCP/container environments.

## Notebook Changes So Far

- Project 5: cells 1, 7, 9, 10, 11; IDs `P05-C00`, `P05-C06`, `P05-C08`,
  `P05-C09`, `P05-C10`.
- Project 6: cells 1, 9, 10, 11; IDs `P06-C00`, `P06-C08`, `P06-C09`, `P06-C10`.
  Added cells 12-13 (`P06-C11`, `P06-C12`) for the opt-in development-only comparison.
- Project 4: cells 1, 8, 9, 10, 11; IDs `P04-C00`, `P04-C07` through `P04-C10`.
  Cell 8 now includes the opt-in, CPU-only local load test.
- Project 7: cells 1, 7, 9, 10, 11; IDs `P07-C00`, `P07-C06`, `P07-C08` through `P07-C10`.
- Project 8: cells 1, 7, 9, 10, 11; IDs `P08-C00`, `P08-C06`, `P08-C08` through `P08-C10`.
- Edited code-cell outputs were cleared to avoid showing old results as new ones.
  Untouched cells and saved historical result/report files are preserved.
# 2026-11-17: GPU Integration And SQL Metric Follow-Up

Final local rerun after value-scoring changes: **104 passed**, with two Docker-only
tests skipped in the CPU suite (previously executed successfully in Docker).
All five notebooks compile. Project 1's protected dataset cell hash is unchanged.

- First GPU suite `20261117T061830369288Z`: Project 5's dataset subprocess lacked
  `PYTHONPATH`; Project 8's report-scorer test helper was omitted from the bundle.
  Preserved the failed manifests/notebooks. Runner-only fixes set the project
  `src` path for child processes and package the missing helper. Each issue had
  one failed execution; no project notebook code was overwritten for these fixes.
- Resumed suite `20261117T064159242835Z`: Project 5 passed all 22 then-current
  tests and finished its A100 comparison in 516.39 seconds including setup.
  Qwen2.5-Coder-7B made 84 calls; original exact-result-hash accuracy was 0% in
  both arms. Many failures were real nonexistent-column errors, but exact hashes
  also penalized harmless output aliases. Those scores are preserved.
- Added a separate final-evaluator value metric: ignore aliases but preserve
  column positions, duplicates, NULLs and requested ordering, with explicit tight
  numeric tolerance. Gold SQL is never supplied as planner feedback. Re-executed
  frozen successful SQL only inside the same restricted, no-external-I/O snapshots;
  no new model calls. Baseline matched 5/27 answerable cases and governed matched
  2/27; neither is production-ready. No PII was observed in either arm.
- Value-rescoring artifacts are in `value_scoring_v2/` under the completed GPU run;
  the regenerated benchmark hash exactly matched the saved source benchmark.
  Three additional regression tests cover aliases, NULLs, duplicates, ordering,
  numeric matching and shape mismatches. All 25 Project 5 tests pass.
- Notebook change in this follow-up: **Project 5 cell 1 `P05-C00`** documents the
  metric distinction; its builder matches. The imported evaluator performs the
  new final scoring automatically. Project 8 passed 23 Colab tests and entered
  its local-model ablation; final scores were still pending at this log entry.
