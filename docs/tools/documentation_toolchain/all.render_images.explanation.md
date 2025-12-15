<!-- toc -->

- [`render_images.py` tool](#render_imagespy-tool)
  * [How to use](#how-to-use)

<!-- tocstop -->

# `render_images.py` tool

- The `render_images.py` tool replaces image code in Markdown/LaTeX files (e.g.,
  `plantUML` or `mermaid` code for diagrams) with rendered images.
- Location: `dev_scripts_helpers/documentation/render_images.py`
- Typical usage to render images in a Markdown file:
  ```bash
  > render_images.py -i knowledge_graph/vendors/README.md --action render --run_dockerized
  ```

## How to use

1. If you don't include the option `--run_dockerized`, make sure `plantuml` and
   `mermaid` are installed on your machine. The easiest way is to use the Docker
   container. All the packages typically needed for development are installed in
   the container.

2. How to use:
   ```bash
   > render_images.py -h
   ```

- We try to let the rendering engine do its job of deciding where to put stuff
  even if sometimes it's not perfect. Otherwise, with any update of the text we
  need to iterate on making it look nice: we don't want to do that.

- `.md` files should be linted by our tools.

3. If you want to use `open` action, make sure that your machine is able to open
   `.html` files in the browser.

### Processing Multiple Files

The tool supports three ways to process multiple files:

1. **Comma-separated list**: Use `--files="file1.md,file2.md,file3.md"` to specify
   multiple files separated by commas.

   ```bash
   > render_images.py --files="file1.md,file2.md,file3.md" --action render
   ```

2. **File containing list**: Use `--from_files="list.txt"` where `list.txt`
   contains one file path per line. Empty lines and lines starting with `#` are
   ignored.

   Example `list.txt`:
   ```
   # Files to render
   docs/chapter1.md
   docs/chapter2.md

   # More files
   docs/chapter3.md
   ```

   ```bash
   > render_images.py --from_files="list.txt" --action render
   ```

3. **Repeated argument**: Use `--input` multiple times to specify each file.

   ```bash
   > render_images.py --input file1.md --input file2.md --input file3.md --action render
   ```

**Notes**:
- When processing multiple files, rendering is always done in-place
  - The `-o` option causes an error when used together with multiple files
- The tool shows a progress bar when processing multiple files.
- All three methods are mutually exclusive: you can only use one at a time.
- The single `-i` option works for processing one file.
