<!-- toc -->

- [Code Coverage for Subprocesses](#code-coverage-for-subprocesses)
  * [Summary](#summary)
  * [Goal](#goal)
  * [System Architecture](#system-architecture)
    + [Core Orchestration](#core-orchestration)
    + [Coverage Management](#coverage-management)
    + [Automatic Activation](#automatic-activation)
    + [Docker Integration](#docker-integration)
    + [Data Flow](#data-flow)
  * [The Fundamental Challenge](#the-fundamental-challenge)
    + [Process Isolation Gaps](#process-isolation-gaps)
    + [Container Execution Isolation](#container-execution-isolation)
    + [Why Standard Tools Fail](#why-standard-tools-fail)
  * [Solution Components](#solution-components)
    + [Hook Installation System](#hook-installation-system)
    + [Parallel Data Collection](#parallel-data-collection)
    + [Docker Integration Strategy](#docker-integration-strategy)
    + [Data Aggregation Phase](#data-aggregation-phase)
  * [Dependencies](#dependencies)
    + [Coverage Hook System](#coverage-hook-system)
    + [Docker-First Architecture](#docker-first-architecture)
    + [Parallel Coverage Collection](#parallel-coverage-collection)
  * [Integration with Testing Workflow](#integration-with-testing-workflow)
    + [Traditional Limitation](#traditional-limitation)
    + [Enhanced Approach](#enhanced-approach)
    + [Workflow Automation](#workflow-automation)
  * [Resources](#resources)

<!-- tocstop -->

# Code Coverage for Subprocesses

## Summary

- Explains why standard coverage tools fail with subprocesses and Docker
  containers
- Describes the hook-based solution that automatically tracks coverage across
  all Python processes
- Details design trade-offs and Docker-first architecture decisions
- Shows business impact of comprehensive subprocess coverage measurement

## Goal

- Capture complete code coverage metrics across all Python processes spawned by
  an application:
  - System calls via `subprocess.run()`, `os.system()`, etc.
  - Docker containerized executables
  - Multiprocessing workers
  - Any Python interpreter launched as a child process
- Requirements:
  - Zero configuration changes to existing test code
  - Automatic coverage tracking in all Python environments
  - Consolidated reporting from all processes
  - Docker-native support without manual container configuration

## System Architecture

The subprocess coverage system consists of four main components working together
to provide comprehensive coverage tracking:

### Core Orchestration

The `run_coverage_subprocess` invoke task serves as the central coordinator. It
executes a complete lifecycle: installs coverage hooks, runs tests with parallel
coverage enabled, merges coverage data from all processes, and performs cleanup.

### Coverage Management

The `hcoverage.py` module manages the technical details of hook installation and
data collection. It handles installing and removing coverage hooks in Python's
site-packages directory and configures the environment for automatic coverage
activation.

### Automatic Activation

The `coverage.pth` file acts as the automatic activation mechanism. When
installed in site-packages, every Python interpreter startup automatically
executes this hook, enabling coverage tracking without any code changes in the
target application.

### Docker Integration

The `hdocker` integration bakes coverage support directly into container images
at build time. This ensures that containerized Python code automatically
includes coverage tools and proper configuration.

### Data Flow

When a developer executes the invoke task, it installs hooks and configures the
environment. As tests run, every Python process (including subprocesses and
containers) automatically activates coverage tracking through the installed
hooks. Each process writes coverage data to uniquely named files to avoid
conflicts. Finally, the invoke task merges all coverage data files and generates
consolidated reports.

## The Fundamental Challenge

Standard coverage tools operate under a single-process assumption: they can only
track code execution within the Python interpreter where coverage was initially
started. This creates blind spots in modern Python applications.

### Process Isolation Gaps

When Python code spawns separate processes, coverage tracking stops:

```python
# Main_Process.Py (Coverage Visible).
def orchestrate_pipeline():
    input_files = discover_files()  # Tracked.

    # Spawns separate Python interpreter.
    subprocess.run(['python', 'processor.py', '--batch-size', '1000'])  # Lost.

    validate_results()  # Tracked again.

# Processor.Py (Invisible to Coverage).
def process_batch(batch_size):  # Not tracked.
    transform_data()  # Missing from coverage.
    save_results()   # Missing from coverage.
```

### Container Execution Isolation

Docker containers create complete isolation from host coverage:

```python
def run_analysis():
    prepare_data()  # Host coverage sees this.

    subprocess.run([
        'docker', 'run', '--rm',
        'analysis-container',
        'python', '/app/analyze.py'
    ])  # Container code isolated from host coverage.

    process_results()  # Host coverage sees this.
```

### Why Standard Tools Fail

Coverage tools like `coverage.py` and `pytest-cov` assume:

- Single process model: All execution happens in the initiating process
- Import-time instrumentation: Modules get instrumented when imported in main
  process
- Shared memory: Coverage data stored in process memory accessible to main
  thread

These assumptions break when processes are isolated.

## Solution Components

### Hook Installation System

- Uses Python site-packages `.pth` file installation rather than environment
  variables
- Every Python interpreter automatically processes `.pth` files during startup
- Provides automatic activation without user intervention across all
  environments
- Requires filesystem modification but ensures consistent coverage tracking
- Eliminates deployment configuration errors
- Implementation: `coverage.pth` contains startup code that initializes coverage
  tracking
- Works across all environments without code changes

### Parallel Data Collection

- Uses individual coverage files per process rather than shared database
- Each process writes coverage data to uniquely named files (process ID and
  timestamp)
- Avoids inter-process synchronization complexity entirely
- Requires post-processing aggregation step but scales linearly with process
  count
- Works across container boundaries without performance bottlenecks
- Handles process crashes gracefully with partial data recovery

### Docker Integration Strategy

- Bakes coverage support into container images at build time through
  `hdocker.build_container_image()`
- Uses build-time integration rather than runtime volume mounting
- Increases container image size slightly but provides zero user configuration
- Ensures consistent deployment behavior across all container orchestration
  systems
- Eliminates runtime configuration errors and environment setup issues

### Data Aggregation Phase

- Performs post-execution merging of all parallel coverage files
- Uses `coverage combine` with path mapping configuration
- Defers complexity to single aggregation step
- Handles host-to-container path translation automatically
- Produces standard coverage reports compatible with existing tooling
- Enables historical coverage tracking and trend analysis

## Dependencies

### Coverage Hook System

- Input: Python site-packages directory write access
- Output: Automatic coverage activation in all Python processes
- Docker integration: Containers built with `hdocker.build_container_image()`
  include coverage support automatically
- Limitation: Manual Docker setups require explicit configuration
- Handles cross-platform installation and cleanup

### Docker-First Architecture

- Core assumption: Production containers use `hdocker.build_container_image()`
- Rationale: Modern applications are increasingly containerized and manual
  configuration introduces inconsistency
- Integration includes: Coverage tools, hook setup, environment variables,
  shared volumes

### Parallel Coverage Collection

- Storage: Individual `.coverage.*` files per process
- Aggregation: `coverage combine` with path mapping
- Cleanup: Automatic removal of individual files after merging

## Integration with Testing Workflow

### Traditional Limitation

```bash
pytest --cov=mymodule  # Misses subprocess and container code.
```

### Enhanced Approach

```bash
invoke run_coverage_subprocess  # Captures comprehensive coverage.
```

### Workflow Automation

The invoke task handles the complete lifecycle:

- Hook installation and environment setup
- Test execution with parallel coverage
- Data aggregation and report generation
- Cleanup of hooks and temporary files

## Resources

- [How-to guide](/docs/tools/all.code_coverage_subprocess.how_to_guide.md) -
  Step-by-step implementation instructions
- [Reference documentation](/docs/tools/all.code_coverage_subprocess.reference.md) -
  Complete API and troubleshooting details
