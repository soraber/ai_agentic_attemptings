# Project 8 Background: Long-Term Agent Memory

## Memory Types

- Working memory: a small recent-message window.
- Episodic memory: timestamped events retrieved by semantic similarity.
- Semantic memory: normalized facts such as preferences and profile attributes.
- Temporal memory: validity intervals, corrections, and supersession links.

## Retrieval

Vector-only retrieval can find relevant wording but may return stale facts. Hybrid
retrieval combines semantic facts, episodic evidence, recency, and temporal
filters. This scaffold uses deterministic lexical similarity offline and leaves a
cached embedding path for the measured run.

## Correction and Conflict

A correction closes the prior fact and creates a new active value while retaining
history. Two incompatible active values without an ordering signal form a conflict;
the agent should abstain rather than silently choose one.

## Deletion

A deletion request creates an audit tombstone and removes the event and derived
fact from active stores and retrieval indexes. Compliance is verified across all
representations, not only hidden in the final answer.

## Evaluation

Exact match and token F1 measure answers; evidence recall checks citations;
temporal accuracy checks the correct validity period; correction adoption and
deletion compliance test lifecycle behavior. Context tokens, index size,
retrieval latency, total latency, and cost expose efficiency tradeoffs.

## Limitations

Lexical retrieval is a reproducible offline proxy, not a state-of-the-art semantic
encoder. Two LoCoMo conversations do not establish broad personalization quality,
and a SQLite deletion proof does not guarantee deletion from provider logs or
backups.

## References

- [LoCoMo repository](https://github.com/snap-research/locomo)
- [SQLite](https://www.sqlite.org/docs.html)
- [OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings)
