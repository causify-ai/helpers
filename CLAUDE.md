# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Architecture Overview

This is the `helpers` repository - a foundational Python library providing
utilities, development tools, and infrastructure components for a larger
ecosystem. The codebase follows a modular architecture with these key
components:

### Core Structure

- **`helpers/`** - Core utility modules (100+ modules) following `h<name>` naming
  convention organized into categories:
  - **Core Infrastructure**: `hdbg`, `hio`, `hsystem`, `hserver`, `henv` -
    debugging, I/O, system operations
  - **Data Processing**: `hpandas`, `hdataframe`, `hnumpy`, `hparquet`, `hcsv` -
    data manipulation and analysis
  - **Testing Framework**: `hunit_test`, `hpytest`, `hcoverage`, `hplayback` -
    comprehensive testing utilities
  - **External Services**: `haws`, `hs3`, `hgit`, `hdocker`, `hchatgpt`,
    `hllm` - cloud and tool integrations
  - **Caching & Performance**: `hcache`, `hcache_simple`, `hjoblib`, `htimer` -
    performance optimization
  - **Command-line & Parsing**: `hparser` - argument parsing and CLI utilities
  - **Text & Markdown**: `hmarkdown*` family, `hstring`, `htext_protect` -
    text processing and markdown utilities
- **`config_root/`** - Configuration system with `Config` class and builders for
  hierarchical configuration management
- **`linters/`** - Pluggable linting framework with custom linters for code
  quality (amp_black, amp_isort, etc.)
- **`dev_scripts_helpers/`** - Development automation scripts organized by
  functionality (git, docker, documentation, etc.)

### Task System Architecture

The repository uses `pyinvoke` for task automation with a modular task system:

- **`tasks.py`** - Entry point that imports all task modules
- **`helpers/lib_tasks_*.py`** - Task modules organized by domain (docker, git,
  pytest, lint, etc.)
- Tasks are decorated with `@task` and accessible via `invoke <task_name>`

### Testing Architecture

- Uses pytest with custom markers: `slow`, `superslow`, `requires_docker_in_docker`,
  `requires_ck_infra`, `requires_ck_aws`, `no_container`
- **Note**: "fast" tests are those without `slow` or `superslow` markers
- **[`/helpers/hunit_test.py`](/helpers/hunit_test.py)** - Base test class with
  helpers for golden file testing and test utilities
- Tests are categorized by speed and infrastructure requirements
- Timeout-based test classification:
  - Fast tests (5s)
  - Slow tests (30s)
  - Superslow tests (3600s)

## Common Development Commands

### Testing

- To run tests

  ```bash
  # Run fast tests only
  invoke run_fast_tests
  # Run slow tests only
  invoke run_slow_tests
  # Run superslow tests only
  invoke run_superslow_tests

  # Run single test file
  invoke docker_cmd --cmd "pytest path/to/test_file.py -v"
  # Run single test class
  invoke docker_cmd --cmd "pytest path/to/test_file.py::TestClass -v"
  # Run single test method
  invoke docker_cmd --cmd "pytest path/to/test_file.py::TestClass::test_method -v"

  # Run coverage for fast tests only
  invoke run_coverage --suite fast --generate-html-report
  # Run coverage for slow tests only
  invoke run_coverage --suite slow --generate-html-report
  # Run coverage for superslow tests only
  invoke run_coverage --suite superslow --generate-html-report
  ```

### Linting and Code Quality

- To lint code

  ```bash
  # Lint all modified files
  invoke lint --modified

  # Lint specific files
  invoke lint --files "file1.py file2.py"

  # Check Python files compilation
  invoke lint_check_python_files --modified
  ```

### Git and Branch Management

- To use branch

  ```bash
  # Create new branch following naming convention
  invoke git_branch_create --name "HelpersTask123_Description"

  # Merge master into current branch
  invoke git_merge_master
  ```

## Key Configuration

- **`repo_config.yaml`** - Repository metadata including Docker image names, S3
  buckets, GitHub settings, ECR configuration
- **`pytest.ini`** - Test configuration with custom markers (`slow`,
  `superslow`, `requires_docker_in_docker`, `requires_ck_infra`, `requires_ck_aws`,
  `no_container`) and options
- **`pyproject.toml`** - Ruff linting configuration (line length 81, Python 3.11
  target) and Fixit settings
- **`mypy.ini`** - Type checking configuration with library-specific ignore
  rules
- **`invoke.yaml`** - Invoke task configuration (auto_dash_names: false, echo:
  true)

## Development Patterns

### Module Import Conventions

```python
import helpers.hdbg as hdbg
import helpers.hio as hio
import config_root.config.config_ as crococon
```

### Testing Patterns

- Inherit from `hunitest.TestCase` for enhanced test utilities
- Use golden file pattern via `check_string()` method
- Mark tests with appropriate speed markers:
  - `@pytest.mark.slow` - slow tests (~30s timeout)
  - `@pytest.mark.superslow` - very slow tests (~3600s timeout)
  - Unmarked tests are considered "fast" (~5s timeout)
- Use `@pytest.mark.requires_docker_in_docker` for tests requiring Docker
  children/sibling containers
- Use `@pytest.mark.requires_ck_infra` for tests requiring CK infrastructure
- Use `@pytest.mark.requires_ck_aws` for tests requiring CK AWS connection
- Use `@pytest.mark.no_container` for invoke target tests that run outside
  containers
- Test outcomes stored in `test/outcomes/` directories following module
  structure

### Code Conventions

- For writing any Python code you MUST follow instructions in
  `@.claude/skills/coding.rules.md` and 
  `@docs/ai_templates/code_template.py`
- For writing unit tests you MUST follow instructions in
  `@.claude/skills/testing.format_rules/SKILL.md` and
  `@docs/ai_templates/unit_test_template.py`
- For writing a notebook you MUST follow instructions in
  `@.claude/skills/notebook.format_rules/SKILL.md` and
  `@docs/ai_templates/notebook_template.ipynb`
- For writing a blog you MUST follow instructions in
  `@.claude/skills/blog.format_rules/SKILL.md`
- For writing markdown text you MUST follow instructions in
  `@.claude/skills/markdown.format_rules/SKILL.md`

# Notes for Claude

- NEVER commit code to git without being explicitly asked to do it
