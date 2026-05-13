These are conventions for writing a README

- A README for a directory with executables contains:
  - A summary of the directory's purpose
  - Directory structure and subdirectory descriptions
  - A list of all files with brief descriptions
  - Detailed documentation for each executable/script
  - Information on how executables interact in workflows

# Overall Structure

READMEs should follow this hierarchical organization:

1. **Summary**: One paragraph describing the directory's purpose
2. **Structure of the Dir**: List subdirectories and their roles
3. **Description of Files**: Alphabetical list of all files with 1-2 line descriptions
4. **Description of Executables**: Detailed docs for each script/tool
4. **Description of workflows**: How executables are put together to implement
   complex functionalities

# Conventions

- Follow the same conventions of `.claude/skills/markdown.rules.md` for writing text

## Document Structure

### Summary Section
- Single paragraph summarizing the directory's purpose
- Should answer: "What does this directory do?"
- Keep to 2-3 sentences

### Structure of the Dir Section
- Bullet list of subdirectories (if any)
- Format: `- <dirname>/` followed by description
- Describe purpose and role in the larger context

### Description of Files Section
- List all files (scripts, configs, docs) in the directory
- Alphabetical order for consistency
- Format: `- <filename>`: description (1-2 lines max)
- For `.py` and `.sh` files, mention what they do
- For `.md`, `.txt`, `.yaml` files, explain their content/purpose
- Keep descriptions concise and action-oriented

### Description of Executables Section
- One `##` header per executable/tool
- Nest subsections with `###` for internal organization
- Standard subsections for each executable:
  - **What It Does**: Explain purpose and key features (2-5 bullets)
  - **Examples**: Show 3-5 usage patterns with actual code blocks
  - Additional sections as needed: Parameters, Workflow, Features, etc.

## For Each Executable (Under `### ToolName`)

### What It Does
- Use bullet points for clarity
- Describe core functionality
- Mention any key features or modes of operation
- Keep each bullet to one sentence

### Examples
- Show the most common use cases (at least 3-5 examples)
- Order examples from simple to complex
- Include example output if helpful
- Use proper bash code blocks with `> ` prefix (no `$` prompt)

## Format of Commands

- Commands should have a short description as a bullet point, followed by the
  command in a fenced code block
  ```
  - Description of what this command does:
    ```bash
    > command --arg value
    ```
  ```

- Break long commands with `\` for readability, indenting continuation lines by 4 spaces so the command is easy to copy-paste

- Example
  - **Good**:
    ```markdown
    - Generate slides with navigation breadcrumbs:
      ```bash
      > notes_to_pdf.py \
          --input lecture.txt \
          --output lecture.pdf \
          --type slides
      ```
    ```

  - **Bad** (don't mix markdown bold with code):
    ```markdown
    **Generate slides with navigation breadcrumbs:**
    ```bash
    > notes_to_pdf.py --input lecture.txt --output lecture.pdf --type slides
    ```
    ```

## Inline Commands

- Short commands mentioned inline in prose (e.g., `run foo.py`) should stay
  inline with backticks
- Only standalone usage instructions need the bullet + fenced block format

## Tables for Command References

- Use tables (Markdown format) for command/tool listings when there are many related items
- Column headers: Name | Description
- Keep descriptions concise (one sentence)
- Good for: git commands, utility scripts, CLI tools
- Format:
  ```markdown
  | Command | Description |
  | :------- | :------- |
  | `command1` | What it does |
  | `command2` | What it does |
  ```
