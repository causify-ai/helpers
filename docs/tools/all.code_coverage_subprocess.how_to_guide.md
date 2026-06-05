<!-- toc -->

- [Enhanced Pytest Coverage for Subprocesses and Docker](#enhanced-pytest-coverage-for-subprocesses-and-docker)
  * [Overview](#overview)
  * [Quick Start](#quick-start)
  * [Manual Setup (Advanced)](#manual-setup-advanced)
    + [Prerequisites](#prerequisites)
    + [Step 1: Configure Coverage for Parallel Execution](#step-1-configure-coverage-for-parallel-execution)
    + [Step 2: Install Coverage Hooks](#step-2-install-coverage-hooks)
    + [Step 3: Prepare Coverage Data Directory](#step-3-prepare-coverage-data-directory)
    + [Step 4: Update Docker Containers (If Applicable)](#step-4-update-docker-containers-if-applicable)
    + [Step 5: Run Tests with Coverage](#step-5-run-tests-with-coverage)
    + [Step 6: Collect and Merge Coverage Data](#step-6-collect-and-merge-coverage-data)
    + [Step 7: View Coverage Report](#step-7-view-coverage-report)

<!-- tocstop -->

# Enhanced Pytest Coverage for Subprocesses and Docker

## Overview

This guide provides comprehensive test coverage for Python subprocesses and
Dockerized applications using coverage hooks and parallel data collection.

## Quick Start

For most use cases, use the automated invoke task:

```bash
# Run Coverage for Entire Project
invoke run_coverage_subprocess

# Run Coverage for Specific Directory
invoke run_coverage_subprocess --target-dir=dev_scripts_helpers/llms

# Generate HTML Report
invoke run_coverage_subprocess --generate-html-report
```

This task automatically:

- Installs coverage hooks
- Sets up subprocess environment
- Runs all tests with coverage tracking
- Combines coverage data from all processes
- Generates reports (text, XML, and optionally HTML)
- Cleans up hooks when finished

## Manual Setup (Advanced)

### Prerequisites

- Python project with pytest tests
- `coverage`, `pytest`, `pytest-cov` packages
- Docker installed (if testing containerized code)

### Step 1: Configure Coverage for Parallel Execution

Update `.coveragerc` in project root:

```ini
[run]
branch = True
parallel = True
concurrency = multiprocessing
sigterm = True

[paths]
source =
    .
    /app
```

### Step 2: Install Coverage Hooks

```bash
python -c "import helpers.hcoverage as hcovera; hcovera.inject()"
export COVERAGE_PROCESS_START=.coveragerc
```

### Step 3: Prepare Coverage Data Directory

```bash
python3 -c "import helpers.hcoverage as hcovera; hcovera.coverage_commands_subprocess()"
```

### Step 4: Update Docker Containers (If Applicable)

Containers built with `hdocker.build_container_image()` automatically include
coverage support.

For manual Docker setups, add to your Dockerfile:

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

### Step 5: Run Tests with Coverage

```bash
coverage run --parallel-mode -m pytest your_test_file.py
```

### Step 6: Collect and Merge Coverage Data

```bash
python3 -c "import helpers.hcoverage as hcovera; hcovera.coverage_combine()"
```

### Step 7: View Coverage Report

Generate text report:

```bash
coverage report
```

Generate HTML report:

```bash
coverage html
python3 -m http.server --directory htmlcov 8000
# Navigate to Http://Localhost:8000
```
