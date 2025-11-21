# Summary

- A short description of the goals of the files in this dir

# Description of tools

- For each script writes a short description of what it does and use examples in
  the format
## `<tool>`

### What it Does

### Examples

- Example command line
  ```bash
  > example
  ```

- For instance

## `notes_to_pdf.py`

### What It Does

- Convert plain‑text notes into polished **PDF**, **HTML**, or **Beamer slides**
  with a single command:

  ```bash
  > notes_to_pdf.py --input <infile.txt> --output <outfile.[pdf|html]> --type [pdf|html|slides]
  ```

### Examples

- Compile to **Beamer slides**
  ```bash
  > notes_to_pdf.py -i lesson.txt -o lesson.pdf --type slides
  ```

- Produce a **stand‑alone HTML** page
  ```bash
  > notes_to_pdf.py -i cheatsheet.txt -o cheatsheet.html --type html
  ```

- Build a **PDF article** (LaTeX)
  ```bash
  > notes_to_pdf.py -i paper.txt -o paper.pdf --type pdf
  ```

- Skip the final viewer **open** step
  ```bash
  > ... --skip_action open`
  ```
