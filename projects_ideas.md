# Five Compact AI Agent Engineering Project Ideas

> **Status:** Planning document; no performance result is claimed yet.  
> **Updated:** 2026-08-02 EDT  
> **Target:** M.S. Computer Engineering graduate applying for AI Agent Engineer roles  
> **Execution limit:** Each completed project must run from a fresh Colab runtime in less than 6 hours.

## Selection Strategy

The existing portfolio already demonstrates LLM fine-tuning, advanced RAG, typed
tools, MCP-style contracts, safety gates, and multi-agent orchestration. These five
ideas add different skills instead of producing larger versions of the same work.

| Project | Primary knowledge area | Main engineering signal | Estimated Colab run |
| --- | --- | --- | ---: |
| 4. Durable Incident-Response Agent | Stateful workflow reliability | Checkpointing, HITL, idempotency, recovery, observability | 45-90 minutes |
| 5. Governed Text-to-SQL Analyst | Data agents and access control | Schema grounding, AST validation, self-repair, PII protection | 60-120 minutes |
| 6. Test-Driven Code-Repair Agent | Software-engineering agents | Repository navigation, constrained patches, tests, rollback | 90-180 minutes |
| 7. Secure Interoperable Agent Gateway | Agent protocols and security | MCP, A2A, authorization, prompt-injection defense | 60-120 minutes |
| 8. Long-Term Memory Agent | Stateful personalization | Episodic/semantic memory, temporal reasoning, deletion | 90-180 minutes |

Together, they cover workflow orchestration, databases, software engineering,
security, protocols, distributed tracing, evaluation, and memory. If only two are
built initially, Projects 4 and 5 provide the strongest signal for the least
execution time.

## Shared Project Contract

The exact folder layout does not need to copy the previous repository. The number
and purpose of the artifacts should remain similar so each project tells a complete
story.

### Functional Artifact Bundle Per Project

Each finished project should produce approximately the following:

1. **One executed notebook:** setup, data, baseline, advanced agent, reliability
   tests, evaluation, error analysis, and artifact export.
2. **One background Markdown file:** concepts, architecture, important methods,
   formulas where useful, alternatives, and limitations.
3. **One report-generation script:** rebuild charts and the PDF from saved result
   files rather than hard-coded values.
4. **One final report PDF:** problem, workflow, experiment controls, results,
   representative cases, limitations, and resume interpretation.
5. **One final-summary JSON:** configuration, compute, runtime, dataset size, and
   final metrics.
6. **One representative-samples JSON:** successful, failed, unsafe, and recovered
   examples.
7. **One trace JSONL:** model calls, tool calls, decisions, errors, timings, token
   use, and estimated cost with secrets redacted.
8. **Two to four report assets:** procedure diagram, quality comparison, and a
   latency/cost or failure-analysis figure.

The repository may also keep one shared executable guideline PDF and one shared
debug log for all projects. File names and subfolders can be changed as long as
the same functions are covered.

### Standard Notebook Flow

Use stable cell IDs so future changes can be reported precisely.

1. `PXX-C00`: scope, hypotheses, baseline, success criteria, and non-goals.
2. `PXX-C01`: runtime inspection and pinned dependency installation.
3. `PXX-C02`: secret loading, configuration, call/token/cost limits, and offline mode.
4. `PXX-C03`: download-once data preparation with checksum and persistent cache.
5. `PXX-C04`: deterministic development and held-out test splits.
6. `PXX-C05`: simplest credible baseline.
7. `PXX-C06`: advanced agent implementation.
8. `PXX-C07`: malformed-output, timeout, duplicate-request, unsafe-request, and
   dependency-failure tests.
9. `PXX-C08`: paired evaluation of quality, safety, trajectory, latency, and cost.
10. `PXX-C09`: representative error analysis and limitations.
11. `PXX-C10`: export evidence and build the report inputs.

Every debugging entry should identify the exact notebook cell changed, symptom,
root cause, fix, and verification result.

### Colab Controls

- Prefer CPU or L4. An A100 is unnecessary for most of these projects.
- Pin a minimal dependency set and run an import smoke test immediately after
  installation to avoid Colab package conflicts.
