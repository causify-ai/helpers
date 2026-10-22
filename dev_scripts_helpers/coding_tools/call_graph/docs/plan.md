# Call Graph Viewer Implementation Plan

## Goal

- Build `call_graph_viewer.py`: a command line that reads a directory of Python code,
  builds its call graph, and writes one HTML page to navigate the code
- The page must:
  - Show how the classes and the functions call each other
  - Show the interface of a function or a class when the mouse hovers over it
  - Show the code of a function or a method when it is clicked, and jump to the
    code of a class when it is clicked
  - Draw the classes with UML notation
  - Zoom the graph in and out
  - Show the neighbors of a function up to N connections (0 shows everything)
  - Have a split view: the graph on one half and the code on the other
  - Go back in the history of the clicks
- Background: the component README
  `dev_scripts_helpers/coding_tools/call_graph_viewer.README.md` (usage,
  architecture, limits)
- Related tool: `dev_scripts_helpers/coding_tools/build_call_graph.py` renders a
  static PDF with `pyan3`; this project builds an interactive page and resolves the
  calls with `jedi`

## Plan Hierarchy

- This file is the canonical roadmap of the project and defines the PRs
- `progress.md` records what is done and what was learned
- `decisions.md` records the decisions and the alternatives considered
- A checked PR is merged. An unchecked PR is not started, implemented but not
  merged, or partly done; the `Status` line in its entry below says which
- There is no execution plan: one person works on the project. Add one when
  several people work in parallel

## Roadmap

- **v1**: A static HTML page, with no server and no network: run
  `call_graph_viewer.py --input DIR --open` and navigate the code of `DIR` as
  described in the goal
  - Status: all the `v1` PRs are implemented and staged on the branch `gp`, with 27
    passing tests; none is committed or merged
  - [ ] `PR_D1`
  - [ ] `PR_E1`
  - [ ] `PR_E2`
  - [ ] `PR_E3`
  - [ ] `PR_V1`
  - [ ] `PR_V2`
  - [ ] `PR_R1`
  - [ ] `PR_V3`
  - [ ] `PR_V4`
  - [ ] `PR_V5`
  - [ ] `PR_C1`
- **v1.1**: The page is fast to build and small enough for a big repo (`helpers/`
  takes 47 seconds and gives a 13 MB page today), and a call inside the code view
  can be clicked
  - Status: not started
  - [ ] `PR_E4`
  - [ ] `PR_R2`
  - [ ] `PR_E5`
  - [ ] `PR_V6`
- **v2**: A local server serves the graph and the code on demand and reloads the
  page when a file changes
  - Status: not started
  - [ ] `PR_S1`
  - [ ] `PR_S2`
  - [ ] `PR_S3`
  - [ ] `PR_S4`
- Releases are cumulative: each version also requires every PR listed under the
  versions before it

# Component Specs

## Extractor (`E`)

### Goal

- Turn a directory of Python code into a `CallGraph`: the symbols (modules,
  classes, functions, methods) and the relations between them (`call`,
  `instantiate`, `inherit`, `compose`)
- Code: `call_graph/extract.py`

### Open Questions

1. How accurate is the call resolution? In `helpers/`, 12% of the references are
   unresolved and 54% are external; nobody has checked how many are real misses
   -> Project
   - Compare with the calls recorded at run time (`sys.setprofile`) while the
     fast tests of `helpers/` run
2. Should `self.m()` also link to the overrides of `m` in the subclasses? The graph
   shows only the method that `jedi` infers, and misses the dynamic dispatch
3. Can the resolution run in parallel (`hjoblib`, one process per group of files)?
   It runs at 3.2 files per second on one core
4. Do `jedi` and `parso` keep up with new Python syntax? The Docker image and the
   thin client use different Python versions

## Renderer (`R`)

### Goal

- Turn a `CallGraph` into one self-contained HTML page: the data, the highlighted
  source, the vendored libraries, and the CSS are inlined
- Code: `call_graph/render.py` and `call_graph/assets/`

### Open Questions

1. What page size is acceptable? `helpers/` gives 13 MB today, 93 KB per source
   file. Is compression enough (`PR_R2`), or does a big repo need the server
   (`v2`)?
2. Is one file better than a dir (`index.html` plus data files)? A dir caches
   better but cannot be mailed or attached to a PR

## Viewer (`V`)

### Goal

- The code that runs in the browser: the neighbors filter, the UML boxes, the
  Cytoscape graph, the tooltips, the code view, and the click history
