# Summary

This directory contains convenience wrapper scripts for Claude AI CLI tools used in
the development workflow.

# Short summary
- `cc`
- `ccc`
- `ccp`

# Description of Executables

## `cc`

- **What It Does**
  - Launches Claude Code in interactive mode
  - Skips permission prompts for faster iteration

- Interactive coding session:
  ```bash
  > cc
  ```

## `ccc`

- **What It Does**
  - Launches Claude Code using the Haiku model
  - Provides faster, cheaper responses for simpler tasks

- Launch with Haiku model:
  ```bash
  > ccc
  ```

## `ccp`

- **What It Does**
  - Executes Claude with a single prompt in text output format
  - Supports non-interactive, single-shot prompts for automation and scripting

- Execute a single prompt:
  ```bash
  > ccp "Fix update_md.py -i docs/datapull/guide.md -a summarize -a apply_style"
  ```
