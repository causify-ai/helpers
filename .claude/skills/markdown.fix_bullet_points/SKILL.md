---
name: markdown.fix_bullet_points
description: Reorganize a markdown file to use bullet points and ensure all fenced code blocks have syntax labels
---

- Given a markdown file passed from the user

- Make sure the text is organized in bullet points

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
