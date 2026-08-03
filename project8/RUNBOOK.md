# Project 8 Execution Runbook

| Cell | Purpose |
| --- | --- |
| `P08-C00` | Scope, three-system comparison, lifecycle, and privacy boundary |
| `P08-C01` | Clone/install/import smoke test and print CUDA/GPU status |
| `P08-C02` | Select `deterministic`, `openai`, or `local_gpu`; load a secret only for OpenAI |
| `P08-C03` | Download pinned LoCoMo once and prepare two-sample subset |
| `P08-C04` | Load sessions, QA, and deterministic lifecycle fixtures |
| `P08-C05` | Recent-window, lexical, and dense/hybrid retrieval smoke tests |
| `P08-C06` | Hybrid semantic/temporal memory, correction, and deletion |
| `P08-C07` | Conflict, supersession, citation, deletion, and cache tests |
| `P08-C08` | Three-system paired evaluation when enabled |
| `P08-C09` | Inspect correction, conflict, deletion, and failure examples |
| `P08-C10` | Generate measured report and validate outputs |

Use an A100 for `local_gpu`. It loads `Qwen/Qwen2.5-7B-Instruct` once in BF16 and
uses normalized `all-MiniLM-L6-v2` embeddings. Dense similarity is used for
episodic retrieval; hybrid retrieval combines 70% dense similarity, 25% lexical
overlap, and 5% recency. Local outputs and caches stay under `output/gpu/` and
`output/runtime/`. API evaluation remains limited to 300 calls, 500 output tokens,
two retries, and USD 8 estimated cost.

Model sources:

- https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
- https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

Deletion verification checks the event store, semantic facts, retrieval results,
and tombstone ledger. Record every notebook change by `P08-CXX`.
