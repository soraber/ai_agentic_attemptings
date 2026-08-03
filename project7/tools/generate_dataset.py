#!/usr/bin/env python3
from pathlib import Path
from project7_agent.dataset import generate_cases,write_cases

path=Path("data/cache/project7_cases.json")
if path.exists() and path.with_suffix(".sha256").exists(): print("Reusing committed Project 7 benchmark.")
else: print(f"Wrote {len(generate_cases())} cases; SHA-256 {write_cases(path)}")
