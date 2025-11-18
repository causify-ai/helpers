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

### Causify Extended Markdown

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

- TODO(gp): Use the invoke to describe the list
```
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

## `Notes_To_Pdf.Py`

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

## `Render_Images.Py`

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

## `Lint_Notes.Py`

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

###

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

## `Extract_Notebook_Images.Py`

### What It Does

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

## `Llm_Transform.Py`

### What It Does

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

## `Run_Pandoc.Py`

### What It Does

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

## `Transform_Notes.Py`

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

## `Extract_Headers_From_Markdown.Py`

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

## `Dockerized_Tikz_To_Bitmap.Py`

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

## `Dockerized_Graphviz.Py`

### What It Does

- Converts a Graphviz `.dot` file into a `.png` image using a Dockerized
  container.

  > ```bash
  > graphviz_wrapper.py --input input.dot --output output.png
  > ```

- This script serves as a thin wrapper around Dockerized Graphviz for consistent
  rendering across systems.

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

## `Dockerized_Latex.Py`

### What It Does

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

## `Dockerized_Mermaid.Py`

### What It Does

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

## `Dockerized_Pandoc.Py`

### What It Does

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

## `Dockerized_Prettier.Py`

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

## `Save_Screenshot.Py`

### What It Does

1. Prompts you to select a screen region (`⌘ + Ctrl + 4`).
2. Saves it as `screenshot.YYYY‑MM‑DD_HH‑MM‑SS.png` (or your chosen name).
3. Prints and copies the Markdown embed `<img src="path/to/file.png">`.

## `Generate_Images.Py`

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

## Useful Tools

### Mermaid

- To render on-line: [https://mermaid.live](https://mermaid.live)

- Resources:
  - [https://mermaid.js.org/syntax/examples.html](https://mermaid.js.org/syntax/examples.html)

### Graphviz

- To render on-line:
  [https://dreampuf.github.io/GraphvizOnline](https://dreampuf.github.io/GraphvizOnline)

- Resources:
  - [https://graphviz.org/gallery/](https://graphviz.org/gallery/)

### Markdown

- To render on-line:
  [https://markdownlivepreview.com/](https://markdownlivepreview.com/)

### Pandoc

- To render on-line: [https://pandoc.org/try/](https://pandoc.org/try/)

### Tikz

- To render on-line use Overleaf

- Resources
  - [https://www.overleaf.com/learn/latex/TikZ_package](https://www.overleaf.com/learn/latex/TikZ_package)
  - [https://texample.net/](https://texample.net/)
  - [https://www.integral-domain.org/lwilliams/Resources/tikzsnippets.php](https://www.integral-domain.org/lwilliams/Resources/tikzsnippets.php)
  - [https://tikz.pablopie.xyz/](https://tikz.pablopie.xyz/)
  - [https://tikzit.github.io/](https://tikzit.github.io/)
  - [https://latexdraw.com/](https://latexdraw.com/)
