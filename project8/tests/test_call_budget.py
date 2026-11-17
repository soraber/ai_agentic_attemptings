import pytest

from project8_agent.config import Project8Config
from project8_agent.locomo import CachedLocalAnswerer


def test_local_call_cap_counts_failed_generation(tmp_path):
    class BrokenBackend:
        def generate(self, *args):
            raise ValueError("bad model response")

    answerer = CachedLocalAnswerer(Project8Config(max_model_calls=1), tmp_path / "cache.json", BrokenBackend())
    with pytest.raises(ValueError):
        answerer.answer("s", "q", "episodic", [])
    with pytest.raises(RuntimeError, match="budget"):
        answerer.answer("s", "q", "episodic", [])
    assert answerer.usage_summary()["model_calls"] == 1
