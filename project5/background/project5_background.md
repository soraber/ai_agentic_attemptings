# Project 5 Background: Governed Text-to-SQL

## Text-to-SQL as an Agent Workflow

Text-to-SQL converts a question into an executable database program. Correct SQL
syntax is not enough: the query must select the intended schema, produce the right
rows, obey authorization, and avoid exposing sensitive data.

The governed workflow separates planning from execution:

```text
retrieve schema -> plan -> parse AST -> authorize -> explain -> execute -> verify
```

## Schema Linking

Schema linking maps words in a question to tables, columns, relationships, and
business definitions. Deterministic and OpenAI runs retain the lexical baseline.
The A100 path encodes the question and seven schema descriptions with normalized
MiniLM vectors, then ranks tables by cosine similarity. Schema retrieval reduces
prompt size and discourages invented columns.

## Why Use A Local GPU Model

The A100 path runs Qwen2.5-Coder 7B in BF16. A 7B model is large enough to test
local code-oriented planning while fitting comfortably on a 40 GB A100 alongside
the embedding model and KV cache. Deterministic decoding makes repeated prompts
comparable. The model still has no execution authority: JSON parsing, Pydantic,
SQLGlot, region/column policy, `EXPLAIN`, and read-only DuckDB form independent
layers after generation.

## SQL AST Validation

String filters are fragile because comments, quoting, nested queries, and dialect
syntax can hide dangerous operations. SQLGlot parses SQL into an abstract syntax
tree (AST). Policy walks typed nodes and column references to enforce:

- one query statement;
- `SELECT`-class expressions only;
- approved tables and columns;
- no external file or network functions;
- authorized regions;
- bounded result size.

## Execution and Result Accuracy

Execution accuracy asks whether SQL runs. Result-hash accuracy asks whether its
normalized columns and rows equal the gold result. The latter catches executable
but semantically wrong queries.

```text
result_hash = SHA256(canonical_json(columns, sorted_rows))
```

## Repair

Parser and database errors are compact evidence for a bounded repair attempt. The
agent receives the question, selected schema, prior SQL, and sanitized error, then
may produce one correction. Repair remains subject to the complete AST policy.

## Governance

Read-only credentials, row-level authorization, column denial, masking, output
limits, and approval address different risks. Masking is defense in depth; policy
should prevent unauthorized PII from being selected in the first place.

Text retrieved from a database is untrusted. A stored note saying "ignore policy"
must remain data and must never change tool selection or authorization.

## Limitations

- Synthetic schemas are cleaner than production warehouses.
- Dense linking can still miss organization-specific business synonyms.
- Read-only DuckDB does not reproduce distributed warehouse latency or IAM.
- Result hashes prove equality only for the fixed data snapshot.

## Primary References

- [DuckDB Python API](https://duckdb.org/docs/stable/clients/python/overview)
- [SQLGlot documentation](https://sqlglot.com/)
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Qwen2.5-Coder 7B Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)
- [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
