<!-- toc -->

- [Summary](#summary)
- [Description of Executables](#description-of-executables)
  * [`llm_cli.py`](#llm_clipy)
    + [What It Does](#what-it-does)
    + [Examples](#examples)
  * [`llm_transform.py`](#llm_transformpy)
    + [What It Does](#what-it-does-1)
    + [Examples](#examples-1)
  * [`llm_review.py`](#llm_reviewpy)
    + [What It Does](#what-it-does-2)
    + [Examples](#examples-2)
  * [`llm_apply_cfile.py`](#llm_apply_cfilepy)
    + [What It Does](#what-it-does-3)
    + [Examples](#examples-3)
  * [`inject_todos.py`](#inject_todospy)
    + [What It Does](#what-it-does-4)
    + [Examples](#examples-4)
  * [`ai_review.py`](#ai_reviewpy)
    + [What It Does](#what-it-does-5)
    + [Examples](#examples-5)
  * [`print_daily_cost.py`](#print_daily_costpy)
    + [What It Does](#what-it-does-6)
    + [Examples](#examples-6)
  * [Dockerized Variants](#dockerized-variants)
    + [What They Do](#what-they-do)

<!-- tocstop -->

# Summary

This directory contains a suite of CLI tools for applying Large Language Model
(LLM) transformations to code and text files. The tools support code review,
refactoring, text transformation, and automated TODO injection, with
Docker-based execution to handle dependencies and API credentials.

# Description of Executables

## `llm_cli.py`

### What It Does

General-purpose CLI script to apply LLM transformations to text files or text
input. This script provides a command-line interface to the
`apply_llm_with_files` function from `helpers.hllm_cli`. It reads text from an
input file or command line, processes it using an LLM (either via the llm CLI
executable or the llm Python library), and writes the result to an output file or
prints to screen.

Key features:
- Supports multiple LLM models (GPT-4, Claude, etc.) via either the llm CLI
  executable or Python library
- Can process input files in-place, write to output files, or print to stdout
- Supports reading from stdin and writing to stdout for pipeline integration
- Optional system prompts (inline or from file) to guide LLM behavior
- Progress bar support with automatic or explicit output size estimation
- Optional automatic linting of output files

### Examples

- Basic usage with input and output files
  ```bash
  > llm_cli.py --input input.txt --output output.txt
  > llm_cli.py -i input.txt -o output.txt
  ```

- In-place editing (writes back to input file)
  ```bash
  > llm_cli.py --input input.txt
  > llm_cli.py -i input.txt
  ```

- Read from stdin and write to stdout
  ```bash
  > echo "What is 2+2?" | llm_cli.py --input - --output -
  > cat input.txt | llm_cli.py -i - -o output.txt
  ```

- Read from stdin and write to file
  ```bash
  > echo "What is 2+2?" | llm_cli.py --input - --output output.txt
  > cat input.txt | llm_cli.py -i - -o output.txt
  ```

- Basic usage with input text
  ```bash
  > llm_cli.py --input_text "What is 2+2?" --output output.txt
  ```

- Print to screen instead of file
  ```bash
  > llm_cli.py --input_text "What is 2+2?" --output -
  > llm_cli.py -i input.txt -o -
  > echo "What is 2+2?" | llm_cli.py -i - -o -
  ```

- Use llm CLI executable instead of library
  ```bash
  > llm_cli.py -i input.txt -o output.txt --use_llm_executable
  ```

- With system prompt and specific model
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt "You are a helpful assistant" \
      --model gpt-4
  ```

- With system prompt from file
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt_file system_prompt.txt
  ```

- With automatic progress bar (estimates output size)
  ```bash
  > llm_cli.py -i input.txt -o output.txt -b
  > llm_cli.py -i input.txt -o output.txt --progress_bar
  ```

- With progress bar and explicit output size
  ```bash
  > llm_cli.py -i input.txt -o output.txt --expected_num_chars 5000
  ```

- Apply linting to output file after processing
  ```bash
  > llm_cli.py -i input.txt -o output.txt --lint
  > llm_cli.py -i input.txt --lint  # In-place editing with linting
  ```

## `llm_transform.py`

### What It Does

- Applies predefined or custom LLM transformations to code files, particularly
  useful for code review and refactoring.
- Executes transformations in Docker containers to isolate dependencies and
  environment requirements.
- Can generate cfiles (lists of code issues) for further processing with
  `llm_apply_cfile.py`.

### Examples

- Basic transformation:
  ```bash
  > llm_transform.py -i input.txt -o output.txt -p uppercase
  ```

- List available transformations:
  ```bash
  > llm_transform.py --list
  ```

- Code review (generates cfile):
  ```bash
  > llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_review
  ```

- Propose refactoring (generates cfile):
  ```bash
  > llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_propose_refactoring
  ```

- Compare original and transformed text:
  ```bash
  > llm_transform.py -i input.txt -o output.txt -p my_transform --compare
  ```

## `llm_review.py`

### What It Does

- Automatically reviews code files using LLMs against configurable guidelines.
- Can review specific files, directories, or git changesets (modified files,
  last commit, branch changes).
- Executes reviews in Docker containers and logs findings to a reviewer log
  file.

### Examples

- Review specific files:
  ```bash
  > llm_review.py --files="dir1/file1.py dir2/file2.md dir3/file3.ipynb"
  ```

- Review all modified files in git:
  ```bash
  > llm_review.py --modified
  ```

- Review files from last commit:
  ```bash
  > llm_review.py --last_commit
  ```

- Review branch changes with custom guidelines:
  ```bash
  > llm_review.py --branch --guidelines_doc_filename custom_guidelines.md
  ```

- Review directory excluding specific files:
  ```bash
  > llm_review.py --dir_name src/ --skip_files test_*.py
  ```

## `llm_apply_cfile.py`

### What It Does

- Reads a cfile (a structured file with code transformation instructions) and
  applies each transformation line-by-line.
- Executes transformations in Docker containers for dependency isolation.
- Useful for batch processing code changes identified by review tools.

### Examples

- Basic usage:
  ```bash
  > llm_apply_cfile.py --cfile cfile.txt
  ```

- With debug output:
  ```bash
  > llm_apply_cfile.py --cfile cfile.txt --debug
  ```

- With custom prompt and fast model:
  ```bash
  > llm_apply_cfile.py --cfile cfile.txt --prompt "Fix the issue" --fast_model
  ```

- Force rebuild Docker container:
  ```bash
  > llm_apply_cfile.py --cfile cfile.txt --dockerized_force_rebuild
  ```

## `inject_todos.py`

### What It Does

- Reads a cfile containing TODO items and injects them as code comments into
  source files.
- Assigns TODOs to a specified user/target for tracking.
- Useful for converting review findings or refactoring suggestions into
  actionable TODO comments.

### Examples

- Inject TODOs from cfile:
  ```bash
  > inject_todos.py --cfile todos.txt --todo_target username
  ```

- With verbose logging:
  ```bash
  > inject_todos.py --cfile todos.txt --todo_target username -v DEBUG
  ```

## `ai_review.py`

### What It Does

- Alternative interface for applying LLM-based transformations with review
  focus.
- Supports stdin/stdout for pipeline integration and optional post-transform
  processing.
- Can skip post-transforms and provides debug mode for troubleshooting.

### Examples

- Review from file:
  ```bash
  > ai_review.py -i input.py -o output.py --prompt "Review for bugs"
  ```

- Review from stdin to stdout:
  ```bash
  > cat file.py | ai_review.py -i - -o - --prompt "Review code quality"
  ```

- Fast model with debug output:
  ```bash
  > ai_review.py -i input.py -o output.py --prompt "Check style" --fast_model --debug
  ```

- Skip post-transforms:
  ```bash
  > ai_review.py -i input.py -o output.py --prompt "Review" --skip-post-transforms
  ```

## `print_daily_cost.py`

### What It Does

- Fetches and displays daily API costs from OpenAI and Anthropic billing APIs.
- Queries the OpenAI Costs API and Anthropic Admin API for cost data.
- Displays results in a formatted text table showing per-provider and total costs.
- Requires OPENAI_API_KEY and ANTHROPIC_ADMIN_API_KEY environment variables.

### Examples

- Print today's costs:
  ```bash
  > print_daily_cost.py
  ```

- Print costs with debug logging:
  ```bash
  > print_daily_cost.py -v DEBUG
  ```

- Print costs for a specific date:
  ```bash
  > print_daily_cost.py --date 2025-12-30
  ```

## Dockerized Variants

### What They Do

- `dockerized_llm_transform.py`, `dockerized_llm_review.py`, and
  `dockerized_llm_apply_cfile.py` are internal tools.
- These are called automatically by their non-dockerized counterparts to execute
  transformations within Docker containers.
- They ensure all dependencies (e.g., OpenAI API libraries) are available and
  isolate the execution environment.
- Users typically do not call these directly - use the main tools instead.
