# Project 6 Background: Test-Driven Code Repair

## Repository Understanding

Coding agents need a compact map of symbols, imports, docstrings, tests, and call
relationships. Python's `ast` module provides this structure without executing
repository code.

## Fault Localization

Failing-test traces provide file, line, assertion, and exception evidence. A
repair loop should inspect the smallest relevant region first and avoid loading an
entire repository into the model context.

## Constrained Patches

Unified diffs are auditable and compatible with `git apply --check`. Policy must
validate target paths, changed-line count, file type, and patch syntax before any
write occurs. A small patch budget discourages unrelated rewrites.

## Test-Driven Iteration

The advanced loop performs:

```text
plan -> inspect -> patch -> public tests -> hidden tests -> accept
                            |                |
                            +-> summarize -> retry or rollback
```

Hidden tests matter because a patch may overfit the visible assertion. Each case
starts from a clean copy to prevent contamination.

## Local GPU Planning

The A100 comparison loads one Qwen2.5-Coder 7B model in BF16 and reuses it for all
bugs and attempts. Reuse separates model-load time from repair latency and avoids
wasting GPU memory on duplicate model instances. The local model receives the same
source, sanitized public-test failure, relative allowlist path, and changed-line
budget as the API planner. Its JSON response is converted into a typed patch
proposal before the existing deterministic controls run.

Local inference changes where generation happens, not the trust boundary. A model
cannot accept its own patch, see hidden-test details, expand its path allowlist, or
disable rollback.

## Metrics

- Pass@1 and verified repair within three attempts.
- Public and hidden test pass rates.
- Patch validity and changed-line count.
- Regression, overfitting, and rollback correctness.
- Latency, calls, tokens, and cost per verified repair.

## Limitations

QuixBugs functions are small and do not represent dependency-heavy repositories,
large builds, flaky tests, or cross-service changes. Subprocess limits are useful
containment, not a hardened untrusted-code sandbox.

## Primary References

- [QuixBugs](https://github.com/jkoppel/QuixBugs)
- [Python AST](https://docs.python.org/3/library/ast.html)
- [git apply](https://git-scm.com/docs/git-apply)
- [pytest](https://docs.pytest.org/)
- [Qwen2.5-Coder 7B Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)
