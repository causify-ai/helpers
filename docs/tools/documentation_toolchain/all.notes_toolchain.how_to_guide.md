<!-- toc -->

- [Notes Documentation Toolchain](#notes-documentation-toolchain)
  * [1. Generate Slides and PDFs — `notes_to_pdf.py`](#1-generate-slides-and-pdfs--notes_to_pdfpy)
    + [What it does](#what-it-does)
    + [Most used flags](#most-used-flags)
    + [Quickstart recipes](#quickstart-recipes)
    + [CLI flags cheatsheet](#cli-flags-cheatsheet)
    + [Worked examples](#worked-examples)
      - [Slides with navigation breadcrumbs](#slides-with-navigation-breadcrumbs)
      - [Focus on a subsection](#focus-on-a-subsection)
      - [Plain PDF article](#plain-pdf-article)
  * [2. Auto render figures — `render_images.py`](#2-auto-render-figures--render_imagespy)
    + [Supported File types and Code blocks](#supported-file-types-and-code-blocks)
    + [Quick Start Recipes](#quick-start-recipes)
      - [Render to a new file](#render-to-a-new-file)
      - [Render in‑place (Markdown or LaTeX)](#render-in%E2%80%91place-markdown-or-latex)
      - [HTML preview of already‑rendered images](#html-preview-of-already%E2%80%91rendered-images)
      - [Dry‑run (test parsing / comments only)](#dry%E2%80%91run-test-parsing--comments-only)
    + [Flags](#flags)
  * [3. Lint and Prettify — `lint_notes.py`](#3-lint-and-prettify--lint_notespy)
    + [Quickstart recipes](#quickstart-recipes-1)
      - [Prettify with Dockerised Prettier and TOC rebuild](#prettify-with-dockerised-prettier-and-toc-rebuild)
      - [Custom print width and selective actions](#custom-print-width-and-selective-actions)
    + [Flags](#flags-1)
  * [4. Notebook Image Scraping — `extract_notebook_images.py`](#4-notebook-image-scraping--extract_notebook_imagespy)
    + [Flag Options](#flag-options)
  * [5. LLM Powered Transforms — `llm_transform.py`](#5-llm-powered-transforms--llm_transformpy)
    + [Minimum viable command](#minimum-viable-command)
    + [Finding available prompts](#finding-available-prompts)
    + [Flags](#flags-2)
    + [Example recipes](#example-recipes)
  * [6. Pandoc Wrapper — `run_pandoc.py`](#6-pandoc-wrapper--run_pandocpy)
    + [What the script does](#what-the-script-does)
    + [Quickstart commands](#quickstart-commands)
    + [Flags](#flags-3)
  * [7. Automate notes transformations — `transform_notes.py`](#7-automate-notes-transformations--transform_notespy)
    + [What it does](#what-it-does-1)
    + [Supported actions](#supported-actions)
    + [Examples](#examples)
    + [Flags](#flags-4)
  * [8. Scrape headers from a markdown — `extract_headers_from_markdown.py`](#8-scrape-headers-from-a-markdown--extract_headers_from_markdownpy)
    + [Goal](#goal)
    + [Examples](#examples-1)
    + [Flags](#flags-5)
  * [9. TikZ to Bitmap — `dockerized_tikz_to_bitmap.py`](#9-tikz-to-bitmap--dockerized_tikz_to_bitmappy)
    + [Examples](#examples-2)
  * [10. Graphviz Renderer — `dockerized_graphviz.py`](#10-graphviz-renderer--dockerized_graphvizpy)
    + [What it does](#what-it-does-2)
    + [Most used flags](#most-used-flags-1)
    + [Quickstart recipes](#quickstart-recipes-2)
    + [CLI flags cheatsheet](#cli-flags-cheatsheet-1)
  * [11. LaTeX Renderer — `dockerized_latex.py`](#11-latex-renderer--dockerized_latexpy)
    + [What it does](#what-it-does-3)
    + [Most used flags](#most-used-flags-2)
    + [Quickstart recipes](#quickstart-recipes-3)
    + [CLI flags cheatsheet](#cli-flags-cheatsheet-2)
  * [12. Mermaid Renderer — `dockerized_mermaid.py`](#12-mermaid-renderer--dockerized_mermaidpy)
    + [What it does](#what-it-does-4)
    + [Most used flags](#most-used-flags-3)
    + [Quickstart recipes](#quickstart-recipes-4)
    + [CLI flags cheatsheet](#cli-flags-cheatsheet-3)
  * [13. Pandoc Renderer — `dockerized_pandoc.py`](#13-pandoc-renderer--dockerized_pandocpy)
    + [What it does](#what-it-does-5)
    + [Most used flags](#most-used-flags-4)
    + [Quickstart recipes](#quickstart-recipes-5)
    + [CLI flags cheat‑sheet](#cli-flags-cheat%E2%80%91sheet)
  * [14. Prettier Formatter — `dockerized_prettier.py`](#14-prettier-formatter--dockerized_prettierpy)
    + [What it does](#what-it-does-6)
    + [Most used flags](#most-used-flags-5)
    + [Quickstart recipes](#quickstart-recipes-6)
    + [CLI flags cheatsheet](#cli-flags-cheatsheet-4)
  * [15. MacOS screenshot helper — `save_screenshot.py`](#15-macos-screenshot-helper--save_screenshotpy)
    + [What it does](#what-it-does-7)
    + [Flags](#flags-6)

<!-- tocstop -->

# Notes Documentation Toolchain

- This is a high‑level guide to the helper scripts that turn raw `.txt` notes
  into polished PDFs, slide decks, and more.

// TODO(*): Is it worth to report the flags? It's difficult to maintain

## notes_to_pdf.py

### What it does

- Convert plain‑text notes into polished **PDF, HTML, or Beamer slides** with a
  single command:
  ```bash
  > notes_to_pdf.py --input <infile.txt> --output <outfile.[pdf|html]> --type [pdf|html|slides]
  ```

- The most used flags are
  - `--type {pdf|html|slides}`
  - `--toc_type {none|pandoc_native|navigation}`
  - `--debug_on_error`, `--skip_action ...`, `--filter_by_lines A:B`

###  Quickstart recipes

- Compile to **Beamer slides**
  ```
  > notes_to_pdf.py -i lesson.txt -o lesson.pdf --type slides
  ```
- Produce a **stand‑alone HTML** page
  ```
  > notes_to_pdf.py -i cheatsheet.txt -o cheatsheet.html --type html
  ```
- Build a **PDF article** (LaTeX)
  ```
  > notes_to_pdf.py -i paper.txt -o paper.pdf --type pdf
  ```
- Skip the final viewer **open** step
  ```
  > ... --skip_action open`
  ```

- **Tip**: Run with `--preview_actions` to print the exact steps without
  executing them.

### CLI flags cheatsheet

- `--type {pdf,html,slides}`
  - Purpose: Specifies the output format
  - Notes: The "slides" option uses Beamer
- `--toc_type {none,pandoc_native,navigation}`
  - Purpose: Determines the Table of Contents (TOC) style
  - Notes: The `navigation` option inserts slide-friendly breadcrumb frames
- `--filter_by_header "# Intro"`
  - Purpose: Builds an artefact from a section subset
  - Notes: This is useful for testing
- `--filter_by_lines 120:250`
  - Purpose: Compiles only a specified range of lines
  - Notes: Accepts `None` as a sentinel value
- `--debug_on_error`
  - Purpose: On Pandoc failure, generates a _.tex_ file and provides a helpful
    log
  - Notes: No additional notes
- `--script myrun.sh`
  - Purpose: Saves every shell command executed
  - Notes: Useful for reproducing build pipelines
- Docker knobs:
  - Options:
    - `--dockerized_force_rebuild`
    - `--dockerized_use_sudo`
    - `--use_host_tools`
  - Purpose: Controls the use of container vs host for pandoc/latex

- Run `notes_to_pdf.py -h` for the exhaustive list.

### Worked examples

- Slides with navigation breadcrumbs, keeping intermediate files for inspection

// TODO(indro): `--toc_type navigation` fails because of the preprocess step.

  ```bash
  > notes_to_pdf.py \
      --input MSML610/Lesson5-Theory_Statistical_learning.txt \
      --output Lesson5.pdf \
      --type slides \
      --toc_type navigation \
      --debug_on_error \
      --skip_action cleanup_after
  ```

- Focus on a subsection, compiling only from line 362 to EOF for a fast iteration
  when debugging slides
  ```bash
  > notes_to_pdf.py \
      --input Lesson8-Reasoning_over_time.txt \
      --output Focus.pdf \
      --type slides \
      --filter_by_lines 362:None \
      --skip_action cleanup_after
  ```

- Plain PDF article
  ```bash
  > notes_to_pdf.py -i book_notes.txt -o book_notes.pdf --type pdf
  ```

## render_images.py

- This script auto renders figures by
  - detecting fenced code blocks (PlantUML, Mermaid, TikZ, Graphviz, ...)
  - rendering them into images calling the appropriate tool
  - commenting them out the block
  - inlining a `![](img)` markup

- Render the images in a text file
  ```bash
  > render_images.py -i notes/MSML610/Lesson9-Causal_inference.txt \
      -o lesson9.images.txt --run_dockerized
  ```

### Supported File types and Code blocks

- File extension: `.md`, `.txt`
  - Rendering syntax allowed:
    - `plantuml`
    - `mermaid`
    - `graphviz`
    - `tikz`
    - `latex`
  - Output embeds as: `<img src="figs/xxx.png">`
- File extension: `.tex`
  - Rendering syntax allowed:
    - same tags (TikZ & LaTeX especially)
  - Output embeds as: `\includegraphics{...}`

### Quick Start Recipes

- Render to a new file
  ```bash
  > render_images.py -i lesson.md -o lesson.rendered.md --action render --run_dockerized
  ```

- Render in‑place (Markdown or LaTeX)
  ```bash
  > render_images.py -i lesson.md --action render --run_dockerized
  ```

- HTML preview of already‑rendered images
  ```bash
  > render_images.py -i lesson.md --action open --run_dockerized
  ```

- Dry‑run (test parsing / comments only)
  ```bash
  > render_images.py -i lesson.md -o /tmp/out.md --dry_run
  ```

### Flags

- `-i/--in_file_name`
  - Default: required
  - Purpose: Input `.md`, `.tex`, or `.txt`
- `-o/--out_file_name`
  - Default: `<input>`
  - Purpose: Output path (must share extension)
- `--action`
  - Default: `render`
  - Purpose: `render` ↔ `open`
- `--dry_run`
  - Default: False
  - Purpose: Skip actual rendering, still rewrites markup
- `--run_dockerized / --dockerized_*`
  - Default: False
  - Purpose: Use pre-built container images for PlantUML, Mermaid, etc
- `--verbosity/-v`
  - Default: `INFO`
  - Purpose: Logging verbosity

## `lint_notes.py`

- Tidy up Markdown/LaTeX/txt notes by:
  - normalising G‑Doc artifacts
  - running Prettier
  - fixing bullet/heading quirks
  - refreshing the Table of Contents

### Quickstart recipes

- Prettify with Dockerised Prettier and TOC rebuild
  ```bash
  > lint_notes.py -i Lesson10.md \
       --use_dockerized_prettier \
       --use_dockerized_markdown_toc
  ```

- Custom print width and selective actions
  ```bash
  > lint_notes.py -i draft.txt -o tidy.txt -w 100 \
                --action preprocess,prettier,postprocess
  ```

### Flags

- `-i/--infile`
  - Default: stdin
  - Purpose: Input `.txt` or `.md` (also via pipe)
- `-o/--outfile`
  - Default: stdout
  - Purpose: Destination file (omit for pipe)
- `-w/--print-width`
  - Default: None $\rightarrow$ Prettier default
  - Purpose: Line wrap width
- `--use_dockerized_prettier`
  - Default: False
  - Purpose: Run Prettier inside helper container
- `--use_dockerized_markdown_toc`
  - Default: False
  - Purpose: Refresh TOC via containerised `markdown-toc`
- `--action`
  - Default: all five stages
  - Purpose: Comma-separated subset of: `preprocess`, `prettier`, `postprocess`,
    `frame_chapters`, `refresh_toc`
- `-v/--verbosity`
  - Default: INFO
  - Purpose: Logging level

## `extract_notebook_images.py`

- Spins up a docker container and dumps every `png/svg` output cell into a folder.
- You can then publish or reuse the static plots/diagrams already rendered in a
  Jupyter notebook.

- Minimal call:
  ```bash
  > extract_notebook_images.py \
      --in_notebook_filename notebooks/Lesson8.ipynb \
      --out_image_dir notebooks/screenshots
  ```

### Flag Options

- `-i / --in_notebook_filename PATH`
  - Purpose: Notebook to scan
  - Default: required
- `-o / --out_image_dir DIR`
  - Purpose: Folder where images land
  - Default: required
- `--dockerized_force_rebuild`
  - Purpose: Re-build the Docker image (use if you changed extractor code)
  - Default: false
- `--dockerized_use_sudo`
  - Purpose: Prepend `sudo docker ...`
  - Default: auto-detects
- `-v INFO/DEBUG`
  - Purpose: Log verbosity
  - Default: `INFO`

---

## 5. LLM Powered Transforms — `llm_transform.py`

Apply a GPT‑style transformation (rewrite, summarise, critique code, convert to
slides, etc.) to any text file _without_ leaving the terminal / editor.

> _Note: You need to have an `OPENAI_API_KEY` and an internet connection._

### Minimum viable command

```bash
llm_transform.py -i draft.txt -o polished.txt -p rewrite_clearer
```

### Finding available prompts

```bash
llm_transform.py -p list -i - -o -
```

### Flags

- `-i / --input`
  - Role: Source text (`-` = stdin)
  - Notes: None
- `-o / --output`
  - Role: Destination (`-` = stdout)
  - Notes: None
- `-p / --prompt`
  - Role: Prompt tag (`list`, `code_review`, `slide_colorize`, ...)
  - Notes: Required
- `-c / --compare`
  - Role: Print both original & transformed blocks to stdout
  - Notes: Helpful for quick diff
- `-b / --bold_first_level_bullets`
  - Role: Post-format tweak for slide prompts
  - Notes: None
- `-s / --skip-post-transforms`
  - Role: Return raw LLM output, skip prettier/cleanup
  - Notes: None
- Docker flags
  - Flags: `--dockerized_force_rebuild`, `--dockerized_use_sudo`
  - Role: Control container lifecycle
  - Notes: None

### Example recipes

- Turn a code file into a review checklist

  ```bash
  > llm_transform.py -i foo.py -o cfile -p code_review
  vim cfile
  ```

- **Color‑accent the bold bullets for slides**

  ```bash
  > llm_transform.py -i deck.md -o - -p slide_colorize | tee deck.color.md
  ```

- **Inline use in Vim** – visual‑select a block, then:

  ```vim
  :'<,'>!llm_transform.py -p summarize -i - -o -
  ```

## `run_pandoc.py`

### What the script does

- Reads **Markdown** from _stdin_ or `--input` file.
- Dispatches to a named **action** (currently only `convert_md_to_latex`).
- Pushes the Pandoc output to _stdout_ or the `--output` file.

### Quickstart commands

- Convert a Markdown file to LaTeX
  ```
  > run_pandoc.py -i note.md -o note.tex
  ```
- Same, but stream from STDIN to STDOUT
  ```
  > cat note.md | run_pandoc.py -i - -o -
  ```
- Inside Vim (visual range)
  ```
  > :<,'>!run_pandoc.py -i - -o - -v CRITICAL
  ```

**Tip :** pass `-v CRITICAL` to silence helper logging when piping into editors.

### Flags

- `-i / --input`
  - Default: `-`
  - Meaning: Source file or `-` for STDIN
- `-o / --output`
  - Default: `-`
  - Meaning: Destination file or `-` for STDOUT
- `--action`
  - Default: `convert_md_to_latex`
  - Meaning: Transformation to apply. Future-proofed for more actions
- `-v / --log_level`
  - Default: `INFO`
  - Meaning: Standard helper-library verbosity

## `transform_notes.py`

### What it does

- Accepts a **text/Markdown** stream (file or `-`).
- Applies a named **action** (`-a/--action`).
- Writes the result to the given output (in‑place, file, or `-`).

### Example of Supported Actions

- Run `-a list` to print a list of the valid

- `toc`
  - Generate a bullet TOC (top-level by default)
  - Typical Vim one-liner: `:!transform_notes.py -a toc -i % -l 1`
- `format_headers`
  - Re-flow / indent headers (up to `--max_lev`)
  - Typical Vim one-liner: `:%!transform_notes.py -a format -i - --max_lev 3`
- `increase_headers_level`
  - Bump all headers down one level
  - Typical Vim one-liner: `:%!transform_notes.py -a increase -i -`
- `md_list_to_latex`
  - Convert a Markdown list to LaTeX `\begin{itemize}`
  - Typical Vim one-liner: `:%!transform_notes.py -a md_list_to_latex -i -`
- `md_*` family
  - Formatting clean-ups (bold bullets, colorize bold text, etc.)
  - Additional Information: See `-a list` for more details

### Examples

- Re‑flow & clean a file in place
  ```bash
  > transform_notes.py -a md_format -i notes/lecture.txt --in_place
  ```

- Generate a 2‑level TOC to STDOUT
  ```bash
  > transform_notes.py -a toc -i notes/lecture.md -o - -l 2
  ```

- Tidy ChatGPT‑generated Markdown (visual mode in Vim)
  ```
  :'<,'>!transform_notes.py -i - -o - -a md_fix_chatgpt_output
  ```

### Flags

- `-a / --action`
  - Default: Required
  - Purpose: Choose the transformation
- `-l / --max_lev`
  - Default: 5
  - Purpose: Header depth for `format_headers`
- `-i / --input`
  - Default: `-`
  - Purpose: File path or `-` (STDIN)
- `-o / --output`
  - Default: `-`
  - Purpose: File path or `-` (STDOUT)
- `--in_place`
  - Default: False
  - Purpose: Overwrite input file instead of writing elsewhere

---

## 8. Scrape headers from a markdown — `extract_headers_from_markdown.py`

### Goal

Turn a Markdown document into either:

- a **plain list** of headers,
- a **nested header map**, or
- a \*_Vim_ quick‑fix\*\* (`cfile`) that lets you jump between sections with
  `:cnext`.

### Examples

```bash
# Human‑readable map (levels 1‑3) to STDOUT
extract_headers_from_markdown.py -i README.md -o - --mode list --max-level 3

# Build a quick‑fix file and open Vim on it
extract_headers_from_markdown.py -i README.md -o headers.cfile --mode cfile
vim -c "cfile headers.cfile"
```

### Flags

| Flag          | Default | Meaning                        |
| ------------- | ------- | ------------------------------ |
| `--mode`      | `list`  | `list`, `headers`, or `cfile`. |
| `--max-level` | `3`     | Maximum `#` depth to parse.    |

---

## 9. TikZ to Bitmap — `dockerized_tikz_to_bitmap.py`

### Examples

```bash
# Plain 300 DPI conversion
./dockerized_tikz_to_bitmap.py -i figure.tikz -o figure.png

# Custom ImageMagick options (e.g. 600 DPI)
./dockerized_tikz_to_bitmap.py -i fig.tikz -o fig.png -- -density 600 -quality 90
```

_Any extra tokens after `--` are passed verbatim to `convert`._

---

## 10. Graphviz Renderer — `dockerized_graphviz.py`

### What it does

Converts a Graphviz `.dot` file into a `.png` image using a Dockerized
container.

> ```bash
> graphviz_wrapper.py --input input.dot --output output.png
> ```

This script serves as a thin wrapper around Dockerized Graphviz for consistent
rendering across systems.

### Most used flags

- `--input`: path to the `.dot` file
- `--output`: destination `.png` image file
- `--dockerized_force_rebuild`: rebuild the container from scratch
- `--dockerized_use_sudo`: use `sudo` for Docker commands

### Quickstart recipes

| Goal                  | Command                                                                        |
| --------------------- | ------------------------------------------------------------------------------ |
| Convert DOT to PNG    | `graphviz_wrapper.py -i diagram.dot -o diagram.png`                            |
| Rebuild Docker image  | `graphviz_wrapper.py -i diagram.dot -o diagram.png --dockerized_force_rebuild` |
| Use `sudo` for Docker | `graphviz_wrapper.py -i diagram.dot -o diagram.png --dockerized_use_sudo`      |

### CLI flags cheatsheet

| Flag                         | Purpose                      | Notes         |
| ---------------------------- | ---------------------------- | ------------- |
| `-i / --input`               | Path to input `.dot` file    | **required**  |
| `-o / --output`              | Output path for `.png` image | **required**  |
| `--dockerized_force_rebuild` | Force Docker image rebuild   | Optional      |
| `--dockerized_use_sudo`      | Run Docker with `sudo`       | Optional      |
| `-v / --verbosity`           | Logging verbosity            | Default: INFO |

---

## 11. LaTeX Renderer — `dockerized_latex.py`

### What it does

Compiles a LaTeX `.tex` file into a PDF using `pdflatex` inside a Docker
container.
Automatically rebuilds the Docker image if needed.

> ```bash
> latex_wrapper.py --input doc.tex --output doc.pdf
> ```

Supports optional rerun of LaTeX for proper references or table of contents
generation.

### Most used flags

- `--input`: LaTeX source file to compile
- `--output`: Output PDF path
- `--run_latex_again`: Compile the LaTeX file twice
- `--dockerized_force_rebuild`: Force container rebuild
- `--dockerized_use_sudo`: Run Docker with `sudo`

### Quickstart recipes

| Goal                     | Command                                                                   |
| ------------------------ | ------------------------------------------------------------------------- |
| Compile `.tex` to `.pdf` | `latex_wrapper.py -i report.tex -o report.pdf`                            |
| Rebuild Docker image     | `latex_wrapper.py -i report.tex -o report.pdf --dockerized_force_rebuild` |
| Use `sudo` for Docker    | `latex_wrapper.py -i report.tex -o report.pdf --dockerized_use_sudo`      |
| Run LaTeX twice          | `latex_wrapper.py -i paper.tex -o paper.pdf --run_latex_again`            |

### CLI flags cheatsheet

| Flag                         | Purpose                    | Notes                         |
| ---------------------------- | -------------------------- | ----------------------------- |
| `-i / --input`               | Path to input `.tex` file  | **required**                  |
| `-o / --output`              | Output PDF file path       | **required**                  |
| `--run_latex_again`          | Run LaTeX a second time    | Optional, useful for TOC/refs |
| `--dockerized_force_rebuild` | Force Docker image rebuild | Optional                      |
| `--dockerized_use_sudo`      | Run Docker with `sudo`     | Optional                      |
| `-v / --verbosity`           | Logging verbosity          | Default: INFO                 |

---

## 12. Mermaid Renderer — `dockerized_mermaid.py`

### What it does

Renders Mermaid `.mmd` or `.md` diagrams into image files using a Dockerized
container.

> ```bash
> mermaid_wrapper.py --input flowchart.mmd --output flowchart.png
> ```

Automatically sets output to match input name if `--output` is omitted.

### Most used flags

- `--input`: Source Mermaid file
- `--output`: Destination image file (optional)
- `--dockerized_force_rebuild`: Rebuild Docker image
- `--dockerized_use_sudo`: Use `sudo` for Docker

### Quickstart recipes

| Goal                          | Command                                                                       |
| ----------------------------- | ----------------------------------------------------------------------------- |
| Render Mermaid diagram        | `mermaid_wrapper.py -i diagram.mmd -o diagram.png`                            |
| Use input as output (default) | `mermaid_wrapper.py -i diagram.mmd`                                           |
| Rebuild container             | `mermaid_wrapper.py -i diagram.mmd -o diagram.png --dockerized_force_rebuild` |
| Use `sudo` for Docker         | `mermaid_wrapper.py -i diagram.mmd -o diagram.png --dockerized_use_sudo`      |

### CLI flags cheatsheet

| Flag                         | Purpose                            | Notes                      |
| ---------------------------- | ---------------------------------- | -------------------------- |
| `-i / --input`               | Path to input `.mmd` or `.md` file | **required**               |
| `-o / --output`              | Output image file                  | Defaults to input filename |
| `--dockerized_force_rebuild` | Force Docker image rebuild         | Optional                   |
| `--dockerized_use_sudo`      | Run Docker with `sudo`             | Optional                   |
| `-v / --verbosity`           | Logging verbosity                  | Default: INFO              |

---

## 13. Pandoc Renderer — `dockerized_pandoc.py`

### What it does

Converts documents using `pandoc` inside a Docker container.
Supports output to Beamer slides, PDFs, and more with custom CLI flags.

> ```bash
> pandoc_wrapper.py --input notes.md --output slides.pdf -- docker_args...
> ```

Internally builds a Docker container and passes the full `pandoc` command
string.

### Most used flags

- `--input`: source file (e.g., `.md`, `.txt`)
- `--output`: output file (e.g., `.pdf`, `.html`)
- `--container_type`: use `pandoc_only`, `pandoc_latex`, or `pandoc_texlive`
- `--dockerized_force_rebuild`: rebuild image from scratch
- `--dockerized_use_sudo`: run Docker with `sudo`

### Quickstart recipes

| Goal                     | Command                                                                                              |
| ------------------------ | ---------------------------------------------------------------------------------------------------- |
| Convert Markdown to PDF  | `pandoc_wrapper.py --input notes.md --output notes.pdf --container_type pandoc_latex`                |
| Convert to Beamer slides | `pandoc_wrapper.py --input slides.md --output slides.pdf --container_type pandoc_latex -- -t beamer` |
| Rebuild Docker image     | `pandoc_wrapper.py --input notes.md --output notes.pdf --dockerized_force_rebuild`                   |
| Run with sudo            | `pandoc_wrapper.py --input notes.md --output notes.pdf --dockerized_use_sudo`                        |

### CLI flags cheat‑sheet

| Flag                         | Purpose                                                | Notes                  |
| ---------------------------- | ------------------------------------------------------ | ---------------------- |
| `--input`                    | Input source file for Pandoc                           | **required**           |
| `--output`                   | Output file path                                       | Defaults to input name |
| `--data_dir`                 | Additional resource/data path                          | Optional               |
| `--container_type`           | Docker image type: `pandoc_only`, `pandoc_latex`, etc. | Default: `pandoc_only` |
| `--dockerized_force_rebuild` | Force rebuild of Docker image                          | Optional               |
| `--dockerized_use_sudo`      | Use `sudo` for Docker execution                        | Optional               |
| `-v / --verbosity`           | Logging level                                          | Default: INFO          |

---

## 14. Prettier Formatter — `dockerized_prettier.py`

### What it does

Formats text files (`.md`, `.txt`, `.tex`, etc.) using Prettier within a Docker
container.
Avoids environment-specific issues and ensures consistent formatting.

> ```bash
> dockerized_prettier.py --parser markdown --write test.md
> ```

Supports full Prettier CLI flexibility via passthrough of additional options.

### Most used flags

- `--parser`: Prettier parser (e.g. `markdown`)
- `--write`: Apply formatting in-place
- `--tab-width`: Number of spaces per indentation level
- `--dockerized_force_rebuild`: Force rebuild of Docker container
- `--dockerized_use_sudo`: Use `sudo` for Docker commands

### Quickstart recipes

| Goal                              | Command                                                                                      |
| --------------------------------- | -------------------------------------------------------------------------------------------- |
| Format a Markdown file            | `dockerized_prettier.py --parser markdown --write test.md`                                   |
| Use `sudo` for Docker execution   | `dockerized_prettier.py --use_sudo --parser markdown --write test.md`                        |
| Rebuild the Docker image          | `dockerized_prettier.py --dockerized_force_rebuild --parser markdown --write test.md`        |
| Change indentation and wrap style | `dockerized_prettier.py --parser markdown --tab-width 4 --prose-wrap always --write test.md` |

### CLI flags cheatsheet

| Flag                         | Purpose                                               | Notes                                 |
| ---------------------------- | ----------------------------------------------------- | ------------------------------------- |
| `-i / --input`               | Input file path                                       | Required                              |
| `-o / --output`              | Output file path                                      | Optional (defaults to input)          |
| `--parser`                   | Prettier parser type (e.g. `markdown`, `babel`, etc.) | Required via passthrough              |
| `--write`                    | Format and overwrite input file                       | Common usage flag                     |
| `--tab-width`                | Number of spaces per tab                              | Optional, defaults to Prettier config |
| `--dockerized_force_rebuild` | Force Docker image rebuild                            | Optional                              |
| `--dockerized_use_sudo`      | Use `sudo` for Docker commands                        | Optional                              |
| `-v / --verbosity`           | Logging level                                         | Default: INFO                         |

---

## 15. MacOS screenshot helper — `save_screenshot.py`

### What it does

1. Prompts you to select a screen region (`⌘ + Ctrl + 4`).
2. Saves it as `screenshot.YYYY‑MM‑DD_HH‑MM‑SS.png` (or your chosen name).
3. Prints and copies the Markdown embed `<img src="path/to/file.png">`.

### Flags

| Flag                  | Purpose                                  |
| --------------------- | ---------------------------------------- |
| `--dst_dir DIR`       | Target directory (e.g. `notes/figures`). |
| `--filename NAME.png` | Override default timestamped name.       |
| `--override`          | Allow clobbering an existing file.       |

---
