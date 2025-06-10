<!-- toc -->

- [Enhanced Pytest Coverage for Subprocesses and Docker](#enhanced-pytest-coverage-for-subprocesses-and-docker)
  * [Overview](#overview)
  * [Problem & Solution](#problem--solution)
  * [Architecture](#architecture)
  * [Core Configuration](#core-configuration)
    + [Enhanced .coveragerc](#enhanced-coveragerc)
  * [Hook Injection System](#hook-injection-system)
    + [Coverage Hook Installation](#coverage-hook-installation)
  * [Docker Integration](#docker-integration)
    + [Container Preparation](#container-preparation)
    + [Runtime Configuration](#runtime-configuration)
  * [Workflow Implementation](#workflow-implementation)
  * [Key Benefits of the Approach](#key-benefits-of-the-approach)
  * [Design Principles](#design-principles)
  * [Common Usage Patterns](#common-usage-patterns)
    + [Simple Subprocess Test](#simple-subprocess-test)
    + [Docker Container Test](#docker-container-test)
    + [Coverage Data Flow](#coverage-data-flow)
  * [Troubleshooting](#troubleshooting)

<!-- tocstop -->

# Enhanced Pytest Coverage for Subprocesses and Docker

## Overview

- This guide extends `pytest` coverage to capture data from Python subprocesses
  and Dockerized scripts, which are normally excluded from coverage metrics.
- The implemented solution uses coverage hooks and parallel data collection to
  provide comprehensive test coverage reporting.

## Problem & Solution

- **Problem**: Unit tests spawning Python subprocesses or Docker containers
  don't capture coverage data from child processes, leading to incomplete
  coverage metrics.

- **Solution**:
  - Automatically instrument all Python processes (host and container) using
    coverage hooks and parallel data collection
  - Then merge all the coverage results into a unified report.

## Architecture

- The system consists of three main components:
  1. **Coverage Configuration**: Enhanced `.coveragerc` with parallel mode and
     path mapping
  2. **Hook Injection**: Utility to install coverage startup hooks in Python
     environments
  3. **Docker Integration**: Modified containers that generate coverage data to
     shared volumes

## Core Configuration

### Enhanced .coveragerc

- The coverage configuration enables parallel data collection and maps container
  paths to host paths:

  ```ini
  [run]
  branch = True
  # Allow multiple processes to write separate coverage files.
  parallel = True
  # Handle the style of concurrent Python processes.
  concurrency = multiprocessing
  # Ensure coverage data is saved on process termination.
  sigterm = True

  [paths]
  # "/app" in the container is the same as "." on the host.
  source =
      .
      /app
  ```

## Hook Injection System

### Coverage Hook Installation

- The hook injection utility installs a startup hook in Python's site-packages
  directory.

- How it works:
  - Places `coverage.pth` in site-packages with startup code
  - Every Python process automatically imports and starts coverage
  - Uses `COVERAGE_PROCESS_START` environment variable to find config
  - Works for both host subprocesses and container processes

## Docker Integration

### Container Preparation

- Containers are enhanced to include coverage tools and hooks by modifying the
  Dockerfile

  ```dockerfile
  # Install coverage tools at build time.
  RUN pip install coverage pytest pytest-cov

  # Create shared coverage directory.
  RUN mkdir -p /app/coverage_data && chmod 777 /app/coverage_data

  # Install coverage hook in container.
  RUN python -c "
  import site, os
  pth_file = os.path.join(site.getsitepackages()[0], 'coverage.pth')
  with open(pth_file, 'w') as f:
      f.write('import coverage; coverage.process_startup()')
  "
  ```

### Runtime Configuration

- When running containers, mount a shared volume and set environment variables
  integrated into `build_base_cmd` in `helpers.hdocker`:
  ```python
  docker_cmd = [
      "docker", "run", "--rm",
      "-v", f"{host_cov_dir}:/app/coverage_data",  # Mount shared volume
      "-e", f"COVERAGE_FILE=/app/coverage_data/.coverage",
      "-e", f"COVERAGE_PROCESS_START=/app/coverage_data/.coveragerc",
      # ... other options
  ]
  ```

## Workflow Implementation

- Assumptions:
  - Docker containers to be built using `hdocker.build_container_image()`
  - All executables to be run using `hdocker.build_base_cmd()`

- Pre-Test Setup

  ```bash
  # Install coverage hooks on host.
  > python -c "import hcoverage as hcovera; hcovera.inject()"

  # Prepare shared coverage directory.
  > mkdir -p coverage_data
  > cp .coveragerc coverage_data/.coveragerc
  > chmod 644 coverage_data/.coveragerc

  # Or run function.
  > python3 -c "import hcoverage as hcovera; hcovera.coverage_subprocess_commands();"
  ```

- Test Execution

  ```bash
  # Run pytest with subprocesses and containers automatically instrumented.
  > coverage run --parallel-mode -m pytest /dev_script_helpers/llms/test/test_llm_transform.py
  ```

- **What happens automatically**:
  - Host subprocesses: Instrumented via pytest-cov's built-in support + hooks
  - Docker containers: Generate coverage data to mounted volume
  - All processes write separate `.coverage.*` files

- Data Collection and Merging

  ```bash
  # Copy container coverage data to host
  > cp coverage_data/.coverage.* . 2>/dev/null || true

  # Combine all coverage files
  > coverage combine

  # Generate final report
  > coverage report
  > coverage html  # Optional HTML report

  # Or run in function
  > python3 -c "import hcoverage as hcovera; hcovera.combine_commands()"
  ```

## Key Benefits of the Approach

- **Transparency**: No changes needed to existing test code - coverage is
  automatically captured from all Python processes.

- **Comprehensive Coverage**: Captures execution in:
  - Main test process
  - Host subprocesses spawned by tests
  - Python scripts running in Docker containers

- **Leverages Native Tools**: Uses pytest-cov's existing subprocess support
  rather than custom instrumentation.

- **Parallel Processing**: Multiple processes can run simultaneously without
  coverage conflicts.

## Design Principles

1. **Explicit Configuration**: Coverage hooks are explicitly installed, missing
   components cause clear errors
2. **Native Tool Support**: Leverages `pytest-cov` and `coverage` built-in
   capabilities
3. **Consistent Environments**: Same hooks and configuration across host and
   containers
4. **Fail Fast**: Missing coverage tools or configs trigger immediate, clear
   errors

## Common Usage Patterns

### Simple Subprocess Test

```python
def test_subprocess_script():
    # This subprocess will automatically be instrumented
    result = subprocess.run([sys.executable, "my_script.py"], capture_output=True)
    assert result.returncode == 0
```

### Docker Container Test

```python
def test_docker_script():
    # Build base Docker command with coverage support
    base_cmd = build_base_cmd(use_sudo=False)
    # base_cmd includes volume mounts and environment variables for coverage

    # Add specific container and script execution
    docker_cmd = base_cmd + ["my-image", "python", "script.py"]
    result = subprocess.run(docker_cmd, capture_output=True)
    assert result.returncode == 0
    # Container automatically generates coverage data to shared volume
```

### Coverage Data Flow

1. **Host Process**: Writes `.coverage.host-pid`
2. **Subprocess**: Writes `.coverage.subprocess-pid`
3. **Container**: Writes `.coverage.container-id` to mounted volume
4. **Merge Step**: `coverage combine` merges all files into unified report

## Troubleshooting

- **Missing Coverage Data**: Check that hooks are installed and
  `COVERAGE_PROCESS_START` environment variable is set correctly.

- **Container Permissions**: Ensure coverage data directory has appropriate
  permissions (777) for container write access and .coveragerc in host to be
  written with permissions(644).

- **Path Mapping Issues**: Verify `[paths]` section in `.coveragerc` correctly
  maps container paths (e.g., `/app`) to host paths (e.g., `.`).
