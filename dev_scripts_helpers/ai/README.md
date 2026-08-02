# AI Tools

// TODO(gp): dev_scripts_helpers/ai/ -> dev_scripts_helpers/agents or merge
// into dev_scripts_helpers/llms

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
  - TODO(gp): Remove this script since too thin
- `create_instr`
  - Creates instruction files from template with vimdiff comparison for easy editing
  - TODO(gp): Remove this script since not useful
- `README.md`
  - This documentation file

# Automation Tools

- `llm_cli.py`: an interface to llm Python package
  - Runs an LLM
- `llm_transform.py`: apply a transform to a file and / or stdin
  - TODO(gp): This is going to be merged / folded into `llm_cli.py`
- `linters2/cc_lint.py`: apply a set of transformations using Claude Code
- `cc`: wrapper
- `batch_cc.py` 

- Skills
  ./.claude/skills/coding.todoai_gp
  ./dev_scripts_helpers/llms/inject_todos.py

./.claude/skills/coding.create_auto_todo

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

##

### [ ] Apply Skills and Rules
- Create a script to apply a skill to a set of files
  - It should apply it calling CC or an LLM (needs API tokens)
  ```
  Apply rule ## Use `typing` Module Style for Type Hints to src/helpers1292/linters2/test/test_lint.py
  ```

> apply_cc_skill.py --skill ... or --rule ... --files ...

- Is there anything already? linters2/cc_lint.py?

- Sometimes we need to dialogue with an agent, other times we just need an LLM

- Apply rules in chunks
  - Extract a chunk of a markdown file
  - Split it in rules (H1, H2)
  - Apply that chunk of rules to a file
  - Use Claude or an LLM

- Sometimes you need an agent since one prompt requires to read another one
  - Simple logic to inline files if they are reachable (recursively)

- Pass multiple prompts to an LLM to apply on the same text
- Need to fix Claude batch mode
- Can we control Claude instead of kicking off

- P1: Do it in parallel?

Fix the output

### [ ] todo injection logic
- Find / update the todo injection logic

