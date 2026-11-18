# Isolated Environments And Security Follow-Up

Updated: 2026-11-18. Historical runbooks and figures remain evidence of their
original runs; use these setup instructions for new CPU/API work.

## Select An Isolated Kernel

From this repository:

```sh
uv venv --python 3.11.17 .venv-notebook
uv pip install --python .venv-notebook/bin/python --require-hashes -r requirements-notebook-cpu.hashes.txt
uv pip check --python .venv-notebook/bin/python
```

In VS Code select `.venv-notebook/bin/python` as the notebook interpreter. All five
setup cells locate the checkout and validate package versions. They refuse a
shared/system interpreter, do not pip-install into it, and never automatically
pull a repository. The lock includes ipykernel, plotting, and report libraries.
All five setup cells passed in a clean macOS Python 3.11 venv. The GPU optional
steps are **not** installed by this CPU/API lock.

For the smaller regression environment:

```sh
uv venv --python 3.11.17 .venv-upgrade
uv pip install --python .venv-upgrade/bin/python --require-hashes -r requirements-upgrade-cpu.hashes.txt
uv pip check --python .venv-upgrade/bin/python
.venv-upgrade/bin/python tools/run_upgrade_checks.py
```

The regression suite also passed in a Linux ARM64 container without network
access: 144 CPU tests, with two Docker-only tests passing separately. This is not
an x86_64/Colab verification. Full notebook environment and
CPU locks had zero reported advisories in the 2026-11-17 pip-audit scan. The CI
workflow now uses hashes and audits the CPU lock; its new revision has not run
on GitHub. Dependency audits are not substitutes for application security tests.

## Project 6: Patched Sandbox

```sh
docker build -f project6/tools/Dockerfile.sandbox -t project6-test-runner:p0-20261117 project6/tools
PROJECT6_DOCKER_TESTS=1 PYTHONPATH=project6/src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-upgrade/bin/python -m pytest -q -p no:cacheprovider project6/tests/test_docker_integration.py
```

The new tag leaves the historical image unchanged. Its Python base is pinned by
digest and pytest dependencies by distribution hashes. Both real-container tests
passed: nonroot/read-only execution, no host secrets or network routes, resource
limits, timeout, and bounded output. The image ID and test evidence are stored in
`project6/output/runs/upgrade-v2/docker/`. This is not proof against container escapes.

## Project 7: Authenticated HTTP

See [HTTP_AUTH.md](project7/HTTP_AUTH.md) for the resource-server trust boundary,
configuration, and exact transport tests. Stdio remains a separate trusted-launch
mode. Production identity-provider login and TLS deployment are not claimed.

## GPU Status

Do not reuse the historical shared inference lock for Projects 5/8. Its new audit
contains model-library and transitive-dependency findings. The sibling repository
now has advisory-clean Transformers/PEFT training and LangGraph inference locks.
Project 5 and 8 validated the sibling repository's hash-locked inference stack
on MyPro. The launch cells stage the selected original notebook sources and
save the runs under their respective Project 5 and Project 8 Drive folders.

See [saved audit evidence](output/security/p0-20261117/audit_summary.json).

## New Run Provenance And Benchmarks

The main evaluation cells now use `tools/run_manifest.py` and write only fresh
`output/runs/upgrade-v2` runs. Source/data/config hashes, runtime/package metadata,
failure type, and timing are saved without collecting credentials or exception
messages. The latest Project 5 and 8 runs have saved per-case evidence in Drive.
Shared provenance for additional model and provider runs remains a separate check.

Project 6's [SWE-bench preparation](project6/BENCHMARKS.md) and Project 8's
[LongMemEval adapter](project8/BENCHMARKS.md) were checked against real pinned
public data. Prepared raw caches are ignored by git. Project 8's pilot results
are reported separately from official semantic scoring. Public evidence stays under each project's
`output/runs/upgrade-v2/` directory.

References: [pytest advisory](https://github.com/advisories/GHSA-6w46-j5rx-g56g),
[pip-audit](https://pypi.org/project/pip-audit/), and
[MCP authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization).
