<!-- toc -->

- [Summary](#summary)
- [Description of Files](#description-of-files)
- [Description of Executables](#description-of-executables)
  * [`to_gsheet.py`](#to_gsheetpy)
    + [What It Does](#what-it-does)
    + [Examples](#examples)
  * [`from_gsheet.py`](#from_gsheetpy)
    + [What It Does](#what-it-does-1)
    + [Examples](#examples-1)

<!-- tocstop -->

# Summary

This directory contains CLI tools for interacting with Google Sheets, enabling
bidirectional data transfer between CSV files and Google Sheets documents. The
tools use the Google Sheets API (via `helpers/hgoogle_drive_api.py`) to read
and write spreadsheet data.

# Description of Files

- `to_gsheet.py`
  - Upload CSV data to Google Sheets with tab management and overwrite protection
- `from_gsheet.py`
  - Download Google Sheets data to CSV files with file overwrite protection

# Description of Executables

## `to_gsheet.py`

### What It Does

- Reads a CSV file and uploads it to a specified Google Sheets document tab.
- Prints information about the target Google Sheet including file name, tab names, and folder path.
- Protects against accidental overwrites by requiring `--overwrite` flag when tab exists.
- Automatically freezes the header row and sets row height for better readability.

### Examples

- Upload CSV to a new tab:
  ```bash
  > to_gsheet.py \
      --input_file data.csv \
      --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
      --tabname "my_data"
  ```

- Overwrite existing tab with new data:
  ```bash
  > to_gsheet.py \
      --input_file data.csv \
      --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
      --tabname "my_data" \
      --overwrite
  ```

- Upload to default tab name with verbose logging:
  ```bash
  > to_gsheet.py \
      --input_file data.csv \
      --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
      -v DEBUG
  ```

## `from_gsheet.py`

### What It Does

- Downloads data from a Google Sheets document and saves it as a CSV file.
- Prints information about the source Google Sheet including file name, tab names, and folder path.
- Protects against accidental overwrites by requiring `--overwrite` flag when output file exists.
- Can read from a specific tab or default to the first sheet if tab name not specified.

### Examples

- Download first tab to CSV:
  ```bash
  > from_gsheet.py \
      --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
      --output_file data.csv
  ```

- Download specific tab to CSV:
  ```bash
  > from_gsheet.py \
      --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
      --tabname "my_data" \
      --output_file data.csv
  ```

- Overwrite existing CSV file:
  ```bash
  > from_gsheet.py \
      --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
      --tabname "my_data" \
      --output_file data.csv \
      --overwrite
  ```

- Download with verbose logging:
  ```bash
  > from_gsheet.py \
      --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
      --output_file data.csv \
      -v DEBUG
  ```
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
  - Converts Google Drive URLs (documents, sheets, files, or folders) to local directory paths

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

- Converts Google Drive URLs (documents, sheets, files, or folders) to local file system paths
- Supports automatic account detection across multiple Google Drive accounts (causify, gmail, umd)
- Can search for files or folders by name across all configured accounts
- Verifies if the local path exists and reports the result

#### Examples

- Convert a Google Drive document URL to local path with automatic account detection:
  ```bash
  > ./to_local_dir.py --url "https://docs.google.com/document/d/1DK-ZWp4EhY-EpdfH66SOsdZcWkM1VE9o/edit"
  ```

- Convert a Google Drive folder URL to local path:
  ```bash
  > ./to_local_dir.py --url "https://drive.google.com/drive/u/0/folders/15eHDd9GUCJp8Y5YSpxJXZGqP0xiGvjfP"
  ```

- Convert a URL with explicit account specification:
  ```bash
  > ./to_local_dir.py --url "https://docs.google.com/document/d/1DK-ZWp4EhY-EpdfH66SOsdZcWkM1VE9o/edit" --account causify
  ```

- Find a file or folder by name in a specific account:
  ```bash
  > ./to_local_dir.py --file_name "My Document" --account gmail
  ```

- Find a file or folder by name with automatic account detection:
  ```bash
  > ./to_local_dir.py --file_name "My Folder" --account auto
  ```
