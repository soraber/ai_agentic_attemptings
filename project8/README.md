# Project 8: Long-Term Memory Agent

A three-system comparison of recent-window, vector-only episodic, and hybrid
episodic-plus-semantic memory with temporal facts, corrections, conflicts,
consolidation, deletion tombstones, evidence citations, and abstention.

## Status

The OpenAI-backed LoCoMo run and lifecycle evidence are saved in `output/`. A
separate A100 path combines dense event embeddings, lexical/recency fusion, and a
local BF16 answer model under `output/gpu/` without replacing existing evidence.

## Architecture

```text
session events -> working window
              -> episodic lexical/vector index ----+
              -> semantic facts + supersession ----+-> hybrid retrieval -> answer + evidence
              -> tombstones / physical deletion ---+                     -> abstain on conflict
```

See `RUNBOOK.md` for stable cells `P08-C00` through `P08-C10`.

Set `EVAL_BACKEND="local_gpu"` in `P08-C02` to run the local comparison. Deletion,
supersession, conflict, and tombstone checks remain deterministic.
