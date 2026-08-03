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

## 2026-08-03 - Dense Retrieval and A100 Answering

- **Environment:** Local CPU interface validation; A100 execution path prepared
- **Notebook cells:** `P08-C01`, `P08-C02`, `P08-C05`, `P08-C08`, `P08-C09`, and `P08-C10`
- **Symptom:** The measured API run used the lexical retrieval path, and the local GPU option described in the runbook was not implemented
- **Root cause:** The initial scaffold focused on memory lifecycle correctness and cached API evaluation
- **Fix:** Added cached MiniLM event embeddings, dense and hybrid ranking, a BF16 Qwen2.5 answerer, isolated GPU artifacts, and patch-only notebook updates
- **Verification:** Eleven tests pass, including dense ranking and local-answer caching; the LoCoMo download cell and existing API evidence remain unchanged

## 2026-08-03 - Cached API Evaluation and Privacy Validation

- **Environment:** Local macOS kernel with pinned LoCoMo subset and OpenAI Responses API
- **Notebook cells:** `P08-C01`, `P08-C02`, output sanitization in `P08-C03`, and targeted re-execution of `P08-C10`
- **Symptom:** The 240-answer run completed, but `P08-C10` scanned the full upstream clone and flagged a token-shaped public-data string; the saved error output also contained an absolute local path. A first targeted rerun could not open a kernel socket inside the sandbox
- **Root cause:** The privacy validator did not distinguish the external source checkout from project-owned artifacts, and notebook subprocess output used absolute paths
- **Fix:** Continued scanning the extracted subset and all outputs while excluding only the pinned raw clone, sanitized notebook paths, added cache/retry/cost controls, and reran `P08-C10` with local-kernel permission without an API key
- **Verification:** The final expanded suite passed 11 tests; 240 answers completed and were cached; final privacy validation passed; the measured summary retained original token/cost usage; the revised one-page report rendered without clipping or overlap
- **Preservation:** LoCoMo selection, lifecycle fixtures, and memory-store behavior were unchanged
