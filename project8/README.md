# Project 8: Long-Term Memory Agent

A three-system comparison of recent-window, vector-only episodic, and hybrid
episodic-plus-semantic memory with temporal facts, corrections, conflicts,
consolidation, deletion tombstones, evidence citations, and abstention.

## Status

Prepared for execution. A pinned LoCoMo subset is downloaded once in Colab;
deterministic lifecycle fixtures run fully offline. Final model-backed QA results
are absent.

## Architecture

```text
session events -> working window
              -> episodic lexical/vector index ----+
              -> semantic facts + supersession ----+-> hybrid retrieval -> answer + evidence
              -> tombstones / physical deletion ---+                     -> abstain on conflict
```

See `RUNBOOK.md` for stable cells `P08-C00` through `P08-C10`.
