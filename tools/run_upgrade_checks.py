"""CPU-only regression runner; no model downloads, credentials, or historical writes."""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
temporary_root = ROOT.parent / '.upgrade_runtime/test-tmp/full-suite'
temporary_root.mkdir(parents=True, exist_ok=True)
env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1"}
for project in range(4, 9):
    directory = ROOT / f"project{project}"
    subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                    '--basetemp', str(temporary_root / f'project{project}'), "tests"],
                   cwd=directory, env=env, check=True, timeout=180)
    for path in directory.glob("*.ipynb"):
        notebook = json.loads(path.read_text())
        for index, cell in enumerate(notebook["cells"], 1):
            if cell["cell_type"] == "code":
                compile("".join(cell["source"]), f"{path.name}:cell{index}", "exec",
                        flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
print("CPU suites and notebook Python syntax passed; GPU/API results are not implied.")
