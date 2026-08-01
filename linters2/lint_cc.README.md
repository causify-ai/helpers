# lint_cc.py

Claude Code integration for topic-based intelligent formatting.

## What It Does

- Invokes Claude Code with intelligent topic-based or skill-based linting rules
- Detects file types by extension and path pattern to select appropriate rules
- Integrates with Claude rules and skills system for formatting and validation
- Supports batch processing with progress bars for multiple files

## Examples

- Format specific Python files:
  ```bash
  > lint_cc.py --files "file1.py file2.py"
  ```

- Apply a specific coding rule to a file:
  ```bash
  > lint_cc.py --topic coding --files "file.py"
  ```

- Lint modified files in the repository:
  ```bash
  > lint_cc.py --modified
  ```

- Preview command without executing (dry-run):
  ```bash
  > lint_cc.py --dry_run --files "*.md"
  ```

- Process multiple files with progress feedback:
  ```bash
  > lint_cc.py --files "src/*.py" --topic coding
  ```

- Use a different model:
  ```bash
  linters2/lint_cc.py --files dev_scripts_helpers/scraping/download_link_articles.py --skill "coding.add_comments" --model deepseek/deepseek-v4-flash
  ```

- Execute a rule on a single file using one of these formats:
  - Full path (path:line:header format with header validation)
    ```
    --rule ".claude/skills/coding.rules.md:58:## Mark Private Functions"
    ```
  - Line number only (extracts the section starting at that line)
    ```
    --rule ".claude/skills/coding.rules.md:58"
    ```
  - Keyword search: (searches for unique matching rule using rigrule)
    ```
    --rule "dassert"
    ```