- Provide an API-backed evaluation path and a deterministic local mock path.
- Define `MAX_MODEL_CALLS`, `MAX_OUTPUT_TOKENS`, `MAX_RETRIES`, and
  `MAX_ESTIMATED_COST_USD` before the first model call.
- Keep the held-out evaluation between 20 and 100 cases depending on API cost.
- Cache datasets, model outputs, embeddings, and evaluator outputs independently.
- Use deterministic checks for safety and correctness whenever possible. Use an
  LLM judge only for qualities that cannot be measured mechanically.
- Never place API keys, personal data, local absolute paths, or raw environment
  variables in notebook outputs, traces, reports, or Git history.
- Do not choose an improvement percentage in advance. Generate the resume bullet
  only after the controlled evaluation is complete.

## Project 4: Durable Incident-Response Agent

**Keywords:** LangGraph, durable execution, HITL, idempotency, fault injection,
OpenTelemetry, saga compensation

### Goal

Build an incident commander that diagnoses simulated microservice failures,
proposes a remediation, pauses for human approval before a consequential action,
survives an injected process crash, and resumes without repeating the action.

### Knowledge and Skills Demonstrated

- Stateful graph orchestration and explicit workflow state.
- Human-in-the-loop interruption and resumption.
- Checkpointing, idempotency, retry, timeout, and compensation.
- Logs, metrics, traces, correlation IDs, and failure injection.
- Reliability evaluation beyond final-answer quality.

This project makes strong use of a CE and systems background. It shows that an
agent is a recoverable distributed workflow rather than only an LLM prompt loop.

### Compact Dataset

- Generate 24 deterministic incidents across four mock services.
- Each case contains JSON logs, metrics, trace spans, a dependency graph, the gold
  root cause, an allowed remediation, and an escalation condition.
- Tools only simulate actions such as restart, rollback, scale, and open-ticket.
  The notebook must not connect to a real cloud account.

### Advanced Methods and Functions

- LangGraph `StateGraph` with diagnose, verify, plan, approve, execute, validate,
  compensate, and close nodes.
- SQLite-backed checkpointing with persistent thread IDs.
- Dynamic `interrupt()` and `Command(resume=...)` approval flow.
- Idempotency keys and an execution ledger preventing repeated side effects.
- Bounded retries, exponential backoff, timeouts, and deterministic fallback.
- Saga-style compensating action after an intentionally failed remediation.
- Pydantic schemas for state, evidence, action, approval, and result objects.
- OpenTelemetry spans propagated through model and tool calls.

### Controlled Comparison

Compare a stateless linear ReAct workflow with the durable approval-gated graph.
Use the same model, incidents, tools, and held-out cases. Inject a crash immediately
after approval in half of the recovery tests.

### Metrics

- Root-cause and remediation accuracy.
- Unsafe-action block rate and unnecessary-escalation rate.
- Crash-recovery success and duplicate-side-effect count.
- Expected versus observed tool trajectory.
- p50/p95 latency, retries, model/tool calls, tokens, and estimated cost.

### Workload Boundary

Use 50-120 model calls. Expected execution is 45-90 minutes on a Colab CPU. The
notebook must abort cleanly if it reaches the configured call or time budget.

### Suggested Special Artifacts

- Incident state-transition diagram.
- Recovery trace before and after the injected crash.
- Baseline-versus-durable reliability chart.
- Duplicate-side-effect and safety-block table.

### Resume Bullet Template

> Built a checkpointed incident-response agent with HITL approvals, idempotent
> tools, crash recovery, compensation, and OpenTelemetry traces; improved
> `[metric]` from `[baseline]` to `[advanced]` across `[N]` injected incidents
> while recording `[zero/X]` duplicate actions.

## Project 5: Governed Text-to-SQL Analyst

**Keywords:** text-to-SQL, schema linking, SQL AST validation, DuckDB,
self-correction, access control, PII protection

### Goal

Create a natural-language analytics agent that queries a local DuckDB database,
repairs invalid SQL, enforces read-only and row-level policies, masks sensitive
columns, and requests approval before exporting results.

### Knowledge and Skills Demonstrated

- Database schema understanding and semantic schema retrieval.
- Structured planning and constrained tool execution.
- SQL parsing, AST inspection, query limits, and executable evaluation.
- Data governance, PII masking, authorization, and approval flows.
- Bounded self-correction from parser and database errors.

