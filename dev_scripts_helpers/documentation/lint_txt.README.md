# lint_txt.py

- Automated formatter for markdown, LaTeX, and plain text files
- Applies a series of transformations to normalize and improve document structure
- Protects code blocks and comments from formatting changes
- Creates backups before processing and supports reverting changes

## Overview

- `lint_txt.py` processes text documents through a pipeline of formatting
  actions
- Each action transforms specific aspects of the text, from fixing spacing and
  punctuation to handling markdown formatting and validating links

- Supported file types
  - `.md` (markdown)
  - `.tex` (LaTeX)
  - `.txt` (plain text)
  - `.emd` (enhanced markdown)
- Input/output modes: File-based (single or multiple) or stdin/stdout
- Safety features: Automatic backups, revert capability, action filtering

## Quick Start

- Format a markdown file:
  ```bash
  > ./lint_txt.py --in my_file.md
  ```

- Format multiple files:
  ```bash
  > ./lint_txt.py --in file1.md file2.md file3.md
  ```

- Process stdin/stdout:
  ```bash
  > cat my_file.md | ./lint_txt.py --type md
  ```

- Revert a file from backup:
  ```bash
  > ./lint_txt.py --in my_file.md --revert
  ```

- Run specific actions only:
  ```bash
  > ./lint_txt.py --in my_file.md --action preprocess prettier postprocess
  ```

## Available Actions

### Text Processing Actions

- **preprocess**: Handle Google Docs artifacts, convert special characters, format math equations
  - Removes smart quotes, replaces ellipsis (`…` to `...`)
  - Converts bullet markers (`•` to `-`, `*` to temporary markers)
  - Formats math blocks for better readability
  - Collapses multiple blank lines

- **prettier**: Format text with prettier or alternative backends
  - Markdown: supports `prettier`, `mdformat`, `flowmark` backends
  - LaTeX and text: uses prettier
  - Configurable line width (default: 80 characters)
  - Can run in Docker or globally

- **postprocess**: Restore preprocessed content and apply final formatting
  - Undoes temporary bullet markers (`STAR`, `SSTAR` back to `*`, `**`)
  - Capitalizes first letter of list items and numbered lists
  - Handles edge cases from prettier processing

### Structural Actions

- **remove_page_separators**: Remove `---` lines (YAML separators, page breaks)

- **handle_empty_lines**: Remove empty lines in specific contexts
  - After markdown headers
  - Between text and code blocks

- **add_blank_lines_between_headers**: Insert blank line between consecutive headers
  - Improves readability and markdown compliance

- **capitalize_header**: Capitalize first letter of all headers

- **frame_chapters**: Add visual frames around chapter headers
  - Text files: adds ASCII frames
  - LaTeX files: formats sections

### Bullet and List Actions

- **convert_asterisk_bullets_to_dashes**: Normalize `* ` bullets to `- `
  - Ensures consistent bullet point formatting

- **remove_trailing_periods**: Strip trailing periods from lines
  - Useful for markdown lists and headers
  - Removes all periods at line end

- **replace_em_dash_with_colon**: Convert em dash to colon in list definitions
  - Pattern: `text — description` becomes `text: description`
  - Common in reference lists

### Formatting Removal

- **remove_markdown_formatting**: Strip markdown syntax while preserving content
  - Removes: bold (`**text**`), italic (`*text*`, `_text_`), strikethrough (`~~text~~`)
  - Removes: inline code (`` `code` ``), links (`[text](url)`), images (`![alt](url)`)
  - Preserves code block content unchanged
  - Useful for converting markdown to plain text

### Code Block Actions

- **remove_code_block_extra_indentation**: Fix indentation added by prettier
  - Removes unwanted indentation in code blocks
  - Preserves intended indentation structure
  - Runs after content restoration to handle side effects

### Advanced Actions

- **refresh_toc**: Regenerate table of contents for markdown files
  - Scans headers and creates/updates TOC section
  - Configurable depth and formatting

- **check_links**: Validate all URLs in the file
  - Calls separate `check_links.py` script
  - Reports broken links without failing
  - Supports HTTP/HTTPS requests

## Command Line Options

### Input/Output

- `--in <file>`: Input file (or `-` for stdin)
- `--out <file>`: Output file (defaults to `--in` for in-place editing)
- `--type <type>`: File type when using stdin (required for stdin input)
  - Options: `md`, `tex`, `txt`

