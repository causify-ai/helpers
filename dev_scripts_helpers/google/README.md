# Google Tools

CLI tools for Google Drive, Sheets, and Docs: bidirectional CSV/Sheets
transfer, Drive backup via `rclone`, Doc export via `gws`, directory mapping,
and Drive-URL-to-local-path conversion.

## Structure of the Dir

This directory has no subdirectories.

## Description of Files

| File                          | Description                                                                    | Cluster           |
| ------------------------------ | ------------------------------------------------------------------------------- | ------------------ |
| `create_google_drive_map.md`   | Documentation and usage guide for `create_google_drive_map.py`                  | Directory Mapping  |
| `create_google_drive_map.py`   | Generate per-subdirectory tree output and LLM summaries, combine into a map     | Directory Mapping  |
| `from_gsheet.py`               | Download a Google Sheets tab and save it as a CSV file                          | Google Sheets      |
| `gdrive_backup.py`             | List, back up, export, or import a Google Drive directory via `rclone`          | Backup & Sync      |
| `gws_download_doc.py`          | Download a Google Doc to PDF, Word, Markdown, or other formats via `gws`        | Google Docs        |
| `to_gsheet.py`                 | Upload a CSV file to a tab in a Google Sheets document                          | Google Sheets      |
| `to_local_dir.py`              | Convert a Google Drive URL to its local CloudStorage filesystem path            | Path Conversion    |

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

## `gdrive_backup.py`

### What It Does

- Lists, backs up, exports, or imports a Google Drive directory via `rclone`
- `backup` clones data locally, then compresses it into a timestamped `.tgz`
- `export`/`import` move data between the local filesystem and Drive without
  archiving
- Requires `rclone` to be configured with a remote pointing at the Drive
  account (see script header comments)

### Examples

- List the content of a Google Drive directory:
  ```bash
  > gdrive_backup.py \
      --action ls \
      --src_dir gp_drive:alphamatic \
      -v DEBUG
  ```

- Back up a Google Drive directory to a local, compressed archive:
  ```bash
  > gdrive_backup.py \
      --action backup \
      --src_dir gp_drive:alphamatic \
      --dst_dir gdrive_backup
  ```

- Export a subdirectory to plain local files:
  ```bash
  > gdrive_backup.py \
      --action export \
      --src_dir gp_drive:alphamatic/LLC \
      --dst_dir tmp.LLC
  ```

- Import previously exported data back into a Google Drive directory:
  ```bash
  > gdrive_backup.py \
      --action import \
      --src_dir tmp.alphamatic \
      --dst_dir alphamatic_drive:alphamatic
  ```

## `gws_download_doc.py`

### What It Does

- Downloads a Google Doc via the `gws` CLI to a file, format inferred from the
  output extension (`pdf`, `docx`, `odt`, `rtf`, `txt`, `html`, `md`, `epub`,
  `zip`)
- Auto-generates the output filename from the document title when
  `--to_dir` is used instead of `--to_file`
- Requires `gws` to be installed and authenticated (`gws auth login`)

### Examples

- Download a Google Doc as PDF to an explicit file path:
  ```bash
  > gws_download_doc.py \
      --from_url https://docs.google.com/document/d/ABC123/edit \
      --to_file document.pdf
  ```

- Download a Google Doc as Markdown:
  ```bash
  > gws_download_doc.py \
      --from_url https://docs.google.com/document/d/ABC123/edit \
      --to_file document.md
  ```

- Download to a directory, auto-generating the filename from the doc title:
  ```bash
  > gws_download_doc.py \
      --from_url https://docs.google.com/document/d/ABC123/edit \
      --to_dir ./output
  ```

- Auto-generate the filename with a specific extension:
  ```bash
  > gws_download_doc.py \
      --from_url https://docs.google.com/document/d/ABC123/edit \
      --to_dir ./output \
      --extension docx
  ```

## `create_google_drive_map.py`

### What It Does

- Runs `tree` on each subdirectory of `--in_dir` and summarizes it with an LLM
  (`gpt-4o-mini`)
- Combines all per-directory summaries into a single `google_drive_map.md`
- Optionally builds a `directory_table.md` with owner/department/content
  metadata
- Actions (`tree`, `llm`, `combine`, `table`) can be selected, skipped, or
  restricted to a subset

### Examples

- Process a directory using the default actions (tree and llm):
  ```bash
  > create_google_drive_map.py --in_dir /path/to/process
  ```

- Run all available actions (tree, llm, combine, table):
  ```bash
  > create_google_drive_map.py \
      --in_dir /path/to/process \
      --all_actions
  ```

- Process only the first 3 directories, saving to a custom output directory:
  ```bash
  > create_google_drive_map.py \
      --in_dir /path/to/process \
      --limit 1:3 \
      --out_dir analysis
  ```

- Combine existing per-directory LLM outputs into one markdown file:
  ```bash
  > create_google_drive_map.py \
      --in_dir /path/to/process \
      --clear_actions --action combine \
      --out_dir existing_results
  ```

- Start fresh by deleting the existing output directory first:
  ```bash
  > create_google_drive_map.py --in_dir /path/to/process --from_scratch
  ```

## `to_local_dir.py`

### What It Does

- Converts a Google Drive URL (Doc, Sheet, file, or folder) to its local
  CloudStorage path under one of three configured accounts (`causify`,
  `gmail`, `umd`)
- Auto-detects the account by searching each account's local folder tree when
  `--account` is not given
- Also accepts a bare `--file_name` to search for instead of a URL

### Examples

- Automatic account detection for a document:
  ```bash
  > to_local_dir.py \
      --url "https://docs.google.com/document/d/1DK-ZWp4EhY-EpdfH66SOsdZcWkM1VE9o/edit"
  ```

- Automatic account detection for a folder:
  ```bash
  > to_local_dir.py \
      --url "https://drive.google.com/drive/u/0/folders/15eHDd9GUCJp8Y5YSpxJXZGqP0xiGvjfP"
  ```

- Specify the account explicitly:
  ```bash
  > to_local_dir.py \
      --url "https://docs.google.com/document/d/1DK-ZWp4EhY-EpdfH66SOsdZcWkM1VE9o/edit" \
      --account causify
  ```

- Look up a local path by file name instead of URL:
  ```bash
  > to_local_dir.py --file_name "My Document" --account gmail
  ```
