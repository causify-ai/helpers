# Summary

- This document provides a comprehensive guide to the documentation toolchain that converts raw notes, slides, and LaTeX into polished PDFs, slide decks, and HTML
- The toolchain supports multiple documentation workflows including standard LaTeX, Causify markdown extensions, notes format, slides, books, and Jupyter books
- The document catalogs over 30 specialized tools organized into categories: core documentation tools, extraction and conversion tools, dockerized tools, utility and processing tools, and generation and publishing tools
- Each tool is documented with its purpose, usage examples, and integration with the broader documentation ecosystem
- The toolchain emphasizes automation, consistency, and ease of use through command-line interfaces and editor integration

# Documentation Toolchain

- This is a high‑level guide to the workflows that turn raw notes, slides, Latex
  into polished PDFs, slide decks, etc.

- There are several documentation workflows available:
  - **latex**
    - Standard Latex code to convert into PDF files
    - E.g., [`//cmamp/papers`]
    - E.g., [`//cmamp/papers/KaizenFlow`]
  - **markdown**
    - Documentation using Causify markdown extensions
      - E.g., `//helpers/docs`, `//cmamp/docs`, `//tutorials/docs`
      - E.g.,
      [https://github.com/causify-ai/helpers/tree/master/docs](https://github.com/causify-ai/helpers/tree/master/docs)
    - It is automatically rendered with `mkdocs` and published on GitHub
      - E.g., [https://causify-ai.github.io/helpers](https://causify-ai.github.io/helpers)
  - **notes** (aka **.txt**)
    - `Pandoc` markdown with Causify extensions
    - Processed by `preprocess_notes.py` to be converted in standard `Pandoc`
      markdown
    - Can be converted into PDFs and in Anki Q/A
    - E.g., `//notes/notes/...`
      ```
      > vi /Users/saggese/src/notes1/notes/math.machine_learning.txt
      ```
  - **slides**
    - Same as `notes` but we use a different extension `.slides` to clarify that
      they are rendered as slides
    - E.g.,
      ```
      > ls /Users/saggese/src/notes1/MSML610
      > vi /Users/saggese/src/notes1/lectures_source/Lesson00-Class.txt
      ```
    - E.g., `//notes/DATA605`
  - **books**
    - Extended `Pandoc` markdown that can be rendered with `Pandoc`
    - E.g., `//notes/books/book.programming_with_ai`
      ```
      > vi books/programming_with_ai/docs/coding-benchmark.md
      ```
  - **jupyter books**

## Causify Extended Markdown

- We refer to it to "Causify markdown" as some extension we use on top of
  `Pandoc` markdown
- The goal is invariants in formatting that we enforce so that the code looks
  nicely formatted for a human
  - The `linter` formats and enforces some these rules

- E.g.,
  - Cross-repo links
    - E.g., [`//helpers/docs/code_guidelines/all.coding_style_guidelines.reference.md`]
  - Color  
    - E.g., `\red{...}`
  - Primitives we use in the slides  
  - Indented triple fences
  - Triple fences Plugins for tools  
  - Comments  
    - E.g., C-like comments
      `// Comment`
      ```text
      \*
      ...
      */
      ````
  - Framing of titles  
    ```text
    # ##############
    # Hello
    # ##############
    ```
  - Automatically update `> notes_to_pdf.py -h`

- Causify extended markdown is rendered for different backends (e.g., slides,
  mkdocs, ...) by converting the source markdown into something that can be
  rendered by the target tool (e.g., `mkdocs`, `Pandoc`), e.g.,
  - [`//helpers/dev_scripts_helpers/documentation/mkdocs/preprocess_mkdocs.py`]
  - [`//helpers/dev_scripts_helpers/documentation/preprocess_notes.py`]

## List of Tools

- The tools available are
  ```bash
  > ls -1 dev_scripts_helpers/documentation/
  convert_docx_to_markdown.py
  dockerized_graphviz.py
  dockerized_latex.py
  dockerized_mermaid.py
  dockerized_pandoc.py
  dockerized_prettier.py
  dockerized_tikz_to_bitmap.py
  extract_headers_from_markdown.py
  generate_latex_sty.py
  generate_readme_index.py
  generate_script_catalog.py
  latex_abbrevs.sty
  latexdockercmd.sh
  lint_txt.py
  mkdocs
  notes_to_pdf.py
  OLD
  open_md_in_browser.sh
  open_md_on_github.sh
  pandoc.latex
  preprocess_notes.py
  publish_notes.py
  render_images.py
  replace_latex.py
  replace_latex.sh
  run_latex.sh
  run_pandoc.py
  test
  transform_notes.py
  ```

- Short Classification of Tools

  - Core Documentation Tools
    - `notes_to_pdf.py`: Main tool for converting notes to PDF/HTML/slides
    - `render_images.py`: Auto-renders diagrams (PlantUML, Mermaid, TikZ, Graphviz)
    - `lint_txt.py`: Lints and formats Markdown/LaTeX/txt notes
    - `preprocess_notes.py`: Converts Causify notes to Pandoc Markdown
    - `transform_notes.py`: Applies transformations (TOC, headers, lists)
    - `summarize_md.py`: Generates and updates Summary sections in markdown files using LLM

  - Extraction and Conversion Tools
    - `convert_docx_to_markdown.py`: Converts DOCX to Markdown  
    - `pdf_to_md.py`: Converts PDF to Markdown  
    - `extract_headers_from_markdown.py`: Extracts headers for navigation  
    - `extract_notebook_images.py`: Extracts images from Jupyter notebooks  
    - `extract_gdoc_map.py`: Extracts Google Doc links from `.gdoc` files

  - Dockerized Tools
    - `dockerized_tikz_to_bitmap.py`: TikZ to PNG conversion  
    - `dockerized_graphviz.py`: Graphviz DOT to PNG  
    - `dockerized_latex.py`: LaTeX compilation  
    - `dockerized_mermaid.py`: Mermaid diagram rendering  
    - `dockerized_pandoc.py`: Pandoc conversions  
    - `dockerized_prettier.py`: Prettier formatting

  - Utility and Processing Tools
    - `run_pandoc.py`: Runs Pandoc conversions  
    - `replace_latex.py`: Batch LaTeX transformations  
    - `check_links.py`: Validates URL reachability  
    - `process_slides.py`: Processes slides with LLM

  - Generation and Publishing Tools
    - `generate_readme_index.py`: Generates README index  
    - `generate_script_catalog.py`: Creates script catalog  
    - `generate_latex_sty.py`: Generates LaTeX style files  
    - `generate_images.py`: Generates images with DALL-E  
    - `save_screenshot.py`: Screenshot capture utility  
    - `publish_notes.py`: Publishes notes to remote server  
    - `create_google_drive_map.py`: Creates directory structure summaries  
    - `llm_transform.py`: LLM-based text transformations  

# Description of tools

## `notes_to_pdf.py`

### What It Does

- Convert plain‑text notes into polished **PDF**, **HTML**, or **Beamer slides**
  with a single command:

  ```bash
  > notes_to_pdf.py --input <infile.txt> --output <outfile.[pdf|html]> --type [pdf|html|slides]
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
      --input lectures_source/Lesson5-Theory_Statistical_learning.txt \
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

## `render_images.py`

### What It Does

- This script auto renders figures by:
  - Detecting fenced code blocks (PlantUML, Mermaid, TikZ, Graphviz, ...)
  - Rendering them into images calling the appropriate tool
  - Commenting them out the block
  - Inlining a `![](img)` markup

- Render the images in a text file
  ```bash
  > render_images.py -i lectures_source/Lesson9-Causal_inference.txt \
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

- Render multiple files using comma-separated list

  ```bash
  > render_images.py --files="file1.md,file2.md,file3.md" --action render
  ```

- Render multiple files from a file list

  ```bash
  > render_images.py --from_files="files_to_render.txt" --action render
  ```

  Where `files_to_render.txt` contains:
  ```
  # List of files to render
  docs/chapter1.md
  docs/chapter2.md
  docs/chapter3.md
  ```

- Render multiple files using repeated argument

  ```bash
  > render_images.py --file_name file1.md --file_name file2.md --file_name file3.md --action render
  ```

## `lint_notes.py`

### What It Does

- Tidy up notes in different formats (selected with the file extension or
  `--type`):
  - Markdown
  - LaTeX
  - Txt notes

- Various preprocessing and postprocessing steps:
  - Refreshing the Table of Contents
  - Normalising Google Docs artifacts
  - Running Prettier
  - Fixing bullet/heading quirks

- The actions are:
    "preprocess",
    "prettier",
    "postprocess",
    "frame_chapters",
    "refresh_toc",

### Examples

- Basic usage

  ```bash
  > lint_txt.py -i input.md -o output.md
  ```

- Process specific actions only
  ```
  > lint_txt.py -i input.md -o output.md --action preprocess,prettier
  ```

- Prettify with Dockerized Prettier and TOC rebuild

  ```bash
  > lint_txt.py -i Lesson10.md \
      --use_dockerized_prettier \
      --use_dockerized_markdown_toc
  ```

- Custom print width and selective actions

  ```bash
  > lint_txt.py -i draft.txt -o tidy.txt -w 100 \
      --action preprocess,prettier,postprocess
  ```

- Use in vim for inline formatting
  ```verbatim
  :%!lint_txt.py
  ```

## `extract_notebook_images.py`

### What It Does

- Spins up a docker container and dumps every `png/svg` output cell into a
  folder.
- You can then publish or reuse the static plots/diagrams already rendered in a
  Jupyter notebook.

### Examples

- Minimal call:
  ```bash
  > extract_notebook_images.py \
      --in_notebook_filename notebooks/Lesson8.ipynb \
      --out_image_dir notebooks/screenshots
  ```

## `llm_transform.py`

### What It Does

- Apply a GPT‑style transformation (rewrite, summarise, critique code, convert
  to slides, etc.) to any text file _without_ leaving the terminal / editor.

- **Note**: You need to have an `OPENAI_API_KEY` and an internet connection.

### Examples

- Basic transformation on a text file

  ```bash
  > llm_transform.py -i draft.txt -o polished.txt -p rewrite_clearer
  ```

- List all available prompts

  ```bash
  > llm_transform.py -p list_prompts -i - -o -
  ```

- Turn a code file into a review checklist (outputs vim cfile format)

  ```bash
  > llm_transform.py -i foo.py -o cfile -p code_review
  > vim cfile
  ```

- Propose refactoring for a Python file

  ```bash
  > llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_propose_refactoring
  ```

- Color‑accent the bold bullets for slides

  ```bash
  > llm_transform.py -i deck.md -o - -p slide_colorize | tee deck.color.md
  ```

- Inline use in Vim, visual‑select a block, then:

  ```vim
  :'<,'>!llm_transform.py -p summarize -i - -o -
  ```

- Compare original and transformed text side-by-side

  ```bash
  > llm_transform.py -i notes.txt -o result.txt -p improve_clarity --compare
  ```

## `run_pandoc.py`

### What It Does

- Reads **Markdown** from _stdin_ or `--input` file.
- Dispatches to a named **action** (currently only `convert_md_to_latex`).
- Pushes the Pandoc output to _stdout_ or the `--output` file.

### Examples

- Convert a Markdown file to LaTeX
  ```bash
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

## `transform_notes.py`

### What It Does

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

## `summarize_md.py`

### What It Does

- Generate a summary of a markdown file using LLM and update the `# Summary` section
- Reads the content of a markdown file
- Uses the `llm` CLI tool to generate a 3-5 bullet point summary
- Automatically finds and replaces existing `# Summary` section or adds one at the beginning
- Supports multiple LLM models (default: `gpt-4o-mini`)

### Examples

- Summarize a markdown file using default model
  ```bash
  > summarize_md.py --input file.md
  ```

- Summarize using a specific model
  ```bash
  > summarize_md.py --input file.md --model gpt-4o
  ```

- Dry run to preview changes without modifying the file
  ```bash
  > summarize_md.py --input file.md --dry_run
  ```

- Summarize README with verbose logging
  ```bash
  > summarize_md.py --input README.md -v DEBUG
  ```

## `extract_headers_from_markdown.py`

### What It Does

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

- Convert a `.tex` file containing TikZ code into a `.png` image using a Dockerized toolchain consisting of pdflatex and ImageMagick.

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

### What It Does

- Converts a Graphviz `.dot` file into a `.png` image using a Dockerized
  container.

  ```bash
  > dockerized_graphviz.py --input input.dot --output output.png
  ```

- This script serves as a thin wrapper around Dockerized Graphviz for consistent
  rendering across systems.

### Examples

- Convert DOT to PNG
  ```bash
  > dockerized_graphviz.py -i diagram.dot -o diagram.png
  ```
- Rebuild Docker image
  ```bash
  > dockerized_graphviz.py -i diagram.dot -o diagram.png --dockerized_force_rebuild
  ```
- Use `sudo` for Docker
  ```bash
  > dockerized_graphviz.py -i diagram.dot -o diagram.png --dockerized_use_sudo
  ```

## `dockerized_latex.py`

### What It Does

- Compiles a LaTeX `.tex` file into a PDF using `pdflatex` inside a Docker
  container.
- Automatically rebuilds the Docker image if needed.
- Supports optional rerun of LaTeX for proper references or table of contents
  generation
  ```bash
  > dockerized_latex.py --input doc.tex --output doc.pdf
  ```

### Examples

- Compile `.tex` to `.pdf`
  ```bash
  > dockerized_latex.py -i report.tex -o report.pdf
  ```
- Rebuild Docker image
  ```bash
  > dockerized_latex.py -i report.tex -o report.pdf --dockerized_force_rebuild
  ```
- Use `sudo` for Docker
  ```bash
  > dockerized_latex.py -i report.tex -o report.pdf --dockerized_use_sudo
  ```
- Run LaTeX twice
  ```bash
  > dockerized_latex.py -i paper.tex -o paper.pdf --run_latex_again
  ```

## `dockerized_mermaid.py`

### What It Does

- Renders Mermaid `.mmd` or `.md` diagrams into image files using a Dockerized
  container.
- Automatically sets output to match input name if `--output` is omitted

### Examples

- Basic Mermaid diagram rendering

  ```bash
  > dockerized_mermaid.py --input flowchart.mmd --output flowchart.png
  ```

- Short form with input and output
  ```bash
  > dockerized_mermaid.py -i diagram.mmd -o diagram.png
  ```

- Use input filename as output (default behavior)
  ```bash
  > dockerized_mermaid.py -i diagram.mmd
  ```

- Rebuild container image before rendering
  ```bash
  > dockerized_mermaid.py -i diagram.mmd -o diagram.png --dockerized_force_rebuild
  ```

- Use `sudo` for Docker execution
  ```bash
  > dockerized_mermaid.py -i diagram.mmd -o diagram.png --dockerized_use_sudo
  ```

## `dockerized_pandoc.py`

### What It Does

- Converts documents using `pandoc` inside a Docker container
- Supports output to Beamer slides, PDFs, and more with custom CLI flags.

```bash
> dockerized_pandoc.py --input notes.md --output slides.pdf -- docker_args...
```

- Internally builds a Docker container and passes the full `pandoc` command
  string.

### Examples

- Convert Markdown to PDF
  ```bash
  > dockerized_pandoc.py --input notes.md --output notes.pdf --container_type pandoc_latex
  ```
- Convert to Beamer slides
  ```bash
  > dockerized_pandoc.py --input slides.md --output slides.pdf --container_type pandoc_latex -- -t beamer
  ```
- Rebuild Docker image
  ```bash
  > dockerized_pandoc.py --input notes.md --output notes.pdf --dockerized_force_rebuild
  ```
- Run with sudo
  ```bash
  > dockerized_pandoc.py --input notes.md --output notes.pdf --dockerized_use_sudo
  ```

## `dockerized_prettier.py`

### What It Does

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

## `save_screenshot.py`

### What It Does

1. Prompts you to select a screen region (`⌘ + Ctrl + 4`).
2. Saves it as `screenshot.YYYY‑MM‑DD_HH‑MM‑SS.png` (or your chosen name).
3. Prints and copies the Markdown embed `<img src="path/to/file.png">`.

## `generate_images.py`

### What It Does

- Generate multiple images using OpenAI's DALL-E API from prompts.
- This script generates images (default: 5) from one or more prompts using OpenAI's image generation API.
- Supports both standard and HD quality modes.
- Accepts prompts either from command line or from a file.
- Supports two file formats:
  - **Single description**: entire file content is treated as one prompt
  - **Multiple descriptions**: numbered format with multiple prompts
- Shows progress bar when generating multiple images.
- Reports the number of descriptions found when processing multiple prompts.

### Examples

- Generate standard quality images using command line prompt
  ```bash
  > generate_images.py "A sunset over mountains" --dst_dir ./images --low_res
  ```

- Generate HD quality images using command line prompt
  ```bash
  > generate_images.py "A sunset over mountains" --dst_dir ./images
  ```

- Generate with custom image count
  ```bash
  > generate_images.py "A cat wearing a hat" --dst_dir ./images --count 3
  ```

- Generate images using single description from file
  ```bash
  > generate_images.py --input descr.txt --dst_dir ./images
  ```

  Where `descr.txt` contains:
  ```
  A beautiful sunset over mountains with vibrant colors
  ```

- Generate images from multiple descriptions in file
  ```bash
  > generate_images.py --input descriptions.txt --dst_dir ./images --count 2
  ```

  Where `descriptions.txt` contains:
  ```
  1. **Description of the image 1**
     A digital painting illustrating a futuristic cityscape where data streams
     flow like rivers through the streets.
  2. **Description of the image 2**
     An editorial illustration depicting a metaphorical "decision tree" growing
     in a corporate office.
  3. **Description of the image 3**
     A minimalist flat design showing a set of scales balancing two concepts.
  ```

  This will:
  - Detect 3 descriptions in the file
  - Print "Found 3 descriptions in input file"
  - Generate 2 images for each description (6 images total)
  - Show progress bar for all 6 images
  - Save images as `desc_01_image_01_hd.png`, `desc_01_image_02_hd.png`, etc.

- Generate low-res images using prompt from file
  ```bash
  > generate_images.py --input descr.txt --dst_dir ./images --low_res
  ```

- Dry run mode to preview what would be generated without making API calls
  ```bash
  > generate_images.py --input descriptions.txt --dst_dir ./images --count 2 --dry_run
  ```

  This will:
  - Parse the input file and detect all descriptions
  - Print all descriptions that would be processed
  - Show which filenames would be generated
  - Display settings (quality, size, count)
  - Skip actual API calls and image downloads
  - Useful for testing and validating input before spending API credits

## `convert_docx_to_markdown.py`

### What It Does

- Convert Microsoft Word `.docx` files to Markdown using Dockerized Pandoc
- Extracts embedded media (images) from the document into a separate folder
- Applies cleanup transformations to fix common Google Docs artifacts, e.g.,
  - Removes escaped characters like `\#`, `\*`, `\_`
  - Fixes heading formats
  - Normalizes bullet points and quotation marks
  - Converts HTML entities to markdown equivalents

### Examples

- Basic conversion from DOCX to Markdown
  ```bash
  > IN_FILE="/Users/saggese/Downloads/Document.docx"
  > OUT_FILE="paper/paper.md"
  > convert_docx_to_markdown.py --docx_file $IN_FILE --md_file $OUT_FILE
  ```
- The script will:
  - Create a `paper_figs/` directory for extracted images
  - Convert the document to Markdown
  - Extract and organize all embedded images
  - Apply cleanup transformations

## `check_links.py`

### What It Does

- Check if all URL links in a file are reachable via HTTP/HTTPS
- Extracts URLs from Markdown files in various formats:
  - `[text](https://example.com)` (Markdown links)
  - `https://example.com` (standalone URLs)
  - `/path/to/file.md` (local repository paths, converted to GitHub URLs)
- Validates each URL by making HTTP requests
- Generates a vim cfile with broken URLs for easy navigation
- Skips image files (`.png`, `.jpg`, `.jpeg`) and email addresses

### Examples

- Check links in a Markdown file
  ```bash
  > check_links.py --in_file README.md
  ```

- Check links with verbose output
  ```bash
  > check_links.py --in_file docs.txt -v DEBUG
  ```

- Check links and save broken URLs to custom cfile
  ```bash
  > check_links.py --in_file README.md --cfile broken_links.txt
  ```

- The script will:
  - Extract all URLs from the file
  - Check each URL for reachability
  - Report summary with counts of reachable and broken URLs
  - Generate vim cfile for quick navigation to broken links

## `generate_readme_index.py`

### What It Does

- Generate or refresh a Markdown index in a README file
- Scans a directory for all Markdown files and creates an organized index
- Generates two-line summaries for each file using LLM or placeholders
- Supports two modes:
  - `generate`: Create index from scratch
  - `refresh`: Update index, keeping existing summaries and adding new files
- Each entry includes file name, relative path, and summary

### Examples

- Generate new README index with placeholder summaries
  ```bash
  > generate_readme_index.py --index_mode generate --dir_path /path/to/docs
  ```

- Refresh existing README index (keep summaries for existing files)
  ```bash
  > generate_readme_index.py --index_mode refresh --dir_path /path/to/docs
  ```

- Generate index with AI-generated summaries
  ```bash
  > generate_readme_index.py --index_mode generate --dir_path /path/to/docs --model gpt-4o-mini
  ```

- Generate index for Git repository root
  ```bash
  > generate_readme_index.py --index_mode generate --model gpt-4o-mini
  ```

## `generate_script_catalog.py`

### What It Does

- Generate a Markdown catalog of all executable scripts in a repository
- Extracts docstrings from Python scripts and shell scripts
- Organizes scripts by directory
- Creates a formatted reference document showing:
  - Script location
  - Script purpose (from docstring)
  - Usage examples (from docstring)

### Examples

- Generate catalog for current directory
  ```bash
  > generate_script_catalog.py
  ```

- Generate catalog for specific directory
  ```bash
  > generate_script_catalog.py --src_dir dev_scripts/
  ```

- Generate catalog with custom output location
  ```bash
  > generate_script_catalog.py --src_dir . --dst_file docs/scripts.md
  ```

- Generate catalog for single script
  ```bash
  > generate_script_catalog.py --src_file path/to/script.py
  ```

## `publish_notes.py`

### What It Does

- Publish notes to a remote documentation server via SSH
- Converts notes to PDF or HTML format using `notes_to_pdf.py`
- Uploads generated files to a remote server
- Supports batch processing of multiple note files
- Manages remote documentation directory (list, clean, publish)

### Examples

- Publish all notes
  ```bash
  > publish_notes.py publish
  ```

- Clean and republish all notes from scratch
  ```bash
  > publish_notes.py rm publish
  ```

- List files on remote documentation server
  ```bash
  > publish_notes.py ls
  ```

- Custom temporary directory for artifacts
  ```bash
  > publish_notes.py publish --tmp_dir /tmp/notes_build
  ```

## `replace_latex.py`

### What It Does

- One-off script for batch LaTeX text transformations
- Applies standard cleanup rules to LaTeX/Markdown files:
  - Normalize terminology (e.g., "gaussian" → "Gaussian", "iid" → "IID")
  - Expand contractions (e.g., "doesn't" → "does not")
  - Convert "iff" to LaTeX symbol `$\iff$`
  - Format textit commands to Markdown italics
- Can run Pandoc before and after transformations to verify changes
- Supports aggressive mode for more transformations

### Examples

- Apply replacements to a file
  ```bash
  > replace_latex.py -a replace --file notes/finance.portfolio_theory.txt
  ```

- Check transformations with Pandoc before and after
  ```bash
  > replace_latex.py -a pandoc_before -a replace -a pandoc_after --file notes/finance.txt
  ```

- Apply aggressive transformations
  ```bash
  > replace_latex.py -a replace --file notes/finance.txt --aggressive
  ```

- Reset file to git version and apply replacements
  ```bash
  > replace_latex.py -a checkout -a replace --file notes/finance.txt
  ```

## `extract_gdoc_map.py`

### What It Does

- Extract Google Doc links from `.gdoc` files in a directory
- `.gdoc` files are JSON files containing Google Doc IDs
- Scans directory recursively for all `.gdoc` files
- Generates Markdown-formatted links to the actual Google Docs
- Supports two output styles:
  - `default`: Directory path as main bullet, filename as sub-bullet with link
  - `full_path`: Full path in link text

### Examples

- Extract links from directory with default style
  ```bash
  > extract_gdoc_map.py --input_dir "/path/to/google/drive"
  ```

- Extract links and save to file
  ```bash
  > extract_gdoc_map.py --input_dir "/path/to/docs" --output_file "doc_links.md"
  ```

- Use full path style for link text
  ```bash
  > extract_gdoc_map.py --input_dir "/path/to/docs" --output_file "links.md" --style full_path
  ```

- The script will:
  - Find all `.gdoc` files recursively
  - Parse JSON to extract Google Doc IDs
  - Generate clickable links to `https://docs.google.com/document/d/{doc_id}`
  - Format as Markdown list

## `pdf_to_md.py`

### What It Does

- Convert PDF files to Markdown using PyMuPDF (fitz)
- Extracts text with formatting information to identify headers
- Extracts embedded images and vector graphics
- Analyzes font sizes to determine heading levels (H1, H2, H3)
- Preserves document structure with proper Markdown formatting
- Applies Prettier formatting to final Markdown output
- Requires `uv` for dependency management (automatically installs PyMuPDF)

### Examples

- Convert PDF to Markdown with images
  ```bash
  > uv run pdf_to_md.py --input document.pdf --output output_dir
  ```

- With verbose logging
  ```bash
  > uv run pdf_to_md.py --input paper.pdf --output paper_md -v DEBUG
  ```

- The script will:
  - Create `output_dir/` and `output_dir/images/` directories
  - Extract all images to `images/` folder
  - Generate `document.md` with embedded image references
  - Format output using Prettier

## `preprocess_notes.py`

### What It Does

- Convert Causify-extended notes format into standard Pandoc Markdown
- Prepares notes for conversion with `notes_to_pdf.py`
- Applies comprehensive transformations:
  - Handle comment blocks and single-line comments
  - Process abbreviations (e.g., `=>` → `$\implies$`)
  - Convert question format (`* foo` → `- **foo**` or `#### foo` for slides)
  - Add TOC navigation slides (for presentation mode)
  - Colorize bullet points in slides
  - Process color commands
- Supports three output types: `pdf`, `html`, `slides`
- Optional Q&A formatting mode

### Examples

- Preprocess notes for PDF generation
  ```bash
  > preprocess_notes.py --input notes.txt --output notes_processed.md --type pdf
  ```

- Preprocess for slides with navigation TOC
  ```bash
  > preprocess_notes.py --input lecture.txt --output lecture.md --type slides --toc_type navigation
  ```

- Preprocess for HTML output
  ```bash
  > preprocess_notes.py --input document.txt --output document.md --type html
  ```

- Preprocess Q&A formatted notes
  ```bash
  > preprocess_notes.py --input qa.txt --output qa.md --type pdf --qa
  ```

## `process_slides.py`

### What It Does

- Process Markdown slides using LLM prompts for enhancement or critique
- Extracts individual slides from Markdown documents
- Applies LLM transformations to each slide independently
- Supports parallel processing for batch operations
- Can use either direct LLM API calls or `llm_transform` script
- Provides progress tracking and error handling options

### Examples

- Process slides with LLM action
  ```bash
  > process_slides.py --in_file slides.md --action slide_format --out_file processed.md
  ```

- Process with llm_transform script
  ```bash
  > process_slides.py --in_file lecture.md --action slide_critique --out_file critique.md --use_llm_transform
  ```

- Process specific slide range with parallel execution
  ```bash
  > process_slides.py --in_file slides.md --action format --out_file out.md --limit 10:20 --num_threads 4
  ```

- Continue on errors (don't abort)
  ```bash
  > process_slides.py --in_file slides.md --action enhance --out_file enhanced.md --no_abort_on_error
  ```

## `create_google_drive_map.py`

### What It Does

- Generate directory structure summaries using `tree` command and LLM analysis
- Creates comprehensive documentation of Google Drive or filesystem hierarchies
- Workflow:
  - Runs `tree` on each directory
  - Summarizes content with LLM (gpt-4o-mini)
  - Optionally combines all summaries into single Markdown file
  - Optionally creates a metadata table with owner/department information
- Supports selective action execution and range limiting
- Can process directories in parallel

### Examples

- Basic usage - run tree and LLM on all directories
  ```bash
  > create_google_drive_map.py --in_dir /path/to/google_drive
  ```

- Run only tree collection
  ```bash
  > create_google_drive_map.py --in_dir /path/to/folders --action tree
  ```

- Run only LLM summarization (requires existing tree files)
  ```bash
  > create_google_drive_map.py --in_dir /path/to/folders --action llm
  ```

- Combine existing summaries into single file
  ```bash
  > create_google_drive_map.py --in_dir /path/to/folders --action combine
  ```

- Create directory metadata table
  ```bash
  > create_google_drive_map.py --in_dir /path/to/folders --action table
  ```

- Process only first 5 directories
  ```bash
  > create_google_drive_map.py --in_dir /path/to/folders --limit 1:5
  ```

- Full workflow with custom output directory
  ```bash
  > create_google_drive_map.py --in_dir /projects/code --out_dir analysis --all
  ```

- Start fresh by deleting existing output
  ```bash
  > create_google_drive_map.py --in_dir /path/to/folders --from_scratch
  ```

## `generate_latex_sty.py`

### What It Does

- One-off utility script for generating LaTeX style abbreviations
- Creates LaTeX `\newcommand` macros for:
  - Vector notation (e.g., `\va` → `\vv{a}`, `\vvv` → `\vv{v}`)
  - Matrix notation (e.g., `\mA` → `\mat{A}`, `\mSigma` → `\mat{\Sigma}`)
  - Mathcal notation (e.g., `\calA` → `\mathcal{A}`)
- Generates Perl scripts for converting between abbreviation styles
- Creates vim spell-check files for LaTeX abbreviations
- Primarily used for initial setup and style file generation

### Examples

- Generate LaTeX abbreviation style file
  ```python
  python generate_latex_sty.py
  ```
  - Output: `latex_abbrevs.tmp.sty`
  - Uncomment desired function in `__main__` block to generate different outputs

- The script provides these generation functions:
  - `generate_latex()`: Creates LaTeX style file with abbreviations
  - `generate_vim_spell_check()`: Creates vim spell-check file
  - `generate_perl1()`, `generate_perl2()`, `generate_perl3()`: Generate Perl conversion scripts
  - `generate_mathcal()`: Generates mathcal notation macros

# Useful Tools

## Mermaid

- To render on-line: [https://mermaid.live](https://mermaid.live)

- Resources:
  - [https://mermaid.js.org/syntax/examples.html](https://mermaid.js.org/syntax/examples.html)

## Graphviz

- To render on-line:
  [https://dreampuf.github.io/GraphvizOnline](https://dreampuf.github.io/GraphvizOnline)

- Resources:
  - [https://graphviz.org/gallery/](https://graphviz.org/gallery/)

## Markdown

- To render on-line:
  [https://markdownlivepreview.com/](https://markdownlivepreview.com/)

## Pandoc

- To render on-line: [https://pandoc.org/try/](https://pandoc.org/try/)

## Tikz

- To render on-line use Overleaf

## Resources
- [https://www.overleaf.com/learn/latex/TikZ_package](https://www.overleaf.com/learn/latex/TikZ_package)
- [https://texample.net/](https://texample.net/)
- [https://www.integral-domain.org/lwilliams/Resources/tikzsnippets.php](https://www.integral-domain.org/lwilliams/Resources/tikzsnippets.php)
- [https://tikz.pablopie.xyz/](https://tikz.pablopie.xyz/)
- [https://tikzit.github.io/](https://tikzit.github.io/)
- [https://latexdraw.com/](https://latexdraw.com/)
