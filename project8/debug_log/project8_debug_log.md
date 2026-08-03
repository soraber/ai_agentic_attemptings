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
- **Verification:** The final expanded suite passed 12 tests; 240 answers completed and were cached; final privacy validation passed; the measured summary retained original token/cost usage during a zero-call cached rerun; the revised one-page report rendered without clipping or overlap
- **Preservation:** LoCoMo selection, lifecycle fixtures, and memory-store behavior were unchanged

## 2026-08-03 - Completed Colab A100 Evaluation

- **Environment:** Colab A100-SXM4-40GB runtime; MiniLM dense retrieval and Qwen2.5-7B-Instruct in BF16
- **Notebook cells:** Source changed only in `P08-C01`, `P08-C02`, and `P08-C07`; outputs were populated through `P08-C10`; temporary export cell `P08-TEMP-EXPORT` was removed after artifact transfer
- **Symptom:** VS Code first auto-connected Project 8 to a CPU kernel, then the Colab kernel picker looped without selecting the mounted A100 server
- **Root cause:** The extension could authenticate its Colab terminal and filesystem provider but failed to resolve the notebook-to-kernel selection state
- **Fix:** Stopped picker debugging at the user-defined 10-minute limit, uploaded the exact local notebook, and executed it through authenticated A100 terminal `jupyter nbconvert`
- **Symptom:** The first real inference returned explanatory text in the boolean `abstained` field and failed strict Pydantic validation
- **Root cause:** Deterministic open-model decoding did not always respect JSON field types despite the structured prompt
- **Fix:** Added `normalize_local_answer()` to repair only common type-shape errors before strict `GeneratedAnswer` construction, plus a regression test for string evidence IDs and explanatory abstention text
- **Verification:** The expanded suite passed 12 tests in 0.53 seconds; 240 answer-system pairs completed using 150 new model calls and 90 cache hits; report and privacy validation passed; the final PDF was rendered and checked
- **Measured result:** Dense episodic retrieval led the local run at 10.00% token F1 and 15.00% evidence recall; hybrid reached 6.63% and 13.13%; deletion compliance remained 100%
- **Preservation:** `P08-C03` and `P08-C04` data preparation were unchanged, API artifacts remained primary, and local artifacts were isolated under `output/gpu/`