- Code: `call_graph/assets/call_graph_viewer_core.js` (logic without a DOM) and
  `call_graph/assets/call_graph_viewer_app.js` (DOM and Cytoscape)

### Open Questions

1. How to show a big graph? At 0 neighbors, `helpers/` has 1,693 nodes: the HTML
   boxes and the layout get slow. A module-level overview could be the first view
   -> Project
2. Is the force layout the best default? A layered layout (callers above callees)
   may read better for call graphs but needs two more vendored libraries
3. Should a click re-center the neighborhood, as now, or only select the symbol?
4. Does the viewer need a dark theme? The page has a light theme only

## CLI (`C`)

### Goal

- The command line `call_graph_viewer.py`: extract, optionally prune, render, write
  the file, and open it
- Code: `dev_scripts_helpers/coding_tools/call_graph_viewer.py`

### Open Questions

1. Should the command accept the files changed in a branch (`--branch`, as in
   `hselect_input_output.add_file_selection_args()`) and open on what they affect?
   This answers "what can this PR break?" -> Project
2. Should `--focus` accept several symbols?

## Server (`S`)

### Goal

- `call_graph_viewer.py --serve`: serve the same page and the data from a local
  process, so a big repo is never loaded at once and the page follows the code

### Open Questions

1. Is a server needed at all? Decide with the measurements after `v1.1`: if the
   cache and the compression give a page below 2 MB and a build below 5 seconds,
   the server may not be worth its cost
2. How is it used in Docker? Bind to `0.0.0.0` inside the container and forward the
   port, as in `dev_scripts_helpers/docker/docker_jupyter_port_forward.py`
3. When a file changes, re-resolve everything or only the file and the files that
   import it?

# PRs

- PRs are listed in the order of the roadmap, `v1` first
- PRs not assigned to a version follow, grouped by component and ordered by number
- Every `v1` PR is implemented: the code is staged on the branch `gp`, and nothing
  is committed or merged
  - The PRs are cuts of the files listed in the table of the `v1` section, of about
    400 lines of non-test code each (the vendored libraries are not counted)
  - Use `/github.split_branch_in_PRs` to cut them, in the order of the roadmap
  - File the GitHub issues for the `v1` PRs before opening them
- The entries of `v1` say what was implemented, and what is missing before the
  merge

## v1: Static HTML Page

- Demo: `call_graph_viewer.py --input helpers --focus hio.to_file --open` opens a
  page where a click on a class box, a method row, or a function shows its code,
  Back returns to the previous view, and the neighbors box changes the number of
  connections shown

### Requirements Covered

| Requirement of the goal                         | Status      | PRs                  |
| :---------------------------------------------- | :---------- | :------------------- |
| Calls between the classes and the functions     | Implemented | `PR_E3`, `PR_V3`     |
| Interface on hover                              | Implemented | `PR_V4`              |
| Click shows the code of a function or a method  | Implemented | `PR_V4`, `PR_V5`     |
| Click on a class jumps to its code              | Implemented | `PR_V4`, `PR_V5`     |
| UML notation for the classes                    | Implemented | `PR_V2`, `PR_V3`     |
| Zoom in and out                                 | Implemented | `PR_V3`              |
| Neighbors up to N connections (0 is everything) | Implemented | `PR_V1`, `PR_V5`     |
| Split view, graph and code                      | Implemented | `PR_V5`              |
| Back in the history of the clicks               | Implemented | `PR_V5`              |

### Where the `v1` Code Is

- Line numbers are the ones at the time of writing; the paths are relative to
  `dev_scripts_helpers/coding_tools/`

