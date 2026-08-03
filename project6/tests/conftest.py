from __future__ import annotations

import pytest


@pytest.fixture()
def buggy_repo(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (root / "test_public.py").write_text("from calc import add\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")
    (root / "test_hidden.py").write_text("from calc import add\n\ndef test_negative():\n    assert add(-2, -3) == -5\n", encoding="utf-8")
    return root
