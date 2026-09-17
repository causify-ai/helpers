# `transform_text.py`

- Applies one of several text/Markdown transformations to a file or stream
- Reads from a file or stdin (`-`) and writes to a file or stdout (`-`)
- Used as a Vim filter (`:!` / `:%!`) to reformat notes, headers, lists, and
  bullets in place, or to reflow the current buffer through a pipe

## Overview

- `transform_text.py` dispatches on the `-a/--action` flag to one of a fixed
  set of transforms (table of contents generation, header formatting, list
  and bullet conversions, TODO checkboxes, Markdown clean-up, and slide
  figure blocks)
- Every action reads the full input as a single string, transforms it, and
  writes the full output back out
- Actions that don't need an LLM (e.g., converting Markdown to LaTeX via
  `pandoc`, or removing/adding bullets) live here; LLM-backed transforms
  live in `dev_scripts_helpers/llms/llm_transform.py`

## Quick Start

- List all the available actions with a one-line description each:
  ```bash
  > ./transform_text.py -a list
  ```

- Create a 1-level table of contents from the current Vim buffer:
  ```vim
  :!transform_text.py -a toc -i % -l 1
  ```

- Reflow and colorize the current file, up to 3 header levels:
  ```bash
  > ./transform_text.py -a md_format -i notes/lecture.txt --max_lev 3
  ```

- Turn every line of a plain list into a TODO checklist item, in Vim:
  ```vim
  :%!transform_text.py -a md_add_checkbox -i -
  ```

- Convert a Markdown list to a LaTeX `\begin{itemize}` block, in Vim:
  ```vim
  :%!transform_text.py -a md_list_to_latex -i -
  ```

## Available Actions

- **test**: compute the hash of the input, to test the input/output flow
- **format_headers**: reflow and indent Markdown headers (up to `--max_lev`)
- **increase_headers_level**: bump every header down one level
- **toc**: generate a bullet-list table of contents from the headers
- **md_list_to_latex**: convert a Markdown list to a LaTeX `itemize` block
- **md_to_latex**: convert Markdown to LaTeX with `pandoc`, then format
- **md_remove_formatting**: strip Markdown formatting (bold, italic, links, …)
- **md_remove_bullets**: strip leading `- ` bullets and leading whitespace
- **md_clean_up**: remove weird/copy-pasted characters
- **md_only_format**: reflow the Markdown, no other change
- **md_bold_bullets**: bold every first-level bullet
- **md_add_checkbox**: prefix each non-empty line with `- [ ] `
- **md_colorize_bold_text**: add LaTeX colors to `**bold**` text
- **md_format**: clean up, colorize bold text, and reflow
- **slide_format_figures**: format Markdown figure blocks for slides
- **slide_add_figure**: wrap content in a two-column figure block for slides

## Configuration & Inputs

### Command-line Arguments

| Argument | Type | Default | Description |
| :------- | :--- | :------ | :---------- |
| `-a, --action` | str | required | The transform to apply (see `-a list`) |
| `-i, --input` | str | `-` | Input file, or `-` for stdin |
| `-o, --output` | str | `-` | Output file, or `-` for stdout; defaults to the input file if omitted |
| `-l, --max_lev` | int | `5` | Max header level for `format_headers` |
| `-v, --verbosity` | str | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

## Output & Side Effects

- Writes the transformed text to the output file (or stdout for `-`)
- If `-o/--output` is not passed, the input file is overwritten in place
- `-a list` prints the action table to stdout and exits without touching any
  file
