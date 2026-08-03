# Project 6 Data

The manifest pins twelve Python QuixBugs cases to commit
`4257f44b0ff1181dedaedee6a447e133219fcebf`. `tools/fetch_quixbugs.py` clones once,
checks out that detached commit, verifies every declared source/test path, and
caches it under `data/cache/`.

Gold corrected programs remain outside planner prompts and are used only by an
optional evaluator. Local unit tests use tiny synthetic repositories.
