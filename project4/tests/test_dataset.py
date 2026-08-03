from __future__ import annotations

from collections import Counter

from project4_agent.dataset import dataset_sha256, generate_incidents


def test_benchmark_is_balanced_reproducible_and_split() -> None:
    first = generate_incidents(20260802)
    second = generate_incidents(20260802)
    assert len(first) == 24
    assert Counter(case.evidence.service.value for case in first) == {
        "gateway": 6,
        "checkout": 6,
        "payments": 6,
        "inventory": 6,
    }
    assert Counter(case.split for case in first) == {"development": 8, "test": 16}
    assert dataset_sha256(first) == dataset_sha256(second)


def test_public_view_excludes_hidden_evaluation_labels() -> None:
    public = generate_incidents()[0].public_view()
    assert "gold_root_cause" not in public
    assert "allowed_remediation" not in public
    assert "requires_escalation" not in public
    assert "force_action_failure" not in public
