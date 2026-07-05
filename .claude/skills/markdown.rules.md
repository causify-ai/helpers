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
- Backtick each element of a tuple/triple individually, not the whole tuple
  - **Bad**: `` `(subject, relation, object)` ``
  - **Good**: `` (`subject`, `relation`, `object`) ``

## Do Not Combine Bold with Verbatim

- Do not wrap bold around backtick-quoted text (verbatim + bold is redundant)
  - **Bad**: `**`lib_llm_cli.py`**`
  - **Good**: `` `lib_llm_cli.py` ``
- Backtick formatting already makes text visually distinct and bold adds no signal

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

- Keep the split clean: reserve **bold** for labels/key terms, use _italic_ for
  emphasized or contrasted terms inside a bullet
  - **Bad**: `**Composition** vs. **Comparison**` (both bolded mid-bullet)
  - **Good**: `_Composition_ vs. _Comparison_`

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

## Avoid Unstable Details

- Do not add details that change frequently and cannot be maintained
  - **Bad**: `` `lib_llm_cli.py` (637 lines) ``
  - **Good**: `` `lib_llm_cli.py` ``
- Line counts, version numbers, dates, and similar metrics drift and mislead when stale
- Prefer stable identifiers (file names, API names) over volatile metadata
- Avoid version-pinned product/model names in claims that go stale; prefer a
  generic phrase with a date qualifier
  - **Bad**: `**GPT-4-Turbo** and **Gemini-1.5-Pro** fail on this task`
  - **Good**: `frontier models (as of 2024) fail on this task`

# Code Blocks and Commands

## Leave Fenced Code Blocks Alone
- If there is a fenced code block, do not remove it

## Command Formatting

- Make sure all Linux/macOS shell commands are prepended with the appropriate prefix:
  - `>` when they are bash commands
  - `docker>` when they are commands run inside Docker
  - `claude>` when they are commands run inside Claude
  - `prompt>` when they are text typed into an LLM prompt
  - `LLM>` when they are text emitted by an LLM
- Render a literal prompt or model output as a fenced code block with the
  prefix, not as an inline italic quote
  - **Bad**: `_"Let's think step by step"_`
  - **Good**:
    ```text
    prompt> Let's think step by step
    ```
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

- For long commands with multiple options, format with one option per line using backslash continuation:
  - **Bad** (single long line is hard to read):
    ```bash
    > notes_to_pdf.py --input data605/lectures_md/final_enhanced_markdown_lecture_2.txt --output tmp.pdf --type slides --skip_action cleanup_after --debug_on_error --toc_type navigation --filter_by_slides 1:4
    ```
  - **Good** (one option per line is clearer):
    ```bash
    > notes_to_pdf.py \
      --input data605/lectures_md/final_enhanced_markdown_lecture_2.txt \
      --output tmp.pdf \
      --type slides \
      --skip_action cleanup_after \
      --debug_on_error \
      --toc_type navigation \
      --filter_by_slides 1:4
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
- For software architecture diagrams, use Mermaid with C4 style
  - C4 model: Context, Container, Component, Code
  - Mermaid supports C4 natively via `c4context`, `c4container`, `c4component` diagrams
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
- Reserve math mode for real equations; do not wrap plain multipliers or ratios
  - **Bad**: `$10$-$30\times$ cheaper`
  - **Good**: `10-30x cheaper`
