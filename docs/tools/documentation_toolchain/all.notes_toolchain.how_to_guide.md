<!-- toc -->

- [Notes Documentation Toolchain](#notes-documentation-toolchain)
  * [notes_to_pdf.py](#notes_to_pdfpy)
    + [What it does](#what-it-does)
    + [Examples](#examples)
  * [render_images.py](#render_imagespy)
    + [What it does](#what-it-does-1)
    + [Examples](#examples-1)
    + [Interface](#interface)
  * [`lint_notes.py`](#lint_notespy)
    + [What it does](#what-it-does-2)
    + [Examples](#examples-2)
    + [Interface](#interface-1)
  * [`extract_notebook_images.py`](#extract_notebook_imagespy)
    + [What it does](#what-it-does-3)
    + [Example](#example)
    + [Interface](#interface-2)
  * [`llm_transform.py`](#llm_transformpy)
    + [What it does](#what-it-does-4)
    + [Examples](#examples-3)
    + [Interface](#interface-3)
  * [`run_pandoc.py`](#run_pandocpy)
    + [What it does](#what-it-does-5)
    + [Example](#example-1)
    + [Interface](#interface-4)
  * [`transform_notes.py`](#transform_notespy)
    + [What it does](#what-it-does-6)
    + [Examples](#examples-4)
    + [Interface](#interface-5)
  * [`extract_headers_from_markdown.py`](#extract_headers_from_markdownpy)
    + [What it does](#what-it-does-7)
    + [Examples](#examples-5)
  * [`dockerized_tikz_to_bitmap.py`](#dockerized_tikz_to_bitmappy)
    + [Examples](#examples-6)
  * [`dockerized_graphviz.py`](#dockerized_graphvizpy)
    + [What it does](#what-it-does-8)
    + [Interface](#interface-6)
    + [Examples](#examples-7)
  * [dockerized_latex.py](#dockerized_latexpy)
    + [What it does](#what-it-does-9)
    + [Examples](#examples-8)
  * [dockerized_mermaid.py](#dockerized_mermaidpy)
    + [What it does](#what-it-does-10)
    + [Examples](#examples-9)
  * [dockerized_pandoc.py](#dockerized_pandocpy)
    + [What it does](#what-it-does-11)
    + [Example](#example-2)
  * [`dockerized_prettier.py`](#dockerized_prettierpy)
    + [What it does](#what-it-does-12)
    + [Examples](#examples-10)
    + [Interface](#interface-7)
  * [`save_screenshot.py`](#save_screenshotpy)
    + [What it does](#what-it-does-13)

<!-- tocstop -->

# Notes Documentation Toolchain

- This is a high‑level guide to the helper scripts that turn raw `.txt` notes
  into polished PDFs, slide decks, and more.

// TODO(\*): Is it worth to report the flags? It's difficult to maintain

## notes_to_pdf.py

### What it does

- Convert plain‑text notes into polished **PDF, HTML, or Beamer slides** with a
  single command:

  ```bash
  > notes_to_pdf.py --input <infile.txt> --output <outfile.[pdf|html]> --type [pdf|html|slides]
  ```

- The interface is:
  ```
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

  Convert a txt file into a PDF / HTML / slides using `pandoc`.

  # From scratch with TOC:
  > notes_to_pdf.py -a pdf --input ...

  # For interactive mode:
  > notes_to_pdf.py -a pdf --no_cleanup_before --no_cleanup --input ...

  # Check that can be compiled:
  > notes_to_pdf.py -a pdf --no_toc --no_open_pdf --input ...

  > notes_to_pdf.py     --input notes/IN_PROGRESS/math.The_hundred_page_ML_book.Burkov.2019.txt     -t pdf     --no_cleanup --no_cleanup_before --no_run_latex_again --no_open

  options:
    -h, --help            show this help message and exit
    -i INPUT, --input INPUT
    -o OUTPUT, --output OUTPUT
                          Output file
    --type {pdf,html,slides}
                          Type of output to generate
    --filter_by_header FILTER_BY_HEADER
                          Filter by header
    --filter_by_lines FILTER_BY_LINES
                          Filter by lines (e.g., `0:10`, `1:None`, `None:10`)
    --script SCRIPT       Bash script to generate with all the executed sub-
                          commands
    --preview_actions     Print the actions and exit
    --toc_type {none,pandoc_native,navigation}
    --no_run_latex_again
    --debug_on_error
    --gdrive_dir GDRIVE_DIR
                          Directory where to save the output to share on Google
                          Drive
    --use_host_tools      Use the host tools instead of the dockerized ones
    --action {cleanup_before,preprocess_notes,render_images,run_pandoc,copy_to_gdrive,open,cleanup_after}
                          Actions to execute
    --skip_action {cleanup_before,preprocess_notes,render_images,run_pandoc,copy_to_gdrive,open,cleanup_after}
                          Actions to skip
    --all                 Run all the actions (cleanup_before preprocess_notes
                          render_images run_pandoc open cleanup_after)
    --dockerized_force_rebuild
                          Force to rebuild the Docker container
    --dockerized_use_sudo
                          Use sudo inside the container
    -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                          Set the logging level
  ```

### Examples

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

- The interface

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

### Interface

// TODO

## `extract_notebook_images.py`

### What it does

- Spins up a docker container and dumps every `png/svg` output cell into a
  folder.
- You can then publish or reuse the static plots/diagrams already rendered in a
  Jupyter notebook.

### Example

- Minimal call:
  ```bash
  > extract_notebook_images.py \
      --in_notebook_filename notebooks/Lesson8.ipynb \
      --out_image_dir notebooks/screenshots
  ```

### Interface

// TODO

## `llm_transform.py`

### What it does

- Apply a GPT‑style transformation (rewrite, summarise, critique code, convert
  to slides, etc.) to any text file _without_ leaving the terminal / editor.

- **Note**: You need to have an `OPENAI_API_KEY` and an internet connection.

### Examples

- TODO

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

// TODO

## `run_pandoc.py`

### What it does

- Reads **Markdown** from _stdin_ or `--input` file.
- Dispatches to a named **action** (currently only `convert_md_to_latex`).
- Pushes the Pandoc output to _stdout_ or the `--output` file.

### Example

- Convert a Markdown file to LaTeX
  ```
  > run_pandoc.py -i note.md -o note.tex
  ```
- Same, but stream from `stdin` to `stdout`
  ```
  > cat note.md | run_pandoc.py -i - -o -
  ```
- Inside Vim (visual range)
  ```
  :<,'>!run_pandoc.py -i - -o - -v CRITICAL
  ```

- **Tip:** pass `-v CRITICAL` to silence helper logging when piping into
  editors.

### Interface

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
    - Convert a Markdown list to LaTeX `\begin{itemize}`
    - Typical Vim one-liner: `:%!transform_notes.py -a md_list_to_latex -i -`
  - `md_*` family
    - Formatting clean-ups (bold bullets, colorize bold text, etc.)
    - Additional Information: See `-a list` for more details

- Re‑flow & clean a file in place

  ```bash
  > transform_notes.py -a md_format -i notes/lecture.txt
  ```

- Generate a 2‑level TOC to STDOUT

  ```bash
  > transform_notes.py -a toc -i notes/lecture.md -o - -l 2
  ```

- Tidy ChatGPT‑generated Markdown (visual mode in Vim)
  ```
  :'<,'>!transform_notes.py -i - -o - -a md_fix_chatgpt_output
  ```

### Interface

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

## `dockerized_tikz_to_bitmap.py`

- Converts

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

## `dockerized_graphviz.py`

### What it does

- Converts a Graphviz `.dot` file into a `.png` image using a Dockerized
  container.

  > ```bash
  > graphviz_wrapper.py --input input.dot --output output.png
  > ```

- This script serves as a thin wrapper around Dockerized Graphviz for consistent
  rendering across systems.

### Interface

### Examples

- Convert DOT to PNG
  ```
  > graphviz_wrapper.py -i diagram.dot -o diagram.png
  ```
- Rebuild Docker image
  ```
  > graphviz_wrapper.py -i diagram.dot -o diagram.png --dockerized_force_rebuild
  ```
- Use `sudo` for Docker
  ```bash
  > graphviz_wrapper.py -i diagram.dot -o diagram.png --dockerized_use_sudo
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
  ```
  > latex_wrapper.py -i report.tex -o report.pdf
  ```
- Rebuild Docker image
  ```
  > latex_wrapper.py -i report.tex -o report.pdf --dockerized_force_rebuild
  ```
- Use `sudo` for Docker
  ```
  > latex_wrapper.py -i report.tex -o report.pdf --dockerized_use_sudo
  ```
- Run LaTeX twice
  ```
  > latex_wrapper.py -i paper.tex -o paper.pdf --run_latex_again
  ```

## dockerized_mermaid.py

### What it does

- Renders Mermaid `.mmd` or `.md` diagrams into image files using a Dockerized
  container.

### Examples

- TODO

  ```bash
  > mermaid_wrapper.py --input flowchart.mmd --output flowchart.png
  ```

- Automatically sets output to match input name if `--output` is omitted

- Mermaid diagram
  ```
  > mermaid_wrapper.py -i diagram.mmd -o diagram.png
  ```
- Use input as output (default)
  ```
  > mermaid_wrapper.py -i diagram.mmd
  ```
- Rebuild container
  ```
  > mermaid_wrapper.py -i diagram.mmd -o diagram.png --dockerized_force_rebuild
  ```
- Use `sudo` for Docker
  ```
  > mermaid_wrapper.py -i diagram.mmd -o diagram.png --dockerized_use_sudo
  ```

## dockerized_pandoc.py

### What it does

- Converts documents using `pandoc` inside a Docker container
- Supports output to Beamer slides, PDFs, and more with custom CLI flags.

```bash
> pandoc_wrapper.py --input notes.md --output slides.pdf -- docker_args...
```

- Internally builds a Docker container and passes the full `pandoc` command
  string.

### Example

- Convert Markdown to PDF
  ```
  > pandoc_wrapper.py --input notes.md --output notes.pdf --container_type pandoc_latex
  ```
- Convert to Beamer slides
  ```
  > pandoc_wrapper.py --input slides.md --output slides.pdf --container_type pandoc_latex -- -t beamer
  ```
- Rebuild Docker image
  ```
  > pandoc_wrapper.py --input notes.md --output notes.pdf --dockerized_force_rebuild
  ```
- Run with sudo
  ```
  > pandoc_wrapper.py --input notes.md --output notes.pdf --dockerized_use_sudo
  ```

## `dockerized_prettier.py`

### What it does

- Formats text files (`.md`, `.txt`, `.tex`, etc.) using Prettier within a
  Docker container
- Avoids environment-specific issues and ensures consistent formatting.
- Supports full Prettier CLI flexibility via passthrough of additional options.

  > ```bash
  > dockerized_prettier.py --parser markdown --write test.md
  > ```

### Examples

- Format a Markdown file
  ```
  > dockerized_prettier.py --parser markdown --write test.md
  ```
- Use `sudo` for Docker execution
  ```
  > dockerized_prettier.py --use_sudo --parser markdown --write test.md
  ```
- Rebuild the Docker image
  ```
  > dockerized_prettier.py --dockerized_force_rebuild --parser markdown --write test.md
  ```
- Change indentation and wrap style
  ```
  dockerized_prettier.py --parser markdown --tab-width 4 --prose-wrap always --write test.md
  ```

### Interface

- Interface
  ```
  > dockerized_prettier.py -h
  usage: dockerized_prettier.py [-h] -i IN_FILE_NAME [-o OUT_FILE_NAME]
                                [--dockerized_force_rebuild]
                                [--dockerized_use_sudo]
                                [-v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}]

  Run `prettier` inside a Docker container to ensure consistent formatting across
  different environments.

  This script builds the container dynamically if necessary and formats the
  specified file using the provided `prettier` options.

  Examples
  # Basic usage:
  > dockerized_prettier.py --parser markdown --prose-wrap always --write     --tab-width 2 test.md

  # Use sudo for Docker commands:
  > dockerized_prettier.py --use_sudo --parser markdown --prose-wrap always     --write --tab-width 2 test.md

  # Set logging verbosity:
  > dockerized_prettier.py -v DEBUG --parser markdown --prose-wrap always     --write --tab-width 2 test.md </pre>

  # Process a file:
  > cat test.md
  - a
    - b
          - c
  > dockerized_prettier.py --parser markdown --prose-wrap always     --write --tab-width 2 test.md

  options:
    -h, --help            show this help message and exit
    -i IN_FILE_NAME, --in_file_name IN_FILE_NAME
                          Input file or `-` for stdin
    -o OUT_FILE_NAME, --out_file_name OUT_FILE_NAME
                          Output file or `-` for stdout
    --dockerized_force_rebuild
                          Force to rebuild the Docker container
    --dockerized_use_sudo
                          Use sudo inside the container
    -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                          Set the logging level
  ```

## `save_screenshot.py`

### What it does

1. Prompts you to select a screen region (`⌘ + Ctrl + 4`).
2. Saves it as `screenshot.YYYY‑MM‑DD_HH‑MM‑SS.png` (or your chosen name).
3. Prints and copies the Markdown embed `<img src="path/to/file.png">`.
