<!-- toc -->

- [Enhanced Pytest Coverage for Subprocesses and Docker](#enhanced-pytest-coverage-for-subprocesses-and-docker)
  * [Overview](#overview)
  * [Problem & Solution](#problem--solution)
  * [Architecture](#architecture)
  * [Setup Guide](#setup-guide)
    + [Prerequisites](#prerequisites)
    + [Step 1: Configure Coverage for Parallel Execution](#step-1-configure-coverage-for-parallel-execution)
    + [Step 2: Install Coverage Hooks](#step-2-install-coverage-hooks)
    + [Step 3: Prepare Coverage Data Directory](#step-3-prepare-coverage-data-directory)
    + [Step 4: Update Docker Containers (if applicable)](#step-4-update-docker-containers-if-applicable)
    + [Step 5: Run Tests with Coverage](#step-5-run-tests-with-coverage)
    + [Step 6: Collect and Merge Coverage Data](#step-6-collect-and-merge-coverage-data)
    + [Step 7: View Coverage Report](#step-7-view-coverage-report)
  * [Configuration Reference](#configuration-reference)
    + [Key Configuration Options](#key-configuration-options)
    + [Environment Variables](#environment-variables)
  * [Hook Injection System](#hook-injection-system)
    + [Coverage Hook Installation](#coverage-hook-installation)
    + [Function Reference](#function-reference)
  * [Docker Integration](#docker-integration)
    + [Container Preparation](#container-preparation)
    + [Runtime Configuration](#runtime-configuration)
    + [Integration with hdocker](#integration-with-hdocker)
  * [Workflow Implementation](#workflow-implementation)
  * [Coverage Data Flow](#coverage-data-flow)
    + [File Naming Convention](#file-naming-convention)
    + [Data Collection Process](#data-collection-process)
  * [Key Benefits of the Approach](#key-benefits-of-the-approach)
  * [Design Principles](#design-principles)
  * [Common Usage Patterns](#common-usage-patterns)
    + [Simple Subprocess Test](#simple-subprocess-test)
    + [Docker Container Test](#docker-container-test)
  * [Troubleshooting](#troubleshooting)

<!-- tocstop -->

# Enhanced Pytest Coverage for Subprocesses and Docker

## Overview

- This guide **extends `pytest` coverage** to capture data from **Python
  subprocesses** and **Dockerized scripts**, normally excluded from coverage
  metrics.
- Uses **coverage hooks** and **parallel data collection** for **comprehensive
  test coverage reporting**.

## Problem & Solution

- **Problem**: Unit tests spawning **Python subprocesses** or **Docker
  containers** miss coverage data from child processes, leading to **incomplete
  metrics**.
- **Solution**:
  - **Automatically instrument** all Python processes using **coverage hooks**
    and **parallel data collection**.
  - **Merge results** into a unified report.

## Architecture

- Three main components:
  1. **Coverage Configuration**: Enhanced `.coveragerc` with **parallel mode**
     and **path mapping**.
  2. **Hook Injection**: Utility to install **coverage startup hooks** in Python
     environments.
  3. **Docker Integration**: Modified containers generate **coverage data** to
     **shared volumes**.

## Setup Guide

### Prerequisites

- **Python project** with **pytest tests**.
- **Docker** installed.
- **`coverage`, `pytest`, `pytest-cov`** packages.
- Access to modify **Docker containers**.

### Step 1: Configure Coverage for Parallel Execution

- Update `.coveragerc` in **project root**:

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

- Run:
  ```bash
  python -c "import hcoverage as hcovera; hcovera.inject()"
  ```

### Step 3: Prepare Coverage Data Directory

- Run:
  ```bash
  python3 -c "import hcoverage as hcovera; hcovera.coverage_subprocess_commands()"
  ```
- Or manually:
  ```bash
  mkdir -p coverage_data
  cp .coveragerc coverage_data/.coveragerc
  chmod 644 coverage_data/.coveragerc
  ```

### Step 4: Update Docker Containers (if applicable)

- Add to **Dockerfile**:
  ```dockerfile
  RUN pip install coverage pytest pytest-cov
  RUN mkdir -p /app/coverage_data && chmod 777 /app/coverage_data
  RUN python -c "
  import site, os
  pth_file = os.path.join(site.getsitepackages()[0], 'coverage.pth')
  with open(pth_file, 'w') as f:
      f.write('import coverage; coverage.process_startup()')
  "
  ```

### Step 5: Run Tests with Coverage

- Run:
  ```bash
  coverage run --parallel-mode -m pytest your_test_file.py
  ```

### Step 6: Collect and Merge Coverage Data

- Run:
  ```bash
  python3 -c "import hcoverage as hcovera; hcovera.combine_commands()"
  ```
- Or manually:
  ```bash
  cp coverage_data/.coverage.* . 2>/dev/null || true
  coverage combine
  coverage report
  coverage html
  ```

### Step 7: View Coverage Report

- Run:
  ```bash
  coverage report
  ```
- Open **HTML report**:
  ```bash
  open htmlcov/index.html  # macOS
  xdg-open htmlcov/index.html  # Linux
  ```

## Configuration Reference

### Key Configuration Options

- **`parallel = True`**: Enables separate **coverage files**.
- **`concurrency = multiprocessing`**: Handles **concurrent processes**.
- **`sigterm = True`**: Saves **coverage data** on termination.
- **`[paths]`**: Maps **container paths** to **host paths**.

### Environment Variables

- **`COVERAGE_PROCESS_START`**: Points to **.coveragerc**, set by **hook
  injection**.
- **`COVERAGE_FILE`**: Specifies **coverage data file**, set by **Docker
  integration**.

## Hook Injection System

### Coverage Hook Installation

- Places `coverage.pth` in **site-packages** with:
  ```python
  import coverage; coverage.process_startup()
  ```

### Function Reference

- **`hcoverage.inject()`**: Installs **hooks**, may raise `OSError` or
  `ImportError`.
- **`hcoverage.coverage_subprocess_commands()`**: Prepares **coverage data
  directory**.
- **`hcoverage.combine_commands()`**: Merges **coverage data**, generates
  **reports**.

## Docker Integration

### Container Preparation

- **Requirements**:
  - **Coverage tools**: `RUN pip install coverage pytest pytest-cov`.
  - **Shared directory**:
    `RUN mkdir -p /app/coverage_data && chmod 777 /app/coverage_data`.
  - **Coverage hook**: Installs `coverage.pth` in **site-packages**.

### Runtime Configuration

- **Volume mount**: `-v {host_coverage_dir}:/app/coverage_data`.
- **Environment variables**:
  - `-e COVERAGE_FILE=/app/coverage_data/.coverage`
  - `-e COVERAGE_PROCESS_START=/app/coverage_data/.coveragerc`.

### Integration with hdocker

- **`hdocker.build_base_cmd()`**: Adds **volume mounts** and **environment
  variables**.
- **`build_container_image()`**: Builds **Docker images** with **coverage
  support**.

## Workflow Implementation

- **Assumptions**:
  - Containers built with `hdocker.build_container_image()`.
  - Executables run with `hdocker.build_base_cmd()`.

- **Pre-Test Setup**:
  - Install **hooks**: `hcoverage.inject()`.
  - Prepare **directory**: `hcoverage.coverage_subprocess_commands()`.

- **Test Execution**:
  - Run: `coverage run --parallel-mode -m pytest`.
  - **Subprocesses** and **containers** auto-instrumented.

- **Data Collection and Merging**:
  - Copy: `cp coverage_data/.coverage.* .`.
  - Combine: `coverage combine`.
  - Report: `coverage report; coverage html`.

## Coverage Data Flow

### File Naming Convention

- **Main processes**: `.coverage.{hostname}.{pid}`.
- **Subprocesses**: `.coverage.{hostname}.{pid}`.
- **Containers**: `.coverage.{container_id}`.

### Data Collection Process

- **Generation**: Each **Python process** writes **coverage file**.
- **Collection**: Copies **container files** to **host**.
- **Merge**: Combines files into `.coverage`.

## Key Benefits of the Approach

- **Transparency**: No changes to **test code**.
- **Comprehensive Coverage**: Captures **main process**, **subprocesses**,
  **container scripts**.
- **Leverages Native Tools**: Uses **pytest-cov** for **subprocess support**.
- **Parallel Processing**: Supports **concurrent processes**.

## Design Principles

- **Explicit Configuration**: **Hooks** installed explicitly, errors **clear**.
- **Native Tool Support**: Leverages `pytest-cov` and `coverage`.
- **Consistent Environments**: Same **hooks** across **host** and
  **containers**.
- **Fail Fast**: Missing **tools** or **configs** trigger **immediate errors**.

## Common Usage Patterns

### Simple Subprocess Test

```python
def test_subprocess_script():
    result = subprocess.run([sys.executable, "my_script.py"], capture_output=True)
    assert result.returncode == 0
```

### Docker Container Test

```python
def test_docker_script():
    base_cmd = build_base_cmd(use_sudo=False)
    docker_cmd = base_cmd + ["my-image", "python", "script.py"]
    result = subprocess.run(docker_cmd, capture_output=True)
    assert result.returncode == 0
```

## Troubleshooting

- **Missing Coverage Data**: Check **hooks** with
  `python -c "import site; print(site.getsitepackages())"`.
- **Container Permissions**: Ensure **777 permissions** for **coverage
  directory**, **644** for `.coveragerc`.
- **Path Mapping Issues**: Verify `[paths]` maps **/app** to **.** in
  `.coveragerc`.
