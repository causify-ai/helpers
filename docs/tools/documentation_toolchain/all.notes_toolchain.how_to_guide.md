<!-- toc -->

- [notes_to_pdf.py](#notes_to_pdfpy)
  * [What it does](#what-it-does)
    + [Examples](#examples)
    + [Interface](#interface)
  * [render_images.py](#render_imagespy)
    + [What it does](#what-it-does-1)
    + [Examples](#examples-1)
    + [Interface](#interface-1)
  * [`lint_notes.py`](#lint_notespy)
    + [What it does](#what-it-does-2)
    + [Examples](#examples-2)
    + [Interface](#interface-2)
  * [`extract_notebook_images.py`](#extract_notebook_imagespy)
    + [What it does](#what-it-does-3)
    + [Example](#example)
    + [Interface](#interface-3)
  * [`llm_transform.py`](#llm_transformpy)
    + [What it does](#what-it-does-4)
    + [Examples](#examples-3)
    + [Interface](#interface-4)
  * [`run_pandoc.py`](#run_pandocpy)
    + [What it does](#what-it-does-5)
    + [Examples](#examples-4)
    + [Interface](#interface-5)
  * [`transform_notes.py`](#transform_notespy)
    + [What it does](#what-it-does-6)
    + [Examples](#examples-5)
    + [Interface](#interface-6)
  * [`extract_headers_from_markdown.py`](#extract_headers_from_markdownpy)
    + [What it does](#what-it-does-7)
    + [Examples](#examples-6)
    + [Interface](#interface-7)
  * [`dockerized_tikz_to_bitmap.py`](#dockerized_tikz_to_bitmappy)
    + [Examples](#examples-7)
    + [Interface](#interface-8)
  * [`dockerized_graphviz.py`](#dockerized_graphvizpy)
    + [What it does](#what-it-does-8)
    + [Examples](#examples-8)
    + [Interface](#interface-9)
  * [dockerized_latex.py](#dockerized_latexpy)
    + [What it does](#what-it-does-9)
    + [Examples](#examples-9)
    + [Interface](#interface-10)
  * [dockerized_mermaid.py](#dockerized_mermaidpy)
    + [What it does](#what-it-does-10)
    + [Examples](#examples-10)
    + [Interface](#interface-11)
  * [`dockerized_pandoc.py`](#dockerized_pandocpy)
    + [What it does](#what-it-does-11)
    + [Examples](#examples-11)
    + [Interface](#interface-12)
  * [`dockerized_prettier.py`](#dockerized_prettierpy)
    + [What it does](#what-it-does-12)
    + [Examples](#examples-12)
    + [Interface](#interface-13)
  * [`save_screenshot.py`](#save_screenshotpy)
    + [What it does](#what-it-does-13)
    + [Examples](#examples-13)
    + [Interface](#interface-14)

<!-- tocstop -->

# notes_to_pdf.py

## What it does

- Convert plain‑text notes into polished **PDF, HTML, or Beamer slides** with a
  single command:

  ```bash
  > notes_to_pdf.py --input <infile.txt> --output <outfile.[pdf|html]> --type [pdf|html|slides]
  ```

### Examples

- Compile to **Beamer slides**

  ```bash
  > notes_to_pdf.py -i lesson.txt -o lesson.pdf --type slides
  ```

- Produce a **stand‑alone HTML** page

  ```bash
  > notes_to_pdf.py -i cheatsheet.txt -o cheatsheet.html --type html
  ```

- Build a **PDF article** (LaTeX)

  ```bash
  > notes_to_pdf.py -i paper.txt -o paper.pdf --type pdf
  ```

- Skip the final viewer **open** step

  ```bash
  > ... --skip_action open`
  ```

- **Tip**: Run with `--preview_actions` to print the exact steps without
  executing them.

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

- Focus on a subsection, compiling only from line 362 to EOF for a fast
  iteration when debugging slides

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

### Interface

```bash
> notes_to_pdf.py -h
usage: notes_to_pdf.py [-h] -i INPUT -o OUTPUT --type {pdf,html,slides}
                       [--filter_by_header FILTER_BY_HEADER]
                       [--filter_by_lines FILTER_BY_LINES] [--script SCRIPT]
                       [--preview_actions]
                       [--toc_type {none,pandoc_native,navigation}]
                       [--no_run_latex_again] [--debug_on_error]
                       [--gdrive_dir GDRIVE_DIR] [--use_host_tools]
                       [--action {cleanup_before,preprocess_notes,render_images,run_pandoc,copy_to_gdrive,open,cleanup_after} | --skip_action {cleanup_before,preprocess_notes,render_images,run_pandoc,copy_to_gdrive,open,cleanup_after}]
                       [--all] [--dockerized_force_rebuild]
                       [--dockerized_use_sudo]
                       [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]
```

## render_images.py

### What it does

- This script auto renders figures by
  - Detecting fenced code blocks (PlantUML, Mermaid, TikZ, Graphviz, ...)
  - Rendering them into images calling the appropriate tool
  - Commenting them out the block
  - Inlining a `![](img)` markup

- Render the images in a text file

  ```bash
  > render_images.py -i notes/MSML610/Lesson9-Causal_inference.txt \
      -o lesson9.images.txt --run_dockerized
  ```

The supported File types and code blocks are:

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
    - Same tags (TikZ & LaTeX especially)
  - Output embeds as: `\includegraphics{...}`

### Examples

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

### Interface

```bash
> render_images.py -h
usage: render_images.py [-h] -i IN_FILE_NAME [-o OUT_FILE_NAME]
                        [--action {open,render} | --skip_action {open,render}]
                        [--all] [--dry_run] [--dockerized_force_rebuild]
                        [--dockerized_use_sudo]
                        [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Replace sections of image code with rendered images, commenting out the
original code, if needed.

See `docs/work_tools/documentation_toolchain/all.render_images.explanation.md`.

Usage:

# Create a new Markdown file with rendered images:
> render_images.py -i ABC.md -o XYZ.md --action render --run_dockerized

# Render images in place in the original Markdown file:
> render_images.py -i ABC.md --action render --run_dockerized

# Render images in place in the original LaTeX file:
> render_images.py -i ABC.tex --action render --run_dockerized

# Open rendered images from a Markdown file in HTML to preview:
> render_images.py -i ABC.md --action open --run_dockerized

options:
  -h, --help            show this help message and exit
  -i IN_FILE_NAME, --in_file_name IN_FILE_NAME
                        Path to the input file
  -o OUT_FILE_NAME, --out_file_name OUT_FILE_NAME
                        Path to the output file
  --action {open,render}
                        Actions to execute
  --skip_action {open,render}
                        Actions to skip
  --all                 Run all the actions ()
  --dry_run             Update the file but do not render images
  --dockerized_force_rebuild
                        Force to rebuild the Docker container
  --dockerized_use_sudo
                        Use sudo inside the container
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## `lint_notes.py`

### What it does

- Tidy up Markdown/LaTeX/txt notes by:
  - Normalising G‑Doc artifacts
  - Running Prettier
  - Fixing bullet/heading quirks
  - Refreshing the Table of Contents

### Examples

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

- Custom Line width

  ```bash
  > lint_notes.py -i test.txt -o tested.txt -w 10
  ```

### Interface

```bash
> lint_notes.py -h
usage: lint_notes.py [-h] -i IN_FILE_NAME [-o OUT_FILE_NAME]
                     [--type TYPE]
                     [--print-width PRINT_WIDTH]
                     [--use_dockerized_prettier]
                     [--use_dockerized_markdown_toc]
                     [--action {preprocess,prettier,postprocess,frame_chapters,refresh_toc}
                      | --skip_action {preprocess,prettier,postprocess,frame_chapters,refresh_toc}]
                     [--all] [--dockerized_force_rebuild]
                     [--dockerized_use_sudo]
                     [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Lint and prettify Markdown, text, or LaTeX note files. It supports preprocessing,
formatting via Prettier, postprocessing, chapter framing, and automatic TOC insertion.

Usage:

# Format a Markdown file using all actions and Dockerized tools:
> lint_notes.py -i notes.md -o notes_clean.md --use_dockerized_prettier \
  --use_dockerized_markdown_toc --all

# Run only preprocessing and prettification:
> lint_notes.py -i draft.md -o draft_clean.md --action preprocess prettier

# Frame chapters and update TOC only:
> lint_notes.py -i notes.md --action frame_chapters refresh_toc

options:
  -h, --help            Show this help message and exit
  -i IN_FILE_NAME, --in_file_name IN_FILE_NAME
                        Path to the input file (use '-' for stdin)
  -o OUT_FILE_NAME, --out_file_name OUT_FILE_NAME
                        Path to the output file (use '-' for stdout)
  --type TYPE           File type: 'md', 'tex', or 'txt' (required for stdin)
  -w, --print-width PRINT_WIDTH
                        Maximum line width for Prettier (default: 80)
  --use_dockerized_prettier
                        Use Dockerized Prettier for formatting
  --use_dockerized_markdown_toc
                        Use Dockerized markdown-toc to generate TOC
  --action {preprocess,prettier,postprocess,frame_chapters,refresh_toc}
                        Actions to execute
  --skip_action {preprocess,prettier,postprocess,frame_chapters,refresh_toc}
                        Actions to skip
  --all                 Run all actions (default)
  --dockerized_force_rebuild
                        Force rebuild of the Docker container
  --dockerized_use_sudo
                        Use sudo inside the container
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## `extract_notebook_images.py`

### What it does

- Spins up a docker container and dumps every `png/svg` output cell into a
  folder.
- You can then publish or reuse the static plots/diagrams already rendered in a
  Jupyter notebook.

### Example

- Minimal call

  ```bash
  > extract_notebook_images.py \
      --in_notebook_filename notebooks/Lesson8.ipynb \
      --out_image_dir notebooks/screenshots
  ```

- Enforce rebuild and use sudo commands

  ```bash
    > extract_notebook_images.py \
      --in_notebook_filename notebooks/Lesson8.ipynb \
      --out_image_dir notebooks/screenshots --dockerized_force_rebuild --dockerized_use_sudo
  ```

### Interface

```bash
usage: extract_notebook_images.py [-h] --in_notebook_filename IN_NOTEBOOK_FILENAME --out_image_dir
                                  OUT_IMAGE_DIR [--dockerized_force_rebuild] [--dockerized_use_sudo]
                                  [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Extract images from a Jupyter notebook by running inside a Docker container.

This script builds the container dynamically if necessary and extracts images
from the specified Jupyter notebook using the NotebookImageExtractor module.
```

```bash
Extract images from notebook test_images.ipynb and save them to `screenshots`
directory.
> dev_scripts_helpers/notebooks/extract_notebook_images.py     -i dev_scripts_helpers/notebooks/test_images.ipynb     -o dev_scripts_helpers/notebooks/screenshots
```

```bash
options:
  -h, --help            show this help message and exit
  --in_notebook_filename IN_NOTEBOOK_FILENAME
                        Input notebook filename
  --out_image_dir OUT_IMAGE_DIR
                        Output image directory
  --dockerized_force_rebuild
                        Force to rebuild the Docker container
  --dockerized_use_sudo
                        Use sudo inside the container
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## `llm_transform.py`

### What it does

- Apply a GPT‑style transformation (rewrite, summarise, critique code, convert
  to slides, etc.) to any text file _without_ leaving the terminal / editor.

- **Note**: You need to have an `OPENAI_API_KEY` and an internet connection.

### Examples

```bash
llm_transform.py -i draft.txt -o polished.txt -p rewrite_clearer
```

- Finding available prompts

  ```bash
  llm_transform.py -p list -i - -o -
  ```

- Turn a code file into a review checklist

  ```bash
  > llm_transform.py -i foo.py -o cfile -p code_review
  vim cfile
  ```

- Color‑accent the bold bullets for slides

  ```bash
  > llm_transform.py -i deck.md -o - -p slide_colorize | tee deck.color.md
  ```

- Inline use in Vim, visual‑select a block, then:

  ```vim
  :'<,'>!llm_transform.py -p summarize -i - -o -
  ```

### Interface

```bash
usage: llm_transform.py [-h] [-i IN_FILE_NAME] [-o OUT_FILE_NAME] [--debug] -p PROMPT [-f]
                        [--dockerized_force_rebuild] [--dockerized_use_sudo] [-c] [-b] [-s]
                        [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Read input from either stdin or a file, apply a specified transformation using
an LLM, and then write the output to either stdout or a file. It is
particularly useful for integrating with editors like Vim.

The script `dockerized_llm_transform.py` is executed within a Docker container to ensure
all dependencies are met. The Docker container is built dynamically if
necessary. The script requires an OpenAI API key to be set in the environment.
```

```bash
Examples
# Basic Usage
> llm_transform.py -i input.txt -o output.txt -p uppercase

# List of transforms
> llm_transform.py -i input.txt -o output.txt -p list

# Code review
> llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_review

# Propose refactoring
> llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_propose_refactoring
```

```bash
options:
  -h, --help            show this help message and exit
  -i IN_FILE_NAME, --in_file_name IN_FILE_NAME
                        Input file or `-` for stdin
  -o OUT_FILE_NAME, --out_file_name OUT_FILE_NAME
                        Output file or `-` for stdout
  --debug               Print before/after the transform
  -p PROMPT, --prompt PROMPT
                        Prompt to apply
  -f, --fast_model      Use a fast LLM model vs a high-quality one
  --dockerized_force_rebuild
                        Force to rebuild the Docker container
  --dockerized_use_sudo
                        Use sudo inside the container
  -c, --compare         Print the original and transformed
  -b, --bold_first_level_bullets
                        Bold the first level bullets
  -s, --skip-post-transforms
                        Skip the post-transforms
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## `run_pandoc.py`

### What it does

- Reads **Markdown** from _stdin_ or `--input` file.
- Dispatches to a named **action** (currently only `convert_md_to_latex`).
- Pushes the Pandoc output to _stdout_ or the `--output` file.

### Examples

- Convert a Markdown file to LaTeX

  ```bash
  > run_pandoc.py -i note.md -o note.tex
  ```

- Same, but stream from `stdin` to `stdout`

  ```bash
  > cat note.md | run_pandoc.py -i - -o -
  ```

- Inside Vim (visual range)

  ```vim
  :<,'>!run_pandoc.py -i - -o - -v CRITICAL
  ```

- **Tip:** pass `-v CRITICAL` to silence helper logging when piping into
  editors.

### Interface

```bash
usage: run_pandoc.py [-h] -i IN_FILE_NAME [-o OUT_FILE_NAME] [--action ACTION]
                     [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Run pandoc on stdin/file to stdout/file.

- Read value from stdin/file
- Transform it using Pandoc according to different transforms
  (e.g., `convert_md_to_latex`)
- Write the result to stdout/file.
```

To run in VIM:

```vim
:'<,'>!dev_scripts/documentation/run_pandoc.py -i - -o - -v CRITICAL
```

This script is derived from `dev_scripts/transform_template.py`.

```bash
options:
  -h, --help            show this help message and exit
  -i IN_FILE_NAME, --in_file_name IN_FILE_NAME
                        Input file or `-` for stdin
  -o OUT_FILE_NAME, --out_file_name OUT_FILE_NAME
                        Output file or `-` for stdout
  --action ACTION       Action to perform
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## `transform_notes.py`

### What it does

- Accepts a **text/Markdown** stream (file or `-`).
- Applies a named **action** (`-a/--action`).
- Writes the result to the given output (in‑place, file, or `-`).

### Examples

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

* Convert a Markdown list to LaTeX `\begin{itemize}`
  - Typical Vim one-liner: `:%!transform_notes.py -a md_list_to_latex -i -`
  - `md_*` family
    - Formatting clean-ups (bold bullets, colorize bold text, etc.)
    - Additional Information: See `-a list` for more details

- Re‑flow & clean a file in place

  ```bash
  > transform_notes.py -a md_format -i notes/lecture.txt --in_place
  ```

- Generate a 2‑level TOC to STDOUT

  ```bash
  > transform_notes.py -a toc -i notes/lecture.md -o - -l 2
  ```

- Tidy ChatGPT‑generated Markdown (visual mode in Vim)

  ```vim
  :'<,'>!transform_notes.py -i - -o - -a md_fix_chatgpt_output
  ```

### Interface

```bash
usage: transform_notes.py [-h] [-i IN_FILE_NAME] [-o OUT_FILE_NAME] -a ACTION [-l MAX_LEV]
                          [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Perform one of several transformations on a txt file, e.g.,

1) `toc`: create table of context from the current file, with 1 level
    > transform_notes.py -a toc -i % -l 1

2) `format`: format the current file with 3 levels
    :!transform_notes.py -a format -i % --max_lev 3
    > transform_notes.py -a format -i notes/ABC.txt --max_lev 3
    - In vim
    :!transform_notes.py -a format -i % --max_lev 3
    :%!transform_notes.py -a format -i - --max_lev 3

3) `increase`: increase level
    :!transform_notes.py -a increase -i %
    :%!transform_notes.py -a increase -i -

4) `md_list_to_latex`: convert a markdown list to a latex list
    :!transform_notes.py -a md_list_to_latex -i %
    :%!transform_notes.py -a md_list_to_latex -i -

- The input or output can be filename or stdin (represented by '-')
- If output file is not specified then we assume that the output file is the
  same as the input

options:
  -h, --help            show this help message and exit
  -i IN_FILE_NAME, --in_file_name IN_FILE_NAME
                        Input file or `-` for stdin
  -o OUT_FILE_NAME, --out_file_name OUT_FILE_NAME
                        Output file or `-` for stdout
  -a ACTION, --action ACTION
  -l MAX_LEV, --max_lev MAX_LEV
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## `extract_headers_from_markdown.py`

### What it does

- Turn a Markdown document into either:
  - A **plain list** of headers
  - A **nested header map**
  - A \*_Vim_ quick‑fix\*\* (`cfile`) that lets you jump between sections with
    `:cnext`.

### Examples

- Human‑readable map (levels 1‑3) to `stdout`

  ```bash
  > extract_headers_from_markdown.py -i README.md -o - --mode list --max-level 3
  ```

- Build a quick‑fix file and open Vim on it

  ```bash
  > extract_headers_from_markdown.py -i README.md -o headers.cfile --mode cfile
  > vim -c "cfile headers.cfile"
  ```

### Interface

```bash
usage: extract_headers_from_markdown.py [-h] -i IN_FILE_NAME [-o OUT_FILE_NAME]
                                        [--mode {list,headers,cfile}] [--max-level MAX_LEVEL]
                                        [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Extract headers from a Markdown file and generate a Vim cfile.

The script:
- Processes the input Markdown file
- Extracts headers up to a specified maximum level
- Prints a human-readable header map
- Generates an output file in a format that can be used with Vim's quickfix
  feature.

# Extract headers up to level 3 from a Markdown file and save to an output file:
> extract_headers_from_markdown.py -i input.md -o cfile --mode cfile --max-level 3

# Extract headers up to level 2 and print to stdout:
> extract_headers_from_markdown.py -i input.md -o - --mode headers

# To use the generated cfile in Vim:
- Open Vim and run `:cfile output.cfile`
  > vim -c "cfile cfile"

- Navigate between headers using `:cnext` and `:cprev`

options:
  -h, --help            show this help message and exit
  -i IN_FILE_NAME, --in_file_name IN_FILE_NAME
                        Input file or `-` for stdin
  -o OUT_FILE_NAME, --out_file_name OUT_FILE_NAME
                        Output file or `-` for stdout
  --mode {list,headers,cfile}
                        Output mode
  --max-level MAX_LEVEL
                        Maximum header levels to parse
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## `dockerized_tikz_to_bitmap.py`

- Convert a TikZ file to a PNG image using a dockerized version of `pdflatex`
  and `imagemagick`.

### Examples

- Plain 300 DPI conversion

  ```bash
  > dockerized_tikz_to_bitmap.py -i figure.tikz -o figure.png
  ```

- Custom ImageMagick options (e.g. 600 DPI)

  ```bash
  > dockerized_tikz_to_bitmap.py -i fig.tikz -o fig.png -- -density 600 -quality 90
  ```
  - Any extra tokens after `--` are passed verbatim to `convert`

### Interface

```bash
usage: dockerized_tikz_to_bitmap.py [-h] -i INPUT -o OUTPUT [--dockerized_force_rebuild]
                                    [--dockerized_use_sudo] [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
  -o OUTPUT, --output OUTPUT
  --dockerized_force_rebuild
                        Force to rebuild the Docker container
  --dockerized_use_sudo
                        Use sudo inside the container
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## `dockerized_graphviz.py`

### What it does

- Converts a Graphviz `.dot` file into a `.png` image using a Dockerized
  container.

  > ```bash
  > graphviz_wrapper.py --input input.dot --output output.png
  > ```

- This script serves as a thin wrapper around Dockerized Graphviz for consistent
  rendering across systems.

### Examples

- Convert DOT to PNG

  ```bash
  > graphviz_wrapper.py -i diagram.dot -o diagram.png
  ```

- Rebuild Docker image

  ```bash
  > graphviz_wrapper.py -i diagram.dot -o diagram.png --dockerized_force_rebuild
  ```

- Use `sudo` for Docker

  ```bash
  > graphviz_wrapper.py -i diagram.dot -o diagram.png --dockerized_use_sudo
  ```

### Interface

```bash
usage: dockerized_graphviz.py [-h] -i INPUT -o OUTPUT [--dockerized_force_rebuild] [--dockerized_use_sudo]
                              [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Convert a Graphviz dot file to a PNG image.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
  -o OUTPUT, --output OUTPUT
  --dockerized_force_rebuild
                        Force to rebuild the Docker container
  --dockerized_use_sudo
                        Use sudo inside the container
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## dockerized_latex.py

### What it does

- Compiles a LaTeX `.tex` file into a PDF using `pdflatex` inside a Docker
  container.
- Automatically rebuilds the Docker image if needed.
- Supports optional rerun of LaTeX for proper references or table of contents
  generation

  ```bash
  > latex_wrapper.py --input doc.tex --output doc.pdf
  ```

### Examples

- Compile `.tex` to `.pdf`

  ```bash
  > latex_wrapper.py -i report.tex -o report.pdf
  ```

- Rebuild Docker image

  ```bash
  > latex_wrapper.py -i report.tex -o report.pdf --dockerized_force_rebuild
  ```

- Use `sudo` for Docker

  ```bash
  > latex_wrapper.py -i report.tex -o report.pdf --dockerized_use_sudo
  ```

- Run LaTeX twice

  ```bash
  > latex_wrapper.py -i paper.tex -o paper.pdf --run_latex_again
  ```

### Interface

```bash
usage: dockerized_latex.py [-h] -i INPUT -o OUTPUT [--run_latex_again] [--dockerized_force_rebuild]
                           [--dockerized_use_sudo] [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Run `latex` inside a Docker container.

This script builds the container dynamically if necessary and formats the
specified file using the provided `prettier` options.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
  -o OUTPUT, --output OUTPUT
  --run_latex_again
  --dockerized_force_rebuild
                        Force to rebuild the Docker container
  --dockerized_use_sudo
                        Use sudo inside the container
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## dockerized_mermaid.py

### What it does

- Renders Mermaid `.mmd` or `.md` diagrams into image files using a Dockerized
  container.

### Examples

```bash
> mermaid_wrapper.py --input flowchart.mmd --output flowchart.png
```

- Automatically sets output to match input name if `--output` is omitted

- Mermaid diagram

  ```bash
  > mermaid_wrapper.py -i diagram.mmd -o diagram.png
  ```

- Use input as output (default)

  ```bash
  > mermaid_wrapper.py -i diagram.mmd
  ```

- Rebuild container

  ```bash
  > mermaid_wrapper.py -i diagram.mmd -o diagram.png --dockerized_force_rebuild
  ```

- Use `sudo` for Docker

  ```bash
  > mermaid_wrapper.py -i diagram.mmd -o diagram.png --dockerized_use_sudo
  ```

### Interface

```bash
usage: dockerized_mermaid.py [-h] -i INPUT [-o OUTPUT] [--dockerized_force_rebuild] [--dockerized_use_sudo]
                             [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Run `mermaid` inside a Docker container.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
  -o OUTPUT, --output OUTPUT
  --dockerized_force_rebuild
                        Force to rebuild the Docker container
  --dockerized_use_sudo
                        Use sudo inside the container
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## `dockerized_pandoc.py`

### What it does

- Converts documents using `pandoc` inside a Docker container
- Supports output to Beamer slides, PDFs, and more with custom CLI flags.

```bash
> pandoc_wrapper.py --input notes.md --output slides.pdf -- docker_args...
```

- Internally builds a Docker container and passes the full `pandoc` command
  string.

### Examples

- Convert Markdown to PDF

  ```bash
  > pandoc_wrapper.py --input notes.md --output notes.pdf --container_type pandoc_latex
  ```

- Convert to Beamer slides

  ```bash
  > pandoc_wrapper.py --input slides.md --output slides.pdf --container_type pandoc_latex -- -t beamer
  ```

- Rebuild Docker image

  ```bash
  > pandoc_wrapper.py --input notes.md --output notes.pdf --dockerized_force_rebuild
  ```

- Run with sudo

  ```bash
  > pandoc_wrapper.py --input notes.md --output notes.pdf --dockerized_use_sudo
  ```

### Interface

```bash
usage: dockerized_pandoc.py [-h] [--dockerized_force_rebuild] [--dockerized_use_sudo] [--input INPUT]
                            [--output OUTPUT] [--data_dir DATA_DIR] [--container_type CONTAINER_TYPE]
                            [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Run `pandoc` inside a Docker container.

This script builds the container dynamically if necessary.

> pandoc tmp.pandoc.no_spaces.txt     -t beamer --slide-level 4 -V theme:SimplePlus     --include-in-header=latex_abbrevs.sty     --toc --toc-depth 2     -o tmp.pandoc.no_spaces.pdf

options:
  -h, --help            show this help message and exit
  --dockerized_force_rebuild
                        Force to rebuild the Docker container
  --dockerized_use_sudo
                        Use sudo inside the container
  --input INPUT
  --output OUTPUT
  --data_dir DATA_DIR
  --container_type CONTAINER_TYPE
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

## `dockerized_prettier.py`

### What it does

- Formats text files (`.md`, `.txt`, `.tex`, etc.) using Prettier within a
  Docker container
- Avoids environment-specific issues and ensures consistent formatting.
- Supports full Prettier CLI flexibility via passthrough of additional options.

  ```bash
  > dockerized_prettier.py --parser markdown --write test.md
  ```

### Examples

- Format a Markdown file

  ```bash
  > dockerized_prettier.py --parser markdown --write test.md
  ```

- Use `sudo` for Docker execution

  ```bash
  > dockerized_prettier.py --use_sudo --parser markdown --write test.md
  ```

- Rebuild the Docker image

  ```bash
  > dockerized_prettier.py --dockerized_force_rebuild --parser markdown --write test.md
  ```

- Change indentation and wrap style

  ```bash
  dockerized_prettier.py --parser markdown --tab-width 4 --prose-wrap always --write test.md
  ```

### Interface

```bash
> dockerized_prettier.py -h
usage: dockerized_prettier.py [-h] -i IN_FILE_NAME [-o OUT_FILE_NAME]
                              [--dockerized_force_rebuild]
                              [--dockerized_use_sudo]
                              [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Run `prettier` inside a Docker container to ensure consistent formatting
across different environments.

This script builds the container dynamically if necessary and formats the
specified file using the provided `prettier` options.

Examples

# Basic usage:

> dockerized_prettier.py --parser markdown --prose-wrap always --write
> --tab-width 2 test.md

# Use sudo for Docker commands:

> dockerized_prettier.py --use_sudo --parser markdown --prose-wrap always
> --write --tab-width 2 test.md

# Set logging verbosity:

> dockerized_prettier.py -v DEBUG --parser markdown --prose-wrap always
> --write --tab-width 2 test.md </pre>

# Process a file:

> cat test.md
- A
  - B - c
    > dockerized_prettier.py --parser markdown --prose-wrap always --write
    > --tab-width 2 test.md

options: -h, --help show this help message and exit -i IN_FILE_NAME,
--in_file_name IN_FILE_NAME Input file or `-` for stdin -o OUT_FILE_NAME,
--out_file_name OUT_FILE_NAME Output file or `-` for stdout
--dockerized_force_rebuild Force to rebuild the Docker container
--dockerized_use_sudo Use sudo inside the container
-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL} Set the logging level
```

## `save_screenshot.py`

### What it does

1. Prompts you to select a screen region (`⌘ - Ctrl - 4`).
2. Saves it as `screenshot.YYYY‑MM‑DD_HH‑MM‑SS.png` (or your chosen name).
3. Prints and copies the Markdown embed `<img src="path/to/file.png">`.

### Examples

- Take screenshot and auto-name it with timestamp:

  ```bash
  > take_screenshot.py
  ```

- Save to a specific directory with a custom filename:

  ```bash
  > take_screenshot.py --dst_dir ./screenshots --filename example.png
  ```

- Allow overwriting an existing file:

  ```bash
  > take_screenshot.py --filename my.png --override
  ```

### Interface

```bash
usage: save_screenshot.py [-h] [--dst_dir DST_DIR] [--filename FILENAME] [--override]
                          [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                          [positional ...]

Take a screenshot and save it to a file.

The script should be run from the command line outside of a Docker
container.

positional arguments:
  positional            ...

options:
  -h, --help            show this help message and exit
  --dst_dir DST_DIR     Destination directory
  --filename FILENAME   File name
  --override            Override if file exists
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```