### Compact Dataset

- Build a deterministic e-commerce database with 6-8 related tables.
- Create 50 natural-language questions with gold SQL and expected result hashes.
- Include ambiguous questions, invalid joins, PII requests, unauthorized-region
  requests, oversized exports, and prompt-injection text stored in table cells.

### Advanced Methods and Functions

- Embedding-based retrieval over table and column descriptions.
- Pydantic query plan containing intent, tables, joins, filters, and SQL.
- SQLGlot parsing and AST traversal rather than string-based SQL filtering.
- Allow `SELECT` only; reject DDL, DML, external I/O, unauthorized columns,
  cross-region access, and unbounded export.
- Run `EXPLAIN`, enforce row/time limits, and execute through a read-only DuckDB
  connection.
- Feed parser and execution errors into a maximum two-attempt repair loop.
- Mask PII and require human approval for result export.
- Save plans, AST decisions, repairs, result hashes, and policy outcomes.

### Controlled Comparison

Compare one-shot SQL generation with the governed schema-retrieval and repair
agent. Hold the model, prompt examples, database, decoding, and test questions
constant.

### Metrics

- Execution accuracy and result-hash accuracy.
- Schema-selection accuracy and first-attempt SQL validity.
- Repair success within two attempts.
- Unsafe-query block rate and benign-query false-block rate.
- PII leakage, latency, tool/model calls, tokens, and cost.

### Workload Boundary

Use 100-180 model calls. Expected execution is 60-120 minutes on a Colab CPU.
Database setup and deterministic policy tests should run without an API key.

### Suggested Special Artifacts

- Query lifecycle and policy-gate diagram.
- Execution-accuracy and repair-rate chart.
- Safety confusion matrix.
- Representative SQL repair and blocked-PII examples.

### Resume Bullet Template

> Engineered a governed text-to-SQL agent using schema retrieval, SQLGlot AST
> validation, read-only DuckDB execution, and bounded self-repair; achieved
> `[X]%` execution accuracy and blocked `[Y/Z]` unsafe requests on `[N]` held-out
> analytics tasks.

## Project 6: Test-Driven Code-Repair Agent

**Keywords:** coding agents, AST repository mapping, fault localization,
constrained diffs, pytest feedback, rollback, regression testing

### Goal

Build an agent that localizes a small Python bug, proposes a minimal patch, applies
it in an isolated repository copy, runs tests, diagnoses failures, and accepts or
rolls back the patch within a strict attempt budget.

### Knowledge and Skills Demonstrated

- Coding-agent architecture and repository navigation.
- Python AST analysis, test-trace interpretation, and fault localization.
- Constrained patch generation and secure subprocess execution.
- Test-driven iteration, rollback, and hidden regression testing.
- Agent trajectory and patch-quality evaluation.

### Compact Dataset

- Pin a commit of the Python portion of QuixBugs.
- Select 12-20 bugs that install and test reliably in Colab.
- Keep gold patches hidden from the agent and use them only for evaluation.
- Start every case from a clean repository copy so patches cannot contaminate
  later cases.

### Advanced Methods and Functions

- Repository map built from Python AST symbols, imports, docstrings, and tests.
- Fault localization from failing pytest traces and optional coverage data.
- Plan, inspect, patch, test, reflect, accept, and rollback state graph.
- Structured unified-diff output, path allowlist, `git apply --check`, and maximum
  changed-line budget.
- Subprocess test runner with time, memory, and output limits.
- Maximum three patch attempts with compact failure summaries.
- Public tests plus hidden generated tests to detect overfitting patches.
- Full diff, test, rollback, and trajectory logging.

### Controlled Comparison

Compare a one-shot patch generated from the issue, source file, and initial test
failure with the test-driven repair loop. Both systems use the same model and
starting repository.

### Metrics

- Pass@1 and verified repair rate within three attempts.
- Public-test and hidden-test pass rates.
- Regression and patch-overfitting rates.
- Patch validity, mean changed lines, and rollback correctness.
- Tool/model calls, latency, tokens, and cost per verified repair.

### Workload Boundary

Use 80-220 model calls. Expected execution is 90-180 minutes on a Colab CPU.
Stop after three attempts per bug and mark environment failures separately from
agent failures.

### Suggested Special Artifacts

