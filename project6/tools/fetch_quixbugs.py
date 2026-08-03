#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path | None = None) -> str:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/quixbugs_manifest.json")
    parser.add_argument("--destination", type=Path, default=ROOT / "data/cache/QuixBugs")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if not (args.destination / ".git").exists():
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", manifest["repository"], str(args.destination)])
    run(["git", "checkout", "--detach", manifest["commit"]], cwd=args.destination)
    actual = run(["git", "rev-parse", "HEAD"], cwd=args.destination)
    if actual != manifest["commit"]:
        raise SystemExit(f"QuixBugs commit mismatch: {actual}")
    missing = []
    for case in manifest["cases"]:
        for key in ("source", "public_test"):
            if not (args.destination / case[key]).exists():
                missing.append(case[key])
    if missing:
        raise SystemExit("Missing pinned paths: " + ", ".join(missing))
    print(f"QuixBugs ready at {actual}; {len(manifest['cases'])} cases verified")


if __name__ == "__main__":
    main()
