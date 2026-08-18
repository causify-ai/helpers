This file contains a mapping between "file type" and files containing rule /
conventions and templates

Based on the files that you need to operate, read and follow the corresponding
rules

- A rules file (`.claude/skills/<TOPIC>.rules.md`) holds why/when: principles
  and decision criteria
- A template file (`.claude/templates/<TOPIC>.template.<EXT>`) holds what to
  copy: a skeleton or worked example
- See `.claude/skills/skill.rules.md` `## Rules vs Templates` for the full
  convention

# Text

## Structured Text
- For writing structured bullet-point text you MUST follow instructions in
  `.claude/skills/text.rules.md`

## Markdown
- For writing markdown text you MUST follow instructions in
  `.claude/skills/markdown.rules.md`

## Visuals
- For diagrams, images, and other illustrations you MUST follow instructions
  in `.claude/skills/visuals.rules.md`, using:
  - The rules `.claude/skills/graphviz.rules.md` and the template
    `.claude/templates/graphviz.template.md` for Graphviz diagrams, or the
    template `.claude/templates/graphviz_architecture.template.md` for the
    hierarchy-aware architecture style
  - The template `.claude/templates/image.template.md` for image
    descriptions
  - The template `.claude/templates/tikz.template.md` for TikZ diagrams
- For a publication-quality SVG figure you MUST follow
  `.claude/skills/svg.rules.md`
- For a publication-quality TikZ figure you MUST follow
  `.claude/skills/tikz.rules.md`

# Development Tools

## Agent Skills
- For skills you MUST follow instructions in `.claude/skills/skill.rules.md`

## AI Instructions
- For writing an AI task instruction file you MUST follow the patterns in
  the template `.claude/templates/ai.instruction_template.md`

## Auto Task
- For writing or reviewing an `auto_task` plan (GitHub issue problem /
  solution) you MUST follow `.claude/skills/auto_task.rules.md`

## GitHub PR Plan
- For splitting a branch into a sequence of PRs you MUST follow the template
  `.claude/templates/github_PR_plan.template.md`

## Cfile
- For generating a vim quickfix `cfile` you MUST follow
  `.claude/skills/cfile.rules.md`

# Developing Software

## Architecture
- For designing software architecture and organizing code you MUST follow:
  - The rules `.claude/skills/architecture.rules.md`
  - For a standalone architecture doc: the template
    `.claude/templates/architecture_doc.template.md`

## Coding
- For writing Python file (files with a `.py` extension) you MUST follow:
  - The rules `.claude/skills/coding.rules.md`
  - The template `.claude/templates/coding.template.py`
  - For a package `__init__.py`: the template `.claude/templates/__init__.py`

## Bash
- For writing shell script (files with a `.sh` extension) you MUST follow:
  - The rules `.claude/skills/bash.rules.md`

## Testing
- For a file storing unit tests (files under a `test/` dir named
  `test_<file>.py`) you MUST follow:
  - The rules `.claude/skills/coding.rules.md`
  - The rules `.claude/skills/testing.rules.md`
  - The template `.claude/templates/testing.template.py`

## Pytest
- For diagnosing and triaging failing pytest runs you MUST follow:
  - The rules `.claude/skills/pytest.rules.md`

## Readme
- For a README of a directory with executables you MUST follow instructions
  in `.claude/skills/readme.rules.md` and the template
  `.claude/templates/readme.template.md`
- For a README of a single executable / script you MUST follow instructions
  in `.claude/skills/readme_file.rules.md`

# Tutorials

## Notebooks
- For Jupyter notebook (files with a `.ipynb` extension) you MUST follow:
  - The rules `.claude/skills/notebook.rules.md`
  - The template `.claude/templates/notebook.template.ipynb`
  - The paired script template `.claude/templates/notebook.template.py`
  - The utility-module template
    `.claude/templates/notebook_utils_template.py`
  - For a notebook presenting a package API: the templates
    `.claude/templates/API_notebook.template.ipynb` and
    `.claude/templates/API_notebook.template.py`

## Tool Tutorials
- For a "Learn X in 60 Minutes" tutorial you MUST follow
  `.claude/skills/tool_X_in_60_mins.rules.md`
- For a "Learn X in 30 Minutes" tutorial you MUST follow
  `.claude/skills/tool_X_in_30_mins.rules.md`

## Package Landscape
- For a package/library functionality-cluster comparison doc you MUST
  follow the template `.claude/templates/package.template.md`

# Books and Lectures

## Lectures
- For a Typst-based lecture notes doc you MUST follow the template
  `.claude/templates/lectures.template.md`

## Book
- For a book table of contents / map you MUST follow the template
  `.claude/templates/book_map.template.md`

## Slides
- For creating slides (i.e., files with a `txt` extension) you MUST follow
  instructions in `.claude/skills/slides.rules.md` and the template
  `.claude/templates/slides.template.md`

## Latex
- For writing LaTeX formulas and mathematical notation you MUST follow
  instructions in `.claude/skills/latex.rules.md`

## Typst
- For writing Typst chapters (files with a `.typ` extension) you MUST follow
  the template `.claude/templates/typst.template.typ`

## Blog
- For writing blog posts you MUST follow instructions in
  `.claude/skills/blog.rules.md`

## References
- For formatting references to books or papers you MUST follow instructions
  in `.claude/skills/references.rules.md`
