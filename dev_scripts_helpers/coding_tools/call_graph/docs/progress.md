# Call Graph Viewer: Progress

- What is done, what we learned, what is next
- Roadmap: `plan.md`; decisions: `decisions.md`

## Status

| Milestone | Target | Status                                                                  |
| :-------- | :----- | :---------------------------------------------------------------------- |
| v1        | none   | Implemented in the working tree of the branch `gp`; no PR is merged yet |
| v1.1      | none   | Not started                                                             |
| v2        | none   | Not started, to be decided after `v1.1`                                 |

- Tests: 27 pass with the dependencies installed (13 extraction, 3 rendering, 7
  browser logic through `node`, 3 end to end, 1 `uv run`); without `jedi`,
  `networkx`, `jinja2`, and `pygments`, the 7 browser-logic tests pass and 3 files
  skip
- Checked by hand in headless Chrome with real mouse events, on the fixture and on
  `helpers/`: a click on a method row shows its code, a click on a function and on
  a class header, Back and Forward restore the views, the tooltip shows the
  interface, 0 neighbors shows all nodes; no console error

## Built

- Extractor: `call_graph/extract.py` (see the component README)
- Renderer and page: `call_graph/render.py` and `call_graph/assets/`
- Command line: `dev_scripts_helpers/coding_tools/call_graph_viewer.py`
- Usage, architecture, and limits: `dev_scripts_helpers/coding_tools/call_graph_viewer.README.md`

## Findings

1. **Resolution speed**: `helpers/` (150 files, 2,073 symbols, 14,229 references)
   takes 47 s wall clock (42 s user) on one core, 3.2 files per second
   - Command: `call_graph_viewer.py --input helpers --exclude_tests`, macOS,
     `jedi` 0.20.1, on 2026-10-21
2. **Resolution outcome** on the same run: 4,842 references resolved (34%), 7,695
   external (54%), 1,692 unresolved (12%); 3,940 edges
3. **Page size**: 13.3 MB (13,956,174 bytes) for `helpers/`, 93 KB per source
   file; the vendored libraries are 0.77 MB
   - A 3-file fixture gives 0.8 MB, so the libraries dominate a small page
4. **Page load**: headless Chrome renders the `helpers/` page opened on
   `hio.to_file` (52 of 1,693 nodes, 93 edges) in about 2 s, including the start
   of the browser
5. **A real repo found a bug the fixture could not**: escaping `<!--` as `<\!--`
   is not valid JSON, so `JSON.parse()` failed on any source containing `<!--`;
   every `<` is now written as `\u003c`, covered by a unit test
6. **`ruff check` is unsafe here**: `pyproject.toml` sets `fix = true` and one run
   rewrote 93 things against the coding rules (`from helpers import hio`,
   `list[str]`, `X | None`); lint with the editor diagnostics and format with
   `ruff format`
7. **0 neighbors on a big repo is slow**: the status line shows 1,693 nodes for
   `helpers/`; the first view of a big graph needs a limit (the page opens on the
   most connected symbol when a graph has more than 120 nodes)

## Next

1. File the GitHub issues for the `v1` PRs and cut the working tree into them with
   `/github.split_branch_in_PRs`, in the order of the roadmap
2. Review `decisions.md` D4 to D6, which are proposed
3. Start `v1.1` with `PR_E4` (cache) and `PR_R2` (smaller page)

## History

| Date       | Done                                                                                                                                                       |
| :--------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-10-21 | Libraries proposed and chosen: static HTML for `v1` and a server for `v2`, `jedi` only, vendored JavaScript (`decisions.md` D1 to D3)                    |
| 2026-10-21 | `v1` implemented in the working tree: extractor, renderer, viewer, command line, 27 tests, component README; measured `helpers/`; fixed the JSON escaping |
| 2026-10-21 | Wrote the plan following `docs/planning/all.plan_work.how_to_guide.md`                                                                                      |
