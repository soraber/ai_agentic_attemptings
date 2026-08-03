# Project 8 Debug Log

Record date, environment, exact `P08-CXX` cell, symptom, root cause, minimal fix,
verification, and preservation notes.

## 2026-08-02 - Initial Scaffold

- **Environment:** Local pre-execution workspace
- **Notebook cell:** `P08-C00` through `P08-C10`
- **Symptom:** None
- **Fix:** Created pinned LoCoMo selector, lifecycle store, evaluation, and tools

## 2026-08-02 - Lexical Retrieval Favored Pronoun Over Verb

- **Environment:** Local deterministic tests
- **Notebook cell:** Retrieval used by `P08-C05` and `P08-C08`; cells unchanged
- **Symptom:** A recent event sharing only the pronoun `I` outranked the event containing `moved` for a question using `move`
- **Root cause:** Raw overlap retained stopwords and did not normalize a simple past-tense suffix
- **Fix:** Removed a small fixed stopword set and normalized common `-ed` forms
- **Verification:** The LoCoMo conversion/retrieval test and full Project 8 suite pass
