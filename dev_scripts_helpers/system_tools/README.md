# system_tools/

General-purpose developer system utilities: file operations, screenshots,
notifications, editor shortcuts, and other everyday workflow tools.

## Screenshots & Capture

- **[save_screenshot.py](save_screenshot.py)**: Capture a macOS screen region
  (interactive) and save as PNG.
- **[website_screenshot.py](website_screenshot.py)**: Capture a full-page
  screenshot of a URL using Playwright (headless browser).
- **[capture_notebook_cells.py](capture_notebook_cells.py)**: Extract specific
  cells from a Jupyter notebook as an image.

## File Operations

- **[ffind.py](ffind.py)**: Find files/dirs by name pattern.
- **[replace_text.py](replace_text.py)**: Search and replace text across files.
- **[zip_files.py](zip_files.py)**: Compress files in a directory tree.
- **[compress_files.sh](compress_files.sh)**: Compress files using gzip.
- **[create_links.py](create_links.py)**: Create symbolic links in bulk.
- **[extract_cfile.py](extract_cfile.py)**: Extract code from C-style files.
- **[remove_escape_chars.py](remove_escape_chars.py)**: Strip escape characters
  from text files.
- **[remove_empty_lines.sh](remove_empty_lines.sh)**: Remove blank lines from
  files.
- **[remove_redundant_paths.sh](remove_redundant_paths.sh)**: Remove duplicate
  or nested paths from a list.
- **[remove_symlink.sh](remove_symlink.sh)**: Remove a symbolic link.
- **[fix_perms.sh](fix_perms.sh)**: Fix file permissions in a directory tree.

## Notifications & Messaging

- **[tg.py](tg.py)**: Send a notification via Telegram.
- **[email_notify.py](email_notify.py)**: Send an email notification.

## Editor Shortcuts (vi* / v* helpers)

Quick-launch scripts that open files in `vim` with various filters:

- **`viack`**: Open vim on files matching an `ack`/`ag` search.
- **`vic`**: Open vim on files matching a pattern.
- **`vif`**: Open vim on files from `find`.
- **`vil`**: Open vim on files from `locate`.
- **`vile`**: Open vim on files ending with a given extension.
- **`vit`**: Open vim on files from a tag list.
- **`viw`**: Open vim with a word/phrase search.
- **`vi_all_py.sh`**: Open all Python files in vim.
- **`i`** / **`il`** / **`it`**: Shortcut aliases for quick file opening.

## Path & Environment

- **`path`**: Display/manipulate `$PATH`.
- **`print_paths.sh`**: Print each `$PATH` entry on its own line.
- **`export_vars.sh`**: Export environment variables from a file.
- **`mkbak`**: Create a timestamped backup of a file.
- **`mk_targets`**: Generate build targets.

## Development Utilities

- **[tree.sh](tree.sh)**: Directory tree listing.
- **[timestamp](timestamp)**: Print a formatted timestamp.
- **`ack`**: Grep replacement wrapper.
- **[lib_rig.py](lib_rig.py)**: Library / rig management.
- **`mdm`** / **[mdm_utils.py](mdm_utils.py)**: Markdown management utilities.
- **`rig`** / **`rigc`** / **`rigdef`** / **`rigdefc`** / **`rigrule`** / **`rigtodo`** / **`rigtodoc`**: Rig workflow helpers.
- **`vigit`** / **`vigitp`**: Open git-tracked files in vim.
- **[git_fix_perms.sh](git_fix_perms.sh)**: Fix git file permissions.
- **`kga`**: Kubernetes alias helper.
