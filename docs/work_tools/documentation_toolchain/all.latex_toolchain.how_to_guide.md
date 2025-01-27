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
  - `dockerized_pandoc.py`
    - Run `pandoc` inside a Docker container, building a container if needed
    - Not tested directly but through `run_dockerized_pandoc()` in
      `helpers/test/test_hdocker.py`
  - `dockerized_prettier.py`
    - Run `prettier` inside a Docker container to ensure consistent formatting
      across different environments, building a container if needed
    - Not tested directly but through `run_dockerized_prettier()` in
      `helpers/test/test_hdocker.py`
  - `generate_latex_sty.py`
    - One-off script to generate the latex file with abbreviations
  - `generate_script_catalog.py`
    - Generate a markdown file with the docstring for any script in the repo
    - TODO(gp): Unclear what to do with this. This can be a way to create
      an index of all the scripts, if we use some consistent docstring
  - `lint_notes.py`
    - Lint "notes" files.
    - Tested by `dev_scripts_helpers/documentation/test/test_lint_notes.py`
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
  - `notes_to_pdf.py`
    - Convert a txt file into a PDF / HTML / slides using `pandoc`
  - `open_md_in_browser.sh`
    - Render a markdown using `pandoc` (installed locally) and then open it in a
      browser
  - `open_md_on_github.sh`
    - Open a markdown filename on GitHub
  - `pandoc.latex`
    - `latex` template used by `notes_to_pdf.py`
  - `preprocess_notes.py`
    - Convert a notes text file into markdown suitable for `notes_to_pdf.py`
  - `notes_to_pdf.py`
    - Convert a `txt` file storing nodes into a PDF / HTML / beamer slides using
      `pandoc`
  - `open_md_on_github.sh`
    - Render a markdown using Pandoc and then open it in a browser.
  - `open_md_on_github.sh`
    - Open a markdown filename on GitHub.
  - `process_md_headers.py`
    - Extract headers from a Markdown file and generate a Vim cfile
  - `publish_notes.py`
    - Publish all notes to a Google dir.
  - `render_images.py`
    - Replace sections of image code with rendered images, commenting out the
      original code, if needed.
  - `replace_latex.py`, `replace_latex.sh`
    - Scripts for one-off processing of latex files
  - `run_latex.sh`
    - Dockerized latex flow
    - TODO(gp): Convert to Python
  - `run_pandoc.py`
    - Run pandoc on stdin/file to stdout/file.
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

- Use `llm_transform.py -t list`
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
  > notes_to_pdf.py --input notes/MSML610/Lesson1-Intro.txt --output tmp.pdf -t slides
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
  > docker run --rm -it --workdir /Users/saggese/src/cmamp1 --mount type=bind,source=/Users/saggese/src/cmamp1,target=/Users/saggese/src/cmamp1 lint_latex:latest sh -c ''\''./tmp.lint_latex.sh'\''' papers/DataFlow_stream_computing_framework/DataFlow_stream_computing_framework.tex
  papers/DataFlow_stream_computing_framework/DataFlow_stream_computing_framework.tex 320ms (unchanged)
  ```