- Repair state-machine diagram.
- Bug-by-bug repair matrix.
- Repair-rate and cost comparison.
- Representative successful patch, overfitting patch, and rollback trace.

### Resume Bullet Template

> Developed a test-driven Python repair agent with AST repository retrieval,
> constrained diffs, pytest feedback, rollback, and hidden regression tests;
> increased verified repair rate from `[A/B]` to `[C/B]` within a three-attempt
> budget.

## Project 7: Secure Interoperable Agent Gateway

**Keywords:** MCP, A2A, capability discovery, scoped authorization,
prompt-injection defense, taint tracking, distributed tracing

### Goal

Build two small agents that communicate through A2A and use shared MCP tools,
then measure defenses against indirect prompt injection, malicious tool metadata,
unauthorized delegation, duplicate delivery, and secret-exfiltration attempts.

### Knowledge and Skills Demonstrated

- Difference between agent-to-agent and agent-to-tool protocols.
- Capability discovery, typed delegation, task lifecycle, and schema versioning.
- Authentication, least privilege, provenance, and policy enforcement.
- Prompt-injection and tool-poisoning red-team evaluation.
- Correlated traces across multiple agents and tools.

### Compact Scenario and Dataset

- Implement a procurement requester agent and a compliance-review agent.
- Both may search a local policy corpus through MCP; only the reviewer may invoke
  the approval tool.
- Create 40 paired cases: benign requests, incomplete requests, unauthorized
  actions, malicious retrieved documents, poisoned tool descriptions, duplicate
  deliveries, and schema-invalid payloads.
- Use canary secrets and mock procurement records only.

### Advanced Methods and Functions

- A2A Agent Cards for capability discovery and typed task delegation.
- A2A task IDs, statuses, artifacts, cancellation, and idempotent retry.
- MCP tools with JSON Schema inputs/outputs and side-effect annotations.
- Agent-specific mock bearer scopes and deterministic authorization checks.
- Provenance labels and taint propagation from untrusted retrieved content.
- Tool-name and schema pinning to detect metadata poisoning.
- Policy engine before every tool call, handoff, and side effect.
- Secret-pattern detection, output redaction, and HITL approval for writes.
- Correlation IDs propagated across A2A messages, MCP tools, and OpenTelemetry.

### Controlled Comparison

Run the protocol workflow with defenses disabled and enabled on the same benign and
attack cases. Also report protocol overhead compared with direct local function
calls. The goal is security and interoperability, not lower latency.

### Metrics

- Agent discovery, delegation, and contract-validation success.
- Attack success, secret leakage, unauthorized tool calls, and unsafe writes.
- Benign task success and false-positive block rate.
- Retry recovery, duplicate-action count, and trace completeness.
- Added latency, serialization overhead, tokens, and cost.

### Workload Boundary

Use 80-160 model calls. Expected execution is 60-120 minutes on a Colab CPU.
Protocol, authorization, and failure-injection tests must also run deterministically
without a model.

### Suggested Special Artifacts

- A2A delegation plus MCP tool-call diagram.
- Threat model and trust-boundary diagram.
- Attack-versus-benign outcome matrix.
- Correlated trace showing delegation, rejection, retry, and approval.

### Resume Bullet Template

> Built a secure two-agent gateway using A2A delegation and MCP tools with scoped
> authorization, provenance tracking, idempotent retries, and prompt-injection
> defenses; reduced attack success from `[A]%` to `[B]%` while retaining `[C]%`
> benign task completion.

## Project 8: Long-Term Memory Agent

**Keywords:** long-term memory, episodic memory, semantic memory, temporal
retrieval, conflict resolution, memory consolidation, deletion compliance

### Goal

Build and evaluate a multi-session assistant that separates working, episodic,
semantic, and temporal memory while supporting corrections, conflicts, deletion,
and evidence-cited answers.

### Knowledge and Skills Demonstrated

- Agent state and memory lifecycle design.
- Embedding retrieval, structured storage, temporal reasoning, and consolidation.
- Conflict detection, supersession, deletion, and privacy verification.
- Multi-session evaluation and memory-cost analysis.
- Difference between context-window history and durable memory.

### Compact Dataset

- Use an audited subset of the public LoCoMo benchmark: two conversations and
  approximately 50-100 QA items.
