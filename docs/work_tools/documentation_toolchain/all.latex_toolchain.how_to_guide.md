<!-- toc -->

- [Definitions](#definitions)
- [Files](#files)
- [Editing `txt` files](#editing-txt-files)
  * [Generate the summary of the headers](#generate-the-summary-of-the-headers)
  * [Format a chunk of `txt` file](#format-a-chunk-of-txt-file)
  * [List possible LLM transforms](#list-possible-llm-transforms)
  * [Convert notes to slides](#convert-notes-to-slides)
- [Latex Toolchain](#latex-toolchain)
  * [Running and linting Latex files](#running-and-linting-latex-files)

<!-- tocstop -->

# Definitions

- "Notes" are `txt` files in extended markdown that include:
  - Latex
  - Block comments
  - Calls to external tools, such as `mermaid`, `plantuml`, `tikz`, ...

- Notes files can be converted to:
  - PDF (through a conversion to an intermediate Latex file)
  - HTML
  - Slides (through beamer)
  - Questions / answers (through Anki)

# Files
```
> ls -1 dev_scripts_helpers/documentation
```

- In the directory `//helpers/dev_scripts_helpers/documentation`
  - `convert_docx_to_markdown.py`
    - Convert Docx file to markdown using Dockerized `pandoc` and save the figs
      in a directory
  - `convert_docx_to_markdown.sh`
    - Wrapper to simplify calling `convert_docx_to_markdown.py`
  - `generate_latex_sty.py`
    - One-off script to generate the latex file
  - `generate_script_catalog.py`
    - Generate a markdown file with the docstring for any script in the repo
    - TODO(gp): Unclear what to do with this
  - `latex_abbrevs.sty`
    - Latex macros
  - `latexdockercmd.sh`
    - Wrapper for Latex docker container
    - TODO(gp): probably obsolete
  - `lint_latex.sh`
    - Dockerized linter for Latex using `prettier`
    - TODO(gp): This is the new flow, but it needs to be converted in Python
  - `lint_latex2.sh`
    - Dockerized linter for Latex using `latexindent.pl`
    - TODO(gp): This is the old flow
  - `open_md_in_browser.sh`
    - Render a markdown using `pandoc` (installed locally) and then open it in a
      browser
  - `open_md_on_github.sh`
    - Open a markdown filename on GitHub
  - `pandoc.latex`
    - `latex` template used by `notes_to_pdf.py`
  - `preprocess_notes.py`
    - Convert a text file storing notes into markdown suitable for
      `notes_to_pdf.py`
    - The transformations are
      - Convert the text in pandoc / latex format
      - Handle banners around chapters
      - Handle comments
  - `notes_to_pdf.py`
    - Convert a `txt` file storing nodes into a PDF / HTML / beamer slides using
      `pandoc`
  - `render_images.py`
    - Render images from code (e.g., plantUML, mermaid) in Markdown / LaTeX
      files
  - `replace_latex.py`, `replace_latex.sh`
    - Scripts for one-off processing of latex files
  - `run_latex.sh`
    - Dockerized latex flow
    - TODO(gp): Convert to Python
  - `run_notes_to_pdf.py`
    - Read value from stdin/file
    - Transform it using `pandoc` according to different transforms (e.g.,
      `convert_md_to_latex`)
    - Write the result to stdout/file.
    - TODO(gp): Is this obsolete?
  - `test_lint_latex.sh`
    - Run latex linter and check if the file was modified
  - `transform_notes.py`
    - Perform one of several transformations on a text file, e.g.,
      1. `toc`: create table of context from the current file, with 1 level
      2. `format`: format the current file with 3 levels
      3. `increase`: increase level

# Editing `txt` files

## Generate the summary of the headers

- In `vim`
  ```bash
  :!helpers_root/dev_scripts_helpers/documentation/process_md_headers.py -i % -m 1
  ```
  ```bash
  Probability 1
  Random variables 735
  Mathematical expectation of RVs 1161
  Interesting RVs 1803
  Probability inequalities 2124
  Statistical Inference 2194
  Statistical test 3707
  ```
- This script also generates a `vim` `cfile` that can be navigated with `vic`

- To get the summary up to 2 levels:
  ```bash
  :!helpers_root/dev_scripts_helpers/documentation/process_md_headers.py -i % -m 2
  ```

## Format a chunk of `txt` file

- In vim
  ```bash
  :'<,'>!helpers_root/dev_scripts_helpers/llms/llm_transform.py -i - -o - -t md_format
  ```

## List possible LLM transforms

- Use `-t list`
  ```bash
  code_comment
  code_docstring
  code_type_hints
  code_unit_test
  code_1_unit_test
  md_rewrite
  md_format
  slide_improve
  slide_colorize
  ```

## Convert notes to slides

- Convert notes to slides:
  ```bash
  > notes_to_pdf.py --input notes/MSML610/Lesson1-Intro.txt --output tmp.pdf -t slides --skip_action copy_to_gdrive --skip_action open --skip_action cleanup_after
  ```

# Latex Toolchain

## Running and linting Latex files

- We organize each project is in a directory (e.g., under `//papers`)
- Under each dir there are several scripts that assign some variables and then
  call the main scripts to perform the actual work by calling
  `run_notes_to_pdf.py`
  - `run_latex.sh`
  - `lint_latex.sh`

- Scripts are "dockerized" scripts, which build a Docker container with
  dependencies and then run use it to process the data

- To run the Latex flow we assume (as usual) that user runs from the top of the
  tree

- To create the PDF from the Latex files:

  ```bash
  > papers/DataFlow_stream_computing_framework/run_latex.sh
  ...
  ```

- To lint the Latex file:
  ```
  > papers/DataFlow_stream_computing_framework/lint_latex.sh
  ...
  + docker run --rm -it --workdir /Users/saggese/src/cmamp1 --mount type=bind,source=/Users/saggese/src/cmamp1,target=/Users/saggese/src/cmamp1 lint_latex:latest sh -c ''\''./tmp.lint_latex.sh'\''' papers/DataFlow_stream_computing_framework/DataFlow_stream_computing_framework.tex
  papers/DataFlow_stream_computing_framework/DataFlow_stream_computing_framework.tex 320ms (unchanged)
  ```
