#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from project4_agent.dataset import generate_incidents, write_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Project 4 benchmark")
    parser.add_argument("--seed", type=int, default=20260802)
    parser.add_argument(
        "--output", type=Path, default=Path("data/cache/project4_incidents.json")
    )
    parser.add_argument(
        "--force", action="store_true", help="replace an existing benchmark"
    )
    args = parser.parse_args()

    if args.output.exists() and not args.force:
        print(f"Reusing {args.output}; pass --force to regenerate it.")
        return

    path, checksum_path, checksum = write_dataset(args.output, args.seed)
    cases = generate_incidents(args.seed)
    split_counts = Counter(case.split for case in cases)
    service_counts = Counter(case.evidence.service.value for case in cases)
    print(f"Wrote {len(cases)} incidents to {path}")
    print(f"Splits: {dict(split_counts)}")
    print(f"Services: {dict(service_counts)}")
    print(f"SHA-256: {checksum}")
    print(f"Checksum file: {checksum_path}")


if __name__ == "__main__":
    main()
