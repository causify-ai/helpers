This document contains all the rules that must be followed when writing markdown
text.

## Formatting Guidelines

### Every Document Has a Summary Header

- Every document should have a summary paragraph with a header `# Summary` with
  a short paragraph containing what's the content of the document

### Headers and Paragraphs

- Use headers and paragraphs
  ```
  # Header 1

  ## Header 2
  ```

### List of Items

- In lists of items
  - Bold the item whenever possible
  - Use verbatim when the item is a script, a command (e.g., `python`, `bash`,
    `latex`)
  - Use `:` to separate file and description instead of `-`
  - **Bad**:
    ```
    - notes_to_pdf.py - Main tool for converting notes to PDF/HTML/slides
    - render_images.py - Auto-renders diagrams (PlantUML, Mermaid, TikZ, Graphviz)
    ```
  - **Good**:
    ```
    - `notes_to_pdf.py`: Main tool for converting notes to PDF/HTML/slides
    - `render_images.py`: Auto-renders diagrams (PlantUML, Mermaid, TikZ, Graphviz)
    ```

### Use Verbatim

- Use verbatim for libraries, executables, scripts
  - E.g., `notes_to_pdf.py`, `python`, `pandas`

### Use and Do Not Use &

- **Bad**: Extraction & Conversion Tools
- **Good**: Extraction and Conversion Tools

## Use Bullet Lists

- Write text using bullet lists following the directions in
  `.claude/skills/text.rules.bullet_points.md`

### Use Fenced Code Blocks

- Every fenced code blocks must have a valid programming language
  (e.g., `python`, `bash`, `latex`, `verbatim`)
  - E.g.,
    ````
    ```python
    ````
  - If it doesn't have a valid tag, then infer it from the content of the fenced
    block. If you are not sure, do not modify it but leave it empty

- The fenced code block should be aligned with the text and the bullet points
  ````
  - Do this and that:
    ```bash
    > do_this_and_that
    ```
  ````

### Use `>` For Commands
- Prepend a `>` before each bash command
- E.g., convert
  ```bash
  pipenv install requests
  pipenv shell
  ```
  to
  ```bash
  > pipenv install requests
  > pipenv shell
  ```

### Use Diagrams Over Text When Possible

- Summarize systems or relationships using:
  - Graphviz
  - Mermaid
  - Tikz-style charts
- Add annotation arrows and layered explanations

### Try to avoid level 4 headers

- Avoid level 4 headers, especially when they are just short, and convert them
  into a list
  - **Bad**
    ```markdown
    #### 9. Generated Files (Always Exclude)

    ```markdown
    *.log
    *.tmp
    *.cache
    build/
    dist/
    ```

    - **Why**: Generated at runtime, not needed in the image
    ```
  - **Good**
    ```markdown
    - Generated Files (Always Exclude)
      ```markdown
      *.log
      *.tmp
      *.cache
      build/
      dist/
      ```
      - **Why**: Generated at runtime, not needed in the image
    ```

### Limit Use of Bold

- Use bold sparingly and to highlight parts of text and not entire phrases
  - **Bad**
    ````markdown
    - **Delete unused reference files**
      ```bash
      > Dockerfile.ubuntu
      ```

    - **Create your working Dockerfile**
      ```bash
      > cp Dockerfile.ubuntu Dockerfile
      ```

    - **Add your dependencies**
      ```bash
      > echo "numpy\npandas\nscikit-learn" > requirements.in
      > pip-compile requirements.in > requirements.txt
      ```
    ````
  - **Good**
    ```markdown
    **How to choose:**

    - **Use Standard** if you need system-level tools (git, curl, graphviz, etc.)
    - **Use Python Slim** to minimize image size and build time
    - **Use uv** if you want faster, more reliable dependency management
    ```

### Complete Missing Headers

- If a Markdown header doesn't have a title then complete it using the content of
  the following text

### Make sure that the Headers Start from 1

- The markdown headers should start from 1
  - **Bad**
    ```markdown
    ## Level 1

    - Hello

    ### Level 2

    - Good bye
    ```
  - **Good**
    ```markdown
    # Level 1

    - Hello

    ## Level 2

    - Good bye
    ```

## Handle fenced div

- Make sure that all fenced div have a syntax description (e.g., python,
  markdown, verbatim)
  - Bad
    ````markdown
    The simplest ripgrep command searches for a pattern in the current directory:

    ```bash
    > rig "pattern"
    ```
    ````
  - Good
    ````markdown
    - The simplest ripgrep command searches for a pattern in the current
      directory:
      ```bash
      > rig "pattern"
      ```
    ````

## Format commands

- Make sure Linux / MacOS shell commands are prepended with:
  - `>` when they are bash commands
  - `docker>` when they are commands run inside Docker
  - `claude>` when they are commands run inside Claude

## Do not abuse level 4 headers

- Do not use header level 3 (i.e., ###), but use bold when there are too many of
  them with too small of content
- E.g., convert
  ```
  ### What It Does
  ...

  ### Examples
  ...
  ```
  to
  ```
  **What it does**
  ...

  **Examples**
  ...
  ```

## Do not abuse bold

- Do not abuse bold in the explanation of commands
  - Bad
    ```
    - **Extract with higher DPI** for better image quality:
    ```
  - Good
    ```
    - Extract with higher DPI for better image quality:
    ```

## Add table

- If the file contains a description of commands add a table at the beginning
  with a summary of all the commands
  - E.g.,
    ```
    | Script                     | Location                                          | Description                                                                                                             |
    | :------------------------- | :------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------- |
    | `concatenate_pdfs.py`      | `helpers_root/dev_scripts_helpers/documentation/` | Combines multiple PDF files into a single PDF (used for creating full book from chapters)                               |
    | `count_book_pages.py`      | `class_scripts/`                                  | Counts pages in all PDF files in `{DIR}/book/` directory using macOS `mdls` command                                     |
    ```

## Body Structure

- **Section Headings**
  - Use `##` for main sections with clear, descriptive titles
  - Use `###` for subsections
  - Capitalize major words in headings

