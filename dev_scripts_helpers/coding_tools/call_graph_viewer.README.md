# `call_graph_viewer.py`

- Reads a directory of Python code and builds its call graph
- Writes one self-contained HTML page to navigate the code
  - A graph on the left shows how functions and classes call each other
  - A code view on the right shows the source of the selected symbol
- Use it to understand an unfamiliar package or to see what a change can
  affect

## Examples

- Write the call graph of a directory and open it in the browser:

  ```bash
  > call_graph_viewer.py --input helpers --open
  ```

- Skip the tests and choose the output file:

  ```bash
  > call_graph_viewer.py \
      --input helpers \
      --exclude_tests \
      --output call_graph.html
  ```

- Open on a function, showing the symbols within 2 connections:

  ```bash
  > call_graph_viewer.py \
      --input helpers \
      --focus hdbg.dassert_eq \
      --radius 2
  ```

- Embed only that neighborhood, to get a small page for a big repo:

  ```bash
  > call_graph_viewer.py \
      --input helpers \
      --focus hdbg.dassert_eq \
      --radius 2 \
      --prune
  ```

## Using the Page

- **Graph**
  - A class is a UML box with its name, attributes, and methods
    - `+` public, `#` protected (`_x`), `-` private (`__x`)
    - Static methods are underlined and abstract methods are in italics
  - Arrows follow UML
    - Dashed open arrow: "uses" (a call or an instantiation)
    - Solid line with a hollow triangle: inheritance
    - Solid line with a filled diamond on the owner: composition
  - Scroll to zoom, drag to pan, use `Fit` to see everything
  - Symbols are grouped in a box per module (toggle with `Modules`)
- **Hover** a function, a class, or a row of a class box to see its interface:
  signature, docstring, members, and the number of in / out connections
  - Hover an edge to see the underlying calls and their lines
- **Click** a function, a method, or a class to show its code
  - The graph re-centers on the clicked symbol
  - The code view highlights the definition and lists what it calls and what
    calls it, as chips that are also clickable
  - Click an edge to show the code of the caller, with the call lines marked
- **Neighbors** is the number of connections shown around the selected symbol
  - `0` shows everything
  - The direction selects callers only, callees only, or both
- **Back / Forward**: every click, neighbor change, or search is a browser
  history entry, so the browser Back button and the arrows in the toolbar go
  through the click history
  - The state is in the URL hash (e.g., `#node=helpers.hio.to_file&n=1&dir=both`),
    so a link opens the same view
- **Split view**: drag the divider between the graph and the code

## Configuration & Inputs

### Command-line Arguments

| Argument | Type | Default | Description |
| :------- | :--- | :------ | :---------- |
| `-i`, `--input` | str | required | Directory of Python code to analyze |
| `-o`, `--output` | str | `tmp.call_graph_viewer.html` | HTML file to write |
| `--project_root` | str | closest ancestor with `.git` | Directory used to name modules and to resolve absolute imports |
| `--focus` | str | none | Symbol selected on open: a full name or a unique suffix |
| `--radius` | int | 1 | Initial number of connections around the focus (`0` is everything) |
| `--title` | str | `Call graph: <dir>` | Title of the page |
| `--exclude_tests` / `--no_exclude_tests` | flag | off | Skip `test/` dirs and `test_*.py` files |
| `--prune` / `--no_prune` | flag | off | Embed only the symbols within `--radius` of `--focus` |
| `--dry_run` | flag | off | Analyze the code without writing the file |
| `--open` | flag | off | Open the output in the default browser |

- Without `--focus`, a small graph (up to 120 functions and classes) opens whole
  and a bigger one opens around its most connected symbol

### Dependencies

- Python: `jedi`, `networkx`, `jinja2`, `pygments`, `tqdm`
  - Declared in the `uv run` header of the script
  - Already in the Docker image of `helpers`
- JavaScript: vendored in `call_graph/assets/vendor/` (see `LICENSES.md`)
  - `cytoscape`, `cytoscape-fcose` (with `cose-base` and `layout-base`),
    `cytoscape-node-html-label`, `Split.js`
  - All are MIT licensed and inlined in the output, so the page needs no network

## Output & Side Effects

- Writes one HTML file (about 100 KB per analyzed source file, plus 0.8 MB for
  the libraries)
  - Use `--prune` for a smaller page
- Logs to the screen and to `call_graph_viewer.py.log`
- A syntax error in an analyzed file stops the run with the file name: exclude
  the file or the directory
