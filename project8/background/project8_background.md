# Project 8 Background: Long-Term Agent Memory

## Memory Types

- Working memory: a small recent-message window.
- Episodic memory: timestamped events retrieved by semantic similarity.
- Semantic memory: normalized facts such as preferences and profile attributes.
- Temporal memory: validity intervals, corrections, and supersession links.

## Retrieval

Vector-only retrieval can find relevant wording but may return stale facts. Hybrid
retrieval combines semantic facts, episodic evidence, recency, and temporal
filters. The offline baseline uses lexical similarity. The A100 path caches
normalized MiniLM event vectors, uses cosine similarity for episodic retrieval,
and fuses 70% dense similarity, 25% lexical overlap, and 5% recency for hybrid
ranking.

## Local Answer Generation

Qwen2.5 7B Instruct runs in BF16 and returns a typed answer, evidence IDs, and an
abstention flag. Every prompt contains only the selected memory events. Outputs are
cached by model, sample, question, system, and exact context, so retrieval changes
invalidate the right answers without repeating unchanged generations.

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

The compact embedding model is efficient but not specialized for long dialogue.
Two LoCoMo conversations do not establish broad personalization quality, and a
SQLite deletion proof does not guarantee deletion from provider logs or backups.

## References

- [LoCoMo repository](https://github.com/snap-research/locomo)
- [SQLite](https://www.sqlite.org/docs.html)
- [OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings)
- [Qwen2.5 7B Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
