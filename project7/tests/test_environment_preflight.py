import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('environment', Path(__file__).parents[2]/'tools/notebook_environment.py')
environment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(environment)


def test_notebook_environment_rejects_shared_interpreter(monkeypatch, tmp_path):
    monkeypatch.setattr(environment.sys, 'prefix', environment.sys.base_prefix)
    with pytest.raises(RuntimeError, match='isolated'):
        environment.validate(tmp_path/'unused')


def test_notebook_environment_detects_lock_mismatch(monkeypatch, tmp_path):
    monkeypatch.setattr(environment.sys, 'prefix', str(tmp_path/'venv'))
    lock = tmp_path/'requirements.txt'
    lock.write_text('pydantic==0.0.0\n')
    with pytest.raises(RuntimeError, match='lock mismatch'):
        environment.validate(lock)
