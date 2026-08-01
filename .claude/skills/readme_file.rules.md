Conventions for writing a README for a single executable / script.

# Overall Structure

- Single-file READMEs should follow this hierarchical organization:
  - **Summary**: One paragraph describing the file's purpose and main
  responsibility
  - **Examples**: 3-5 realistic usage patterns (simple → complex)
  - **Configuration & Inputs**: Parameters, environment variables, file formats
  - **Output & Side Effects**: What the script produces and any state changes
  - **Software Architecture**: Data flow, key functions, design patterns

# Writing Conventions

- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
  for text formatting
- Keep descriptions concise and action-oriented
- Use architecture diagrams sparingly (ASCII or mermaid) only when data flow is complex
- Limit descriptions to specified word counts
- For scripts: emphasize entry point, main algorithm, and transformation pipeline

# Section Details

## Summary Section

- Bullet points describing what the file does
- Include: Primary purpose, main inputs, main outputs
- Answer: "What does this file do and when would I use it?"
- Keep under 100 words
- Example:
  ```markdown
  # `process_logs.py`

  - Aggregates and analyzes application log files from multiple sources
  - Parses structured logs, filters by log level, and produces statistical
    summaries
  - Used in observability pipelines to identify error trends and performance
    anomalies
  ```

## Examples Section

- 3-5 realistic usage patterns ordered simple → complex
- Start each with short description, follow with fenced bash code block
- Include example output if helpful for understanding
- Use `> ` prefix (no `$` prompt)
- Format (same as directory README):
  ```markdown
  - Basic usage with defaults:
    ```bash
    > python process_logs.py --input app.log
    ```

  - Filter for recent events and save to custom location:
    ```bash
    > python process_logs.py \
        --input app.log \
        --output summary.parquet \
        --days 3
    ```

  - Enable debug output and process multiple files:
    ```bash
    > python process_logs.py \
        --input logs/*.log \
        --output combined_summary.parquet \
        --days 7 \
        --verbose
    ```
  ```

## Output & Side Effects Section

- Describe all outputs (files, stdout, exit codes)
- List any persistent state changes (databases, caches, temp files)
- Mention error handling and exit codes:
  ```markdown
  ## Output & Side Effects

  ### Files Created
  - Output file at path specified by `--output` (Parquet format with schema validation)
  - Temporary files in `TEMP_DIR` (cleaned up on success, left on error for debugging)

  ### Exit Codes
  - `0`: Success
  - `1`: Malformed input file
  - `2`: Missing required argument
  - `3`: Output directory not writable

  ### Logging
  - Writes to stdout (INFO level by default, DEBUG if `--verbose`)
  - Failed record details logged to `process_logs.error.log`
  ```

## Software Architecture Section

### Data Flow

- Describe input → processing → output pipeline
- Use prose or ASCII diagram for complex flows
- Include data transformations at each stage
- Example:
  ```markdown
  ### Data Flow

  1. **Input**: Read CSV file with headers (columns: timestamp, user_id, event_type)
  2. **Parsing**: Convert timestamp strings to datetime, validate user_id format
  3. **Filtering**: Keep only events from last 7 days, exclude test users
  4. **Aggregation**: Group by user_id, count events per type
  5. **Output**: Write results to Parquet with schema validation
  ```

### Key Functions & Modules

- List main functions with 1-line descriptions of responsibility
- Highlight entry point with description of control flow
- Include function signature for public APIs
- Format as bullet list or table:
  ```markdown
  ### Key Functions

  - `load_data(filepath: str) → pd.DataFrame`
    - Reads CSV file, handles missing values, returns structured dataframe
  - `filter_events(df: pd.DataFrame, days: int) → pd.DataFrame`
    - Filters rows where timestamp is within last N days
  - `aggregate_stats(df: pd.DataFrame) → dict`
    - Groups by user_id, computes event counts and durations, returns summary dict
  - `main()`
    - Orchestrates: load → filter → aggregate → save workflow
  ```

### Design Patterns

- Describe architectural approach (functional, object-oriented, pipeline, etc.)
- Mention caching, memoization, or performance optimizations if relevant
- Example:
  ```markdown
  ### Design Patterns

  - **Pipeline architecture**: Data flows through immutable transformations (no side effects)
  - **Lazy evaluation**: DataFrames loaded on-demand via generators
  - **Error recovery**: Continues processing on malformed records, logs warnings
  ```

## Configuration & Inputs Section

- List all command-line arguments or config file parameters
- Include type, default value, and validation rules
- Document environment variables if used
- Format as table or bullet list with code blocks:
  ```markdown
  ## Configuration & Inputs

  ### Command-line Arguments

  | Argument | Type | Default | Description |
  | :------- | :--- | :------ | :---------- |
  | `--input` | str | required | Path to input CSV file |
  | `--output` | str | `result.parquet` | Path to write output |
  | `--days` | int | 7 | Number of days to include |
  | `--verbose` | flag | false | Enable debug logging |

  ### Environment Variables

  - `LOG_LEVEL`: Set logging verbosity (DEBUG, INFO, WARN, ERROR)
  - `TEMP_DIR`: Directory for intermediate files (default: `/tmp`)
  ```

# Architecture Documentation for Scripts

## For Command-Line Tools

Include:
- **Argument parsing strategy**: argparse, click, manual, etc.
- **Error handling**: How invalid inputs are handled
- **Logging configuration**: Log levels, output destinations
- **Performance characteristics**: Time/space complexity for large inputs

## For Data Processing Scripts

Include:
- **Input format specifications**: Schema, encoding, allowed values
- **Transformation steps**: Order matters; document invariants
- **Intermediate data structures**: What's held in memory vs. streamed
- **Output guarantees**: Determinism, sorting, deduplication rules

## For Library-like Scripts

Include:
- **Public API**: Functions/classes meant for import
- **Internal implementation**: Private functions (prefix with `_`)
- **State management**: Global variables, caching, initialization
- **Extension points**: Where users can hook custom logic

# Format Rules

- Commands as bullet + fenced code block (see directory README rules)
- Break long commands with `\`, indent continuation by 4 spaces
- Use backticks for inline code: `variable_name`, `--flag`
- Use tables for multi-parameter reference (Argument, Type, Default, Description)
- Use prose for narrative explanations (data flow, rationale)
- Keep each section to 150 words unless architecture is complex (then expand)
