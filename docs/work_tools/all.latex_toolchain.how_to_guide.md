

<!-- toc -->

- [Latex Toolchain](#latex-toolchain)
  * [Running and linting Latex files](#running-and-linting-latex-files)
  * [Embedding Mermaid and PlanUML figures](#embedding-mermaid-and-planuml-figures)
  * [Finding citations](#finding-citations)
  * [TODOs](#todos)

<!-- tocstop -->

#
```
> ls -1 //helpers_root/dev_scripts_helpers/documentation
- convert_docx_to_markdown.py
  - Convert Docx file to Markdown using Dockerized pandoc and save the figs

- convert_docx_to_markdown.sh
  - Wrapper to simplify calling `convert_docx_to_markdown.py`

- convert_txt_to_pandoc.py
  - Convert a txt file into markdown suitable for pandoc.py, e.g.,
    - convert the text in pandoc / latex format
    - handle banners around chapters
    - handle comments

- generate_latex_sty.py
  - One-off script to generate the latex file

- generate_script_catalog.py
  - Generate a markdown file with the docstring for any script in the repo
  - TODO(gp): Unclear what to do with this

- latex_abbrevs.sty
  - Latex macros

- latexdockercmd.sh
  - Wrapper for Latex docker container
  - Probably obsolete

- lint_latex.sh
  - Dockerized linter for Latex using prettier
  - This is the new flow.

- lint_latex2.sh
  - Dockerized linter for Latex using `latexindent.pl`
  - This is the old flow

- open_md_in_browser.sh
  - Render a markdown using `pandoc` (installed locally) and then open it in a
    browser

- open_md_on_github.sh
  - Open a filename (e.g,. a markdown) on GitHub

- pandoc.latex
  - `latex` template used by `pandoc.py`

- pandoc.py
  - Convert a `txt` file with nodes into a PDF / HTML using `pandoc`

- render_md.py
  - Add rendered images to all plantUML sections in the markdown files.

- replace_latex.py
- replace_latex.sh
  - Scripts for one-off processing of latex files

- run_latex.sh
  - Dockerized latex flow

- run_pandoc.py
  - Read value from stdin/file
  - Transform it using `pandoc` according to different transforms
    (e.g., `convert_md_to_latex`)
  - Write the result to stdout/file.

- `test/test_render_md.py`

- test_lint_latex.sh
  -  Run latex linter and check if the file was modified

- transform_txt.py
  - Perform one of several transformations on a txt file, e.g.,
    1) `toc`: create table of context from the current file, with 1 level
    2) `format`: format the current file with 3 levels
    3) `increase`: increase level

# Latex Toolchain

## Running and linting Latex files

We organize each project is in a directory (e.g., under `//papers`)

Under each dir there are two scripts:

- `run_latex.sh`
- `lint_latex.sh` that assign some variables and then call the main scripts to
  perform the actual work:
- `dev_scripts/latex/run_latex.sh`
- `dev_scripts/latex/lint_latex.sh`

Both main scripts are "dockerized" scripts, which build a Docker container with
dependencies and then run use it to process the data

To run the Latex flow we assume (as usual) that user runs from the top of the
tree

To create the PDF from the Latex files:
```
> papers/DataFlow_stream_computing_framework/run_latex.sh
...
```

To lint the Latex file:
```
> papers/DataFlow_stream_computing_framework/lint_latex.sh
...
+ docker run --rm -it --workdir /Users/saggese/src/cmamp1 --mount type=bind,source=/Users/saggese/src/cmamp1,target=/Users/saggese/src/cmamp1 lint_latex:latest sh -c ''\''./tmp.lint_latex.sh'\''' papers/DataFlow_stream_computing_framework/DataFlow_stream_computing_framework.tex
papers/DataFlow_stream_computing_framework/DataFlow_stream_computing_framework.tex 320ms (unchanged)
```

## Embedding Mermaid and PlanUML figures

Update ./dev_scripts/documentation/render_md.py

- Rename to render_figures.py
- It works on both Markdown and Latex files
- Find a mermaid/plantuml block and then add an image

%`mermaid %flowchart %  Vendor Data --> VendorDataReader --> DataReader --> User %`

## Finding citations

The simplest way is to use Google Scholar and then use the "Cite" option to get
a Bibtex entry

Some interesting links are
https://tex.stackexchange.com/questions/143/what-are-good-sites-to-find-citations-in-bibtex-format

## TODOs

- Add a script to decorate the file with separators as part of the linting
  ```
  % ################################################################################
  \section{Adapters}
  % ================================================================================
  \subsection{Adapters}
  % --------------------------------------------------------------------------------
  \subsubsection{Adapters}
  ```

- Convert the Latex toolchain into Python code

- Add a script to run a ChatGPT prompt on a certain chunk of text

- Easily create a vimfile to navigate the TOC
