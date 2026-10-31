# Call Graph Viewer: Decisions

- Every non-obvious choice, why it was made, and what else was considered. Newest
  at the bottom of each section
- Each PR adds its decisions here and links them in its description
- Roadmap: `plan.md`

## Delivery

### D1. A static HTML page in `v1`, a local server in `v2`

- **Decision**: `v1` writes one self-contained HTML file; a local server is
  planned for `v2` (`PR_S1` to `PR_S4`)
- **Why**: a file needs no process and no port, opens offline, can be mailed or
  attached to a PR, and gives tests a plain JSON to compare. The cost is a page
  that grows with the code (13 MB for `helpers/`) and no live update
- **Alternatives**: a server first (lazy loading, live update, but a process to
  run, a Docker port to forward, and a web dependency)
- **Status**: accepted by GP on 2026-10-21

### D2. `jedi` is the only resolver

- **Decision**: resolve each call, base class, and attribute type with
  `jedi.Script.goto()`; `ast` finds the definitions and the positions
- **Why**: `jedi` infers the types, so `self.foo()`, an aliased import such as
  `hdbg.dassert()`, and a call on a local variable (`d.speak()`) resolve; it is
  in the Docker image. The cost is 47 s for 150 files (`progress.md`, finding 1)
- **Alternatives**: `ast` plus an import-alias map (fast, imprecise, was the first
  proposal); `pyan3` (not in the image, little maintained)
- **Status**: accepted by GP on 2026-10-21

### D3. The JavaScript libraries are vendored in the repo

- **Decision**: copy the minified libraries, unmodified and with their licenses, to
  `call_graph/assets/vendor/` and inline them in the page
- **Why**: the page works offline and the versions are pinned by the files
- **Alternatives**: pinned CDN links (the page needs the network)
- **Status**: accepted by GP on 2026-10-21

## Viewer

### D4. The neighbors are computed on methods, drawn on classes

- **Decision**: the filter is a BFS on the graph of functions and methods; the
  result is projected on the drawn nodes (a method collapses into its class box,
  and the calls between two nodes become one `uses` edge)
- **Why**: "N connections of a method" is exact, and the page keeps the UML box as
  one node. The row of the selected method and the rows in the neighborhood are
  highlighted in the box
- **Alternatives**: a node per method inside a compound class node (exact edges,
  but a box that is no longer a UML class); a graph of classes only (loses the
  method-level neighborhood)
- **Status**: proposed

### D5. A plain tooltip instead of `tippy.js`

- **Decision**: a `div` of about 30 lines shows the interface on hover; the
  planned `tippy.js`, `popper`, and `cytoscape-popper` are not vendored
- **Why**: three fewer vendored files. The rows of a UML box are in an overlay that
  ignores the mouse, so the tooltip is placed from the mouse position anyway
- **Alternatives**: `tippy.js` with `cytoscape-popper`
- **Status**: proposed; this changes the library list that GP agreed to on
  2026-10-21

### D6. `fcose` is the default layout

- **Decision**: the force layout `cytoscape-fcose` is the default and
  `breadthfirst` (built in) is the "tree" option
- **Why**: `fcose` handles compound nodes (the module boxes) and the size of the
  UML boxes; `breadthfirst` costs no library
- **Alternatives**: `cytoscape-dagre` (a layered layout that may read better for
  calls, but needs `dagre` and has no compound support), see the open question 2 of
  the Viewer
- **Status**: proposed
