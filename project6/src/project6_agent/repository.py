from __future__ import annotations

import ast
import re
from pathlib import Path

from .schemas import RepositorySymbol


def build_repository_map(root: str | Path) -> list[RepositorySymbol]:
    root = Path(root)
    symbols: list[RepositorySymbol] = []
    for path in sorted(root.rglob("*.py")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.append(
                    RepositorySymbol(
                        path=path.relative_to(root).as_posix(),
                        name=node.name,
                        kind="class" if isinstance(node, ast.ClassDef) else "function",
                        line=node.lineno,
                        imports=sorted(set(imports)),
                        docstring=ast.get_docstring(node),
                    )
                )
    return symbols


def localize_trace(output: str) -> list[tuple[str, int]]:
    matches = re.findall(r"([A-Za-z0-9_./-]+\.py):(\d+)", output)
    seen: set[tuple[str, int]] = set()
    locations = []
    for path, line in matches:
        item = (path, int(line))
        if item not in seen:
            seen.add(item)
            locations.append(item)
    return locations
