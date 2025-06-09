# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is the `helpers` repository - a foundational Python library providing utilities, development tools, and infrastructure components for a larger ecosystem. The codebase follows a modular architecture with these key components:

### Core Structure

- **`helpers/`** - Core utility modules (hdbg, hio, hpandas, etc.) following `h<name>` naming convention. Each module provides focused functionality (debugging, I/O, pandas extensions, etc.)
- **`config_root/`** - Configuration system with `Config` class and builders for hierarchical configuration management
- **`linters/`** - Pluggable linting framework with custom linters for code quality (amp_black, amp_isort, etc.)
- **`dev_scripts_helpers/`** - Development automation scripts organized by functionality (git, docker, documentation, etc.)

### Task System Architecture

The repository uses `pyinvoke` for task automation with a modular task system:
- **`tasks.py`** - Entry point that imports all task modules
- **`helpers/lib_tasks_*.py`** - Task modules organized by domain (docker, git, pytest, lint, etc.)
- Tasks are decorated with `@task` and accessible via `invoke <task_name>`

### Testing Architecture

- Uses pytest with custom markers: `slow`, `superslow`, `requires_docker_in_docker`
- **`helpers/hunit_test.py`** - Base test class with helpers for golden file testing and test utilities
- Tests are categorized by speed and infrastructure requirements
- Timeout-based test classification with different timeouts per category

## Common Development Commands

### Testing
```bash
# Run fast tests only
invoke run_fast_tests

# Run all tests
invoke run_tests

# Run specific test categories
invoke run_slow_tests
invoke run_superslow_tests

# Run tests with coverage
invoke run_coverage

# Run single test file
pytest path/to/test_file.py::TestClass::test_method
```

### Linting and Code Quality
```bash
# Lint all modified files
invoke lint --modified

# Lint specific files
invoke lint --files "file1.py file2.py"

# Check Python files compilation
invoke lint_check_python_files --modified
```

### Docker Development
```bash
# Start bash shell in development container
invoke docker_bash

# Build local development image
invoke docker_build_local_image

# Run Jupyter in container
invoke docker_jupyter
```

### Git and Branch Management
```bash
# Create new branch following naming convention
invoke git_branch_create --name "HelpersTask123_Description"

# Show files in current branch vs master
invoke git_branch_files

# Merge master into current branch
invoke git_merge_master
```

## Key Configuration

- **`repo_config.yaml`** - Repository metadata including Docker image names, S3 buckets, GitHub settings
- **`pytest.ini`** - Test configuration with custom markers and options
- **`mypy.ini`** - Type checking configuration with library-specific ignore rules
- **`invoke.yaml`** - Invoke task configuration

## Development Patterns

### Module Import Conventions
```python
import helpers.hdbg as hdbg
import helpers.hio as hio
import config_root.config.config_ as crococon
```

### Task Implementation
- Tasks in `lib_tasks_*.py` files use `@task` decorator
- Minimize dependencies in task functions (they run outside Docker)
- Call `hlitauti.report_task()` at start of each task

### Testing Patterns
- Inherit from `hunitest.TestCase` for enhanced test utilities
- Use golden file pattern via `check_string()` method
- Mark tests with appropriate speed markers
- Use `pytest.mark.requires_docker_in_docker` for Docker-dependent tests

### Configuration Management
- Use `Config` class from `config_root.config.config_` for hierarchical configs
- Support config versioning (currently v3)
- Use `DUMMY` placeholder for multi-phase config building

## Linting Framework

The custom linting system in `linters/` provides:
- Modular linter plugins (`amp_*.py` files)
- Base framework in `linters/base.py`
- Integration with invoke tasks for automated linting
- Support for parallel execution via joblib

When running `invoke lint`, it executes appropriate linters based on file types and applies fixes automatically where possible.