# Project 4 Background: Durable Agent Execution

## 1. Why Durability Matters

An LLM can choose a useful action while the surrounding system still behaves
incorrectly. A process may crash after an external action succeeds but before the
agent records success. Retrying the step can then repeat a payment, deployment,
notification, or infrastructure change.

A durable agent treats model decisions as only one component of a stateful
workflow. State transitions, approvals, tool calls, and results are persisted so
the workflow can recover and explain what happened.

## 2. State Machines Versus Prompt Loops

A linear prompt loop usually performs:

```text
observe -> reason -> call tool -> answer
```

A state graph gives each transition an explicit contract:

```text
diagnose -> verify -> plan -> approve -> execute -> validate -> close
                                      \-> reject ---------> close
                                                 \-> compensate
```

Explicit nodes make it possible to validate intermediate outputs, apply different
retry policies, pause for human input, and evaluate the trajectory rather than only
the final message.

## 3. Checkpointing

A checkpoint stores the workflow state after a completed step. Let `S_k` be the
state after node `k`. If node `k + 1` fails, recovery loads `S_k` and repeats only
the unfinished work.

Useful checkpoint fields include:

- Thread and incident IDs.
- Current node and status.
- Diagnosis and evidence references.
- Proposed action and policy result.
- Approval decision.
- Tool idempotency key and execution result.
- Retry count, timestamps, and trace IDs.

Checkpointing does not itself guarantee correct side effects. It must be combined
with idempotent tool design.

## 4. Idempotency and Exactly-Once Effects

An operation is idempotent when applying it repeatedly with the same key produces
the same externally visible result as applying it once.

For request `r` and idempotency key `k`:

```text
execute(r, k) = saved_result(k), if k already completed
execute(r, k) = perform_and_save(r, k), otherwise
```

In this project, the simulated effect and ledger entry are committed in one SQLite
transaction. A crash is injected after the commit. On retry, the advanced executor
finds the completed key and returns the prior result. The stateless baseline has no
such ledger and may create a second effect.

Real distributed systems cannot generally promise exactly-once execution without
cooperation from the external service. The practical design is usually at-least-once
delivery plus idempotent receivers, unique operation IDs, and reconciliation.

## 5. Human-in-the-Loop Approval

Human approval is appropriate before external, destructive, costly, or
scope-expanding actions. The workflow should persist state before requesting
approval and bind the response to the exact proposed action.

An approval payload should include:

- Proposed action and target.
- Evidence and confidence.
- Expected effect and rollback option.
- Policy result and unresolved risk.
- Correlation and idempotency IDs.

Approval is not a substitute for authorization. A human must not be allowed to
approve an action that the service identity is not authorized to perform.

## 6. Retry, Timeout, and Backoff

Retries are useful for transient failures but dangerous for side effects. A bounded
exponential schedule can be written as:

```text
delay_i = min(delay_max, delay_0 * 2^i) + jitter_i
```

Every retry must have:

- A maximum attempt count.
- A timeout.
- A classification of retryable and permanent errors.
- The same idempotency key for the same intended action.
- Trace evidence showing why the retry occurred.

## 7. Compensation and the Saga Pattern

Some multi-step operations cannot be rolled back with a database transaction. A
saga defines a compensating action for each completed forward action.

Examples:

| Forward action | Possible compensation |
| --- | --- |
| Scale service from 2 to 4 replicas | Restore previous replica count |
| Roll back deployment | Restore the prior deployment if validation fails |
| Open incident ticket | Close or annotate the duplicate ticket |

Compensation is a new action with its own failure modes. It should be idempotent,
authorized, traced, and validated.

## 8. Observability

Logs explain discrete events, metrics summarize numerical behavior, and traces show
causal work across components. OpenTelemetry provides a shared model for spans and
correlation.

Important span attributes include:

- `incident.id`
- `workflow.thread_id`
- `agent.node`
- `tool.name`
- `tool.idempotency_key`
- `approval.result`
- `retry.attempt`
- `error.type`

Sensitive prompts, secrets, and raw environment values should not be exported.

## 9. Evaluation Design

Final-answer accuracy is insufficient for an action-taking agent. Project 4
measures:

- **Diagnosis accuracy:** predicted root cause equals the hidden label.
- **Remediation accuracy:** proposed action equals the allowed action.
- **Safety-block rate:** unsafe actions blocked divided by unsafe attempts.
- **Recovery success:** crash cases that reach a correct terminal state.
- **Duplicate effects:** repeated simulated side effects for one incident/action.
- **Trajectory accuracy:** required nodes and tool calls occurred in a valid order.
- **Latency and cost:** p50/p95 time, model calls, tokens, and estimated API cost.

Baseline and advanced systems must receive the same evidence, model, decoding
settings, and held-out incidents. Otherwise, reliability changes cannot be isolated.

## 10. Limitations

- The tools are simulations, so results do not prove safety in a production cloud.
- SQLite represents one durable store but not a multi-region deployment.
- Twenty-four incidents are enough for a focused demonstration, not broad coverage.
- A simulated human approval policy is not a substitute for real operator studies.
- Model accuracy may vary with provider updates unless a model snapshot is pinned.

## Primary References

- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)
