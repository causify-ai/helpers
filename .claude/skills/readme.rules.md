These are conventions for writing a README

- A README for a directory with executables contains:
  - A short description of all the executables in a directory
  - A description of how executables interact with each others
    in terms of workflows

# Conventions

- Follow the same conventions of `.claude/skills/markdown.rules.md` for writing
  text 

## Format of Commands
- Commands in a README should have a short description and then the command
  indented properly
  ```bash
  - Description
    > command
  ```
- Break long commands with `\` for readability, indenting continuation lines by
  4 spaces so the command is easy to copy-paste

- Example
  - **Good**

    ````
    - With system prompt from file:
      ```bash
      > llm_cli.py -i input.txt -o output.txt \
          --system_prompt_file system_prompt.txt
      ```
    ````
  - **Bad**
    ````
    **With system prompt from file:**
    ```bash
    > llm_cli.py -i input.txt -o output.txt \
        --system_prompt_file system_prompt.txt
    ```
    ````

## Inline Commands

- Short commands mentioned inline in prose (e.g., `run foo.py`) should stay
  inline with backticks
- Only standalone commands need the bullet + fenced block format
