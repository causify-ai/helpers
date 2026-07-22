# System Tools

General-purpose developer utilities for file operations, screenshots,
notifications, and editor shortcuts. Provides quick access to common workflow
tasks and system integration.

## Structure of the Dir

This directory has no subdirectories.

## Description of Files

- `capture_notebook_cells.py`
  - Extract specific cells from Jupyter notebooks as PNG images
- `compress_files.sh`
  - Compress files using gzip in a directory tree
- `create_links.py`
  - Create symbolic links in bulk for directory linking
- `email_notify.py`
  - Send email notifications via SMTP
- `extract_cfile.py`
  - Extract code from C-style vim cfile format
- `ffind.py`
  - Find files and directories by name pattern
- `fix_perms.sh`
  - Fix file permissions recursively in a directory tree
- `git_fix_perms.sh`
  - Correct git repository file permissions
- `lib_rig.py`
  - Library and rig management utilities
- `mdm_utils.py`
  - Markdown management utilities and helpers
- `remove_empty_lines.sh`
  - Remove blank lines from files
- `remove_escape_chars.py`
  - Strip escape characters from text files
- `remove_redundant_paths.sh`
  - Remove duplicate and nested paths from a list
- `remove_symlink.sh`
  - Remove symbolic links safely
- `replace_text.py`
  - Search and replace text across multiple files
- `save_screenshot.py`
  - Capture macOS screen regions interactively as PNG
- `tg.py`
  - Send notifications via Telegram
- `tree.sh`
  - Display directory tree listing
- `website_screenshot.py`
  - Capture full-page screenshots of URLs using Playwright
- `zip_files.py`
  - Compress files into ZIP archives

# Description of Executables

## `save_screenshot.py`

### What It Does

- Captures macOS screen regions interactively with mouse selection
- Saves screenshots as PNG files with customizable output location
- Supports full screen or region capture with visual feedback

### Examples

- Capture screen region and save as PNG:
  ```bash
  > save_screenshot.py
  ```

## `website_screenshot.py`

### What It Does

- Captures full-page website screenshots using Playwright headless browser
- Saves rendered output as PNG for documentation or testing
- Supports multiple pages and custom viewport sizes

### Examples

- Capture full webpage:
  ```bash
  > website_screenshot.py --url "https://example.com" --output screenshot.png
  ```

## `ffind.py`

### What It Does

- Finds files and directories by name pattern or glob expression
- Supports recursive directory search with multiple filters
- Outputs results suitable for pipeline processing

### Examples

- Find Python files in directory tree:
  ```bash
  > ffind.py --pattern "*.py" /path/to/search
  ```

## `replace_text.py`

### What It Does

- Search and replace text across multiple files
- Supports regex patterns and file type filtering
- Provides preview and dry-run modes before applying changes

### Examples

- Replace text in files:
  ```bash
  > replace_text.py --search "old" --replace "new" /path/to/files
  ```

## `tg.py`

### What It Does

- Sends notifications via Telegram bot
- Integrates with system messages and alerts
- Requires Telegram API configuration

### Examples

- Send Telegram notification:
  ```bash
  > tg.py "Your message here"
  ```

## `email_notify.py`

### What It Does

- Sends email notifications via SMTP
- Supports HTML and plain text email formats
- Configurable sender and recipient addresses

### Examples

- Send email notification:
  ```bash
  > email_notify.py --to recipient@example.com --subject "Alert" --body "Message"
  ```

## `create_links.py`

### What It Does

- Creates symbolic links in bulk for multiple files or directories
- Supports batch link creation with pattern matching
- Preserves link structure for directory hierarchies

### Examples

- Create symbolic links:
  ```bash
  > create_links.py --source /path/to/source --destination /path/to/links
  ```
