---
description: Reorganize a markdown file to use bullet points and ensure all fenced code blocks have syntax labels
---

- Given a markdown file passed from the user

# Step 1
- Make sure the text is organized in bullet points

# Step 2
- Make sure that all fenced div have a syntax description (e.g., python,
  markdown, verbatim)
  - Bad
    ````markdown
    The simplest ripgrep command searches for a pattern in the current directory:
  
    ```bash
    > rg "pattern"
    ```
    ````
  - Good
    ````markdown
    - The simplest ripgrep command searches for a pattern in the current
      directory:
      ```bash
      > rg "pattern"
      ```
    ````

# Step 3
- Make sure Linux / MacOS shell commands are prepended with:
  - `>` when they are bash commands
  - `docker>` when they are commands run inside Docker
  - `claude>` when they are commands run inside Claude

# Step 4
- Run `lint_txt.py -i <FILE>` to reformat the text
