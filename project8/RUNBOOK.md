# Project 8 Execution Runbook

| Cell | Purpose |
| --- | --- |
| `P08-C00` | Scope, three-system comparison, lifecycle, and privacy boundary |
| `P08-C01` | Clone/install/import smoke test |
| `P08-C02` | Config, optional API secret, and cache budgets |
| `P08-C03` | Download pinned LoCoMo once and prepare two-sample subset |
| `P08-C04` | Load sessions, QA, and deterministic lifecycle fixtures |
| `P08-C05` | Recent-window and episodic retrieval smoke tests |
| `P08-C06` | Hybrid semantic/temporal memory, correction, and deletion |
| `P08-C07` | Conflict, supersession, citation, deletion, and cache tests |
| `P08-C08` | Three-system paired evaluation when enabled |
| `P08-C09` | Inspect correction, conflict, deletion, and failure examples |
| `P08-C10` | Generate measured report and validate outputs |

Use CPU for deterministic retrieval or L4 for optional local embedding models.
API extraction/evaluation is opt-in and limited to 300 calls, 500 output tokens,
two retries, and USD 8 estimated cost. Cache extraction and model outputs so
retrieval experiments do not repeat calls.

Deletion verification checks the event store, semantic facts, retrieval results,
and tombstone ledger. Record every notebook change by `P08-CXX`.
