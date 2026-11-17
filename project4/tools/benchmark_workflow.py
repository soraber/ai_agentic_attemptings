"""Save CPU-only workflow load evidence in a fresh versioned output directory."""
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from project4_agent.load_test import run_load_test

if __name__ == "__main__":
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "output/runs/upgrade-v1/load" / stamp
    source_hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted((ROOT / "src").rglob("*.py"))}
    summary = run_load_test(output)
    (output / "run_manifest.json").write_text(json.dumps({"generated_at_utc": stamp,
        "python": platform.python_version(), "machine": platform.machine(), "os": platform.system(),
        "source_sha256": source_hashes, "model_calls": 0}, indent=2) + "\n")
    print(json.dumps({"output": output.relative_to(ROOT).as_posix(), "runs": [
        {key: value for key, value in row.items() if key != "node_timing"} for row in summary["concurrency_runs"]]}))
