# AI Agentic Attemptings

Compact, evaluation-driven AI agent engineering projects spanning workflow
reliability, governed data access, coding agents, protocol
security, and long-term memory.

> **Version:** ver 0.19: verified A100 SQL and memory comparisons<br>
> **Updated:** 2026-11-18 05:25 EST

## Upgrade Status

The new P0 follow-up adds hash-locked CPU/API notebook environments, a patched and
retested Docker executor, and Project 7's authenticated Streamable HTTP boundary.
The final CPU suite passes 144 tests on macOS and offline Linux ARM64. Request
cancellation/revocation controls and shared run manifests are tested. The
patched inference environment ran Project 5's SQL model comparison and Project
8's six-case LongMemEval pilot on one A100.
See [setup/security notes](SECURITY_UPGRADE.md) and
[detailed status](projects_info.md#p0-security-follow-up). No new model-quality
result is inferred from these control tests.

The [prioritized upgrade checklist](upgrade_plan.md) now tracks enforced SQL data
boundaries, isolated code-execution requirements, real MCP transport, durable
recovery, consent/provenance, and persistent memory deletion. New CPU control runs
are stored separately under each project's `output/runs/upgrade-v1/` directory.
New API runs are recorded for Projects 4, 6, and 7, including real Docker execution
and a model-to-MCP tool loop. Project 6's repair loop did not outperform one-shot
in the new run; small synthetic security tests do not establish production safety.
SQL planning failures and memory cache hits have separate accounting. The v2
Project 5 candidate improved governed value matches from 2/27 to 13/27. Project
8's current LongMemEval pilot measured update and abstention behavior over six
cases using a shared answerer. The full official grading and Project 6's
official SWE-bench scoring remain open.
See [projects_info.md](projects_info.md#upgrade-evidence) for
verified evidence, execution requirements, and remaining gates.

## Historical Portfolio Summary

The following values describe the pre-upgrade experiments. Evaluation limitations
and revised interpretations are documented in [projects_info.md](projects_info.md#upgrade-evidence).
In particular, the old code-repair result is not a blind hidden-test estimate,
and the old gateway attack score measures included fixtures, not adaptive attacks.

| Project | Status | Summary |
| --- | --- | --- |
| 4. Durable Incident-Response Agent | Measured API evaluation complete | Across 32 paired observations, the durable workflow preserved task quality while eliminating duplicate effects (50% to 0%) and unsafe allows (80% to 0%); all executed crash trials recovered, with higher mean latency (11.4 ms to 112.0 ms) |
| 5. Governed Text-to-SQL Analyst | API and A100 evaluations complete | API governance raised result-hash accuracy from 14.8% to 37.0% and removed a 2.5% PII leak; the A100 Qwen comparison retained 0% PII leakage but reached 0% result-hash accuracy and 84.6% unsafe blocking, so the API result remains primary |
| 6. Test-Driven Code-Repair Agent | API and A100 evaluations complete | The API repair loop raised verified and hidden-test pass rates from 75.0% to 87.5%; the A100 Qwen run produced no verified repair in either mode but preserved 100% rollback, exposing a proposal-quality limit without weakening fail-closed controls |
| 7. Secure Interoperable Agent Gateway | Measured API evaluation complete | Defenses reduced attack success from 85.2% to 0% with 100% benign success and trace completeness; non-authoritative policy-review accuracy was 84.4% |
| 8. Long-Term Memory Agent | API and A100 evaluations complete | API lexical episodic retrieval reached 11.5% token F1 and 22.3% evidence recall; A100 dense episodic retrieval reached 10.0% and 15.0%, respectively, while both runs preserved 100% deletion compliance |

See [`projects_info.md`](projects_info.md) for project files, goals, methods,
resources, settings, preflight results, judgments, future optimization, and debug
summaries. Detailed project information must be updated there whenever this README
summary changes.

## Project Ideas

See [`projects_ideas.md`](projects_ideas.md) for the ranked project slate,
implementation boundaries, controlled comparisons, metrics, artifact expectations,
and primary technical references.
