---
description: Rules to write bullet lists in markdown or text files
---

## Use Only Text

- Avoid emojis and icons
- Avoid any decorative formatting
  - Do not use line separator like `---`
- Use only basic text
  - **Bad**: A → B
  - **Good**: A -> B

## Text is Formatted with Bullets

- Every text should start with a bullet point

- **Bad**
  ```
  Hello, my name is ...
  ```
- **Good**
  ```
  - Hello, my name is ...
  ```

## Use Bullets

- Use bullet points inside a paragraph

- Each bullet should express one complete atomic idea
  - Keep bullets concise but meaningful (1–3 lines)

- Use bullets to show:
  - Definitions
  - Purpose
  - Components
  - Pros and cons
  - Examples

- Group bullets under clear paragraph headings

- Do not end a bullet point with a period `.`

## Use Nested Bullets

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

## Try to Use Lists

- **Bad**
  ```
  This document covers how to publish documents, books, and blogs across
  different repos (e.g., `//helpers`, `//csfy`, `//tutorials`, and
  `//umd_classes`)
  ```
- **Good**
  ```
  - This document covers how to publish:
    - Documents
    - Books
    - Blogs
    across different repos, e.g.,
    - `//helpers`
    - `//csfy`
    - `//tutorials`
    - `//umd_classes`
  ```

- **Bad**
  ```
  - They appear everywhere: husbands with controlling wives, overly helpful
    friends with chaotic lives, seemingly stable men who suddenly fall apart
  ```
- **Good**
  ```
  - They appear everywhere:
    - Husbands with controlling wives
    - Overly helpful
    - Friends with chaotic lives
    - Seemingly stable men who suddenly fall apart
  ```

## Keep Number Lists in Order

- If there are numbered lists, make sure they are in order starting from 1
  - **Bad**
    ```markdown
    ## 2. First
    ## 2. Second
    ## 3. Third
    ```
  - **Good**
    ```markdown
    ## 1. First
    ## 2. Second
    ## 3. Third
    ```

