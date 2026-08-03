#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from project5_agent.dataset import build_database, generate_benchmark, write_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=Path("data/cache/project5_ecommerce.duckdb"))
    parser.add_argument("--benchmark", type=Path, default=Path("data/cache/project5_questions.json"))
    parser.add_argument("--seed", type=int, default=20260802)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.force or not args.database.exists():
        build_database(args.database, args.seed)
    if args.force or not args.benchmark.exists() or not args.benchmark.with_suffix(".sha256").exists():
        cases = generate_benchmark(args.database, args.seed)
        checksum = write_benchmark(args.benchmark, cases)
        print(f"Wrote {len(cases)} questions; SHA-256 {checksum}")
        print("Categories:", dict(Counter(case.category for case in cases)))
    else:
        print("Reusing committed benchmark and local DuckDB cache.")


if __name__ == "__main__":
    main()
