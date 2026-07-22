# Google Drive Tools

Tools for working with Google Drive files and directories. Enables directory
structure analysis, LLM-powered summarization, and conversion between Google
Drive URLs and local filesystem paths.

## Structure of the Dir

This directory has no subdirectories.

## Description of Files

- `__init__.py`
  - Python package initialization file
- `create_google_drive_map.md`
  - Documentation and usage guide for the create_google_drive_map.py script
- `create_google_drive_map.py`
  - Generates directory structure summaries with tree output and LLM analysis
- `to_local_dir.py`
  - Converts Google Drive URLs to local filesystem paths with account detection

# Description of Executables

## `create_google_drive_map.py`

### What It Does

- Generates directory structure summaries from Google Drive folders
- Runs tree command on each directory, then LLM summarizes content
- Combines all summaries into markdown and creates directory metadata tables
- Supports selective action execution with flexible output locations

### Examples

- Process directory with default tree and LLM actions:
  ```bash
  > create_google_drive_map.py --in_dir /path/to/process
  ```

- Run only tree collection without LLM:
  ```bash
  > create_google_drive_map.py --in_dir /path/to/process --action tree
  ```

- Combine existing LLM summaries into single file:
  ```bash
  > create_google_drive_map.py --in_dir /path/to/process --action combine
  ```

- Create metadata table for directories:
  ```bash
  > create_google_drive_map.py --in_dir /path/to/process --action table
  ```

- Process first 3 directories only:
  ```bash
  > create_google_drive_map.py --in_dir /path/to/process --limit 1:3
  ```

- Start fresh from scratch:
  ```bash
  > create_google_drive_map.py --in_dir /path/to/process --from_scratch
  ```

## `to_local_dir.py`

### What It Does

- Converts Google Drive URLs (documents, sheets, files, folders) to local filesystem paths
- Supports automatic account detection across multiple Google accounts
- Searches files/folders by name across configured accounts
- Verifies local path existence and reports status

### Examples

- Convert Google Drive document URL with automatic detection:
  ```bash
  > to_local_dir.py --url "https://docs.google.com/document/d/1DK-ZWp4EhY-EpdfH66SOsdZcWkM1VE9o/edit"
  ```

- Convert Google Drive folder URL to local path:
  ```bash
  > to_local_dir.py --url "https://drive.google.com/drive/u/0/folders/15eHDd9GUCJp8Y5YSpxJXZGqP0xiGvjfP"
  ```

- Use explicit account specification:
  ```bash
  > to_local_dir.py --url "https://docs.google.com/document/d/1DK-ZWp4EhY-EpdfH66SOsdZcWkM1VE9o/edit" --account causify
  ```

- Find file by name in specific account:
  ```bash
  > to_local_dir.py --file_name "My Document" --account gmail
  ```

- Search with automatic account detection:
  ```bash
  > to_local_dir.py --file_name "My Folder" --account auto
  ```
