

<!-- toc -->

- [Files](#files)
- [Latex Toolchain](#latex-toolchain)
  * [Running and linting Latex files](#running-and-linting-latex-files)
  * [TODOs](#todos)

<!-- tocstop -->

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
  - `preprocess_notes.py`
    - Convert a text file storing notes into markdown suitable for `notes_to_pdf.py`
    - The transformations are
      - Convert the text in pandoc / latex format
      - Handle banners around chapters
      - Handle comments
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
  - `notes_to_pdf.py`
    - Convert a `txt` file storing nodes into a PDF / HTML / beamer slides using
      `pandoc`
  - `render_md.py`
    - Render images for several sections in markdown / latex / notes files
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

# Latex Toolchain

## Running and linting Latex files

- We organize each project is in a directory (e.g., under `//papers`)
- Under each dir there are several scripts that assign some variables and then
  call the main scripts to perform the actual work by calling `run_notes_to_pdf.py`
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
