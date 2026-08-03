# Project 4 Execution Runbook

This runbook prepares and executes the durable incident-response experiment in a
fresh Google Colab runtime. The notebook uses stable IDs so debugging notes can
name the exact changed cell.

## 1. Open and Prepare Colab

1. Open `project4_durable_incident_response_agent.ipynb` from GitHub in Colab.
2. Select **Runtime > Change runtime type**.
3. Choose CPU for deterministic mode or L4 for optional local extensions. The API
   experiment does not require a GPU.
4. Run cells in order. Do not run the full evaluation before the smoke tests pass.

## 2. Cell-by-Cell Procedure

| Cell | Purpose | Expected result |
| --- | --- | --- |
| `P04-C00` | Scope, hypotheses, and non-goals | Markdown only |
| `P04-C01` | Clone/update the repository, inspect runtime, install dependencies | Import smoke test passes |
| `P04-C02` | Load config and secrets; select deterministic or API planner | Secret value is never printed |
| `P04-C03` | Generate or reuse the cached 24-incident benchmark | Dataset checksum and counts printed |
| `P04-C04` | Load deterministic development and test splits | 8 development and 16 test cases |
| `P04-C05` | Run baseline smoke case | One trace and one simulated effect |
| `P04-C06` | Build durable graph and demonstrate approval pause/resume | State resumes under the same thread ID |
| `P04-C07` | Run policy, duplicate-request, crash, timeout, and compensation tests | All deterministic checks pass |
| `P04-C08` | Run the paired baseline and durable evaluation | Summary metrics and budget report printed |
| `P04-C09` | Inspect representative successes and failures | Cases grouped by failure stage |
| `P04-C10` | Export JSON/JSONL evidence and build charts/PDF | Output contract is complete |

## 3. Dependency Installation

The setup cell runs:

```bash
python -m pip install --upgrade-strategy only-if-needed -r requirements-colab.txt
python -m pip install -e . --no-deps
python -m pip check
```

The project does not install Gradio, FastAPI, Google ADK, or other UI frameworks.
The setup cell displays `pip check` output but does not abort on conflicts from an
unrelated preinstalled package. It then imports the Project 4 config and workflow;
those import checks do fail fast. Record relevant conflicts in the debug log before
changing any package version or deciding whether a runtime restart is necessary.

## 4. Secrets

For API mode, add a Colab secret named `OPENAI_API_KEY` and enable notebook access
for that secret. The code checks Colab Secrets first and then the environment.

Optional environment variables:

```text
PROJECT4_MODEL=gpt-5.6-luna
PROJECT4_REASONING_EFFORT=low
PROJECT4_INPUT_USD_PER_MILLION=1.0
PROJECT4_OUTPUT_USD_PER_MILLION=6.0
```

Never paste a key into a notebook cell or store it in `.env.example`.

## 5. First Run: Deterministic Mode

Keep these values in `P04-C02`:

```python
RUN_API_EVAL = False
RUN_FULL_EVAL = False
```

Run through `P04-C07`. This validates data generation, policy checks, approval,
checkpointing, crash recovery, deduplication, and compensation without API cost.

Then set:

```python
RUN_FULL_EVAL = True
```

Run `P04-C08` through `P04-C10` to generate a deterministic reference report.
This is a pipeline validation result, not the final model comparison.

## 6. API Evaluation

After deterministic checks pass:

```python
RUN_API_EVAL = True
RUN_FULL_EVAL = True
```

The default limits are:

- Maximum 120 model calls.
- Maximum 450 output tokens per diagnosis.
- Maximum two transient retries.
- Maximum estimated API cost of USD 5.00.
- Sixteen paired held-out incidents with two repetitions: 64 structured calls
  when diagnosis and planning are separate calls.

The budget guard stops before a call that would exceed the configured limits.
Use the same model, reasoning effort, and prompt for baseline and durable systems.

## 7. Failure Injection

The evaluation injects a crash after the simulated side effect commits. On retry:

- The stateless baseline may repeat the effect because it has no durable execution
  ledger.
- The advanced workflow reuses the idempotency key, reads the committed ledger
  entry, and returns the prior result without repeating the effect.

The project also tests:

- Invalid planner JSON.
- Unsupported actions.
- Low-confidence diagnosis.
- Human rejection.
- Tool timeout.
- Failed remediation followed by compensation.
- Duplicate request delivery.

## 8. Output Verification

Run:

```bash
python tools/validate_project.py --require-results
```

Then confirm:

1. Summary metrics match notebook output.
2. Trace rows contain correlation and thread IDs.
3. No trace contains `OPENAI_API_KEY`, `sk-`, or a local user directory.
4. The report identifies deterministic versus API mode.
5. Baseline and durable results use the same held-out incident IDs.
6. Representative failures are included, not only successes.

## 9. Debugging Rule

For every notebook change, add an entry to
`debug_log/project4_debug_log.md` containing:

- Date and environment.
- Exact cell ID.
- Symptom and error text.
- Root cause.
- Minimal fix.
- Verification command or output.
- Whether prior user-edited cells were preserved.
