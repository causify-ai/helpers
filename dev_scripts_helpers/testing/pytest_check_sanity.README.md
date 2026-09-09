# Pytest Source Sanity Checker

A passing pytest run can still omit tests. This tool compares an independent
Python source inventory with saved pytest collection and execution evidence.
It reports omitted definitions, collected cases without outcomes, skips with
available reasons, failures, and incomplete evidence.

The checker reads files without importing or executing the inspected source.
Run pytest separately in the environment intended for that project.

## Quick Start

Use the repository's Python 3.11 or newer environment. The optional structured
input adapter consumes reports from `pytest-json-report`; the checker itself
does not require that plugin.

```bash
python -m pytest --json-report --json-report-file=pytest-report.json
python -m dev_scripts_helpers.testing.pytest_check_sanity \
  --pytest_input pytest-report.json --code_input . --output sanity.json
```

Set `--code_input` to the report's pytest root directory. A different root is
rejected because it would make source-to-node comparisons misleading. Run the
checker from the helpers checkout with that checkout on Python's import path.

Existing terminal captures are also supported. Capture flat node IDs with
`--collect-only -q` and individual execution outcomes with `-vv --color=no`:

```bash
python -m pytest --collect-only -q --color=no > collected.log
python -m pytest -vv --color=no > executed.log
python -m dev_scripts_helpers.testing.pytest_check_sanity \
  --collection_input collected.log --pytest_input executed.log \
  --code_input . --pytest_cwd . --output sanity.txt --format text
```

Use the same checkout revision, selection options, environment, and root for
both captures. `--pytest_cwd` is the original pytest working directory; it
defaults to the checker's current directory. This matters because verbose
execution paths are relative to the working directory while flat collection
IDs are relative to pytest's root.

## Interpretation

For a run with three passing parameter cases, one skip, one deselection, and
one source test in a directory omitted by pytest, the summary is:

```text
Summary:
  deselected: 1
  not_collected: 1
  passed: 3
  skipped: 1
```

Each case includes its full node ID, source definition when resolved, source
line, outcome, reason, and whether execution of the call stage was observed.
Parameter IDs remain separate, including IDs containing spaces and brackets.

| Status | Meaning |
| --- | --- |
| `passed`, `failed`, `error` | Reported runtime outcome |
| `skipped` | Reported skip; reason retained when available |
| `xfailed`, `xpassed` | Reported expected-failure outcome |
| `deselected` | Explicitly removed from selection in structured evidence |
| `unexecuted` | Collected case without an execution outcome |
| `not_collected` | Source definition absent from a complete collection capture |
| `excluded` | Explicit source exclusion, such as `__test__ = False` |
| `collection_error` | Source affected by a reported collection failure |
| `unknown` | Incomplete collection or conditional source definition |

An unexecuted case is not automatically a skip. A missing log entry never
supplies a skip reason. Structured setup/call/teardown details are preferred
when skip explanations or lifecycle distinctions matter.

Reports also include `source_errors`, `source_uncertainties`,
`collection_errors`, `collection_complete`, and diagnostic warnings. Source
uncertainties identify imported inheritance, complex class resolution, or
potential dynamic module definitions. Observed runtime cases whose source
cannot be resolved have an empty `source` field.

## Configuration

The source scanner reads `python_files`, `python_classes`, and
`python_functions` from `pytest.ini`, `.pytest.ini`, `pyproject.toml`
(`[tool.pytest.ini_options]`), `tox.ini`, or `setup.cfg`. Use `--config` to
select a particular file. Defaults are pytest's conventional naming patterns.
Native pytest TOML configuration and runtime plugin changes to naming rules
are not interpreted; provide an INI configuration with the intended patterns.

Pytest's directory exclusions are deliberately not copied: the purpose is to
find tests hidden by `norecursedirs`, `testpaths`, ignore options, or selection.
Use repeated `--exclude` directory globs for intentional inventory exclusions:

```bash
python -m dev_scripts_helpers.testing.pytest_check_sanity \
  --pytest_input pytest-report.json --code_input . --output sanity.html \
  --format html --exclude 'vendor' --exclude '**/outcomes'
```

Git metadata, conventional virtual environments, and Python cache directories
are excluded by default. Directory symlinks are not followed. File names are
matched with glob patterns; class and function patterns use pytest's
prefix-or-glob convention. `unittest.TestCase` uses the `test` method prefix.

## CI Integration

The default policy fails on omitted, unexecuted, unknown, failed, errored, or
rerun cases. Incomplete collection and source uncertainties also fail the
default policy, even if every observed case passed or no cases were observed.
Skips, explicit exclusions, and deselections are visible but do not fail it.

Exit codes are `0` for a satisfied policy, `1` for a policy failure, and `2` for
source or collection errors. Invalid inputs fail rather than produce a passing
report. Customize policy with a comma-separated `--fail_on` value. Removing
`unknown` explicitly opts out of failing incomplete evidence.

Preserve pytest's own result as well as the checker's result:

```bash
set +e
python -m pytest --json-report --json-report-file=pytest-report.json
pytest_status=$?
python -m dev_scripts_helpers.testing.pytest_check_sanity \
  --pytest_input pytest-report.json --code_input . --output sanity.json
sanity_status=$?
test "$pytest_status" -eq 0 && test "$sanity_status" -eq 0
```

Upload the report as a CI artifact, including on failure. Review intentional
skips and exclusions rather than silently deleting omitted tests from inventory.

## Evidence Limits and Troubleshooting

- Use structured reports when possible. Quiet execution dots, verbose
  collection trees, custom terminal layouts, and interleaved xdist terminal
  output are not a supported complete inventory. Truncated or unsupported
  logs are reported as incomplete.
- `pytest-json-report` under xdist can omit successful collection records.
  Runtime outcomes remain useful, but do not establish collection completeness.
  Supply a separate matching serial collection capture when appropriate.
- A count alone cannot establish which cases were selected. Terminal logs
  with unnamed deselections remain incomplete. Structured reports can retain
  the individual deselected IDs.
- Conditional definitions are inventory candidates, not proof a condition
  evaluated true. Missing conditional definitions are `unknown`.
- The AST scanner resolves same-file simple inheritance. Imported bases,
  multiple inheritance, metaclasses, generated tests, plugin collection hooks,
  and arbitrary decorators may require project-specific runtime review. The
  checker does not claim to prove completeness of all executable Python.
- A separate collection file cannot prove two captures used identical source
  or options. Unexpected runtime IDs invalidate their combined completeness;
  use immutable CI artifacts from the same job to avoid stale captures.
- JSON and text output are deterministic. HTML is a standalone escaped text
  report, so test identifiers and failure text are never interpreted as markup.

## Tests and Architecture

```bash
python -m pytest helpers/test/test_hpytest_sanity.py \
  helpers/test/test_hpytest_sanity_inventory.py \
  dev_scripts_helpers/testing/test/test_pytest_check_sanity.py
```

The end-to-end test runs real pytest processes against a temporary project with
an omitted directory. Unit tests cover parameter IDs, collection failures,
conditional definitions, inheritance, incomplete evidence, and HTML escaping.
See the [architecture](pytest_check_sanity.architecture.md) for the component
boundaries and existing interfaces reused.
