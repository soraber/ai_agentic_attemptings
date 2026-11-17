import pytest
from project6_agent.patching import RepairWorkspace


def test_workspace_cannot_contain_source(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    sentinel = source / "valuable.py"
    sentinel.write_text("keep = True\n")
    with pytest.raises(PermissionError):
        RepairWorkspace(source, tmp_path)
    assert sentinel.read_text() == "keep = True\n"
