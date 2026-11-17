"""Summarize an actual opt-in pytest run without exporting local filesystem paths."""
import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--junit", type=Path, required=True)
args = parser.parse_args()
tree = ET.parse(args.junit)
cases = list(tree.iter("testcase"))
if len(cases) != 2 or any(list(case) for case in cases):
    raise RuntimeError("Expected two passing real-container test cases without skips or failures")
image = json.loads(subprocess.check_output(["docker", "image", "inspect", "project6-test-runner:upgrade-v1"], text=True))[0]
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
out = ROOT / "output/runs/upgrade-v1/docker" / stamp
out.mkdir(parents=True, exist_ok=False)
evidence = {"generated_at_utc": stamp, "tests_passed": len(cases),
    "tests": [{"name": c.attrib["name"], "seconds": float(c.attrib["time"])} for c in cases],
    "image_id": image["Id"], "architecture": image["Architecture"], "os": image["Os"],
    "junit_sha256": hashlib.sha256(args.junit.read_bytes()).hexdigest(),
    "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [ROOT / "tests/test_docker_integration.py", ROOT / "src/project6_agent/runner.py", ROOT / "tools/Dockerfile.sandbox"]},
    "scope": "real no-network/read-only/nonroot/secret-isolation/resource/timeout/output checks; not proof against container escapes"}
(out / "sandbox_validation.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(out.relative_to(ROOT).as_posix())
