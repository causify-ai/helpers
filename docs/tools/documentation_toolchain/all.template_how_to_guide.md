# Template for How-To-Guide
This is a high‑level ready-to-use template to document scripts and how to use them.
<!-- toc -->

* [Tool/Script Name]
  * [`script name.py`](#script-namepy)
    + [What it does](#what-it-does)
    + [Supported File types and Code Blocks](#supported-file-types-and-code-blocks)
    + [Quickstart Recipes](#quickstart-recipes)
    + [Flag Options](#flag-options)
    + [Examples](#examples)

  * [`replicate above structure for multiple files`]
<!-- tocstop -->


### script name.py

### What it does
- Explain in a few lines the objective of the document/script and what it aims to achieve.
Sample reference:
- This script auto renders figures by
  - Detecting fenced code blocks (PlantUML, Mermaid, TikZ, Graphviz, ...)
  - Rendering them into images calling the appropriate tool
  - Commenting them out the block
  - Inlining a `![](img)` markup

### Supported File types and Code Blocks
List the file extensions or formats your tool/script can handle. Mention how each is processed.

Reference Examples:
- Create a new Markdown file with rendered images:
> render_images.py -i ABC.md -o XYZ.md --action render --run_dockerized

- Render images in place in the original Markdown file:
> render_images.py -i ABC.md --action render --run_dockerized

- Render images in place in the original LaTeX file:
> render_images.py -i ABC.tex --action render --run_dockerized

- Open rendered images from a Markdown file in HTML to preview:
> render_images.py -i ABC.md --action open --run_dockerized

### Quickstart Recipes

Show some example codes for running the scripts. Explain what the input and output will look like.

Write all the example codes within ``` ``` blocks.

Example:
- Render the images in a text file
  ```bash
  > render_images.py -i <file_path> \
      -o lesson9.images.txt --run_dockerized
  ```

### Flag Options
Describe each available flag, its purpose, and demonstrate how to use it in the CLI with examples.

Reference:

  -h, --help            show this help message and exit

  -i IN_FILE_NAME, --in_file_name IN_FILE_NAME
                        Path to the input file

  -o OUT_FILE_NAME, --out_file_name OUT_FILE_NAME
                        Path to the output file
  
  --action {open,render}
                        Actions to execute
  
  --skip_action {open,render}
                        Actions to skip
  
  --all                 Run all the actions ()
  
  --dry_run             Update the file but do not render images
  
  --dockerized_force_rebuild
                        Force to rebuild the Docker container
  
  --dockerized_use_sudo
                        Use sudo inside the container
  
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level

### Examples

- Render to a new file

  ```bash
  > render_images.py -i lesson.md -o lesson.rendered.md --action render --run_dockerized
  ```

- Render in‑place (Markdown or LaTeX)

  ```bash
  > render_images.py -i lesson.md --action render --run_dockerized
  ```

- HTML preview of already‑rendered images

  ```bash
  > render_images.py -i lesson.md --action open --run_dockerized
  ```

- Dry‑run (test parsing / comments only)
  ```bash
  > render_images.py -i lesson.md -o /tmp/out.md --dry_run
  ```

