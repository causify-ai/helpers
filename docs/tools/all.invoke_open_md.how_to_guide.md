# The Open Markdown Workflow

<!-- toc -->

- [Open Markdown Workflow](#open-markdown-workflow)
  * [Render a Markdown File](#render-a-markdown-file)
  * [Open a File on GitHub](#open-a-file-on-github)
  * [Render to PDF](#render-to-pdf)
  * [Live Preview](#live-preview)

<!-- tocstop -->

# Open Markdown Workflow

## Render a Markdown File

- Convert a markdown file to HTML with pandoc (the default mode) and open it
  in the browser:

  ```bash
  > i open_md --input xyz.md
  ```

- The rendering tools can run locally (`global` backend, the default) or
  inside Docker:

  ```bash
  > i open_md --input xyz.md --backend dockerized
  ```

- A custom HTML snippet (e.g., a `<style>` block) can replace the bundled
  GitHub-like style in pandoc mode:

  ```bash
  > i open_md --input xyz.md --css my_style.html
  ```

## Open a File on GitHub

- Open the file as rendered by GitHub in the browser:

  ```bash
  > i open_md --input xyz.md --mode github
  ```

## Render to PDF

- Convert the file to PDF through pandoc and a LaTeX engine (e.g., xelatex
  on the `global` backend):

  ```bash
  > i open_md --input xyz.md --mode pdf
  ```

## Live Preview

- Start a grip daemon for live preview:

  ```bash
  > i open_md --input xyz.md --mode grip_daemon
  ```

- Watch the file and re-render it on every change (pandoc, pdf, grip
  modes):

  ```bash
  > i open_md --input xyz.md --daemon
  ```

- The rendered output is opened automatically unless `--skip-open` is
  passed, which only generates the output file.

- The task is a thin wrapper around
  `dev_scripts_helpers/documentation/open_md.py`, which documents the full
  behavior of each mode and backend.