- Preserve source turn IDs and timestamps for evidence evaluation.
- Add deterministic correction, conflicting-fact, and deletion cases because
  benchmark QA alone does not test the complete memory lifecycle.

### Advanced Methods and Functions

- Sliding-window working memory.
- Episodic vector memory over timestamped conversation events.
- Semantic profile facts normalized into SQLite.
- Temporal filtering and recency-aware hybrid retrieval.
- Conflict detection with supersession links rather than silent overwrite.
- Memory consolidation and token-budgeted summaries.
- Deletion tombstones plus removal from structured and vector indexes.
- Evidence citations and abstention when retrieved memories conflict.

### Controlled Comparison

Compare a recent-message window, vector-only episodic memory, and hybrid
episodic-plus-semantic memory. Use the same model and test questions. Select any
retrieval thresholds on a development subset only.

### Metrics

- QA exact match/token F1 and evidence retrieval recall.
- Temporal accuracy, contradiction rate, and unsupported-answer rate.
- Correction adoption and deletion compliance.
- Context tokens, index size, retrieval latency, end-to-end latency, and cost.

### Workload Boundary

Use 150-300 model calls. Expected execution is 90-180 minutes on a Colab CPU or
L4. Cache memory extraction and evaluator outputs so retrieval experiments do not
repeat API calls.

### Suggested Special Artifacts

- Memory ingestion, consolidation, retrieval, and deletion diagram.
- Three-system memory-quality comparison.
- Accuracy-versus-context-token chart.
- Conflict-resolution and verified-deletion examples.

### Resume Bullet Template

> Built a hybrid long-term memory agent with episodic retrieval, normalized
> semantic facts, temporal conflict resolution, and deletion controls; improved
> `[metric]` by `[X]%` over a sliding-window baseline on `[N]` audited memory
> questions.

## Recommended Build Order

1. **Project 4:** Best compact demonstration of production workflow reliability.
2. **Project 5:** Adds database execution and governance with deterministic metrics.
3. **Project 7:** Adds current protocols and measurable agent security.
4. **Project 6:** Build next when targeting coding-agent or developer-tool roles.
5. **Project 8:** Build next when targeting assistants, enterprise agents, or
   personalization platforms.

Two polished additions are enough to begin applying. Complete reports, failure
analysis, and reproducible metrics are more valuable than five partially executed
notebooks.

## Primary Technical References

- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
  for checkpointed HITL pause and resume.
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
  for checkpoints, recovery, replay, and state history.
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) for typed
  tools, sessions, guardrails, handoffs, and agent runtimes.
- [OpenAI Agents SDK tracing](https://openai.github.io/openai-agents-python/tracing/)
  for model, tool, guardrail, and handoff spans.
- [Model Context Protocol specification](https://modelcontextprotocol.io/specification/)
  for interoperable agent-to-tool contracts.
- [A2A Protocol](https://a2a-protocol.org/latest/) for discovery, delegation,
  communication, and task management between agents.
- [DuckDB Python API](https://duckdb.org/docs/stable/clients/python/overview) for
  local analytical execution.
- [SQLGlot](https://sqlglot.com/) for SQL parsing, AST traversal, and validation.
- [Agent trajectory evaluation](https://docs.langchain.com/oss/python/langchain/test/evals)
  for deterministic and judge-based trajectory scoring.
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/) for
  traces, metrics, logs, and correlation.
- [LoCoMo repository](https://github.com/snap-research/locomo) for long-term
  conversational-memory data.
- [QuixBugs repository](https://github.com/jkoppel/QuixBugs) for compact
  program-repair cases.

## Portfolio-Ready Quality Gate

A selected project is complete only when:

- A fresh Colab run finishes in less than 6 hours.
- Dependencies are pinned and pass a clean import test.
- Data is downloaded once, cached, and checksum-verified.
- Baseline and advanced systems use identical held-out cases and model controls.
- Reliability and safety tests execute rather than appearing only in discussion.
- Metrics include quality, safety, trajectory, latency, token use, and cost.
- Representative failures and limitations appear in the notebook and report.
- Output artifacts contain no API keys, personal data, or local absolute paths.
- Notebook results, summary JSON, charts, report PDF, and resume bullet use the
  same final measured values.
