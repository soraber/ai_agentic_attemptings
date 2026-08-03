# AI Agentic Attemptings

Compact, evaluation-driven AI agent engineering projects spanning workflow
reliability, governed data access, coding agents, protocol
security, and long-term memory.

> **Version:** ver 0.3: add Project 4 pre-execution scaffold<br>
> **Updated:** 2026-08-02 22:56 EDT

## Implemented Scaffold

### Project 4: Durable Incident-Response Agent

[`project4/`](project4/) contains the complete pre-execution package for a paired
comparison between a stateless action loop and a checkpointed, approval-gated
LangGraph workflow. It includes a committed 24-incident benchmark, stable-cell
Colab notebook, reusable Python package, SQLite side-effect simulator, policy and
failure-injection tests, background guide, runbook, debug log, validator, and a
measured-result report generator.

The deterministic preflight suite passes 11 tests, including approval resume,
incident-bound policy checks, idempotent crash recovery, compensation replay, and
trace redaction. No full evaluation or performance result is claimed yet; final
JSON, charts, traces, and PDF are generated only after notebook execution.

## Project Ideas

See [`projects_ideas.md`](projects_ideas.md) for the ranked project slate,
implementation boundaries, controlled comparisons, metrics, artifact expectations,
and primary technical references.
