# Create Google Drive Map

## Purpose

* Tool to Generate Directory Maps
- Generates directory structure maps for Google Drive folders
- Creates AI-powered summaries of directory contents
- Combines outputs into a single navigable document

## Usage

* Basic Command
- Command = `create_google_drive_map.py --in_dir /path/to/drive/folder`

* Common Options
- `--in_dir` = directory to process (required)
- `--out_dir` = output directory (default: tmp.run_tree_and_llm)
- `--from_scratch` = delete output directory before processing
- `--limit` = process specific range of directories (e.g., 1:3)

* Action Control
- Default actions = tree generation + LLM analysis
- `--all` = run all actions (tree, llm, combine, table)
- `--action tree` = only generate tree structures
- `--action llm` = only run AI analysis
- `--action combine` = combine existing outputs
- `--action table` = create directory metadata table
- `--skip_action tree` = skip tree generation

## Workflow

* Processing Steps
- Processes each subdirectory alphabetically
- Steps for each directory:
  - Runs `tree --dirsfirst -n -F --charset unicode`
  - Saves tree structure to `tree_XXX.txt`
  - Analyzes with GPT-4o-mini
  - Saves AI summary to `llm_XXX.txt`
- Combines all summaries into `google_drive_map.md`
- Creates directory metadata table in `directory_table.md`

## Examples

* Full Processing With Custom Settings
```bash
create_google_drive_map.py --in_dir /drive/projects \
  --out_dir analysis
```

* Process First 5 Directories
```bash
create_google_drive_map.py --in_dir /drive/folder --limit 1:5
```

* Combine Existing Results
```bash
create_google_drive_map.py --in_dir /drive/folder \
  --action combine \
  --out_dir existing_results
```

* Start Fresh Analysis
```bash
create_google_drive_map.py --in_dir /drive/folder \
  --from_scratch \
  --all
```

* Create Directory Table Only
```bash
create_google_drive_map.py --in_dir /drive/folder \
  --action table \
  --out_dir results
```

## Output Structure

* Output Directory Contents
- Tree structures:
  - `tree_001.txt`, `tree_002.txt`, ...
- AI summaries:
  - `llm_001.txt`, `llm_002.txt`, ...
- Combined outputs:
  - `google_drive_map.md` = combined document
  - `directory_table.md` = directory metadata table
  - `log.txt` = processing log

## Requirements

* System Dependencies
- `tree` command
- `llm` CLI tool (configured with OpenAI API)

* Python Dependencies
- helpers.hdbg
- helpers.hio
- helpers.hparser
- helpers.hsystem