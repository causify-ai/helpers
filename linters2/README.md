# Summary

Comprehensive linting and code formatting tools for Python, Jupyter notebooks, and Markdown files. Includes support for type checking, import normalization, code validation, and integration with Claude Code for intelligent formatting and analysis.

# Structure of the Dir

- `test/`: Unit tests for linting modules, test fixtures, and golden file outcomes

# Description of Files

- `add_class_frames.py`: Injects class frame decorators with class names before class initialization for debugging
- `dockerized_ty.py`: Wrapper to execute ty type checker within a Docker container with standard configuration
- `fix_comments.py`: Converts single-line docstrings to multi-line format
- `lint.py`: Unified linter orchestrating Python, Jupyter, and Markdown file checking with multiple backend tools
- `lint_cc.py`: Claude Code integration for intelligent file formatting and linting using topic-based rules and skills
- `linter_utils.py`: Utility functions supporting linting operations, file filtering, and directory exclusion patterns
- `normalize_import.py`: Refactors Python imports to canonical forms with standardized docstrings and short import aliases
- `pyright_cfile.py`: Adapter converting pyright type checker output to cfile-compatible diagnostic format
- `README.md`: This documentation file

# Description of Executables

## add_class_frames.py

### What It Does

- Injects frame decorators with class names before class initialization
- Skips decorators and comments to avoid separating them from class definitions
- Respects PEP-8 line length limits (79 characters) when adding frames
- Useful for debugging and stack trace readability

### Examples

- Add class frames to Python files:
  ```bash
  > add_class_frames.py file1.py file2.py
  ```

- Add class frames to multiple files:
  ```bash
  > add_class_frames.py *.py
  ```

## dockerized_ty.py

### What It Does

- Executes the ty type checker within a Docker container for reproducible type checking
- Pre-configures ty with standard flags (concise output, no color, excluded test directories)
- Supports force rebuild of Docker image and optional sudo for privileged operations
- Logs output to `ty.log` for review

### Examples

- Run type checking in Docker with standard configuration:
  ```bash
  > dockerized_ty.py
  ```

- Force rebuild the Docker image before type checking:
  ```bash
  > dockerized_ty.py --dockerized_force_rebuild
  ```

- Run with sudo for privileged Docker operations:
  ```bash
  > dockerized_ty.py --dockerized_sudo
  ```

## fix_comments.py

### What It Does

- Converts single-line docstrings to multi-line (three-line) format
- Identifies docstrings with triple quotes (""" or ''') on a single line
- Transforms them to a standardized multi-line format with opening and closing on separate lines
- Preserves indentation and quote type consistency

### Examples

- Fix docstrings in a single file:
  ```bash
  > fix_comments.py file.py
  ```

- Fix docstrings in multiple files:
  ```bash
  > fix_comments.py file1.py file2.py
  ```

## lint.py

### What It Does

- Unified linting orchestrator for Python, Jupyter notebooks, and Markdown files
- Selects files based on git state (modified, branch, last commit) or explicit file lists
- Runs appropriate tools per file type (pyright, jupytext, normalize_import, coverage, etc.)
- Supports dry-run mode to preview commands before execution

### Examples

- Run linting on modified files:
  ```bash
  > lint.py --modified
  ```

- Lint files in current branch vs master:
  ```bash
  > lint.py --branch
  ```

- Run specific actions on modified Python files only:
  ```bash
  > lint.py --modified --file_types "py" \
      --action pre-commit normalize_import
  ```

- Fix pyright type errors via Claude Code:
  ```bash
  > lint.py --modified --file_types "py" \
      --action fix_pyright
  ```

- Preview commands without executing (dry-run):
  ```bash
  > lint.py --modified --dry_run
  ```

## lint_cc.py

### What It Does

- Invokes Claude Code with intelligent topic-based or skill-based linting rules
- Detects file types by extension and path pattern to select appropriate rules
- Integrates with Claude rules and skills system for formatting and validation
- Supports batch processing with progress bars for multiple files

### Examples

- Format specific Python files:
  ```bash
  > lint_cc.py --files "file1.py file2.py"
  ```

- Apply a specific coding rule to a file:
  ```bash
  > lint_cc.py --topic coding --files "file.py"
  ```

- Lint modified files in the repository:
  ```bash
  > lint_cc.py --modified
  ```

- Preview command without executing (dry-run):
  ```bash
  > lint_cc.py --dry_run --files "*.md"
  ```

- Process multiple files with progress feedback:
  ```bash
  > lint_cc.py --files "src/*.py" --topic coding
  ```

- Use a different model
  ```
  linters2/lint_cc.py --files dev_scripts_helpers/scraping/download_link_articles.py --skill "coding.add_comments" --model deepseek/deepseek-v4-flash
  ```

## normalize_import.py

### What It Does

- Rewrites Python import statements to canonical forms with standardized docstrings
- Converts long module paths to short aliases (e.g., `helpers.debug` -> `hdbg`)
- Maintains mapping of long-to-short imports for consistency across codebase
- Generates and manages canonical import maps

### Examples

- Normalize imports in multiple files:
  ```bash
  > normalize_import.py sample_file1.py sample_file2.py
  ```

- Normalize all Python files in a directory:
  ```bash
  > normalize_import.py *.py
  ```

- Generate canonical import mapping:
  ```bash
  > normalize_import.py --generate_map
  ```

- Normalize with verbose output:
  ```bash
  > normalize_import.py --verbose file.py
  ```

## pyright_cfile.py

### What It Does

- Wraps pyright type checker and transforms JSON output to cfile-compatible diagnostic format
- Converts multiline diagnostic messages to comma-separated single-line format
- Truncates long messages to 100 characters with ellipsis for compatibility
- Outputs standardized diagnostics usable by editor and CI/CD integration tools

### Examples

- Run type checking and convert to cfile format:
  ```bash
  > pyright_cfile.py
  ```

- Run type checking on specific files:
  ```bash
  > pyright_cfile.py file1.py file2.py
  ```
