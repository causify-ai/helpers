Conventions for writing a README for a directory with executables.

# Overall Structure

- READMEs for a directory should follow this hierarchical organization:
  - **Summary**: One paragraph describing the directory's purpose
  - **Structure of the Dir**: List subdirectories with <20-word descriptions
  - **Description of Files**: Alphabetical list of all files with 1-line
    descriptions in a table
  - **Description of Executables**: Detailed docs for each script/tool in a table
  - **Description of Workflows** (optional): How executables combine for complex
    features
  - **Description of Architecture**: How code is organized in each directory

# Writing Conventions

- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
  for text formatting
- Keep descriptions concise and action-oriented
- Limit descriptions to specified word counts

# Section Details

## Summary Section
- Single paragraph describing the directory's purpose in terms of 2-3 short
  bullet points
- Answer: _"What does this directory do?"_

## Structure of the Dir Section
- Bullet list of subdirectories (if any) in a markdown table
- Format: `<dirname>/` followed by description (<20 words)
- Example:
  ```markdown
  | File                                   | Description    |
  | -------------------------------------- | ---------------|
  | `ai.claude_code.how_to_guide_figs/`    | Screenshots and images for Claude Code setup and usage guide |
  | `ai.github_copilot_review.how_to_guide_figs/` | Screenshots demonstrating GitHub Copilot review workflow |
  ```

## Description of Files Section
- List all Python and Markdown files in directory formatted in a markdown table
- Alphabetical order for consistency
- `Description` is a <20 words description
- `Cluster` is the functionality
- Example:
  ```markdown
  | File                                   | Description                                                                  | Cluster             |
  | -------------------------------------- | ---------------------------------------------------------------------------- | ------------------- |
  | `bookmark_utils.py`                    | Shared helpers for downloading/uploading Google Sheets data and CSV files    | Shared Utilities    |
  | `download_academic_paper_to_md.py`     | Download an academic paper (arXiv/DOI/PDF), convert to Markdown, summarize   | Content Downloaders |
  | `download_to_md.py`                    | Detect input type and dispatch to the matching `download_*_to_md.py` script  | Content Downloaders |
  | `download_utils.py`                    | Shared helpers for fetching article titles and summarizing text via an LLM   | Shared Utilities    |
  | `podcast_dl.py`                        | Download and format a podcast transcript from various sources                | Podcast Tools       |
  ```

## Description of Executables Section (if Applicable)

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
- Do NOT use bold headers (`**text**`) for example descriptions
- Each example must have a bullet point with description and indented code block

**Example of correct format:**

```markdown
- Generate slides with navigation breadcrumbs:
  ```bash
  > notes_to_pdf.py \
      --input lecture.txt \
      --output lecture.pdf \
      --type slides
  ```
```

### Inline Commands

- Short commands in prose (e.g., `run foo.py`) stay inline with backticks
- Only standalone usage instructions use bullet + fenced block format

## Description of Workflows (if Applicable)

- How executables combine for complex features

## Description of Architecture (if Applicable)

- TODO(gp): Finish this

# Examples
- `dev_scripts_helpers/documentation/README.md`
- `dev_scripts_helpers/llms/README.md`
- `dev_scripts_helpers/ai/README.md`
- `dev_scripts_helpers/coding_tools/README.md`