- The run takes about 45 seconds for 150 files, almost all in `jedi`

## Software Architecture

### Data Flow

```text
DIR --ast--> symbols + references --jedi--> edges --networkx--> prune
    --Pygments--> highlighted source --Jinja2--> one HTML page
```

1. **Collect** (`ast`): for each file, define a symbol per module, class,
   function, and method, with its signature, docstring, and line range
   - Record the position of every call, base class, and attribute type
2. **Resolve** (`jedi`): jump to the definition of the name at each recorded
   position and map it back to a symbol by (file, line)
   - `self.foo()`, `hdbg.dassert()` with an import alias, and `d.speak()` on a
     local variable are resolved from the inferred types
   - Names that resolve outside the analyzed code are counted as `external`,
     names `jedi` cannot infer as `unresolved`
3. **Build** (`networkx`): a multigraph with one edge per (src, dst, kind) where
   kind is `call`, `instantiate`, `inherit`, or `compose`
   - `--prune` keeps the ball of radius `--radius` around `--focus`
4. **Render**: highlight the source once with Pygments (one HTML string per line),
   embed the data as JSON and fill the Jinja2 template
5. **Browse** (in the page): all the logic runs in the browser
   - The neighbors filter is a BFS over the member-level graph: methods are
     separate symbols there, and they collapse into their class when drawn
   - The graph is drawn with Cytoscape, and the UML boxes are HTML labels placed
     on the canvas nodes

### Key Functions & Modules

- `call_graph/extract.py`
  - `extract_call_graph(root_dir, *, project_root, exclude_tests) -> CallGraph`
    - The two-pass extraction above
  - `prune_call_graph(cg, focus, radius) -> CallGraph`
    - Keeps the symbols within `radius` connections of `focus`
  - `find_symbol_id(cg, query) -> str`
    - Resolves a name or a unique suffix into a symbol id
  - `call_graph_to_dict(cg) -> Dict[str, Any]`
    - JSON-serializable form shared by the page and a future server
- `call_graph/render.py`
  - `render_html(cg, title, *, focus, radius) -> str`
    - Assembles the page from the template, the CSS, the JavaScript, and the data
- `call_graph/assets/`
  - `call_graph_viewer.html.j2`, `call_graph_viewer.css`: the page
  - `call_graph_viewer_core.js`: logic without a DOM (neighbors, projection, UML
    box geometry, history state)
    - Tested with `node` in `call_graph/test/test_call_graph_viewer_core.py`
  - `call_graph_viewer_app.js`: DOM, Cytoscape, tooltips, code view, history
- `call_graph_viewer.py`
  - Command line: extract, optionally prune, render, write

### Design Patterns

- **Plain data model**: `CallGraph`, `Symbol`, and `Edge` are dataclasses with no
  behavior, so the page, the tests, and a server use the same data
- **One seam to the data**: the browser code reads the code of a file only through
  `source.getFile()` in `call_graph_viewer_app.js`. v1 answers from the embedded
  data and a server (v2) would answer with `fetch()`
- **Self-contained output**: no network and no server, so the page can be
  attached to a PR or a CI run
- **Stable layout**: selecting a symbol that is already in view only moves the
  highlight, and the layout runs only when the set of drawn nodes changes

## Limitations

- The call graph is static
  - A call through an untyped value, a callback, or a dynamic attribute is
    unresolved, and a call resolves to the method that `jedi` infers, not to
    the overrides
  - A function passed as a value (e.g., `map(f, xs)`) is not a call
  - The count of unresolved calls is in the status line of the page
- Code that runs at import time (module level) is not part of the graph
- String annotations (e.g., `List["Dog"]`) do not create composition edges
- The page has a light theme only

## Plan

- The roadmap is in `call_graph/docs/04-plan.md`, the decisions in
  `call_graph/docs/03-decisions.md`, and the status in `call_graph/docs/07-progress.md`
- `v2` adds a local server (`--serve`) that serves the graph and the code on
  demand and reloads the page when a file changes
  - The browser code reads the code of a file only through `source.getFile()` in
    `call_graph_viewer_app.js`: a server replaces that one object

## Tests

- `call_graph/test/test_extract.py`: extraction on a fixture package
- `call_graph/test/test_render.py`: embedding, highlighting, page assembly
- `call_graph/test/test_call_graph_viewer_core.py`: browser logic through `node`
- `test/test_call_graph_viewer.py`: the executable end to end
- `test/test_call_graph_viewer_uv_run.py`: `uv run` resolves the dependencies
