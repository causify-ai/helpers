# linters2 Module

- Comprehensive linting and code formatting tools for Python, Jupyter notebooks,
  and Markdown files

- Includes support for type checking, import normalization, code validation, and
  integration with Claude Code for intelligent formatting

## Directory Structure

- `test/`
  - Unit tests for linting modules, test fixtures, and golden file outcomes

## Files

- `linter_utils.py`
  - Utility functions supporting linting operations, file filtering, and
    directory exclusion patterns

- `add_class_frames.py`
  - Injects class frame decorators with class names before class initialization
    for debugging

- `dockerized_ty.py`
  - Wrapper to execute ty type checker within a Docker container with standard
    configuration

- `lint.py`
  - Unified linter orchestrating Python, Jupyter, and Markdown file checking with
    multiple backend tools

- `lint_cc.py`
  - Claude Code integration for intelligent file formatting and linting using
    topic-based rules and skills

- `normalize_import.py`
  - Refactors Python imports to canonical forms with standardized docstrings and
    short import aliases

- `pyright_cfile.py`
  - Adapter converting pyright type checker output to cfile-compatible diagnostic
    format

## Executables

### `lint.py`

- **What It Does**:
  - Unified linting orchestrator for Python, Jupyter notebooks, and Markdown
    files
  - Selects files based on git state (modified, branch, last commit) or explicit
    file lists
  - Runs appropriate tools per file type (pyright, jupytext, normalize_import,
    coverage, etc.)
  - Supports dry-run mode to preview commands before execution

- Run linting on modified files:
  ```bash
  > ./lint.py --modified
  ```

- Lint files in current branch vs master:
  ```bash
  > ./lint.py --branch
  ```

- Run specific actions on modified Python files only:
  ```bash
  > ./lint.py --modified --file_types "py" --action pre-commit normalize_import
  ```

- Fix pyright type errors via Claude Code:
  ```bash
  > ./lint.py --modified --file_types "py" --action fix_pyright
  ```

### `lint_cc.py`

- **What It Does**:
  - Invokes Claude Code with intelligent topic-based or skill-based linting rules
  - Detects file types by extension and path pattern to select appropriate rules
  - Integrates with Claude rules and skills system for formatting and validation
  - Supports batch processing with progress bars for multiple files

- Format specific Python files:
  ```bash
  > ./lint_cc.py --files "file1.py file2.py"
  ```

- Apply a specific coding rule to a file:
  ```bash
  > ./lint_cc.py --topic coding --files "file.py"
  ```

- Lint modified files in the repository:
  ```bash
  > ./lint_cc.py --modified
  ```

- Preview command without executing (dry-run):
  ```bash
  > ./lint_cc.py --dry_run --files "*.md"
  ```

### `normalize_import.py`

- **What It Does**:
  - Rewrites Python import statements to canonical forms with standardized
    docstrings
  - Converts long module paths to short aliases (e.g., `helpers.debug` → `hdbg`)
  - Maintains mapping of long-to-short imports for consistency across codebase
  - Generates and manages canonical import maps

- Normalize imports in multiple files:
  ```bash
  > ./normalize_import.py sample_file1.py sample_file2.py
  ```

- Generate canonical import mapping:
  ```bash
  > ./normalize_import.py --generate_map
  ```

### `add_class_frames.py`

- **What It Does**:
  - Injects frame decorators with class names before class initialization
  - Skips decorators and comments to avoid separating them from class definitions
  - Respects PEP-8 line length limits (79 characters) when adding frames
  - Useful for debugging and stack trace readability

- Add class frames to Python files:
  ```bash
  > ./add_class_frames.py file1.py file2.py
  ```

### `dockerized_ty.py`

- **What It Does**:
  - Executes the ty type checker within a Docker container for reproducible type
    checking
  - Pre-configures ty with standard flags (concise output, no color, excluded
    test directories)
  - Supports force rebuild of Docker image and optional sudo for privileged
    operations
  - Logs output to `ty.log` for review

- Run type checking in Docker with standard configuration:
  ```bash
  > ./dockerized_ty.py
  ```

- Force rebuild the Docker image before type checking:
  ```bash
  > ./dockerized_ty.py --dockerized_force_rebuild
  ```

### `pyright_cfile.py`

- **What It Does**:
  - Wraps pyright type checker and transforms JSON output to cfile-compatible
    diagnostic format
  - Converts multiline diagnostic messages to comma-separated single-line format
  - Truncates long messages to 100 characters with ellipsis for compatibility
  - Outputs standardized diagnostics usable by editor and CI/CD integration tools

- Run type checking and convert to cfile format:
  ```bash
  > ./pyright_cfile.py
  ```
