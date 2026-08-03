# Project 7 Background: Secure Agent Interoperability

## A2A and MCP

A2A describes communication between agents: discovery, delegation, task state,
messages, and artifacts. MCP describes how an agent discovers and calls tools or
resources through typed contracts. They solve different boundaries and can be used
together.

## Least Privilege

The requester may search policy but cannot approve procurement. Only the reviewer
holds the `procurement:approve` scope, and approval also requires a human decision.
Tool descriptions do not grant authority; the gateway verifies identity and scope
before every side effect.

## Prompt Injection and Taint

Retrieved documents and remote metadata are untrusted. Provenance labels follow
their content through delegation. Tainted text may inform a summary but cannot
create permissions, select a write tool, or reveal a canary secret.

## Metadata Pinning

Tool names, schemas, and side-effect annotations are hashed. A changed description
or schema fails pin verification before dispatch, limiting tool-poisoning attacks.

## Idempotency and Tracing

A2A tasks carry stable task and correlation IDs. The approval ledger stores task
IDs so duplicate delivery returns the prior artifact rather than repeating a write.
Trace completeness requires discovery, validation, authorization, tool, handoff,
and terminal events under one correlation ID.

## Metrics

Attack success, secret leakage, unauthorized calls, unsafe writes, benign task
success, false blocks, duplicate effects, contract validity, trace completeness,
latency, serialization overhead, tokens, and cost.

## References

- [A2A Protocol](https://a2a-protocol.org/latest/)
- [Model Context Protocol](https://modelcontextprotocol.io/specification/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
