"""Shared fail-closed notebook setup; never mutates the active interpreter."""
from importlib import metadata
from pathlib import Path
import sys


def validate(lock_path):
    if sys.prefix == sys.base_prefix or sys.version_info[:2] != (3, 11):
        raise RuntimeError('Select the isolated Python 3.11 notebook kernel described in SECURITY_UPGRADE.md')
    mismatches = []
    for line in Path(lock_path).read_text().splitlines():
        if not line or line[0].isspace() or line.startswith('#') or '==' not in line:
            continue
        name, version = line.rstrip(' \\').split('==', 1)
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            installed = 'missing'
        if installed != version:
            mismatches.append(f'{name}: {installed}, required {version}')
    if mismatches:
        raise RuntimeError('Isolated notebook lock mismatch; rebuild the kernel, not the shared runtime: '
                           + '; '.join(mismatches[:8]))


def source(project):
    return f'''from pathlib import Path
import os, runpy, sys
if sys.prefix == sys.base_prefix:
    raise RuntimeError("Use the isolated notebook kernel from SECURITY_UPGRADE.md; shared Colab packages are not modified")
candidates = [Path.cwd(), Path.cwd()/"project{project}", Path("/content/ai_agentic_attemptings/project{project}")]
PROJECT_ROOT = next((p.resolve() for p in candidates if (p/"src/project{project}_agent").is_dir()), None)
if PROJECT_ROOT is None:
    raise FileNotFoundError("Open this notebook from the cloned project directory")
check = runpy.run_path(str(PROJECT_ROOT.parent/"tools/notebook_environment.py"))["validate"]
check(PROJECT_ROOT.parent/"requirements-notebook-cpu.hashes.txt")
os.chdir(PROJECT_ROOT)
source_root = PROJECT_ROOT/"src"
if str(source_root) not in sys.path:
    sys.path.insert(0, str(source_root))
print("Isolated Project {project} CPU/API environment verified; GPU mode requires a separately approved GPU lock")
'''
