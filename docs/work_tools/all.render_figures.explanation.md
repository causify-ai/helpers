

<!-- toc -->

- [`render_md.py` tool](#render_mdpy-tool)
  * [How to use](#how-to-use)

<!-- tocstop -->

#### `render_md.py` tool

- We have a `render_md.py` tool to embed images after `plantuml` section.
  Typical usage to insert images to the markdown file and to preview it:
  ```bash
  > render_md.py -i knowledge_graph/vendors/README.md
  ```

##### How to use

1. Make sure `plantuml` is installed on your machine. The easiest way is to use
   the Docker container. All the packages typically needed for development are
   installed in the container.

2. How to use:
   ```bash
   > render_md.py -h
   ```

- We try to let the rendering engine do its job of deciding where to put stuff
  even if sometimes it's not perfect. Otherwise, with any update of the text we
  need to iterate on making it look nice: we don't want to do that.

- `.md` files should be linted by our tools

3. If you want to use `open` action, make sure that your machine is able to open
   `.html` files in the browser.