| PR      | Code                                                                                                  | Tests that pass today                                                                                        |
| :------ | :---------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| `PR_D1` | `call_graph/docs/`                                                                                    | none                                                                                                         |
| `PR_E1` | `call_graph/extract.py`: imports, data model, file discovery (lines 1-202)                            | `Test_get_project_root`, `Test_find_python_files` (3)                                                        |
| `PR_E2` | `call_graph/extract.py`: AST helpers, symbol collection (203-535)                                     | `Test_extract_call_graph.test1`, `test3` (2)                                                                 |
| `PR_E3` | `call_graph/extract.py`: reference resolution, public API (536-762)                                   | `Test_extract_call_graph.test2`, `test4`, `Test_find_symbol_id` (3), `Test_prune_call_graph` (3)             |
| `PR_V1` | `call_graph/assets/call_graph_viewer_core.js`: model, neighborhood, history state (1-284, 419-476)    | `Test_call_graph_viewer_core_js.test1` to `test4`, `test7` (5)                                               |
| `PR_V2` | `call_graph/assets/call_graph_viewer_core.js`: UML class box (285-418)                                | `Test_call_graph_viewer_core_js.test5`, `test6` (2)                                                          |
| `PR_R1` | `call_graph/render.py`, `call_graph/assets/call_graph_viewer.html.j2`, `.css`, `assets/vendor/`       | `call_graph/test/test_render.py` (3)                                                                         |
| `PR_V3` | `call_graph/assets/call_graph_viewer_app.js`: data, UML box HTML, graph (1-56, 137-518)               | none                                                                                                         |
| `PR_V4` | `call_graph/assets/call_graph_viewer_app.js`: tooltip, code view (57-136, 519-607)                    | none                                                                                                         |
| `PR_V5` | `call_graph/assets/call_graph_viewer_app.js`: navigation, history, start (608-722)                    | none                                                                                                         |
| `PR_C1` | `call_graph_viewer.py`, `call_graph_viewer.README.md`                                                 | `test/test_call_graph_viewer.py` (3), `test/test_call_graph_viewer_uv_run.py` (1)                            |

### `PR_D1`: [ ] Project Docs

- Background: the project has a component README and no plan
- Add `call_graph/docs/` with `README.md` (the index), `plan.md`, `progress.md`,
  and `decisions.md`
- `how_we_work.md` is added when a second person joins
- Result: a newcomer finds the plan, the log, and the decisions without asking
- Status: implemented; `how_we_work.md` is not written, it needs the GitHub
  project, the Slack channel, and the Drive links of the team

### `PR_E1`: [ ] Data Model and File Discovery

- Background: about 240 lines of `call_graph/extract.py`, with the imports
- Add the dataclasses `Symbol`, `Edge`, and `CallGraph`
- Add `get_project_root()`: the closest ancestor with `.git`, a dir or a file as
  in a submodule, so that `import helpers.hdbg` resolves when the input is
  `<repo>/helpers`
- Add `find_python_files()`: skips hidden dirs, `__pycache__`, virtual envs,
  `tmp.*` dirs, and, on request, the tests
- Add the fixture package `call_graph/test/call_graph_fixture.py`: inheritance,
  composition, calls through `self`, through an import alias, and through a local
  variable
- Unit tests (`call_graph/test/test_extract.py`): `get_project_root()` finds the
  ancestor with `.git`; `find_python_files()` lists the fixture files, with and
  without `exclude_tests`
- Result: the Python files of a dir are listed and named as modules
- Status: implemented, 3 tests pass. It also skips the dirs `build`, `dist`,
  `node_modules`, and `site-packages`

### `PR_E2`: [ ] Symbol Collection with `ast`

- Background: about 330 lines of `call_graph/extract.py`
- Collect a `Symbol` for each module, class, function, and method:
  - Signature without `self` / `cls`, docstring capped at 2,000 characters,
    decorators, UML visibility from the name (`+`, `#`, `-`), line range
  - Class attributes, from the class body and from `self.x = ...` in `__init__()`
    and `__post_init__()`
  - The position of each call, base class, and attribute type, kept as `_Ref` to
    resolve later (the `ast` byte columns are converted to character columns for
    `jedi`)
- Do not create symbols for nested functions: their calls belong to the enclosing
  function
- Unit tests: the symbols of the fixture (kind, id, line range, signature); the
  attributes, bases, decorators, and visibility of a class. The tests of the working
  tree call `extract_call_graph()`: in this PR they call `_collect_module()`, since
  `jedi` arrives in `PR_E3`
- Result: the definitions of a directory are listed with their interface
- Status: implemented, 2 tests pass (through `extract_call_graph()`, see above).
  Before merging, add tests for a non-ASCII source line (the byte to character
  column conversion), a definition inside an `if` or a `try`, and a composition
  that comes from a class-level annotation

### `PR_E3`: [ ] Reference Resolution with `jedi` and the Public API

- Background: about 225 lines of `call_graph/extract.py`
- Resolve each `_Ref` with `jedi.Script.goto(follow_imports=True)` and map the
  result to a symbol by (file, line)
  - One `Script` per file
  - Count the references as `resolved`, `external` (outside the analyzed code), or
    `unresolved`
  - A call to a class is an `instantiate` edge
  - `inherit` and `compose` edges end only in classes
  - One edge per (src, dst, kind), with the lines of the call sites
