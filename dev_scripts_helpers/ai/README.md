# Summary
This directory contains convenience wrapper scripts for Claude Code CLI tools
used in the development workflow. These scripts provide quick access to
interactive and non-interactive Claude sessions with sensible defaults,
permission handling, and tmux integration

# Description of Files
- `cc`: Interactive Claude Code session launcher with model selection (Anthropic
  direct or OpenRouter) and diagnostics support
- `ccp`: Non-interactive Claude Code CLI runner for single-prompt execution with
  text output
- `create_instr`: Creates new instruction files by copying from a template with
  vimdiff comparison
- `README.md`: This documentation file

# Description of Executables

## `cc`

### What It Does
- Launches Claude Code in interactive mode with dangerously-skip-permissions
  enabled for faster iteration
- Supports model selection via shorthand flags:
  - `--anth`: Anthropic directly (default, clears OpenRouter env vars)
  - `--or_anth`: Claude Haiku 4.5 via OpenRouter
  - `--ds`: DeepSeek V4 Flash via OpenRouter
  - `--dsp`: DeepSeek V4 Pro via OpenRouter
  - `--model MODEL_STR`: Any model through OpenRouter
- Automatically manages tmux window naming (shows "_CC_" during session)
- Includes diagnostics mode for testing Claude installation
- Forwards all additional arguments to the underlying claude command

### Examples
- Start an interactive Claude Code session with Anthropic directly (default):
  ```bash
  > cc
  ```

- Start with DeepSeek V4 Flash via OpenRouter:
  ```bash
  > cc --ds
  ```

- Start with DeepSeek V4 Pro via OpenRouter:
  ```bash
  > cc --dsp
  ```

- Start with Claude Haiku 4.5 via OpenRouter:
  ```bash
  > cc --or_anth
  ```

- Use a custom model through OpenRouter:
  ```bash
  > cc --model openrouter/meta-llama/llama-3.1-8b-instruct
  ```

- Run diagnostics to test Claude installation:
  ```bash
  > cc --test
  ```

- Enable verbose output for debugging:
  ```bash
  > cc -v
  ```

- Pass additional Claude options:
  ```bash
  > cc --anth --some-claude-flag
  ```

## `ccp`

### What It Does
- Runs Claude Code in non-interactive (print) mode with a single prompt
- Outputs results in plain text format
- Skips permission prompts for automated scripting
- Useful for single-shot automation and command-line integration

### Examples
- Execute a simple prompt:
  ```bash
  > ccp "What does this Python function do?"
  ```

- Use in scripting for code generation:
  ```bash
  > ccp "Generate a Python function that sorts a list"
  ```

- Chain with other tools for processing:
  ```bash
  > ccp "Fix the syntax errors in this code: $(cat broken.py)" > fixed.py
  ```

## `create_instr`

### What It Does
- Creates new instruction files (`instr.md`, `instr2.md`, etc.) from a template
- Uses vimdiff to compare the template with the new file for easy editing
- Automatically searches for the instruction template in the repository
- Validates that exactly one template exists before proceeding

### Examples
- Create a new `instr.md` file:
  ```bash
  > create_instr
  ```

- Create an `instr2.md` file:
  ```bash
  > create_instr 2
  ```

- Create an `instr3.md` file with a different suffix:
  ```bash
  > create_instr 3
  ```
