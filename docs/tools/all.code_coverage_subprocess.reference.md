<!-- toc -->

- [Configuration Reference](#configuration-reference)
  * [Key Configuration Options](#key-configuration-options)
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
  * [Troubleshooting](#troubleshooting)

<!-- tocstop -->

# Configuration Reference

- This section provides detailed technical specifications for configurations,
  functions, and tools used to extend pytest coverage to Python subprocesses and
  Dockerized applications.

## Key Configuration Options

- The configuration options are:
  - `parallel = True`: Enables separate coverage files.
  - `concurrency = multiprocessing`: Handles concurrent processes.
  - `sigterm = True`: Saves coverage data on termination.
  - `[paths]`: Maps container paths to host paths.

- The relevant environment variables are:
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

- **`hdocker.get_docker_base_cmd`**: Adds **volume mounts** and **environment
  variables**.
- **`hdocker.build_container_image()`**: Builds **Docker images** with
  **coverage support**.

## Workflow Implementation

- **Assumptions**:
  - Containers built with `hdocker.build_container_image()`.
  - Executables run with `hdocker.get_docker_base_cmd`.

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

## Troubleshooting

- **Missing Coverage Data**: Check **hooks** with
  `python -c "import site; print(site.getsitepackages())"`.
- **Container Permissions**: Ensure **777 permissions** for **coverage
  directory**, **644** for `.coveragerc`.
- **Path Mapping Issues**: Verify `[paths]` maps **/app** to **.** in
  `.coveragerc`.
