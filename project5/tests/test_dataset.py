from __future__ import annotations

from collections import Counter


def test_benchmark_has_fixed_size_categories_and_split(project5_data) -> None:
    _, cases = project5_data
    assert len(cases) == 50
    assert Counter(case.category for case in cases) == {
        "benign": 25,
        "repair": 5,
        "pii": 5,
        "unauthorized": 5,
        "ambiguous": 5,
        "injection": 5,
    }
    assert Counter(case.split for case in cases) == {"development": 10, "test": 40}


def test_public_view_hides_sql_and_result_labels(project5_data) -> None:
    public = project5_data[1][0].public_view()
    assert set(public) == {"question_id", "question", "authorized_regions"}
