# Project 8: Long-Term Memory Agent

A three-system comparison of recent-window, vector-only episodic, and hybrid
episodic-plus-semantic memory with temporal facts, corrections, conflicts,
consolidation, deletion tombstones, evidence citations, and abstention.

## Status

Both comparisons are complete. API lexical episodic retrieval in `output/`
reached 11.50% token F1 and 22.29% evidence recall. A100 dense episodic retrieval
in `output/gpu/` reached 10.00% and 15.00%, respectively. Both runs preserved
100% deletion compliance, and the local artifacts do not replace API evidence.

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
