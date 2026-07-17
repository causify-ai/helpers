# AI Tools

Claude Code CLI wrapper scripts for development workflows. Provides convenient
shortcuts for interactive sessions, non-interactive prompts, and instruction file
generation with model selection and sensible defaults.

## Structure of the Dir

This directory has no subdirectories.

## Description of Files

- `cc`
  - Interactive Claude Code session launcher with model selection (Anthropic or OpenRouter)
- `ccp`
  - Non-interactive Claude Code runner for single-prompt execution with text output
- `create_instr`
  - Creates instruction files from template with vimdiff comparison for easy editing
- `README.md`
  - This documentation file

# Description of Executables

## `cc`

### What It Does

- Launches Claude Code in interactive mode with sensible permissions defaults
- Supports multiple model selection via shorthand flags (Anthropic, DeepSeek, custom)
- Auto-manages tmux window naming to show session state
- Includes diagnostics mode for testing Claude installation
- Forwards additional arguments to underlying claude command

### Examples

- Start interactive session with Anthropic (default):
  ```bash
  > cc
  ```

- Use DeepSeek V4 Flash via OpenRouter:
  ```bash
  > cc --ds
  ```

- Use custom model through OpenRouter:
  ```bash
  > cc --model openrouter/meta-llama/llama-3.1-8b-instruct
  ```

- Run diagnostics to verify installation:
  ```bash
  > cc --test
  ```

- Enable verbose debugging output:
  ```bash
  > cc -v
  ```

## `ccp`

### What It Does

- Runs Claude Code in non-interactive mode with single prompt execution
- Outputs results as plain text to stdout
- Skips permission prompts for automated scripting workflows
- Integrates with shell pipelines and command chaining

### Examples

- Execute simple prompt:
  ```bash
  > ccp "What does this Python function do?"
  ```

- Generate code via prompt:
  ```bash
  > ccp "Generate a Python function that sorts a list"
  ```

- Fix code and pipe to file:
  ```bash
  > ccp "Fix the syntax errors: $(cat broken.py)" > fixed.py
  ```

## `create_instr`

### What It Does

- Creates new instruction files (`instr.md`, `instr2.md`, etc.) from repository template
- Uses vimdiff for side-by-side template comparison and editing
- Validates exactly one template exists before proceeding
- Simplifies instruction file setup for consistent project guidelines

### Examples

- Create new `instr.md` file:
  ```bash
  > create_instr
  ```

- Create `instr2.md` with alternate suffix:
  ```bash
  > create_instr 2
  ```

- Create `instr3.md` for third instruction set:
  ```bash
  > create_instr 3
  ```
