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
RUN pip install --no-cache-dir coverage pytest pytest-cov

# Create Coverage Data Directory with Proper Permissions.
RUN mkdir -p /app/coverage_data && chmod 777 /app/coverage_data

# Setup Coverage Configuration.
COPY .coveragerc /app/coverage_data/.coveragerc
ENV COVERAGE_PROCESS_START=/app/coverage_data/.coveragerc

# Create Coverage.Pth File for Automatic Startup.
# This Ensures Coverage Tracking Starts Automatically When Python Runs.
RUN python - <<PYCODE
import site, os
site_dir = site.getsitepackages()[0]
pth_file = os.path.join(site_dir, 'coverage.pth')
with open(pth_file, 'w') as f:
    f.write('import coverage; coverage.process_startup()')
PYCODE
```

## Troubleshooting

- Missing Coverage Data: Check hooks with
  `python -c "import site; print(site.getsitepackages())"`.
- Container Permissions: Ensure 777 permissions for coverage directory, 644 for
  `.coveragerc`.
- Path Mapping Issues: Verify `[paths]` maps `/app` to `.` in `.coveragerc`.
