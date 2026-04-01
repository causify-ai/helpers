# Summary

The `helpers/` directory is the core Python library providing utilities,
development tools, and infrastructure components for the helpers ecosystem.
Modules follow the `h<name>` naming convention and are organized by domain.

# Directory Structure

- `logging_testing/`
  - Utilities for testing logging behavior across modules
- `notebooks/`
  - Jupyter notebooks and tutorials (e.g., hcache_simple usage)
- `old/`
  - Deprecated and archived modules (conda, tunnels, user_credentials)
- `pandoc_docker_files/`
  - Docker setup files and package lists for pandoc and texlive
- `telegram_notify/`
  - Telegram bot notification module with config and chat ID utilities
- `test/`
  - Unit tests for all modules (90+ test files organized by module name)

# Files

## Core Infrastructure

- `hdbg.py`
  - Debugging utilities with specialized assertions, logging, and fatal error handling
- `hio.py`
  - Filesystem operations, file read/write, and directory management utilities
- `hsystem.py`
  - System interaction: shell commands, environment variables, process management
- `henv.py`
  - Environment variable checks and module installation management
- `hserver.py`
  - Identify which server the code is running on
- `hversion.py`
  - Code version control and Docker container compatibility checking
- `hlogging.py`
  - Logging configuration, custom formatters, and logging utilities
- `hwarnings.py`
  - Suppress annoying Python warnings when imported
- `htraceback.py`
  - Traceback parsing, formatting, and manipulation utilities
- `hprint.py`
  - Debugging and pretty-printing utilities for Python objects
- `hparser.py`
  - Argparse helpers: verbosity, action, limit-range, and other standard arguments
- `hobject.py`
  - Introspect and print the state of a Python object
- `hintrospection.py`
  - Python introspection and module analysis utilities
- `hmodule.py`
  - Dynamic module installation and import management utilities
- `htimer.py`
  - Timer class for measuring and reporting elapsed time
- `htqdm.py`
  - tqdm progress bar stream redirected to Python logger
- `hthreading.py`
  - Timeout decorator to enforce execution time limits on functions
- `hretry.py`
  - Retry decorators for synchronous and asynchronous functions
- `hasyncio.py`
  - Async/await utilities and coroutine management for asyncio
- `hnetwork.py`
  - Network utilities including URL availability checking
- `hopen.py`
  - Cross-platform file opening utility
- `htypes.py`
  - General type aliases and type utilities based on standard Python libraries
- `hwall_clock_time.py`
  - Wall clock time simulation and management for testing and replays

## Data Processing

- `hpandas.py`
  - Pandas utilities aggregating all hpandas_* submodules
- `hpandas_analysis.py`
  - Statistical analysis and ML-related functions for pandas DataFrames
- `hpandas_check_summary.py`
  - DataFrame check and summary reporting utilities
- `hpandas_clean.py`
  - DataFrame cleaning operations (deduplicate, fill NaN, sanitize)
- `hpandas_compare.py`
  - DataFrame comparison utilities for diffing and equality checks
- `hpandas_conversion.py`
  - DataFrame and Series conversion and casting utilities
- `hpandas_dassert.py`
  - Pandas-specific assertions and validation functions
- `hpandas_display.py`
  - DataFrame display formatting and signature generation
- `hpandas_io.py`
  - Pandas I/O operations for local and S3 storage
- `hpandas_multiindex.py`
  - MultiIndex creation, manipulation, and access operations
- `hpandas_stats.py`
  - Pandas statistics, duration computation, and time-series helpers
- `hpandas_transform.py`
  - DataFrame transformation operations (pivot, reshape, normalize)
- `hpandas_utils.py`
  - General-purpose pandas utilities and helper functions
- `hdataframe.py`
  - Lower-level helper functions for processing pandas DataFrames
- `hnumpy.py`
  - NumPy utilities, array helpers, and random seed management
- `hnumba.py`
  - Numba JIT compilation wrapper and acceleration utilities
- `hparquet.py`
  - Parquet file read/write operations using pyarrow
- `hcsv.py`
  - CSV file operations and DataFrame I/O utilities
- `hdatetime.py`
  - Date/time manipulation, parsing, and timezone handling utilities
- `hdict.py`
  - Dictionary manipulation and nested dictionary operation utilities
- `hlist.py`
  - List manipulation, deduplication, and membership utilities
- `hstring.py`
  - String manipulation, formatting, and transformation utilities
- `htable.py`
  - Lightweight rectangular table class with no pandas dependency

## Caching and Performance

- `hcache.py`
  - Advanced function caching using joblib with S3 and git integration
- `hcache_simple.py`
  - Simple caching with JSON or pickle file-based storage backends
- `hjoblib.py`
  - Joblib parallelization, memory caching, and job management
- `hpickle.py`
  - Pickle and JSON serialization and deserialization routines

## Testing Framework

- `hunit_test.py`
  - Enhanced unit testing framework built on unittest and pytest with golden files
- `hunit_test_purification.py`
  - Text purification utilities to sanitize test output for comparison
- `hunit_test_utils.py`
  - Unit test utilities including test renaming and helpers
- `hpytest.py`
  - Pytest integration utilities and test artifact handling
- `hcoverage.py`
  - Code coverage utilities and test coverage analysis helpers
- `hplayback.py`
  - Automatically generate unit tests by recording and replaying function calls
