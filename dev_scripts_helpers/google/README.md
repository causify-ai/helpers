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
