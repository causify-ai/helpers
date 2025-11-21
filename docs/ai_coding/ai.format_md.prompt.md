# Conventions for Writing Markdown Files

## Goals and Philosophy

1) Make the text easy to consume for both humans and AI

2) Focus on:
  - Clarity
  - Brevity
  - Visual structure

3) Think of notes as a hybrid between a textbook and a student’s notebook

- This document is written using the rules described in this document itself

## Formatting Guidelines

#### Every document has a summary header
- Every document should have a summary paragraph with a header `# Summary`
  with a short paragraph containing what's the content of the document 

#### Headers and Paragraphs
- Use headers and paragraphs
  ```
  # Header 1

  ## Header 2
  ```

#### Use Only Text
- Avoid emojis and icons
- Avoid any decorative formatting
  - Do not use line separator like `---`
- Use only basic text
  - **Good**: A -> B
  - **Bad**: A → B
  - **Good**: "hello"
  - **Bad**: “hello”

#### Use Bullets
- Use bullet points inside a paragraph

- Each bullet should express one complete atomic idea
  - Keep bullets concise but meaningful (1–3 lines)

- Use bullets to show:
  - Definitions
  - Purpose
  - Components
  - Pros and cons
  - Examples

- Use `=` for definitions
  - Example:
    ```
    - Latency = the delay before a transfer of data begins after an instruction
    ```

- Group bullets under clear paragraph headings

- Do not end a bullet point with a period `.`

#### Use Nested Bullets
- Use nested bullets to show:
  - Dependencies and relationships
    - E.g., cause -> effect
  - Hierarchy of concepts, e.g.,
    ```
    - Technology
      - Hardware
        - Computers
        - Mobile Devices
      - Software
        - Operating Systems
        - Applications
    ```
  - Components and lists, e.g.,
    ```
    - Allowed formats:
      - Graphviz
      - Mermaid
      - TikZ-style charts
    ```
  - Elaboration, not to extend main bullets, e.g., for
    - Definitions
    - Examples
    - Implications

#### List of Items

- In lists of items
  - Bold the item whenever possible
  - Use verbatim when the item is a script
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

#### Use verbatim for programs
- For libraries, executables, scripts use verbatim
  - E.g., `notes_to_pdf.py`, `python`, `pandas`

#### Use and do not use &
- **Bad**: Extraction & Conversion Tools
- **Good**: Extraction and Conversion Tools

## Writing Style

#### Writing Style
- Use explicit references instead of unclear ones
  - **Good**: "TCP protocol"
  - **Bad**: "it"

- Maintain consistent labels for recurring ideas

- Avoid redundancy in concepts

- Prefer plain language over academic jargon

#### Avoid long prose
- Prefer structured notes over narrative prose

- Use a first-person, self-directed voice, e.g.,
  - **Good**: "Key thing to remember: entropy increases"

#### Use direct statements
- Convert abstract principles into short, direct statements, e.g.,
  - **Good**: "Everyone takes responsibility: no blaming others if work isn't
    finished."
  - **Bad**: "Everyone takes responsibility, owns their projects, and blames no one
    if something doesn't get finished."

#### Try to use lists 

- **Good**
  ```
  - This document covers how to publish:
    - documents
    - books
    - blogs
    across different repos, e.g.,
    - `//helpers`
    - `//csfy`
    - `//tutorials`
    - `//umd_classes`
  ```
- **Bad**
  ```
  This document covers how to publish documents, books, and blogs across
  different repos (e.g., `//helpers`, `//csfy`, `//tutorials`, and
  `//umd_classes`)
  ```

#### Use Diagrams Over Text When Possible
- Summarize systems or relationships using:
  - Graphviz
  - Mermaid
  - Tikz-style charts
- Add annotation arrows and layered explanations
