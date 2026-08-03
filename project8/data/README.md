# Project 8 Data

`locomo_selection.json` pins the official repository and selects two conversations
with 40 QA items each. `tools/fetch_locomo.py` prepares the subset under ignored
`data/cache/` and preserves dialogue IDs, timestamps, answers, and evidence.

`lifecycle_cases.json` is a synthetic offline fixture for corrections, unresolved
conflicts, temporal supersession, and deletion compliance.
