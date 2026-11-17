"""Synchronize explicitly named generated cells without replacing a whole notebook."""
from __future__ import annotations

import argparse
import importlib.util
import hashlib
import json
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=int, choices=range(4, 9))
    parser.add_argument("cells", nargs="+")
    parser.add_argument("--expected-sha256", help="Reviewed current source hash, for one already-upgraded cell")
    parser.add_argument("--append", action="store_true", help="Append explicitly named new builder cells only")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    project = root / f"project{args.project}"
    spec = importlib.util.spec_from_file_location("notebook_builder", project / "tools/build_notebook.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    path = builder.OUTPUT
    notebook = json.loads(path.read_text())
    baseline = json.loads(subprocess.check_output(
        ["git", "show", f"HEAD:{path.relative_to(root).as_posix()}"], cwd=root))
    original = {cell["id"]: cell for cell in baseline["cells"]}
    replacements = {cell["id"]: cell for cell in builder.CELLS}
    requested = set(args.cells)
    actual = {cell["id"] for cell in notebook["cells"]}
    if args.append:
        if requested & (actual | original.keys()) or requested - replacements.keys():
            raise ValueError("Append accepts only new, explicitly named builder cell IDs")
        added = [cell for cell in builder.CELLS if cell["id"] in requested]
        notebook["cells"].extend(added)
        path.write_text(json.dumps(notebook, indent=1) + "\n")
        print(json.dumps({"notebook": path.name, "appended_cells": [
            {"position": len(notebook["cells"]) - len(added) + i + 1, "id": cell["id"]}
            for i, cell in enumerate(added)]}))
        return
    if requested - (actual & replacements.keys() & original.keys()):
        raise ValueError("Unknown cell ID")
    changed = []
    for position, cell in enumerate(notebook["cells"], 1):
        cell_id = cell["id"]
        if cell_id not in requested or cell["source"] == replacements[cell_id]["source"]:
            continue
        reviewed = (len(requested) == 1 and args.expected_sha256 ==
                    hashlib.sha256("".join(cell["source"]).encode()).hexdigest())
        if cell["source"] != original[cell_id]["source"] and not reviewed:
            raise RuntimeError(f"Preserving a locally edited cell: {cell_id}; merge it explicitly")
        cell["source"] = replacements[cell_id]["source"]
        cell["metadata"]["upgrade_version"] = "2026-11-16-v1"
        if cell["cell_type"] == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        changed.append({"position": position, "id": cell_id})
    if changed:
        path.write_text(json.dumps(notebook, indent=1) + "\n")
    print(json.dumps({"notebook": path.name, "changed_cells": changed}))


if __name__ == "__main__":
    main()
