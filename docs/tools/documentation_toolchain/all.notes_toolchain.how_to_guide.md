<!-- toc -->

- [Notes Documentation Toolchain](#notes-documentation-toolchain)
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

| File extension | Rendering syntax allowed                       | Output embeds as           |
| -------------- | ---------------------------------------------- | -------------------------- |
| `.md`, `.txt`  | `plantuml / mermaid / graphviz / tikz / latex` | `<img src="figs/xxx.png">` |
| `.tex`         | same tags (TikZ & LaTeX especially)            | `\includegraphics{...}`    |

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

#### Prettify with Dockerised Prettier + TOC rebuild

```bash
lint_notes.py -i Lesson10.md \
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