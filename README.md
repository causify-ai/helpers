# helpers

This is the `helpers` repository - a foundational Python library providing utilities, development tools, and infrastructure components.

## Structure of the Dir

- `.claude/`
  - Claude Code configuration and hooks
- `.github/`
  - GitHub Actions workflows and repository configuration
- `config_root/`
  - Configuration system with Config class and builders
- `dev_scripts_helpers/`
  - Development automation scripts organized by functionality
- `devops/`
  - DevOps tools and infrastructure scripts
- `docs/`
  - Documentation and guides for the repository
- `docs_mkdocs/`
  - MkDocs configuration and generated documentation
- `helpers/`
  - Core utility modules following h<name> naming convention
- `import_check/`
  - Import validation and checking tools
- `linters/`
  - Pluggable linting framework with custom linters
- `linters2/`
  - Additional linting tools and configurations

## Description of Files

- `CLAUDE.md`
  - Architecture overview and development patterns for Claude Code
- `conftest.py`
  - Pytest configuration and shared test fixtures
- `instr.md`
  - Development instructions and task specifications
- `main_pytest.py`
  - Main pytest runner and test execution controller
- `tasks.py`
  - Entry point for pyinvoke task automation system

## Description of Executables

### `main_pytest.py`

#### What It Does

- Main entry point for running pytest test suites
- Handles test execution configuration and reporting

#### Examples

- Run the test suite:
  ```bash
  > ./main_pytest.py
  ```
