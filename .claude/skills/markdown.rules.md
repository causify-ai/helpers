This document contains all the rules that must be followed when writing markdown
text

# Organization and Structure

## Headers and Organization
- Use headers and paragraphs:
  ```
  # Header 1

  ## Header 2
  ```

- Make sure that the headers start from level 1
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

- Use `##` for main sections with clear, descriptive titles
- Use `###` for subsections
- Capitalize major words in headings
- If a Markdown header doesn't have a title, complete it using the content of
  the following text
- Avoid level 4 headers (####), convert them into lists or bold text instead

## Body Structure
- Write in a direct, conversational tone
- Keep paragraphs short (2-4 sentences typically)
- Separate paragraphs with a single blank line
- Use frequent examples to illustrate points
- Maintain consistent spacing between sections
- Use blank lines to separate different content blocks

# Lists and Items

## Bullet Lists
- Write text using bullet lists following the directions in
  `.claude/skills/text.rules.md`
- Use `-` (dash) consistently for unordered lists
- Indent sub-items with two spaces
- Use ordered lists (`1.`, `2.`, etc.) when sequence matters
- Lists often follow a brief introductory sentence ending with a colon

- Example:
  ```markdown
  - The main advantages are:
    - **First advantage**: Description here
    - **Second advantage**: Description here
      - Sub-point with details
      - Another sub-point
  ```

## List of Items
- In lists of items:
  - Bold the first item whenever possible, e.g.,
    ```markdown
    - The main advantages are:
      - **First advantage**: Description here
      - **Second advantage**: Description here
        - Sub-point with details
        - Another sub-point
    ```
  - Use `:` to separate file and description instead of `-`
    - **Bad**:
      ```
      - notes_to_pdf.py - Main tool for converting notes to PDF/HTML/slides
      - render_images.py - Auto-renders diagrams
      ```
    - **Good**:
      ```
      - `notes_to_pdf.py`: Main tool for converting notes to PDF/HTML/slides
      - `render_images.py`: Auto-renders diagrams
      ```

# Text Formatting

## Use Verbatim
- Use verbatim for libraries, executables, scripts
  - E.g., `notes_to_pdf.py`, `python`, `pandas`

## Emphasis Styles
- **Bold text** (`**text**`):
  - Use for key terms and important concepts
  - Use at the start of list items for headers/labels
  - Use for strong emphasis
  - Use bold sparingly and to highlight parts of text, not entire phrases

- _Italic text_ (`_text_`):
  - Use for questions and hypothetical scenarios
  - Use for terms being defined or emphasized
  - Use for "what if" scenarios

- **Inline code** (`` `code` ``):
  - Use for technical terms, variable names, or code snippets

## Word Choice
- Do not abuse bold in explanations of commands
  - **Bad**
    ```
    - **Extract with higher DPI** for better image quality:
    ```
  - **Good**
    ```
    - Extract with higher DPI for better image quality:
    ```
- Do not use &
  - **Bad**:
    ```
    Extraction & Conversion Tools
    ```
  - **Good**:
    ```
    Extraction and Conversion Tools
    ```

# Code Blocks and Commands

## Command Formatting

- Make sure all Linux/macOS shell commands are prepended with the appropriate prefix:
  - `>` when they are bash commands
  - `docker>` when they are commands run inside Docker
  - `claude>` when they are commands run inside Claude
- E.g., convert:
  ```bash
  pipenv install requests
  pipenv shell
  ```
  to:
  ```bash
  > pipenv install requests
  > pipenv shell
  ```

## Code Block Syntax

- Make sure all fenced blocks have a syntax description (e.g., python, markdown,
  verbatim)
  - **Bad**:
    ```
    > rig "pattern"
    ```
  - **Good**:
    ```bash
    > rig "pattern"
    ```

## Fenced Code Blocks

- Every fenced code block must have a valid programming language (e.g., `python`,
  `bash`, `latex`, `verbatim`)
  - E.g.:
    ````markdown
    ```python
    ````
  - If it doesn't have a valid tag, infer it from the content. If unsure, leave it empty
- The fenced code block should be aligned with the text and the bullet points:
  ````markdown
  - Do this and that:
    ```bash
    > do_this_and_that
    ```
  ````

# Visual Elements

## Tables

- Use standard Markdown tables for comparisons:
  ```markdown
  | Column 1 | Column 2 | Column 3 |
  | :------- | :------- | :------- |
  | Data 1   | Data 2   | Data 3   |
  ```
- Use left-aligned columns (`:-------`)
- Keep column headers bold where appropriate
- If the file describes commands, add a table at the beginning with a summary of all commands

## Diagrams

- Use diagrams instead of long text descriptions when possible
- Summarize systems or relationships using:
  - Graphviz
  - Mermaid
  - TikZ-style charts
- Add annotation arrows and layered explanations

## Links

- Use standard Markdown format: `[text](URL)`
- Link to external references and sources
- Use descriptive link text

## Mathematical Notation

- Inline math: `$E = mc^2$`
- Block math:
  ```markdown
  $$
  E = mc^2
  $$
  ```
