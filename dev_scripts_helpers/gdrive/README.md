# Google Drive Tools

This directory contains tools for working with Google Drive files and directories.

## Structure of the Dir

This directory has no subdirectories.

## Description of Files

- `__init__.py`
  - Python package initialization file
- `create_google_drive_map.md`
  - Documentation for the create_google_drive_map.py script
- `create_google_drive_map.py`
  - Processes directories by generating tree output and creating AI summaries with LLM
- `to_local_dir.py`
  - Converts Google Drive document links to local directory paths

## Description of Executables

### `create_google_drive_map.py`

#### What It Does

- Processes directories by generating tree output and creating AI summaries
- Runs tree command on each directory, then uses LLM to summarize the content
- Can combine all summaries into a single markdown file and create directory metadata tables
- Supports selective action execution and custom output locations

#### Examples

- Process a directory with default settings (tree and LLM actions):
  ```bash
  > ./create_google_drive_map.py --in_dir /path/to/process
  ```

- Process directories and save output to a custom location:
  ```bash
  > ./create_google_drive_map.py --in_dir /path/to/analyze --out_dir results
  ```

- Run only the tree action on directories:
  ```bash
  > ./create_google_drive_map.py --in_dir /path/to/process --action tree
  ```

- Combine existing LLM outputs into a single markdown file:
  ```bash
  > ./create_google_drive_map.py --in_dir /path/to/process --action combine --out_dir existing_results
  ```

- Process only the first 3 directories:
  ```bash
  > ./create_google_drive_map.py --in_dir /path/to/process --limit 1:3
  ```

- Start fresh by deleting existing output directory:
  ```bash
  > ./create_google_drive_map.py --in_dir /path/to/process --from_scratch
  ```

### `to_local_dir.py`

#### What It Does

- Converts Google Drive document URLs to local file system paths
- Supports automatic account detection across multiple Google Drive accounts (causify, gmail, umd)
- Can search for files by name across all configured accounts
- Verifies if the local path exists and reports the result

#### Examples

- Convert a Google Drive URL to local path with automatic account detection:
  ```bash
  > ./to_local_dir.py --url "https://docs.google.com/document/d/1DK-ZWp4EhY-EpdfH66SOsdZcWkM1VE9o/edit"
  ```

- Convert a URL with explicit account specification:
  ```bash
  > ./to_local_dir.py --url "https://docs.google.com/document/d/1DK-ZWp4EhY-EpdfH66SOsdZcWkM1VE9o/edit" --account causify
  ```

- Find a file by name in a specific account:
  ```bash
  > ./to_local_dir.py --file_name "My Document" --account gmail
  ```

- Find a file by name with automatic account detection:
  ```bash
  > ./to_local_dir.py --file_name "My Document" --account auto
  ```