### Formatting Configuration

- `-w, --width <width>`: Maximum line width (default: 80)
  - Applied by prettier during formatting

- `--backend <backend>`: Markdown formatting backend (markdown files only)
  - Options: `prettier`, `mdformat`, `flowmark`
  - Default: uses legacy prettier

- `--mode <mode>`: Execution mode for backend
  - `prettier`: `dockerized` or `global`
  - `mdformat`: `library`, `uvx`, or `global`
  - `flowmark`: `library`, `uvx-rs`, `uvx`, `global`, or `global-rs`

### Docker and Prettier Control

- `--use_dockerized_prettier`: Use Docker version of prettier (default: enabled)
- `--no_use_dockerized_prettier`: Use global prettier installation
- `--use_dockerized_markdown_toc`: Use Docker version for TOC (default: enabled)
- `--no_use_dockerized_markdown_toc`: Use global markdown-toc

### Action Control

- `--action <action> ...`: Run only specified actions
  - Omit to run all default actions
  - Multiple actions can be listed

- `--revert`: Restore file from backup copy
  - Requires input file
  - Looks for backup created before processing

### Other Options

- `-v, --verbosity <level>`: Set logging verbosity
  - `debug`, `info`, `warning`, `error`

## Architecture

### Processing Pipeline

- Protected content extraction (code blocks, comments, math)
- Preprocess (normalize input, handle artifacts)
- Prettier (format according to style guide)
- Postprocess (restore temporary markers, finalize)
- Structural adjustments (spacing, separators)
- Advanced transformations (markdown removal, link checking)
- Content restoration (re-insert protected blocks)
- Output writing

### Content Protection

- Code blocks (triple backticks) are extracted before formatting and restored after
- Comments and math blocks are protected from markdown removal
- YAML front matter (markdown files) is extracted and reattached
- Preserves literal content that should not be modified by formatters

### File Type Handling

- **Markdown files** (`.md`):
  - Extracts and preserves YAML front matter
  - Supports multiple formatting backends
  - Can refresh table of contents
  - Handles markdown-specific transformations

- **LaTeX files** (`.tex`):
  - Sections handled by frame_chapters action
  - Code blocks protected during formatting
  - Math mode content preserved

- **Plain text files** (`.txt`):
  - Chapters framed with ASCII decorations
  - No markdown syntax processing
  - All lines treated as content

### Backup System

- Backup filename: `tmp.lint_txt.<original_filename>`
  - E.g., `my_file.md` -> `tmp.lint_txt.my_file.md`
- Created in same directory as original
- Automatically created before in-place processing
- Used by `--revert` option to restore original

## Examples

### Format with All Default Actions

```bash
> ./lint_txt.py --in documentation.md
```

### Format and Refresh Table of Contents

```bash
> ./lint_txt.py --in documentation.md --action preprocess prettier postprocess refresh_toc
```

### Convert Markdown to Plain Text

```bash
> ./lint_txt.py --in content.md --action remove_markdown_formatting --out content.txt
```

### Check Links Only

```bash
> ./lint_txt.py --in documentation.md --action check_links
```

### Process with Custom Line Width

```bash
> ./lint_txt.py --in article.md --width 100
```

### Use Alternative Markdown Backend

```bash
> ./lint_txt.py --in document.md --backend mdformat --mode library
```

### Revert Previous Formatting

```bash
> ./lint_txt.py --in document.md --revert
```

### Process Multiple Files

```bash
> ./lint_txt.py --in chapter1.md chapter2.md chapter3.md
```

## Notes and Considerations

- **In-place editing**: Backup created before processing, can be reverted
- **Google Docs artifacts**: Removes smart quotes, ellipsis, and other copy-paste artifacts
- **Code block preservation**: Content inside triple backticks is never reformatted
- **Markdown syntax**: Remove formatting action converts markdown to plain text, not safe for all documents
- **Link checking**: Broken links logged but don't fail the process
- **Performance**: Docker-based formatters may have startup overhead
- **Math blocks**: LaTeX math blocks (delimited by `$$`) are protected and not reformatted

## Related Files

- Documentation toolchain guide: `docs/tools/documentation_toolchain/all.notes_toolchain.how_to_guide.md`
