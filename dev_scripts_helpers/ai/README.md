# AI Development Scripts

This directory contains convenience wrapper scripts for Claude AI CLI tools used in
the development workflow.

## Scripts

- cc
  - Launches Claude Code in interactive mode
  - Skips permission prompts for faster iteration
  - **Use case**: Interactive coding sessions where you want real-time assistance
    with code generation, debugging, and refactoring

- `ccc`
  - Launches Claude Code using the Haiku model
  - **Use case**: Faster, cheaper responses for simpler tasks that don't require
    the full Sonnet model capabilities

- `ccp`
  - Executes Claude with a single prompt in text output format
  - **Use case**: Non-interactive, single-shot prompts for automation and scripting
  - E.g.,
    ```bash
    > ccp "Fix update_md.py -i docs/datapull/guide.md -a summarize -a apply_style"
    ```
