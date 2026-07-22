# Google Sheets

CLI tools for bidirectional data transfer between CSV and Google Sheets. Uses
Google Sheets API to read and write spreadsheet data with tab management and
overwrite protection.

## Structure of the Dir

This directory has no subdirectories.

## Description of Files

- `from_gsheet.py`
  - Download Google Sheets data to CSV files with overwrite protection
- `to_gsheet.py`
  - Upload CSV data to Google Sheets with tab management

# Description of Executables

## `to_gsheet.py`

### What It Does

- Uploads CSV file data to specified Google Sheets document tab
- Freezes header row and formats row height for readability
- Protects against accidental overwrites with `--overwrite` flag requirement
- Reports target sheet metadata (name, tabs, folder path)

### Examples

- Upload CSV to new tab:
  ```bash
  > to_gsheet.py \
      --input_file data.csv \
      --url "https://docs.google.com/spreadsheets/d/..." \
      --tabname "my_data"
  ```

- Overwrite existing tab with new data:
  ```bash
  > to_gsheet.py \
      --input_file data.csv \
      --url "https://docs.google.com/spreadsheets/d/..." \
      --tabname "my_data" \
      --overwrite
  ```

- Run with verbose logging:
  ```bash
  > to_gsheet.py \
      --input_file data.csv \
      --url "https://docs.google.com/spreadsheets/d/..." \
      -v DEBUG
  ```

## `from_gsheet.py`

### What It Does

- Downloads data from Google Sheets document and saves as CSV
- Protects against accidental overwrites with `--overwrite` flag requirement
- Reports source sheet metadata (name, tabs, folder path)
- Supports specific tab selection or default first sheet

### Examples

- Download first tab to CSV:
  ```bash
  > from_gsheet.py \
      --url "https://docs.google.com/spreadsheets/d/..." \
      --output_file data.csv
  ```

- Download specific tab:
  ```bash
  > from_gsheet.py \
      --url "https://docs.google.com/spreadsheets/d/..." \
      --tabname "my_data" \
      --output_file data.csv
  ```

- Overwrite existing file:
  ```bash
  > from_gsheet.py \
      --url "https://docs.google.com/spreadsheets/d/..." \
      --tabname "my_data" \
      --output_file data.csv \
      --overwrite
  ```

- Run with verbose output:
  ```bash
  > from_gsheet.py \
      --url "https://docs.google.com/spreadsheets/d/..." \
      --output_file data.csv \
      -v DEBUG
  ```