- **Content Style**
  - Write in a direct, conversational tone
  - Keep paragraphs short (2-4 sentences typically)
  - Separate paragraphs with a single blank line
  - Use frequent examples to illustrate points

## Lists

- Use `-` (dash) consistently for unordered lists
- Indent sub-items with two spaces
- Use ordered lists (`1.`, `2.`, etc.) when sequence matters
- Lists often follow a brief introductory sentence ending with a colon

- Example:

  ```markdown
  The main advantages are:
  - **First advantage**: Description here
  - **Second advantage**: Description here
    - Sub-point with details
    - Another sub-point
  ```

## Emphasis and Formatting

- **Bold text** (`**text**`):
  - Use for key terms and important concepts
  - Use at the start of list items for headers/labels
  - Use for strong emphasis

- _Italic text_ (`_text_`):
  - Use for questions and hypothetical scenarios
  - Use for terms being defined or emphasized
  - Use for "what if" scenarios

- **Inline code** (`` `code` ``):
  - Use for technical terms, variable names, or code snippets

## Tables

- Use standard Markdown tables for comparisons:

  ```markdown
  | Column 1 | Column 2 | Column 3 |
  | :------- | :------- | :------- |
  | Data 1   | Data 2   | Data 3   |
  ```

- Use left-aligned columns (`:-------`)
- Keep column headers bold where appropriate

## Links

- Use standard Markdown format: `[text](URL)`
- Link to external references and sources
- Use descriptive link text

## Mathematical Notation

When mathematical formulas are needed:

- Inline math: `$E = mc^2$`
- Block math:
  ```markdown
  $$
  E = mc^2
  $$
  ```
