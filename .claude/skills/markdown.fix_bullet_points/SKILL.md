---
description: Reorganize a markdown file to use bullet points and ensure all fenced code blocks have syntax labels
---

- Given a markdown file passed from the user

# Organize text in bullet points
- Make sure all the text is organized in bullet points
  ```
  **What it does**:
  - Extracts each page of a PDF file as a separate PNG image
  - Numbers output files sequentially (slides001.png, slides002.png, etc.)
  - Supports customizable DPI for image quality control
  - Creates output directory automatically with optional from-scratch mode
  ```

# Handle fenced div
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

# Format commands
- Make sure Linux / MacOS shell commands are prepended with:
  - `>` when they are bash commands
  - `docker>` when they are commands run inside Docker
  - `claude>` when they are commands run inside Claude

# Do not abuse level 3 headers
- Do not use header level 3, but use bold when there are too many of them with
  too small of content
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

# Do not abuse bold
- Do not abuse bold in the explanation of commands
  - Bad
    ```
    - **Extract with higher DPI** for better image quality:
    ```
  - Good
    ```
    - Extract with higher DPI for better image quality:
    ```

# Add table

- If the file contains a description of commands add a table at the beginning
  with a summary of all the commands
  - E.g.,
    ```
    | Script                     | Location                                          | Description                                                                                                             |
    | :------------------------- | :------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------- |
    | `concatenate_pdfs.py`      | `helpers_root/dev_scripts_helpers/documentation/` | Combines multiple PDF files into a single PDF (used for creating full book from chapters)                               |
    | `count_book_pages.py`      | `class_scripts/`                                  | Counts pages in all PDF files in `{DIR}/book/` directory using macOS `mdls` command                                     |
  ```

# Lint
- At the end of the process, run `lint_txt.py -i <FILE>` to reformat the text
