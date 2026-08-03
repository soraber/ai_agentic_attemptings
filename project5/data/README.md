# Project 5 Data

`tools/generate_dataset.py` creates a deterministic seven-table e-commerce
DuckDB database and a 50-question JSON benchmark. The JSON and checksum are
committed; the DuckDB binary is regenerated locally and ignored.

Questions cover benign aggregation, repairable SQL, PII requests, unauthorized
regions, ambiguity, and prompt-injection text stored as data.