- Add `extract_call_graph()`, `build_nx_graph()` (a `networkx` multigraph),
  `find_symbol_id()` (full id or a unique suffix), `prune_call_graph()` (the
  `networkx` ball around a symbol, with the enclosing classes and modules), and
  `call_graph_to_dict()` (the data shared by the page and a future server)
- Unit tests: the edges of the fixture (a call through `self`, through the alias
  `pbase.helper()`, through the variable `d.speak()`, an instantiation, an
  inheritance, a composition); `find_symbol_id()` with a full id, a suffix, and a
  bare name; `prune_call_graph()` around a method, around a class (its methods are
  seeds), and with radius 0
- Result: `extract_call_graph("helpers")` returns the call graph in Python or in a
  notebook
- Status: implemented, 8 tests pass. `helpers/` (150 files, 14,229 references)
  runs in 47 s and gives 3,940 edges

### `PR_V1`: [ ] Browser Logic: Neighbors, Projection, History State

- Background: about 340 lines of `call_graph/assets/call_graph_viewer_core.js`; the
  file has no DOM, so Node can run it
- Index the symbols and the edges (`buildModel()`)
- Compute the symbols within N connections (`neighborhood()`), following callers,
  callees, or both; a class brings its methods and a module brings all it defines;
  with N = 0 everything is shown
- Project the member-level neighborhood on the drawn nodes (`project()`): a method
  collapses into its class and the calls between two nodes collapse into one `uses`
  edge that keeps the underlying calls
- Add `related()` (callers, callees, bases, subclasses, composed types),
  `findSymbol()`, `mostConnected()`, and `encodeState()` / `decodeState()` for the
  URL hash
- Unit tests (`call_graph/test/test_call_graph_viewer_core.py`, run with
  `node` through `call_graph/test/call_graph_viewer_core_runner.js`, skipped when
  `node` is missing): one connection around a function; two connections following
  callees only, which follows an inheritance edge; radius 0 shows unreachable
  symbols; the projection of a class collapses its methods; the state survives a
  round trip through the hash and ignores an invalid value
- Result: the neighbors filter can be run and checked without a browser
- Status: implemented, 5 tests pass. Before merging, add tests for `related()`,
  `findSymbol()`, and `mostConnected()`, which are only checked by hand

### `PR_V2`: [ ] UML Class Box Geometry

- Background: about 135 lines of `call_graph_viewer_core.js`
- `classBox()`: the header, the attribute and method compartments, and the size in
  pixels; a collapsed box shows at most 14 methods, the ones in the neighborhood
  first
- `rowAt()`: maps a vertical offset in the box to the row under the mouse, so a
  click on a method row selects the method
- `formatSignature()` and `visibilityOf()`: `name(a: int): str`, `+` / `#` / `-`
- Unit tests: the box of a class with a selected method and a hit method (size,
  attribute rows, method rows); `rowAt()` for the header, an attribute, and a method
- Result: the UML box can be drawn and clicked with exact geometry
- Status: implemented, 2 tests pass. The box draws the stereotype `dataclass` and
  the `+` / `#` / `-` marks; static methods are underlined and abstract methods
  are in italics (in `call_graph_viewer.css`)

### `PR_R1`: [ ] Page Shell and Renderer

- Background: about 400 lines (`render.py`, the template, the CSS); the vendored
  libraries are 0.77 MB and are not counted
- Vendor, unmodified and with their licenses, in `call_graph/assets/vendor/`:
  Cytoscape.js, `cytoscape-fcose` with `cose-base` and `layout-base`,
  `cytoscape-node-html-label`, and Split.js (all MIT, see `LICENSES.md`)
- `render_html()` assembles the page with Jinja2
  - Locate the assets with `hgit.find_file_in_git_tree()`, not from `__file__`
  - Highlight the source with Pygments: one HTML string per line, so the viewer
    can scroll to a line range
  - Embed the data as JSON with every `<` written as `\u003c`, so the text cannot
    end the `<script>` element or open a comment
- Add a placeholder `call_graph_viewer_app.js` that prints the number of symbols
  and edges; `PR_V3` replaces it
- Unit tests (`call_graph/test/test_render.py`): the script-safe JSON (a `</script>`
  and a `<!--` stay valid JSON after `json.loads()`); the highlighted HTML has one
  string per source line; the page embeds the title (escaped), the initial view,
  the symbols, and the code
- Result: a `CallGraph` becomes a page that opens offline in a browser
- Status: implemented, 3 tests pass. The working tree has the final
  `call_graph_viewer_app.js`: write the placeholder when cutting the PR

