# Overview
- `notes_to_pdf.py` is a comprehensive document conversion orchestrator that
  transforms markdown/text files into multiple output formats (PDF, HTML,
  presentation slides) using Pandoc/LaTeX/Typst toolchains
- Honors rich Markdown features and custom shorthand, inlining auto-rendered
  diagrams (PlantUML, Mermaid, TikZ, Graphviz, and raw LaTeX such as tables)
  before conversion
- Manages a complete multi-stage pipeline including
  - Preprocessing
  - Image rendering
  - Format conversion
  - Post-processing
- Uses optional Docker containerization for tool isolation
- Converts research notes, lecture materials, and educational content into
  professional-grade documents and presentations
- Users can selectively enable/disable pipeline stages for iterative development
  and debugging

## Features
- Support to create technical lecture slides and books from enhanced pandoc
  markdown
  - Slides
  - Comments (// and /* ... */)
  - TOC
  - Templating
  - Semantic tags
  - Rendering of pictures with different tools (Tikz, graphviz, mermaid, ...)
  - Testing
  - LLM integration (check correctness, formatting, shrink text, ...)
- Supports typst and Latex backend
  - Several fixes for creating typst from pandoc markdown AST (colors, tables)
  - Make typst look similar to Latex (which is golden standard, e.g., Computer
    Modern)
- Utilities
  - Stats
  - Conversion to book
  - Conversion to commentary
  - Create questions and summaries

# Pipeline Scripts

- Before invoking Pandoc, `notes_to_pdf.py` orchestrates two sibling scripts
  and one shared LaTeX style, in this order: `preprocess_notes.py` cleans and
  augments the raw notes, `render_images.py` renders inline diagrams to
  images, and `latex_abbrevs.sty` supplies the LaTeX macros used by the
  LaTeX/Beamer output paths

## `preprocess_notes.py`

- **Input:** Raw notes (`.txt`/`.md`)
- **Output:** Pandoc-ready Markdown
- Handles:
  - Banners around chapters
  - Comments
  - Pandoc directives (YAML front-matter)
  - Abbreviation expansion
  - Question formatting
  - Empty-line cleanup
  - TOC / navigation-slide injection

## `render_images.py`

- Docker-wrapped renderer that replaces PlantUML, Mermaid, TikZ, Graphviz, and
  raw LaTeX (e.g., tables) code blocks with rendered
  `![](figs/<basename>.<index>.png)` images, commenting out the original
  source block
- Caches rendered images to skip re-rendering unchanged diagrams on re-runs
- See `render_images.README.md` for full usage details

## `latex_abbrevs.sty`

- Custom LaTeX style providing bold-underlined vectors (`\vv{x}`), matrices,
  colour presets, 9-level `enumitem` lists, and symbol shorthands
- Copied next to the generated `.tex` file automatically; rarely touched
  unless new macros are needed
- Mined by `_extract_latex_math_defs()` for the Typst slide path (see C4 Code
  section below)

# Architecture (C4 Model)

- This section shows how components are implemented

- **Primary Call Flow:**
  ```
  _main() 
    - _run_all(args)
      - _cleanup_before()
      - _preprocess_notes()
        - _render_images()
      - [_run_pandoc_to_pdf() | _run_pandoc_to_html() | _run_pandoc_to_latex_slides() | _run_pandoc_to_typst_slides()]
      - _compress_pdf() [optional]
      - _copy_to_output()
        - _copy_to_gdrive() [optional]
      - _cleanup_after() [optional]
  ```

- **Function List**

| Function | Purpose |
|----------|---------|
| `_run_all(args)` | Main orchestrator; manages entire pipeline execution and action sequencing |
| `_preprocess_notes()` | Calls external preprocessor script; returns processed file path |
| `_render_images()` | Renders inline diagram/image specs; filters commented code; returns file path |
| `_run_pandoc_to_pdf()` | Converts markdown → LaTeX → PDF via Pandoc and pdflatex (2 passes); returns PDF path |
| `_run_pandoc_to_html()` | Converts markdown to HTML via Pandoc; returns HTML path |
| `_run_pandoc_to_latex_slides()` | Converts markdown to Beamer PDF slides; returns PDF path or .tex if `no_pdf=True` |
| `_run_pandoc_to_typst_slides()` | Converts markdown → Typst/Touying → PDF slides via a 3-step pipeline (markdown → AST → divved-fence transform → typst); prepends LaTeX math abbreviation definitions so pandoc expands them |
| `_extract_latex_math_defs()` | Reads `latex_abbrevs.sty` and returns the `\newcommand` / `\def` math macros (dropping packages, colors, list config, and `\textcolor` helpers) for prepending to the typst input |
| `_compress_pdf()` | Compresses PDF via ghostscript; in-place modification; returns file path |
| `_copy_to_output()` | Copies processed file to output location; returns output path |
| `_copy_to_gdrive()` | Copies output to Google Drive archive directory |
| `_cleanup_before()` | Removes intermediate files matching prefix pattern and cache files |
| `_cleanup_after()` | Removes intermediate files matching prefix pattern |
| `_system()` | Executes shell command; logs output; optionally appends to script; returns exit code |
| `_system_to_string()` | Executes shell command; captures stdout; returns (exit_code, output) |

- **Notable Code Patterns:**

  1. _Global Script Accumulation_: The `_SCRIPT` global list accumulates all
     executed commands if `--script` flag is used, enabling script generation for
     reproducibility.

  2. _File Path Staging_: Each processing function takes input file path and
     returns output path, creating a pipeline of transformations:
     ```
     - original.txt 
     - tmp.preprocess_notes.txt
     - tmp.render_image2.txt
     - tmp.tex (or .html, .pdf)
     - output.pdf (final)
     ```

  3. _Docker Containerization_: Functions like `_run_pandoc_to_pdf()` check
     `use_host_tools` flag and conditionally wrap commands via
     `dshdlipa.run_dockerized_pandoc()` and `dshdlila.run_dockerized_latex()`.

  4. _Two-Pass LaTeX Compilation_: PDF generation runs `pdflatex` twice by
     default (controlled by `no_run_latex_again` flag) to resolve
     cross-references.

  5. _Multiple Slide Engines_: `--slides_engine` flag switches between Beamer
     (LaTeX-based) and Typst/Touying engines, with engine-specific command
     building and compilation logic.

  6. _Common Pandoc Options_: Shared options stored in `_COMMON_PANDOC_OPTS` list
     (margins, highlighting, numbering) to ensure consistency across PDF and HTML
     converters.

  7. _Pandoc AST Transform Flag_: `--use_pandoc_ast_transform` (default off) opts
     into a two-stage AST pipeline (markdown → JSON → target format) instead of the
     default single-shot pandoc call. For PDF, HTML, and beamer slides, the
     single-shot path is the default. The typst slides path always uses a 3-step
     pipeline regardless of this flag (see next point).

  8. _Typst Divved-Fence Conversion_: `_run_pandoc_to_typst_slides()` always
     runs a 3-step pipeline:
     ```
     markdown (+ prepended math defs) → JSON AST (pandoc)
              → transformed AST (convert_pandoc_divved_fence.py)
              → typst file (pandoc)
              → PDF (typst compile)
     ```
     `convert_pandoc_divved_fence.py` replaces pandoc `Div[columns]` AST nodes
     (produced from `:::columns` / `::::column` markdown fences) with
     `RawBlock[typst #grid(...)]` so that multi-column slides render correctly in
     Typst.

  9. _LaTeX → Typst Math Abbreviation Expansion_:
     - Lecture markdown uses LaTeX macros (`\vx`, `\mA`, `\EE`, ...) defined in
       `latex_abbrevs.sty`
     - In the LaTeX/beamer flows these are resolved by including the `.sty` file
       at compile time. Typst cannot do this because pandoc rejects an unknown
       control sequence in math (e.g., `$\vx$` → "unexpected control sequence
       \vx"), emitting it as escaped literal text
     - The `#let` definitions in `typst_abbrevs.typ` therefore cannot resolve
       macros used inside math
     - The working strategy is expansion of the latex macros in step 1, calling
       `_extract_latex_math_defs()` to pull the `\newcommand` / `\def` math
       macros out of `latex_abbrevs.sty` and prepends them (as a raw-LaTeX block,
       not wrapped in `$...$`) to the input, writing `{file}.with_defs.txt`
     - Pandoc's `latex_macros` extension then expands each macro to its full
       LaTeX form before converting math to Typst:
       ```
       $\vx$  →  \boldsymbol{\underline{x}}  →  $bold(underline(x))$
       $\EE$  →  \mathbb{E}                  →  $bb(E)$
       ```
     - Placement matters: the definitions must be a top-level raw-LaTeX block.
       since defs wrapped in `$...$` (inline or display math) do not persist
       across pandoc math blocks

- **External Dependencies**

| Module | Purpose |
|--------|---------|
| `helpers.hdbg` | Assertions and debugging (dassert_*, init_logger) |
| `helpers.hio` | File I/O (from_file, to_file, create_dir) |
| `helpers.hgit` | Git operations (find_file to locate helper scripts) |
| `helpers.hmarkdown` | Markdown processing (filter_by_header, filter_by_slides, process_single_line_comment) |
| `helpers.hopen` | File opening utilities (open_file) |
| `helpers.hdocker` | Docker CLI integration (add_dockerized_script_arg) |
| `helpers.hparser` | Argument parsing utilities (add_verbosity_arg) |
| `helpers.hselect_action` | Action state management (mark_action, select_actions, actions_to_string) |
| `helpers.hprint` | Colored output and formatting (color_highlight, frame, func_signature_to_str) |
| `helpers.hsystem` | System command execution (system, system_to_string) |
| `dev_scripts_helpers.dockerize.lib_latex` | LaTeX Docker wrapper (run_dockerized_latex) |
| `dev_scripts_helpers.dockerize.lib_pandoc` | Pandoc Docker wrapper (run_dockerized_pandoc) |
| `dev_scripts_helpers.dockerize.lib_typst` | Typst Docker wrapper (run_dockerized_typst) |
| `convert_pandoc_divved_fence.py` | AST transformer: converts `Div[columns]` nodes to `RawBlock[typst #grid()]` for multi-column typst slides |
| `latex_abbrevs.sty` | LaTeX math macro definitions; included at compile time in the LaTeX flows and mined by `_extract_latex_math_defs()` for the typst flow |
| `typst_abbrevs.typ` | Typst `#let` companion definitions; `#include`d by `pandoc_touying.typ` for the Typst document layer (colors, tables, text helpers) — not for in-math macros |
| `pandoc_touying.typ` | Pandoc Typst template producing Touying slides |
| `typst_abbrevs_example.md` | Runnable example exercising the abbreviation expansion, with the mechanism documented in its header comment |
| External CLI tools | `pandoc`, `pdflatex`, `typst`, `/opt/homebrew/bin/gs` (ghostscript) |
