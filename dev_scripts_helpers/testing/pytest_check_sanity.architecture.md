# Pytest Sanity Architecture

The implementation separates source discovery from runtime observation so
pytest's own collection exclusions cannot erase the independent inventory.

1. `helpers.hpytest_sanity_inventory` scans matching files with Python's AST
   parser. It records definitions, source exclusions, conditional definitions,
   parse errors, and unresolved dynamic constructs. It never imports the code.
2. `helpers.hpytest_sanity` reads structured `pytest-json-report` objects or
   saved flat collection and verbose execution logs into `PytestEvidence`.
   Collection completeness is separate from runtime outcomes.
3. The same module merges matching captures and reconciles full parameterized
   node IDs with source definitions. It emits sorted rows and status counts.
4. `dev_scripts_helpers.testing.pytest_check_sanity` reads naming configuration,
   selects adapters, renders JSON/text/escaped HTML, and applies the CI policy.

This uses functions and data records rather than an orchestration class with
one method per phase. Inputs are explicit and testable independently.

## Existing Interfaces

The repository's `pytest_marks.py` and `helpers.hpytest` provide mark
collection and log analysis. `pytest_count_files.sh` supplies counts. These
utilities do not independently inventory tests in directories pytest ignores.
Their APIs remain unchanged.

The structured adapter reuses the public report format of
[pytest-json-report](https://github.com/numirias/pytest-json-report), including
collector result nodes, deselection flags, and setup/call/teardown reports.
This avoids introducing a plugin that alters the test run. The separate
collection capture uses pytest's existing `--collect-only -q` output.

## Conservative Reconciliation

Full parameter IDs remain the runtime identity; only the callable's parameter
suffix is removed for source matching. A complete capture needs individual
collected IDs matching the reported count and no collection errors. Runtime
outcomes alone cannot prove an absent source test was omitted.

Separate captures must share their root. Merging retains collected cases with
no outcome and rejects completeness when runtime cases are absent from the
collection capture. It does not infer skip or deselection from missing output.

The scanner's static limits are explicit. Source errors and uncertainties are
reported independently of successful observed cases. The default CI policy
fails uncertainty, and callers can deliberately choose a weaker policy.

## Performance

Directory traversal and parsing are proportional to source size. Reconciliation
uses dictionaries keyed by node ID; final sorting costs approximately
`O(n log n)` for `n` reported cases. Evidence and inventory are kept in memory.
Use inventory exclusions for generated outcomes, vendored trees, and large
non-project fixtures. Repository collection itself is not performed by this
command, so importing a large test suite cannot slow the source-only scan.