### `PR_V3`: [ ] Graph View

- Background: about 440 lines of `call_graph_viewer_app.js`; split the styles from
  the elements and the layout if the review asks
- Create the Cytoscape graph with the UML notation
  - Dashed open arrow: uses; hollow triangle: inheritance; filled diamond on the
    owner: composition
  - A class is an HTML box over a canvas node; a function is a rounded node
  - A box per module (compound node), switchable
- Layout with `fcose` (or `breadthfirst` as a tree); fit the view after the
  layout; run the layout only when the set of drawn nodes or their sizes change, so
  selecting a node in view does not move the graph
- Highlight the selected node and its edges; zoom and pan are built in
- Unit tests: none for the DOM; the logic is tested in `PR_V1` and `PR_V2`. Check
  by hand on the fixture and on `helpers/`
- Result: the graph is on the page and can be zoomed
- Status: implemented. Checked by hand in headless Chrome: real mouse events on the
  fixture, and a render of `helpers/` (52 of 1,693 nodes around `hio.to_file`);
  there is no automated browser test yet (`PR_V9`)

### `PR_V4`: [ ] Tooltips and Code View

- Background: about 170 lines of `call_graph_viewer_app.js`
- A tooltip shows the interface on hover: the signature, the docstring, the
  attributes and methods of a class, the file and line, and the number of in and
  out connections
  - It works on a function, on a class, on one method row, and on an edge (the
    underlying calls)
  - Plain `div`, no library
- The code view shows the file of the selected symbol, highlights its line range,
  and scrolls to it; a click on an edge marks the call lines
- The chips under the title list what the symbol calls and what calls it (plus
  bases, subclasses, composed types); a click on a chip navigates
- Unit tests: none for the DOM; check by hand
- Result: hover shows the interface and a click shows the code
- Status: implemented and checked by hand as above: the tooltip on a method row,
  the lines of a method highlighted after a click, the chips

### `PR_V5`: [ ] Toolbar, Search, Split View, and Click History

- Background: about 115 lines of `call_graph_viewer_app.js` plus the toolbar of the
  template
- Controls: the number of neighbors (0 is everything), the direction (callers,
  callees, both), the layout, the module boxes, and a search box that autocompletes
  all the symbol ids
- Each click, neighbor change, and search is a browser history entry
  (`history.pushState()`); `popstate` restores the view; the state is in the URL
  hash, so a link reopens the view; the arrows of the toolbar call
  `history.back()` and `history.forward()`
- Split.js divides the graph and the code, and the divider can be dragged
- Without a selection, a graph of up to 120 functions and classes opens whole and a
  bigger one opens around its most connected symbol
- Unit tests: none for the DOM; the hash logic is tested in `PR_V1`. Check by hand:
  click a method row, click a function, press Back and Forward
- Result: the full interaction in the goal works on the page
- Status: implemented and checked by hand as above: a click on a method row and on
  a function, then Back and Forward, restore the views; 0 neighbors shows all the
  nodes

### `PR_C1`: [ ] Command Line, Docs, and End-to-End Tests

- Background: `call_graph_viewer.py` has about 170 lines
- The script follows `_parse()` / `_main(parser)` and has a `uv run` header for
  `jedi`, `networkx`, `jinja2`, `pygments`, and `tqdm`
- Options: `--input`, `--output`, `--project_root`, `--focus`, `--radius`,
  `--title`, `--exclude_tests`, `--prune` (embed only the neighborhood), `--dry_run`,
  `--open`, and the verbosity
- The focus is resolved before the page is written, so a typo fails fast
- Add `call_graph_viewer.README.md` and the entry in the README of the dir
- Unit tests: `test/test_call_graph_viewer.py`: the page embeds the symbols and the
  initial view; `--dry_run` writes nothing; `--prune` embeds only the neighborhood;
  `test/test_call_graph_viewer_uv_run.py`: `uv run call_graph_viewer.py --help`
  installs the dependencies and starts
- Result: a user runs one command and gets the page
- Status: implemented, 4 tests pass. `uv run call_graph_viewer.py --help` installs
  the dependencies and starts. The option `--open_app` also exists, through
  `hopen.add_open_arg()`; `--open` is not covered by a test

## v1.1: Faster and Smaller

- Demo: the second run on `helpers/` takes seconds, the page is below 2 MB, and
  clicking a call in the code view jumps to its definition
- Add GitHub issues for these PRs when `v1` is merged: the plan may change after
  the first users
