## 

- We use the following tools for documentation and blogging

- [**MkDocs**](https://www.mkdocs.org/): Static site generator for project
  documentation
- [**Jupyter Book**](https://jupyterbook.org/): Useful for books with code and
  notebooks
- [**Pandoc**](https://pandoc.org/): Combine Markdown into PDF, ePub, or other
  formats

- [https://executablebooks.org/en/latest/gallery](https://executablebooks.org/en/latest/gallery)  
- [https://bvanderlei.github.io/jupyter-guide-to-linear-algebra/intro.html](https://bvanderlei.github.io/jupyter-guide-to-linear-algebra/intro.html)  
- https://github.com/executablebooks/cookiecutter-jupyter-book

- Material mkdocs

- Other tools we have evaluated
  - [**mdBook**](https://rust-lang.github.io/mdBook/): Inspired by GitBook,
    ideal for technical books.
  - [Rust book example](https://github.com/rust-lang/mdBook)  

## Markdown Dialects

- **Markdown**: Lightweight markup language for plain-text formatting
  - **Dialects**: Variants that extend or tweak core Markdown features

### CommonMark
- Standardized version of original Markdown
- Clear spec to reduce inconsistencies
- Many dialects are based on CommonMark

### GitHub Flavored Markdown (GFM)
- Based on CommonMark with extensions for GitHub.
  - Syntax highlighting for fenced code blocks.
  - Tables:
  - Task Lists:
    ```
    - [ ] Task
    - [x] Done
    ```
  - Strikethrough: `~~text~~`
  - Autolinks for URLs.
- Widely used in README.md, issues, PRs.

### Pandoc Markdown
- Very flexible, used by Pandoc converter
- Supports multiple extensions:
  - Footnotes:
  - Citations
  - Tables, definition lists, math.
  - Customizable with `+extension` flags.
- Used for converting Markdown to LaTeX, PDF, HTML, DOCX.

### MyST Markdown
- MyST = "MarkedlY Structured Text"
- Extensions:
  - Directive blocks:
    ```markdown
    ```{note}
    This is a note directive.
    ```
    ```
  - Roles:
    ```markdown
    {ref}`section-name`
    ```
  - Equations: `$E=mc^2$` or `$$...$$`
  - Citations & bibliography integration
- Built for scientific/technical docs (Jupyter, Sphinx)
- Bridges Markdown with reStructuredText features

- MkDocs doesn't natively support the full MyST spec, but you can add it with
  the mkdocs-myst-plugin
  - TODO

## Preprocessor for Markdown Dialects

- To render Markdown we want to perform some transformations

## Lint for Markdown dialects

## Render to PDF

- How to generate a PDF from jupyterbook and from mkdocs

- Render mkdocs as PDFs
  - Plug-in [mkdocs-with-pdf](https://github.com/orzih/mkdocs-with-pdf)

## How to do a blog with mkdocs

