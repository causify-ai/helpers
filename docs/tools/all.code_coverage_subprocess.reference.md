<!-- toc -->

- [Coverage Subprocess Reference](#coverage-subprocess-reference)
  * [Invoke Task](#invoke-task)
  * [Configuration Options](#configuration-options)
  * [Function Reference](#function-reference)
  * [Docker Integration](#docker-integration)
  * [Troubleshooting](#troubleshooting)

<!-- tocstop -->

# Coverage Subprocess Reference

## Invoke Task

```bash
invoke run_coverage_subprocess [--target-dir=DIR] [--generate-html-report]
```

Parameters:

- `target_dir`: Directory to measure coverage (default: ".")
- `generate_html_report`: Generate HTML coverage report (default: False)

## Configuration Options

Required in `.coveragerc`:

```ini
[run]
parallel = True              # Enables separate coverage files
concurrency = multiprocessing # Handles concurrent processes
sigterm = True               # Saves coverage data on termination

[paths]
source =
    .                        # Host path
    /app                     # Container path
```

Environment variables:

- `COVERAGE_PROCESS_START`: Points to `.coveragerc`
- `COVERAGE_FILE`: Specifies coverage data file location

## Function Reference

`hcoverage` module functions:

- `inject()`: Installs coverage hooks in site-packages
- `remove()`: Removes coverage hooks
- `coverage_commands_subprocess()`: Prepares coverage data directory
- `coverage_combine()`: Merges coverage data and generates reports

## Docker Integration

Containers built with `hdocker.build_container_image()` automatically include:

- Coverage tools installation
- Coverage data directory setup
- Hook installation
- Runtime environment variables

Manual Docker setup requires:

```dockerfile
RUN pip install coverage pytest pytest-cov
RUN mkdir -p /app/coverage_data && chmod 777 /app/coverage_data
# Install Coverage Hook in Site-Packages
```

## Troubleshooting

- Missing Coverage Data: Check hooks with
  `python -c "import site; print(site.getsitepackages())"`.
- Container Permissions: Ensure 777 permissions for coverage directory, 644 for
  `.coveragerc`.
- Path Mapping Issues: Verify `[paths]` maps `/app` to `.` in `.coveragerc`.