- `htest_logger.py`
  - Test logging script template
- `hmoto.py`
  - AWS service mocking with moto for unit testing

## Markdown Processing

- `hmarkdown.py`
  - Markdown processing entry point aggregating all hmarkdown_* submodules
- `hmarkdown_bullets.py`
  - Markdown bullet point processing and formatting
- `hmarkdown_coloring.py`
  - Markdown text coloring utilities for LaTeX and HTML output
- `hmarkdown_comments.py`
  - Markdown comment detection, extraction, and removal utilities
- `hmarkdown_div_blocks.py`
  - Utilities for handling HTML div blocks within markdown files
- `hmarkdown_fenced_blocks.py`
  - Fenced code block parsing and manipulation in markdown
- `hmarkdown_filtering.py`
  - Markdown section extraction and content filtering utilities
- `hmarkdown_formatting.py`
  - Markdown text formatting and whitespace normalization utilities
- `hmarkdown_headers.py`
  - Markdown header manipulation, extraction, and level adjustment
- `hmarkdown_rules.py`
  - Markdown rule validation and processing utilities
- `hmarkdown_slides.py`
  - Markdown slide extraction, splitting, and processing for presentations
- `hmarkdown_tables.py`
  - Markdown table parsing, formatting, and manipulation utilities
- `hmarkdown_toc.py`
  - Markdown table of contents generation and YAML frontmatter handling
- `hlint.py`
  - Linting utilities for text and code files
- `htext_protect.py`
  - Utilities for protecting content regions during text processing

## External Services and Cloud

- `haws.py`
  - AWS services integration with boto3 client and resource management
- `hs3.py`
  - S3 file operations, listing, and S3-backed filesystem utilities
- `hsecrets.py`
  - AWS Secrets Manager integration for secret retrieval
- `htranslate.py`
  - AWS Translate service wrapper for text translation
- `hgit.py`
  - Git repository operations, branch management, and diff utilities
- `hdocker.py`
  - Docker container operations, image management, and Docker utilities
- `hdocker_tests.py`
  - Utilities for running tests inside Docker containers
- `hdockerized_executables.py`
  - Wrappers for Dockerized executables: prettier, pandoc, latex, and others
- `hgoogle_drive_api.py`
  - Google Drive and Google Sheets API integration utilities
- `hchatgpt.py`
  - OpenAI API integration with file management and chat utilities
- `hchatgpt_instructions.py`
  - ChatGPT system instructions and prompt templates
- `hllm.py`
  - LLM API integration with caching, cost tracking, and response handling
- `hllm_cli.py`
  - LLM CLI interaction wrapper and cost estimation utilities
- `hllm_cost.py`
  - LLM cost calculation for OpenRouter and other APIs
- `hslack.py`
  - Slack notification utilities for sending messages to channels
- `hemail.py`
  - Email sending utilities via SMTP
- `hsftp.py`
  - SFTP file transfer operations using pysftp
- `hsql.py`
  - SQL database operations as a PostgreSQL wrapper
- `hsql_implementation.py`
  - Low-level SQL implementation with psycopg2 driver
- `hsql_test.py`
  - SQL testing utilities, fixtures, and database test helpers
- `asana_utils.py`
  - Enhanced Asana analytics with time estimation and team grouping
- `github_utils.py`
  - GitHub API utilities for caching and repository data retrieval

## Notebooks and Visualization

- `hnotebook.py`
  - Jupyter notebook configuration and display setup utilities
- `hjupyter.py`
  - Jupyter notebook execution and output capture utilities
- `hmatplotlib.py`
  - Matplotlib utilities, figure management, and plotting helpers
- `hmkdocs.py`
  - MkDocs-specific markdown generation and documentation utilities
- `hlatex.py`
  - LaTeX conversion utilities using pandoc

## Miscellaneous

- `hfile_tree.py`
  - Directory tree building and formatted output utilities
- `hcfile.py`
  - C file parsing and transformation utilities
- `repo_config_utils.py`
  - Repository configuration utilities loaded from YAML
- `stage_linked_file.py`
  - Symbolic link staging utility for git operations

## Task System (`lib_tasks_*.py`)

- `lib_tasks.py`
  - Entry point that aggregates all invoke task modules
- `lib_tasks_aws.py`
  - Invoke tasks for AWS operations and deployments
- `lib_tasks_bash.py`
  - Invoke tasks for bash script execution
- `lib_tasks_docker.py`
  - Invoke tasks for Docker build, run, and management operations
- `lib_tasks_docker_release.py`
  - Invoke tasks for Docker image release and publishing workflows
- `lib_tasks_find.py`
  - Invoke tasks for searching and finding files in the repo
- `lib_tasks_gh.py`
  - Invoke tasks for GitHub pull requests and issues
- `lib_tasks_git.py`
  - Invoke tasks for git branch, merge, and commit operations
- `lib_tasks_integrate.py`
  - Invoke tasks for integrating changes between repositories
- `lib_tasks_lint.py`
  - Invoke tasks for linting and code quality checks
- `lib_tasks_perms.py`
  - Invoke tasks for managing file permissions
- `lib_tasks_print.py`
  - Invoke tasks for printing setup and environment info
- `lib_tasks_pytest.py`
  - Invoke tasks for running pytest suites (fast, slow, superslow)
- `lib_tasks_utils.py`
  - Shared utilities and helpers used across task modules
