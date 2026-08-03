from __future__ import annotations

import pytest

from project5_agent.dataset import build_database, generate_benchmark


@pytest.fixture()
def project5_data(tmp_path):
    database = build_database(tmp_path / "ecommerce.duckdb")
    return database, generate_benchmark(database)
