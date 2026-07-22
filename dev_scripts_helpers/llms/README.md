# LLM Tools

CLI tools for applying LLM transformations to code and text files. Supports code review, refactoring, text transformation, and TODO injection with Dockerized execution for dependency isolation.

## Structure of the Dir

This directory has no subdirectories.

## Description of Files

- `ai_review.py`
  - Alternative LLM interface for review-focused transformations with post-processing
- `inject_todos.py`
  - Inject TODO comments from cfile into source files
- `llm_apply_cfile.py`
  - Apply line-by-line transformations from cfile in Docker containers
- `llm_transform.py`
  - Apply predefined and custom LLM transformations to code files
- `print_daily_cost.py`
  - Fetch and display daily API costs from OpenAI and Anthropic

# Description of Executables

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

- `dockerized_llm_transform.py` is an internal tool.
- It is called automatically by its non-dockerized counterpart to execute
  transformations within Docker containers.
- It ensures all dependencies (e.g., OpenAI API libraries) are available and
  isolates the execution environment.
- Users typically do not call this directly - use the main tool instead.
