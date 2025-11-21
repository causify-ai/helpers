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

- General-purpose CLI for applying LLM transformations to text files or direct
  text input.
- Supports multiple LLM models (GPT-4, Claude, etc.) via either the llm CLI
  executable or Python library.
- Can process input files in-place, write to output files, or print to stdout,
  with optional automatic linting.

### Examples

- Basic file transformation with output:
  ```bash
  > llm_cli.py --input input.txt --output output.txt
  ```

- In-place editing:
  ```bash
  > llm_cli.py -i input.txt
  ```

- Direct text input with stdout:
  ```bash
  > llm_cli.py --input_text "What is 2+2?" --output -
  ```

- With system prompt and specific model:
  ```bash
  > llm_cli.py -i input.txt -o output.txt \
      --system_prompt "You are a helpful assistant" \
      --model gpt-4
  ```

- With progress bar and automatic linting:
  ```bash
  > llm_cli.py -i input.txt -o output.txt -b --lint
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
  > llm_transform.py -i input.txt -o output.txt -p list_prompts
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

## Dockerized Variants

### What They Do

- `dockerized_llm_transform.py`, `dockerized_llm_review.py`, and
  `dockerized_llm_apply_cfile.py` are internal tools.
- These are called automatically by their non-dockerized counterparts to execute
  transformations within Docker containers.
- They ensure all dependencies (e.g., OpenAI API libraries) are available and
  isolate the execution environment.
- Users typically do not call these directly - use the main tools instead.
