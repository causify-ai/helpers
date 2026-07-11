# Pytest Testing System Architecture

## Overview
The pytest testing system provides three coordinated CLI tools for multi-build
test execution, failure analysis, and result consolidation across different
environments (native Docker, Apple, and dev containers). The system enables
developers to:

- Run pytest across 3 build configurations with isolated cache and environment
  setup
- Parse pytest logs to extract, categorize, and analyze test failures
- Consolidate failures across multiple build runs to identify cross-platform
  issues

**Role in codebase**: These are standalone CLI tools invoked via invoke tasks
(`pytest_multi_build`, `pytest_failed`, `pytest_failed_multi_build`). They
support the test execution and debugging workflow for both CI/CD pipelines and
local development

**External systems and integrations**:

- **pytest / pytest_log**: Test execution command that generates structured
  output
- **manage_cache.py**: Cache clearing utility for consistent multi-build state
- **invoke task system**: CLI entry point and task orchestration
- **Filesystem**: Logs, repro scripts, and build-specific output files

**Module responsibilities**:
- **pytest_utils**: Centralized configuration
  - Defines 3 build environments (docker, apple, dev_container)
  - Specifies execution parameters for each build (docker_engine, use_docker_cmd)
  - Used by all three CLI tools to ensure consistency
- **pytest_multi_build**: Orchestrates parallel pytest execution
  - Manages cache clearing between builds
  - Executes pytest with isolated environment variables
  - Captures output to per-build log files
  - Supports both direct targets and custom scripts
- **pytest_failed**: Parses pytest logs and categorizes results
  - Extracts test results from log files
  - Generates categorized reports (passed, failed, skipped, duration stats)
  - Produces environment-specific repro scripts
  - Encodes build name in output filenames for parallel runs
- **pytest_failed_multi_build**: Consolidates cross-build analysis
  - Reads per-build failures from pytest_failed output
  - Builds map of tests to the builds where they failed
  - Creates consolidated summary showing cross-platform failures
  - Generates combined repro script with all build invocations
