# Project 7: Secure Interoperable Agent Gateway

A local protocol-security experiment with procurement requester and compliance
reviewer agents, A2A-style task envelopes, MCP-style typed tools, scoped
authorization, taint tracking, metadata pinning, redaction, approval, idempotency,
and correlated traces.

## Status

Prepared for execution. Forty deterministic benign/attack cases and all protocol
controls run without a model. An optional structured model recommendation is
scored separately and never authorizes or executes a tool.

## Architecture

```text
requester Agent Card -> A2A task -> gateway contract/policy -> reviewer handoff
                                      |                    |
                                      v                    v
                              MCP policy search      approval tool
                                      |                    |
                         provenance + taint      scope + HITL + ledger
                                      +-----------> redacted artifact + trace
```

See `RUNBOOK.md` for stable cells `P07-C00` through `P07-C10`. All records,
credentials, and canary strings are synthetic.
