from project5_agent.semantic_scoring import value_equivalent


def test_value_metric_ignores_aliases_not_values_or_column_count():
    assert value_equivalent((['total_revenue'], [(120.0,)]), (['revenue'], [(120,)]))
    assert not value_equivalent((['total_revenue'], [(121,)]), (['revenue'], [(120,)]))
    assert not value_equivalent((['a', 'b'], []), (['a'], []))


def test_value_metric_preserves_duplicates_nulls_and_requested_order():
    left, right = (['a'], [(1,), (None,)]), (['b'], [(None,), (1,)])
    assert value_equivalent(left, right)
    assert not value_equivalent(left, right, ordered=True)
    assert not value_equivalent((['a'], [(1,), (1,)]), (['b'], [(1,), (2,)]))
    assert not value_equivalent((['a'], [(True,)]), (['b'], [(1,)]))


def test_unordered_numeric_matching_handles_overlapping_tolerances():
    assert value_equivalent((['a'], [(0.5e-6,), (0.0,)]), (['b'], [(0.0,), (1.4e-6,)]))
    assert not value_equivalent((['a'], [(float('nan'),)]), (['b'], [(float('nan'),)]))