- Status: not started. The call positions that `PR_E5` needs are already in `_Ref`
  in `call_graph/extract.py`

### `PR_E4`: [ ] On-disk Cache of the Extraction

- Background: `helpers/` takes 47 s, almost all in `jedi`; a second run with
  another `--focus` repeats it
- Cache the `CallGraph` as JSON, keyed by the (path, mtime, size) of every file,
  so any change re-extracts all (a per-file key is wrong: a call resolves through
  other files)
- Unit tests: a second run on an unchanged dir does not call `jedi`; a changed
  file invalidates the cache
- Result: re-rendering is instant

### `PR_R2`: [ ] Compress the Embedded Source

- Background: `helpers/` gives a 13 MB page, 93 KB per file, mostly highlighted
  HTML
- Embed the highlighted lines as gzip plus base64 and decompress in the browser
  with `DecompressionStream`; `source.getFile()` is already asynchronous
- Target: below 2 MB for `helpers/`
- Unit tests: the compressed block decodes to the same lines

### `PR_E5`: [ ] Record the Call Sites

- Add the position and the target id of each resolved call to the data of a file
  (`_Ref` already has the position)

### `PR_V6`: [ ] Clickable Calls in the Code View

- Wrap each call of the code view in a link that navigates to its definition,
  using the positions of `PR_E5`

## v2: Local Server

- Demo: `call_graph_viewer.py --input helpers --serve` opens the page in a second,
  and an edit to a file shows up in the graph without running the command again
- Decide whether to build it after `v1.1`, see the open question 1 of the Server
- Status: not started; the only part that exists is the data seam below
- The data seam exists: the browser reads the code only through `source.getFile()`
  in `call_graph_viewer_app.js`

### `PR_S1`: [ ] Serve the Page and the Data

- `--serve [--port N]` with `http.server.ThreadingHTTPServer` from the standard
  library; bind to `127.0.0.1`
- `GET /` the page without embedded data, `GET /api/graph` the result of
  `call_graph_to_dict()` without source, `GET /api/file?path=` the highlighted
  lines of one file, and reject a path outside the analyzed dir
- Unit tests: start the server on port 0 in a thread and call it with `http.client`;
  a path with `..` is rejected

### `PR_S2`: [ ] Browser Over `fetch()`

- Replace `source` in `call_graph_viewer_app.js` with an object that calls the
  endpoints; load a file the first time it is opened

### `PR_S3`: [ ] Neighbors on the Server

- `GET /api/neighbors?node=&n=&dir=` computed with `networkx`, so a huge graph
  never reaches the browser

### `PR_S4`: [ ] Watch and Reload

- Poll the mtimes (`--watch`), re-resolve the changed files and the files that
  import them (a reverse import graph), and send `GET /api/events` (server-sent
  events) so the page reloads

## Unscheduled: Extractor

### `PR_E6`: [ ] Calls at Import Time

- Add the calls in the module-level code as edges from the module symbol, for
  example the `_main(_parse())` of a script

### `PR_E7`: [ ] String Annotations

- Resolve `List["Dog"]` to create the composition edge

### `PR_E8`: [ ] Overrides

- Option to link a call through `self` to the overrides in the subclasses, see the
  open question 2 of the Extractor

## Unscheduled: Viewer

### `PR_V7`: [ ] Dark Theme

- Follow `prefers-color-scheme`, including the Cytoscape styles and the Pygments
  colors

### `PR_V8`: [ ] Module Overview for Big Graphs

- A first view with one node per module and the number of calls between modules;
  a click opens the module, see the open question 1 of the Viewer

### `PR_V9`: [ ] Browser Smoke Test

- Run the page in headless Chrome through the DevTools protocol: click a method
  row, check the code view, press Back, check the state
- It was done by hand for `v1` with a script that is not in the repo; skip the test
  when Chrome is missing
- Status: not started

## Unscheduled: CLI

### `PR_C2`: [ ] Open on What a Branch Changes

- `--branch` selects the files changed against the branch point
  (`hselect_input_output.add_file_selection_args()`) and opens on their symbols,
  with the callers as the neighborhood

## Conventions

- Code: `.claude/skills/coding.rules.md`
- Scripts: `.claude/skills/script.rules.md`
- Tests: `.claude/skills/testing.rules.md`
- Do not run `ruff check` on the code: `pyproject.toml` sets `fix = true` and it
  rewrites imports and type hints against the rules; use `ruff format`
- The workflow of a PR: `docs/planning/all.plan_work.how_to_guide.md`
