# Project 7 Execution Runbook

| Cell | Purpose |
| --- | --- |
| `P07-C00` | Scope, protocol boundaries, threats, and comparison |
| `P07-C01` | Clone/install/import smoke test |
| `P07-C02` | Config, optional secret, and budgets |
| `P07-C03` | Generate/reuse 40 paired protocol cases |
| `P07-C04` | Verify development/test split and categories |
| `P07-C05` | Undefended gateway smoke case |
| `P07-C06` | Defended A2A/MCP gateway smoke case |
| `P07-C07` | Schema, scope, taint, poisoning, duplicate, and redaction tests |
| `P07-C08` | Paired evaluation when enabled |
| `P07-C09` | Inspect attacks, blocks, and correlated traces |
| `P07-C10` | Generate measured report and validate outputs |

Start with `RUN_API_EVAL=False` and `RUN_FULL_EVAL=False`. Deterministic checks
must pass before a measured run. API mode adds one structured policy recommendation
per held-out case, limited by 160 calls, 500 output tokens per call, two retries,
and USD 6 estimated cost. Recommendations are scored but cannot authorize tools.

The gateway uses local function calls but preserves protocol envelopes, Agent
Cards, JSON Schemas, task IDs/statuses/artifacts, tool annotations, correlation
IDs, bearer scopes, and duplicate-delivery semantics. This isolates protocol and
security logic without network flakiness.
