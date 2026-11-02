# <Directory Name>

<One-line description of what this directory contains>

<Optional: 2-3 bullet points expanding on the purpose>

## Structure of the Dir

<List subdirectories if any: optional section if no subdirs>

- `<subdir1>/`, <Brief description of subdirectory (<20 words)>
- Example:
  ```markdown
  | File                                   | Description    |
  | -------------------------------------- | ---------------|
  | `ai.claude_code.how_to_guide_figs/`    | Screenshots and images for Claude Code setup and usage guide |
  | `ai.github_copilot_review.how_to_guide_figs/` | Screenshots demonstrating GitHub Copilot review workflow |
  ```

## Description of Files

<List all Python and Markdown files in alphabetical order with 1-line
descriptions (<20 words)>

- `<file1.py>`, <One-line description of what this file does>
- Example:
  ```markdown
  | File                                   | Description                                                                  | Cluster             |
  | -------------------------------------- | ---------------------------------------------------------------------------- | ------------------- |
  | `bookmark_utils.py`                    | Shared helpers for downloading/uploading Google Sheets data and CSV files    | Shared Utilities    |
  | `download_academic_paper_to_md.py`     | Download an academic paper (arXiv/DOI/PDF), convert to Markdown, summarize   | Content Downloaders |
  | `download_to_md.py`                    | Detect input type and dispatch to the matching `download_*_to_md.py` script  | Content Downloaders |
  | `download_utils.py`                    | Shared helpers for fetching article titles and summarizing text via an LLM   | Shared Utilities    |
  | `podcast_dl.py`                        | Download and format a podcast transcript from various sources                | Podcast Tools       |
  ```

# Description of Executables

## `<script_name.py>`

### What It Does

<1-3 bullet points describing the tool's purpose>
- <Main functionality>
- <Key inputs/outputs>
- <Important side effects>

### Examples

<3-5 realistic usage patterns ordered from simple to complex>

- <Simple use case: short description>:
  ```bash
  > ./script_name.py --basic-arg value
  ```

- <Common workflow: short description>:
  ```bash
  > ./script_name.py --input file.txt --output result.txt
  ```

- <Advanced usage: short description>:
  ```bash
  > ./script_name.py --input file.txt --output result.txt --verbose --config custom.yaml
  ```

## `<another_tool.sh>`

### What It Does

<1-3 bullet points describing the tool's purpose>
- <Functionality>
- <Behavior>
- <Effect>

### Examples

- <First simple example>:
  ```bash
  > ./another_tool.sh input_dir
  ```

- <Second example with options>:
  ```bash
  > ./another_tool.sh input_dir --format csv
  ```

- <Complex example with multiple flags>:
  ```bash
  > ./another_tool.sh input_dir --format csv --recursive --output results.csv
  ```

# Description of Workflows

<Optional section describing how tools combine for complex features>

<Use bullet points or prose to describe multi-tool workflows>

## <Workflow Name>

- **Purpose**: <What this workflow accomplishes>

- **Steps**:
  1. <Use tool A to prepare data>
     ```bash
     > tool_a.py --prepare input_file
     ```

  2. <Use tool B to process data>
     ```bash
     > tool_b.py --process prepared_file
     ```

  3. <Use tool C to analyze results>
     ```bash
     > tool_c.py --analyze processed_file
     ```
