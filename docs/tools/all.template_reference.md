# Reference Guide: <script.py>


Template to document scripts and detail technical aspects of the file/script.

<!-- toc -->

  * [What it does](#what-it-does)
    + [Sample reference:](#sample-reference)
  * [Input and Output Types](#input-and-output-types)
  * [Supported File types and Code Blocks](#supported-file-types-and-code-blocks)
  * [Flag Options](#flag-options)
  * [Examples](#examples)
  * [Common Error Codes and Exceptions](#common-error-codes-and-exceptions)
- [Dependencies](#dependencies)

<!-- tocstop -->

## What it does

- Explain in a few lines the objective of the document/script and what it aims
  to achieve.

### Sample reference:

- This script auto renders figures by
  - Detecting fenced code blocks (PlantUML, Mermaid, TikZ, Graphviz, ...)
  - Rendering them into images calling the appropriate tool
  - Commenting them out the block
  - Inlining a `![](img)` markup

### Input and Output Types

Detail what input formats are accepted and the output format of any files
generated, if any and contents of the output.

### Supported File types and Code Blocks

List the file extensions or formats your tool/script can handle. Mention how
each is processed.

Reference Examples:

- Create a new Markdown file with rendered images:

  > render_images.py -i ABC.md -o XYZ.md --action render --run_dockerized

- Render images in place in the original Markdown file:

  > render_images.py -i ABC.md --action render --run_dockerized

- Render images in place in the original LaTeX file:

  > render_images.py -i ABC.tex --action render --run_dockerized

- Open rendered images from a Markdown file in HTML to preview:
  > render_images.py -i ABC.md --action open --run_dockerized

### Flag Options

Describe each available flag, its purpose, and demonstrate how to use it in the
CLI with examples.

Reference:
```
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
```
=======
- Examples
  - This script auto renders figures by:
    - Detecting fenced code blocks (PlantUML, Mermaid, TikZ, Graphviz, ...)
    - Rendering them into images calling the appropriate tool
    - Commenting them out the block
    - Inlining a `![](img)` markup

### Input and Output Types

- Detail what input formats are accepted and the output format of any files
  generated, if any and contents of the output.

### Supported File types and Code Blocks

- List the file extensions or formats your tool/script can handle. Mention how
  each is processed.

### Reference Examples:

- Create a new Markdown file with rendered images:
  ```bash
  > render_images.py -i ABC.md -o XYZ.md --action render --run_dockerized
  ```

- Render images in place in the original Markdown file:
  ```bash
  > render_images.py -i ABC.md --action render --run_dockerized
  ```

- Render images in place in the original LaTeX file:
  ```bash
  > render_images.py -i ABC.tex --action render --run_dockerized
  ```

- Open rendered images from a Markdown file in HTML to preview:
  ```bash
  > render_images.py -i ABC.md --action open --run_dockerized
  ```

### Flag Options

- Describe each available flag, its purpose, and demonstrate how to use it 
  with examples

- Report the output of running the script with `--help`

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

### Common Error Codes and Exceptions

Error/Issue: Likely Cause: Possible Fix:

## Dependencies

Mention any and all dependencies needed to run your code.
=======
- Error/Issue:
  - Likely Cause:
  - Possible Fix:

## Dependencies

- Mention any and all dependencies needed to run your code.

