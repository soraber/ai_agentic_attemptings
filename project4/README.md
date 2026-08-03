# Project 4: Durable Incident-Response Agent

A compact, controlled experiment comparing a stateless incident-response loop with
a durable, approval-gated agent. The advanced workflow checkpoints state, resumes
after failures, deduplicates side effects, compensates failed actions, and emits
correlated traces.

## Status

The project is prepared for execution but has not yet produced final experiment
results. Deterministic unit tests may be run locally; full notebook evaluation is
intended for Google Colab.

## Core Questions

1. Can a durable workflow recover from a crash without repeating a side effect?
2. Do explicit policy and approval gates block unsafe actions without blocking
   legitimate remediations?
3. What reliability, latency, token, and cost overhead is introduced by durable
   execution?
4. Which failures come from diagnosis quality, planning, policy, tools, or runtime
   recovery?

## Architecture

The advanced workflow uses these stages:

```text
incident evidence
      |
      v
diagnose -> verify -> plan -> policy gate -> approval interrupt
                                             |
                                             v
                         checkpoint -> execute -> validate
                                             |          |
                                             |          v
                                             +----> compensate
                                                        |
                                                        v
                                                       close
```

The baseline receives the same incident evidence, planner, and simulated action
catalog but runs as a stateless linear loop without checkpointed approval or an
idempotency ledger.

## Repository Map

| Path | Purpose |
| --- | --- |
| [`project4_durable_incident_response_agent.ipynb`](project4_durable_incident_response_agent.ipynb) | Stable-cell Colab notebook for the complete experiment |
| [`RUNBOOK.md`](RUNBOOK.md) | Commands, cell order, configuration, and troubleshooting |
| [`requirements-colab.txt`](requirements-colab.txt) | Narrow dependency ranges for a fresh Colab runtime |
| [`config/default.json`](config/default.json) | Experiment limits, model defaults, split, and pricing inputs |
| [`src/project4_agent/`](src/project4_agent/) | Dataset, schemas, planners, policy, simulator, workflow, evaluation, and telemetry |
| [`tools/build_notebook.py`](tools/build_notebook.py) | Deterministically rebuilds the notebook with stable cell IDs |
| [`tools/generate_report.py`](tools/generate_report.py) | Builds final charts and PDF from measured JSON artifacts |
| [`tools/generate_incident_dataset.py`](tools/generate_incident_dataset.py) | Generates the fixed 24-incident benchmark outside the notebook |
| [`tools/validate_project.py`](tools/validate_project.py) | Checks required files, notebook cells, dataset, config, and output contract |
| [`tests/`](tests/) | Deterministic tests for data, policy, idempotency, recovery, and evaluation helpers |
| [`background/project4_background.md`](background/project4_background.md) | Concepts and tradeoffs behind durable agent execution |
| [`debug_log/project4_debug_log.md`](debug_log/project4_debug_log.md) | Cell-specific issue and fix history |
| [`data/`](data/) | Generated benchmark and cache documentation |
| [`output/`](output/) | Final summaries, samples, traces, report, and report assets |

## Execution Modes

### Deterministic Mode

Uses a rule-based planner and no external model calls. This mode validates the
workflow, safety controls, failure injection, artifact export, and report pipeline.
It is the default.

### API Mode

Uses the OpenAI Responses API for structured diagnosis and planning. The default
model is `gpt-5.6-luna`, selected for a bounded high-volume evaluation, but the
model is configurable through `PROJECT4_MODEL`. API mode is opt-in and requires an
`OPENAI_API_KEY` secret.

## Quick Start

From the `project4` directory:

```bash
python -m pip install -r requirements-colab.txt
python -m pip install -e . --no-deps
python tools/generate_incident_dataset.py
pytest -q
python tools/validate_project.py
```

For the complete experiment, open the notebook in Colab and follow
[`RUNBOOK.md`](RUNBOOK.md). Keep `RUN_API_EVAL = False` for the first run.

## Expected Final Outputs

After a complete evaluation, `output/` should contain:

- `project4_final_summary.json`
- `project4_representative_samples.json`
- `project4_traces.jsonl`
- `project4_report.pdf`
- `project4_report_assets/procedure_diagram.svg`
- `project4_report_assets/quality_metrics.png`
- `project4_report_assets/recovery_safety.png`
- `project4_report_assets/latency_cost_tradeoff.png`

These files are generated from measured notebook results. Placeholder performance
numbers must not be committed.

## Safety Boundary

All remediation tools are simulations. They write only to a local SQLite ledger
and never connect to Kubernetes, cloud providers, production databases, ticketing
systems, or external infrastructure.
