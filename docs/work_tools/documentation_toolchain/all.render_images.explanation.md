

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
  > render_images.py -i knowledge_graph/vendors/README.md --action render
  ```

## How to use

1. Make sure `plantuml` and `mermaid` are installed on your machine. The easiest
   way is to use the Docker container. All the packages typically needed for
   development are installed in the container.

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
