"""Value-equivalence checks on the fixed fixture, separate from strict result hashes."""
from __future__ import annotations

import math
from decimal import Decimal

import sqlglot

from .execution import query_snapshot, restricted_snapshot


def _cell_equal(left, right):
    if left is None or right is None:
        return left is right
    numeric = (int, float, Decimal)
    if not isinstance(left, bool) and not isinstance(right, bool) and isinstance(left, numeric) and isinstance(right, numeric):
        if isinstance(left, int) and isinstance(right, int):
            return left == right
        return (math.isfinite(float(left)) and math.isfinite(float(right))
                and math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-6))
    return type(left) is type(right) and left == right


def value_equivalent(actual, expected, ordered=False):
    actual_columns, actual_rows = actual
    expected_columns, expected_rows = expected
    if len(actual_columns) != len(expected_columns) or len(actual_rows) != len(expected_rows):
        return False
    def equal_row(left, right):
        return len(left) == len(right) and all(_cell_equal(a, b) for a, b in zip(left, right))
    if ordered:
        return all(equal_row(a, b) for a, b in zip(actual_rows, expected_rows))
    # Bipartite matching retains duplicates and handles overlapping numeric tolerances.
    neighbors = [[j for j, expected_row in enumerate(expected_rows) if equal_row(row, expected_row)]
                 for row in actual_rows]
    matched = {}
    def assign(index, seen):
        for candidate in neighbors[index]:
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate not in matched or assign(matched[candidate], seen):
                matched[candidate] = index
                return True
        return False
    return all(assign(index, set()) for index in range(len(actual_rows)))


def grade_saved_queries(rows, cases, database_path):
    by_id = {case.question_id: case for case in cases}
    results = []
    for original in rows:
        row = dict(original)
        case = by_id[row['question_id']]
        row.update(value_result_correct=None, value_evaluation_error=None)
        if case.should_execute:
            row['value_result_correct'] = False
            if row['executed']:
                try:
                    with restricted_snapshot(database_path, case.authorized_regions) as (connection, _):
                        expected = query_snapshot(connection, case.gold_sql, 100, 5)
                        actual = query_snapshot(connection, row['sql'], 100, 5)
                    ordered = sqlglot.parse_one(case.gold_sql, read='duckdb').args.get('order') is not None
                    row['value_result_correct'] = value_equivalent(actual, expected, ordered)
                except Exception as exc:
                    row.update(value_result_correct=None, value_evaluation_error=type(exc).__name__)
        results.append(row)
    return results
