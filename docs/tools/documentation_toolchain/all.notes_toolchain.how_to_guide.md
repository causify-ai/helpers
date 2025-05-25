<!-- toc -->

- [Notes Documentation Toolchain](#notes-documentation-toolchain)
- - [Tool Dockerized Components Guide](#tool-dockerized-components-guide)
  * [1 · Dockerized Graphviz](#1--dockerized-graphviz)
  * [2 · Dockerized LaTeX](#2--dockerized-latex)
  * [3 · Dockerized Mermaid](#3--dockerized-mermaid)
  * [4 · Dockerized Pandoc](#4--dockerized-pandoc)
  * [5 · Dockerized Prettier](#5--dockerized-prettier)
  * [1 · Generate slides & PDFs — `notes_to_pdf.py`](#1-%C2%B7-generate-slides--pdfs--notes_to_pdfpy)
    + [What it does](#what-it-does)
    + [Most‑used flags](#most%E2%80%91used-flags)
    + [Quick‑start recipes](#quick%E2%80%91start-recipes)
    + [CLI flags cheat‑sheet](#cli-flags-cheat%E2%80%91sheet)
    + [Worked examples](#worked-examples)
      - [Slides with navigation breadcrumbs](#slides-with-navigation-breadcrumbs)
      - [Focus on a subsection](#focus-on-a-subsection)
      - [Plain PDF article (no slides)](#plain-pdf-article-no-slides)
  * [2 · Auto‑render figures — `render_images.py`](#2-%C2%B7-auto%E2%80%91render-figures--render_imagespy)
    + [Supported File types and Code blocks](#supported-file-types-and-code-blocks)
    + [Quick Start Recipes](#quick-start-recipes)
      - [Render to a new file](#render-to-a-new-file)
      - [Render in‑place (Markdown or LaTeX)](#render-in%E2%80%91place-markdown-or-latex)
      - [HTML preview of already‑rendered images](#html-preview-of-already%E2%80%91rendered-images)
      - [Dry‑run (test parsing / comments only)](#dry%E2%80%91run-test-parsing--comments-only)
    + [Flags](#flags)
  * [3 · Lint & prettify — `lint_notes.py`](#3-%C2%B7-lint--prettify--lint_notespy)
    + [Quickstart recipes](#quickstart-recipes)
      - [In‑place prettify with Dockerised Prettier + TOC rebuild](#in%E2%80%91place-prettify-with-dockerised-prettier--toc-rebuild)
      - [Custom print width & selective actions](#custom-print-width--selective-actions)
    + [Flags](#flags-1)
  * [4 · Notebook image scraping — `extract_notebook_images.py`](#4-%C2%B7-notebook-image-scraping--extract_notebook_imagespy)
    + [Flag Options](#flag-options)
  * [5 · LLM‑powered transforms — `llm_transform.py`](#5-%C2%B7-llm%E2%80%91powered-transforms--llm_transformpy)
    + [Minimum viable command](#minimum-viable-command)
    + [Finding available prompts](#finding-available-prompts)
    + [Flags](#flags-2)
    + [Example recipes](#example-recipes)

<!-- tocstop -->

# Notes Documentation Toolchain

This is a high‑level guide to the helper scripts that turn raw `.txt` lecture
notes into polished PDFs, slide decks, and more.

---

## 1 · Dockerized Graphviz

### ✅ What
Converts Graphviz DOT files into PNG images that are later inserted into slides.

### 💡 Why
- Removes manual dependency installation across systems.
- Ensures version consistency of Graphviz.
- Provides high-level abstraction and hides complex code.

### 🔧 How
Two key functions:
- `_parse()`:
  - Creates a parser object for CLI execution.
  - Adds required input and output arguments.
  - Appends Docker and verbosity arguments.
- `main()`:
  - Parses known and unknown arguments.
  - Initializes logger.
  - Calls Graphviz Docker function with:
    - `args.input`
    - `cmd_opts`
    - `args.output`
    - `force_rebuild`
    - `use_sudo`

### 🔗 Dependency – `run_dockerized_graphviz()` in `hdocker.py`
- Calls `build_container_image()`.
- Converts paths to Docker format.
- Constructs full Docker command string.
- Optionally uses `sudo` for Docker execution.
- Final command is run with `hsystem.system()`.

### 🔗 Dependency – `build_container_image()`
1. Defines the container image.
2. Checks for image existence and rebuild flag.
3. If needed:
   - Creates temp Dockerfile directory.
   - Constructs Docker command string.
   - Executes via `hsystem.system()`.

---

## 2 · Dockerized LaTeX

### ✅ What
Runs LaTeX using `pdflatex` inside Docker to produce PDF output.

### 💡 Why
- Provides clean abstraction.
- Hides system-level LaTeX setup complexity.

### 🔧 How
Two main functions:
- `parser()`:
  - Creates CLI object.
  - Adds file paths and Docker args.
- `main()`:
  - Parses known and unknown args.
  - Initializes logging.
  - Calls `run_basic_latex()`.

### 🔗 Dependency – `run_basic_latex()` in `hdocker.py`
- Validates file paths and extensions.
- Builds `pdflatex` command string.
- Calls `run_dockerized_latex()` (twice if needed).
- Changes output extension to PDF and moves file if needed.

### 🔗 Dependency – `run_dockerized_latex()`
1. Sets container image and Dockerfile.
2. Calls `build_container_image()`.
3. Converts paths to Docker format.
4. Prepares param dictionary.
5. Converts all paths in params to Docker format.
6. Ensures input is at command end (bug workaround).
7. Appends `sudo` if needed.
8. Cleans spacing and runs command using `hsystem.system()`.

---

## 3 · Dockerized Mermaid

### ✅ What
Runs Mermaid chart/diagram rendering inside Docker.

### 🔧 How
Acts as a lightweight placeholder for calling `run_dockerized_mermaid()`.

### 🔗 Dependency – `run_dockerized_mermaid()` in `hdocker.py`
1. Defines the container image.
2. Retrieves input/output paths.
3. Uses sibling container.
4. Converts paths to Docker format.
5. Constructs CLI command.
6. Prepends `sudo` if needed.
7. Executes with `process_docker_cmd()`.

---

## 4 · Dockerized Pandoc

### ✅ What
Provides a high-level abstraction for running Pandoc inside Docker.

### 🔧 How
Two functions:
- `_parse()`:
  - Builds CLI parser.
  - Adds Docker, file path, verbosity options.
- `_main()`:
  - Parses args.
  - Defaults `args.output` if needed.
  - Constructs Pandoc command string.
  - Calls `run_dockerized_pandoc()`.

### 🔗 Dependency – `run_dockerized_pandoc()` in `hdocker.py`
1. Handles container type:
   - `pandoc_only`: Lightweight.
   - `pandoc_latex`: Custom build with TeXLive.
   - `pandoc_texlive`: Uses texlive/texlive + apt.
2. Builds container.
3. Converts paths.
4. Mounts volumes.
5. Prepares command and arguments.
6. Assembles final Docker command.
7. Executes via `hsystem.system()`.

---

## 5 · Dockerized Prettier

### ✅ What
Formats `.md`, `.txt`, `.tex` using Prettier via Docker.

### 💡 Why
- Ensures consistent formatting across environments.
- Avoids need to install plugins manually.

### 🔧 How
Two key functions:
- `_parse()`:
  - Adds input/output, Docker, verbosity args to parser.
- `_main()`:
  - Parses args and logs.
  - Handles empty `cmd_opts`.
  - Calls `run_dockerized_prettier()`.

### 🔗 Dependency – `run_dockerized_prettier()` in `hdocker.py`
1. Defines container image.
2. Chooses image per `file_type` (`md`, `txt`, `tex`).
3. Uses sibling container.
4. Converts paths to Docker format.
5. If output = input, adds `--write`.
6. Chooses executable based on file type.
7. Constructs bash command with redirection if needed.
8. Builds and executes Docker command.

---

## 1 · Generate slides & PDFs — `notes_to_pdf.py`

### What it does

Convert plain‑text notes into polished **PDF, HTML, or Beamer slides** with a
single command.

> ```bash
> notes_to_pdf.py --input <infile.txt> --output <outfile.[pdf|html]> --type [pdf|html|slides]
> ```

### Most‑used flags

* `--type {pdf|html|slides}`
* `--toc_type {none|pandoc_native|navigation}`
* `--debug_on_error`, `--skip_action ...`, `--filter_by_lines A:B`

### Quick‑start recipes

| Goal                                | Command                                                            |
| ----------------------------------- | ------------------------------------------------------------------ |
| Compile to **Beamer slides**        | `notes_to_pdf.py -i lesson.txt -o lesson.pdf --type slides`        |
| Produce a **stand‑alone HTML** page | `notes_to_pdf.py -i cheatsheet.txt -o cheatsheet.html --type html` |
| Build a **PDF article** (LaTeX)     | `notes_to_pdf.py -i paper.txt -o paper.pdf --type pdf`             |
| Skip the final viewer **open** step | `... --skip_action open`                                           |

_TIP  Run with `--preview_actions` to print the exact steps without executing
them._

### CLI flags cheat‑sheet

| Flag                                         | Purpose                                                                   | Notes                                                 |
| -------------------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------- |
| `--type {pdf,html,slides}`                   | Output format                                                             | "slides" uses Beamer                                  |
| `--toc_type {none,pandoc_native,navigation}` | TOC style                                                                 | `navigation` inserts slide‑friendly breadcrumb frames |
| `--filter_by_header "# Intro"`               | Build artefact from a _section subset_                                    | Useful for testing                                    |
| `--filter_by_lines 120:250`                  | Compile only a range of lines                                             | Accepts `None` sentinel                               |
| `--debug_on_error`                           | On Pandoc failure, generate _.tex_ and drop you a helpful log             |                                                       |
| `--script myrun.sh`                          | Save every shell command executed                                         | Repro build pipelines                                 |
| Docker knobs                                 | `--dockerized_force_rebuild`, `--dockerized_use_sudo`, `--use_host_tools` | Control container vs host pandoc/latex                |

_Run `notes_to_pdf.py -h` for the exhaustive list._

### Worked examples

#### Slides with navigation breadcrumbs

TODO(indro): `--toc_type navigation` fails because of the preprocess step.

```bash
notes_to_pdf.py \
  --input MSML610/Lesson5-Theory_Statistical_learning.txt \
  --output Lesson5.pdf \
  --type slides \
  --toc_type navigation \
  --debug_on_error \
  --skip_action cleanup_after
```

_Highlights_: adds breadcrumb navigation, keeps intermediates for inspection.

#### Focus on a subsection

```bash
notes_to_pdf.py \
  --input Lesson8-Reasoning_over_time.txt \
  --output Focus.pdf \
  --type slides \
  --filter_by_lines 362:None \
  --skip_action cleanup_after
```

Compiles only from line 362 to EOF—fast iteration when debugging slides.

#### Plain PDF article (no slides)

```bash
notes_to_pdf.py -i book_notes.txt -o book_notes.pdf --type pdf
```

---

## 2 · Auto‑render figures — `render_images.py`

Detects fenced code blocks (PlantUML, Mermaid, TikZ, Graphviz, ...), renders
them into images and swaps the block with `![](img)` markup.

Example:

```bash
render_images.py -i notes/MSML610/Lesson9-Causal_inference.txt \
                -o lesson9.images.txt --run_dockerized
```

### Supported File types and Code blocks

| File extension | Rendering syntax allowed                       | Output embeds as        |
| -------------- | ---------------------------------------------- | ----------------------- |
| `.md`, `.txt`  | `plantuml / mermaid / graphviz / tikz / latex` | `<img src="figs/xxx.png">`     |
| `.tex`         | same tags (TikZ & LaTeX especially)            | `\includegraphics{...}` |

### Quick Start Recipes

#### Render to a new file

```bash
render_images.py -i lesson.md -o lesson.rendered.md --action render --run_dockerized
```

#### Render in‑place (Markdown or LaTeX)

```bash
render_images.py -i lesson.md --action render --run_dockerized
```

#### HTML preview of already‑rendered images

```bash
render_images.py -i lesson.md --action open --run_dockerized
```

#### Dry‑run (test parsing / comments only)

```bash
render_images.py -i lesson.md -o /tmp/out.md --dry_run
```

### Flags

| Flag                                | Default      | Purpose                                                    |
| ----------------------------------- | ------------ | ---------------------------------------------------------- |
| `-i/--in_file_name`                 | **required** | Input `.md`, `.tex`, or `.txt`                             |
| `-o/--out_file_name`                | `<input>`    | Output path (must share extension)                         |
| `--action`                          | `render`     | `render` ↔ `open`                                         |
| `--dry_run`                         | _False_      | Skip actual rendering, still rewrites markup               |
| `--run_dockerized / --dockerized_*` | _False_      | Use pre‑built container images for PlantUML, Mermaid, etc. |
| `--verbosity/-v`                    | `INFO`       | Logging verbosity                                          |

---

## 3 · Lint & prettify — `lint_notes.py`

A tidying‑up tool for Markdown/LaTeX notes: normalise G‑Doc artifacts, run
Prettier, fix bullet/heading quirks, refresh the Table of Contents – all from a
single command or straight from vim.

### Quickstart recipes

#### In‑place prettify with Dockerised Prettier + TOC rebuild

```bash
lint_notes.py -i Lesson10.md --in_place \
              --use_dockerized_prettier \
              --use_dockerized_markdown_toc
```

#### Custom print width & selective actions

```bash
lint_notes.py -i draft.txt -o tidy.txt -w 100 \
              --action preprocess,prettier,postprocess
```

### Flags

| Flag                            | Default                   | Purpose                                                                                             |
| ------------------------------- | ------------------------- | --------------------------------------------------------------------------------------------------- |
| `-i/--infile`                   | **stdin**                 | Input `.txt` or `.md` (also via pipe)                                                               |
| `-o/--outfile`                  | **stdout**                | Destination file (omit for pipe)                                                                    |
| `--in_place`                    | _False_                   | Overwrite the input file                                                                            |
| `-w/--print-width`              | _None_ → Prettier default | Line wrap width                                                                                     |
| `--use_dockerized_prettier`     | _False_                   | Run Prettier inside helper container                                                                |
| `--use_dockerized_markdown_toc` | _False_                   | Refresh TOC via containerised `markdown-toc`                                                        |
| `--action`                      | all five stages           | Comma‑separated subset of: `preprocess`, `prettier`, `postprocess`, `frame_chapters`, `refresh_toc` |
| `-v/--verbosity`                | `INFO`                    | Logging level                                                                                       |

---

## 4 · Notebook image scraping — `extract_notebook_images.py`

Spins up a docker container and dumps every `png/svg` output cell into a folder.
You can then publish or reuse the static plots/diagrams already rendered in a
Jupyter notebook.

Minimal call:

```bash
extract_notebook_images.py \
    --in_notebook_filename notebooks/Lesson8.ipynb \
    --out_image_dir notebooks/screenshots
```

### Flag Options

| Flag                               | Purpose                                                       | Default      |
| ---------------------------------- | ------------------------------------------------------------- | ------------ |
| `-i / --in_notebook_filename PATH` | Notebook to scan                                              | **required** |
| `-o / --out_image_dir DIR`         | Folder where images land                                      | **required** |
| `--dockerized_force_rebuild`       | Re‑build the Docker image (use if you changed extractor code) | _false_      |
| `--dockerized_use_sudo`            | Prepend `sudo docker ...`                                     | auto‑detects |
| `-v INFO/DEBUG`                    | Log verbosity                                                 | `INFO`       |

---

## 5 · LLM‑powered transforms — `llm_transform.py`

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

| Flag                                                                 | Role                                                          | Notes                  |
| -------------------------------------------------------------------- | ------------------------------------------------------------- | ---------------------- |
| `-i / --input`                                                       | Source text (`-` = stdin)                                     | —                      |
| `-o / --output`                                                      | Destination (`-` = stdout)                                    | —                      |
| `-p / --prompt`                                                      | **Prompt tag** (`list`, `code_review`, `slide_colorize`, ...) | required               |
| `-c / --compare`                                                     | Print _both_ original & transformed blocks to stdout          | helpful for quick diff |
| `-b / --bold_first_level_bullets`                                    | Post‑format tweak for slide prompts                           |                        |
| `-s / --skip-post-transforms`                                        | Return raw LLM output, skip prettier/cleanup                  |                        |
| Docker flags (`--dockerized_force_rebuild`, `--dockerized_use_sudo`) | Control container lifecycle                                   |

### Example recipes

* **Turn a code file into a review checklist**

  ```bash
  llm_transform.py -i foo.py -o cfile -p code_review
  vim cfile
  ```

* **Color‑accent the bold bullets for slides**

  ```bash
  llm_transform.py -i deck.md -o - -p slide_colorize | tee deck.color.md
  ```

* **Inline use in Vim** – visual‑select a block, then:

  ```vim
  :'<,'>!llm_transform.py -p summarize -i - -o -
  ```

---
