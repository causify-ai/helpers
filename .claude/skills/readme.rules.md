Conventions for writing a README for a directory with executables.

# Overall Structure

- READMEs should follow this hierarchical organization:

1. **Summary**: One paragraph describing the directory's purpose
2. **Structure of the Dir**: List subdirectories with <20-word descriptions
3. **Description of Files**: Alphabetical list of all files with 1-line descriptions
4. **Description of Executables**: Detailed docs for each script/tool
5. **Description of Workflows** (optional): How executables combine for complex features

# Writing Conventions

- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
  for text formatting
- Keep descriptions concise and action-oriented
- Limit descriptions to specified word counts

# Section Details

## Summary Section
- Single paragraph describing the directory's purpose in terms of 2-3 short
  bullet points
- Answer: "What does this directory do?"

## Structure of the Dir Section
- Bullet list of subdirectories (if any)
- Format: `- <dirname>/` followed by description (<20 words)
- Example:
  ```markdown
  - `ai.claude_code.how_to_guide_figs/`
    - Screenshots and images for Claude Code setup and usage guide
  - `ai.github_copilot_review.how_to_guide_figs/`
    - Screenshots demonstrating GitHub Copilot review workflow
  ```

## Description of Files Section
- List all Python and Markdown files in directory
- Alphabetical order for consistency
- Format: `- <filename>` with description (<20 words)
- Example:
  ```markdown
  - `ai.coding.prompt.md`
    - Python coding standards including assertions, logging patterns, and script templates
  - `ai.unit_test.prompt.md`
    - Unit testing conventions including test structure, naming patterns, and golden file testing
  ```

## Description of Executables Section

Find all executable files and create one `##` header per tool.

### Tables for Command References

- Find all executable filesS
- Use Markdown tables for many related commands
- Column headers: Name | Description
- One-sentence descriptions
- Good for: git commands, utility scripts, CLI tools
- Format:
  ```markdown
  | Command | Description |
  | :------- | :------- |
  | `command1` | What it does |
  | `command2` | What it does |
  ```

### For Each Executable

- Find all executable files and create one `##` header per tool

- **What It Does**: 1-3 bullets describing tool's purpose
  - Mention important inputs, outputs, and side effects
  - Use bullet points for clarity
  - Keep each bullet to one sentence

- **Examples**: 3-5 realistic usage patterns ordered simple → complex
  - Start with short description
  - Follow with fenced bash code block (see format rules below)
  - Include example output if helpful

### Format of Commands

- Commands as bullet + fenced code block:
  ````markdown
  - Description of what this command does:
    ```bash
    > command --arg value
    ```
  ````

- Break long commands with `\` for readability, indent continuation lines by 4 spaces:
  ````markdown
  - Generate slides with navigation breadcrumbs:
    ```bash
    > notes_to_pdf.py \
        --input lecture.txt \
        --output lecture.pdf \
        --type slides
    ```
  ````

- Use `> ` prefix (no `$` prompt)

- **Bad**: Don't mix markdown bold with code:
  ```markdown
  **Generate slides:**
  ```bash
  > notes_to_pdf.py --input lecture.txt --output lecture.pdf
  ```
  ```

### Inline Commands

- Short commands in prose (e.g., `run foo.py`) stay inline with backticks
- Only standalone usage instructions use bullet + fenced block format
