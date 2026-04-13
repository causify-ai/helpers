---
description: Format README commands to use bullet-point descriptions followed by fenced bash code blocks
---

- Commands in a readme must follow the format below
  - Description

    ```bash
    > command
    ```
  - Good

    ````
    - With system prompt from file:
    ```bash
    > llm_cli.py -i input.txt -o output.txt \
        --system_prompt_file system_prompt.txt
    ```
    ````
  - Bad
    ````
    **With system prompt from file:**
    ```bash
    > llm_cli.py -i input.txt -o output.txt \
        --system_prompt_file system_prompt.txt
    ```
    ````

## Scope

- Apply this format to ALL standalone shell commands in the README, including
  those in "Installation", "Usage", "Examples", and "Development" sections
- Do not change non-command content (prose descriptions, architecture diagrams,
  links, or tables)

## Multi-line Commands

- Break long commands with `\` for readability, indenting continuation lines by
  4 spaces so the command is easy to copy-paste

## Inline Commands

- Short commands mentioned inline in prose (e.g., `run foo.py`) should stay
  inline with backticks; only standalone commands need the bullet + fenced
  block format

## When to Rewrite

- Convert any standalone command wrapped in `**bold**`, `*italic*`, plain prose,
  or numbered list items to the bullet + fenced block format
