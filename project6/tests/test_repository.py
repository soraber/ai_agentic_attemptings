from __future__ import annotations

from project6_agent.repository import build_repository_map, localize_trace


def test_ast_map_and_trace_localization(buggy_repo) -> None:
    symbols = build_repository_map(buggy_repo)
    assert any(item.path == "calc.py" and item.name == "add" for item in symbols)
    assert localize_trace("FAILED test_public.py:4 at calc.py:2") == [("test_public.py", 4), ("calc.py", 2)]
