## 

- We use the following tools for documentation and blogging

### MkDocs
- [**MkDocs**](https://www.mkdocs.org/): Static site generator for project
  documentation

### Jupyter Book
- [**Jupyter Book**](https://jupyterbook.org/): Useful for books with code and
  notebooks
- It's based on CommonMark (a Markdown standard) but adds syntax for scientific
  and technical publishing
- It's designed to map closely to reStructuredText (reST) features so that
  Markdown can be used in the Sphinx ecosystem

### Pandoc
- [**Pandoc**](https://pandoc.org/): Combine Markdown into PDF, ePub, or other
  formats
  - Aims for maximum portability: you write in Pandoc Markdown and convert to
    HTML, PDF, LaTeX, DOCX, and more
  - Supports multiple dialects: Pandoc Markdown, Markdown Extra, GitHub-Flavored
    Markdown (GFM)

- [https://executablebooks.org/en/latest/gallery](https://executablebooks.org/en/latest/gallery)  
- [https://bvanderlei.github.io/jupyter-guide-to-linear-algebra/intro.html](https://bvanderlei.github.io/jupyter-guide-to-linear-algebra/intro.html)  
- https://github.com/executablebooks/cookiecutter-jupyter-book

### Material for MkDocs
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) is a
  popular theme and extension for MkDocs, which is a static site generator for
  project documentation written in Markdown
	- MkDocs = turns Markdown files into a static documentation website
	- Material for MkDocs = makes that website look beautiful and adds powerful features.

- Inspired by Google's Material Design guidelines, i.e., clean, modern, responsive
- Lots of color palettes, light/dark modes, and logo customization

- Advanced navigation:
  - Auto-generated sidebar and table of contents
  - Breadcrumbs and sticky navigation
  - Tabs, sections, version dropdowns, etc

- Markdown extensions:
  - Syntax highlighting for code blocks
  - Admonitions (!!! note blocks) and callouts
  - Built-in support for math (MathJax), Mermaid diagrams, and more
  - Works great with the MyST plugin, too!

- Search:
  - Instant full-text search across your docs
  - Works offline with lunr.js

- Plugins & Integrations:
  - Works well with MkDocs plugins for blogging, versioning, PDF export, etc
  - Excellent support for custom JS/CSS
  - Good support for GitHub Pages deployment

- Great for docs-as-code:
    Used by open-source projects, scientific documentation, knowledge bases, internal wikis, and more

##  Other tools

### mdBooks
- [**mdBook**](https://rust-lang.github.io/mdBook/): Inspired by GitBook,
  ideal for technical books.
- [Rust book example](https://github.com/rust-lang/mdBook)  

### Sphinx

- **Purpose**
  - Designed for Python documentation
  - Supports general technical docs
- **Input Format**
  - Primarily reStructuredText (`.rst`)
  - Supports Markdown with plugins (`myst-parser`)
- **Features**
  - Rich cross-referencing
  - Automatic API docs (`autodoc`)
  - Extensions for LaTeX, PDF output
  - Theming system (ReadTheDocs theme popular)
- **Output Formats**
  - HTML
  - PDF (via LaTeX)
  - EPUB
- **Complexity**
  - Steeper learning curve
  - More configuration options
- **Ecosystem**
  - Large extension ecosystem
  - Widely used in Python community

| Feature               | Sphinx                | MkDocs                    |
|-----------------------|-----------------------|---------------------------|
| Input Format          | reStructuredText, MD  | Markdown                  |
| Output Formats        | HTML, PDF, EPUB       | HTML                      |
| Extensions            | Large ecosystem       | Smaller, plugins available|
| Learning Curve        | Steeper               | Easier                    |
| Theming               | Custom, RTD theme     | Material theme popular    |
| Best For              | API docs, Python libs | Project websites, wikis   |

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

- It supports many extra features not in standard Markdown: citations, footnotes,
  tables, definition lists, math (via LaTeX), fenced code blocks with attributes,
  etc.


### MyST Markdown
- MyST = "MarkedlY Structured Text"
- Extensions:
  - Directive blocks (like reST) using {% directive %} blocks
    ```markdown
    ```{note}
    This is a note directive.
    ```
    ```
  - Roles (inline extensions) using {role} syntax
    ```markdown
    {ref}`section-name`
    ```
  - Better support for equations, citations, figures, and complex structures.
  - Equations: `$E=mc^2$` or `$$...$$`
  - Citations & bibliography integration
  - YAML metadata and configuration.

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

- Use pandoc

## How to do a blog with mkdocs

