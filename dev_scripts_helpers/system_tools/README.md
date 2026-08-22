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
- `mdm`
  - Unified markdown file manager (command-line tool)
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
  - Save an image from an interactive macOS screenshot, the clipboard, or a URL
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

- Saves an image to a file, from one of three sources:
  - An interactive macOS screen region capture (default)
  - The system clipboard (`--from_clipboard`)
  - A URL (`--url`)
- Saves the image under `--path` (created if missing), with a custom
  `--filename` or a timestamped default name
- For `--url`, infers the `png`, `jpg`, `jpeg` extension from the URL
  - Screenshots and clipboard pastes are always saved as PNG
- On macOS, copies a Markdown image reference (`![](path)`) to the clipboard

### Examples

- Capture a screen region interactively and save as PNG:
  ```bash
  > save_screenshot.py
  ```

- Save the image currently on the clipboard:
  ```bash
  > save_screenshot.py --from_clipboard
  ```

- Download an image from a URL:
  ```bash
  > save_screenshot.py --url https://example.com/image.png
  ```

- Save into a specific dir with a specific file name:
  ```bash
  > save_screenshot.py --from_clipboard --path msml610/lectures_source/figures --filename Lesson12_4x3_environment.png
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

## `mdm` — Markdown Manager

### What It Does

- Unifies management of research ideas, blog posts, and Claude Code skills across
  multiple repositories into one powerful command-line tool. Replaces separate
  command families (`skill*`, `blog*`, `res*`, `story*`) with a consistent
  interface.

### Content Types Managed

- **skill**: Claude Code skills in `<helpers_root>/.claude/skills/`
- **blog**: Blog posts in `<blog_repo>/blog/posts/`
- **research**: Research ideas in `<umd_classes1>/research/ideas/`
- **story**: Short stories in `<notes1>/short_stories/`

### Core Actions

- **list**: List markdown files with optional filtering
  - Shows skill names only for skills
  - Shows full file paths for other content types
  - Supports optional name filters to narrow results
- **full_list**: Display all markdown files with complete paths
  - Useful for seeing directory structure
- **describe**: Show descriptions of markdown files
  - Works primarily with skills containing metadata
- **edit**: Open file in vim with automatic template generation
  - Creates new files with appropriate templates if they don't exist
  - Blog posts: YAML frontmatter with title, author, date, TL;DR
  - Skills: Summary section headers
  - Research: Headers with idea names
- **directory**: Print the directory path for given type
  - Useful for scripting and automation
- **types**: Print unique prefixes before first dot

### Smart Prefix Matching

Both type and action arguments support prefix matching (first match wins):

**Type Prefixes:**
- `sk` → `skill`
- `bl` → `blog`
- `res` → `research`
- `st` → `story`

**Action Prefixes:**
- `l` → `list`
- `f` → `full_list`
- `d` → `describe` or `directory` (first match)
- `e` → `edit`
- `t` → `types`

### Examples

- List all skills:
  ```bash
  > mdm skill list
  ```

- See full paths for all skills:
  ```bash
  > mdm skill full_list
  ```

- Filter research items by pattern:
  ```bash
  > mdm research list causal
  ```

- Create or edit a new blog post:
  ```bash
  > mdm blog edit My_New_Post
  ```

- Get the directory path for a content type:
  ```bash
  > mdm research directory
  ```

- See unique content types in skills:
  ```bash
  > mdm skill types
  ```

- Use prefix shortcuts:
  ```bash
  > mdm bl l              # Same as: mdm blog list
  > mdm sk e my_skill     # Same as: mdm skill edit my_skill
  > mdm res d             # Same as: mdm research directory
  ```
