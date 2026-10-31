# `open_md.py`

- Renders one or more Markdown files and opens the result in the browser or in
  the PDF viewer
- Supports five modes: open on GitHub, HTML or PDF with `pandoc`, HTML with
  `grip`, and a live `grip` server
- Input: Markdown files, selected with `--input`, `--files`, `--from_file`, or
  a git-based selection (`--modified`, `--branch`, ...)
- Output: `tmp.*` files in the current dir, opened with `open` (macOS) or
  `xdg-open` (Linux)
- Used to preview docs with the same look as GitHub: diagrams rendered, links
  to repo-root paths working, and optional live reload on every save

## Examples

- Render a file to HTML with `pandoc` (default mode, GitHub-like style, TOC of
  depth 2 unless the file has one):
  ```bash
  > open_md.py --input xyz.md
  ```

- Open a file on GitHub, on the current branch:
  ```bash
  > open_md.py --input xyz.md --mode github
  ```

- Render to PDF, with a TOC of depth 3:
  ```bash
  > open_md.py --input xyz.md --mode pdf --toc_depth 3
  ```

- Render the Markdown files modified in the client, one output per file:
  ```bash
  > open_md.py --modified
  ```

- Render a file with `pandoc`, encoding the links with a repo-root path
  (e.g., `[prd](/docs/prd.md)`) as GitHub URLs on `master`, with a custom style:
  ```bash
  > open_md.py \
      --input xyz.md \
      --link_type master \
      --css my_style.html
  ```

- Watch several files and re-render them on every change, reloading the
  already open browser tabs:
  ```bash
  > open_md.py --from_file files.txt --daemon
  ```

## Configuration & Inputs

### Command-line Arguments

Exactly one file selection (the first seven arguments) is required: the script
never defaults to the files modified in the branch, to avoid opening many tabs
by mistake.

| Argument                     | Type | Default   | Description                                                                |
| :--------------------------- | :--- | :-------- | :------------------------------------------------------------------------- |
| `-i`, `--input`              | str  |           | Select a single file                                                       |
| `-f`, `--files`              | str  |           | Select files, as a space-separated list in a single argument               |
| `--from_file`                | str  |           | Select the files listed in a file, one path per line                       |
| `--modified`                 | flag | false     | Select the files modified in the client (staged and unstaged)              |
| `--branch`                   | flag | false     | Select the files modified with respect to the branch point                 |
| `--last_commit`              | flag | false     | Select the files in the previous commit                                    |
| `--all_files`                | flag | false     | Select all the files in the repo                                           |
| `--mode`                     | str  | `pandoc`  | One of `github`, `pandoc`, `pdf`, `grip`, `grip_daemon`                    |
| `--backend`                  | str  | `global`  | `global` uses the installed tools, `dockerized` uses Docker or `uvx`       |
| `--link_type`                | str  | `local`   | Encoding of repo-root links: `local`, `branch`, or `master`                |
| `--toc`                      | flag | false     | Always add a TOC, even if the file has a `<!-- toc -->` marker             |
| `--no_toc`                   | flag | false     | Never add a TOC                                                            |
| `--toc_depth`                | int  | 2         | Depth of the TOC, from 1 to 6                                              |
| `--css`                      | str  | none      | HTML snippet for the header, replacing the bundled GitHub-like style       |
| `--daemon`                   | flag | false     | Watch the files and re-render on every change                              |
| `--skip_open`                | flag | false     | Do not open the output (set by `--daemon` for re-runs)                     |
| `--live_reload`              | flag | false     | Make the HTML reload itself when re-rendered (set by `--daemon`)           |
| `--dockerized_force_rebuild` | flag | false     | Rebuild the Docker image (`dockerized` backend)                            |
| `--dockerized_use_sudo`      | flag | false     | Use `sudo` for Docker (`dockerized` backend)                               |
| `--no_report_command_line`   | flag | false     | Do not print the executed command line                                     |
| `-v`                         | str  | `INFO`    | Log level: `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`        |

Constraints:

- `--toc` and `--no_toc` are mutually exclusive
- `--toc_depth` must be between 1 and 6
- `--toc`, `--no_toc`, and `--toc_depth` have an effect in the `pandoc` and `pdf`
  modes only
- `--css` applies to the `pandoc` mode only
- `--link_type` is ignored by `--mode github`
- Outside `--mode github`, the selected files must have distinct basenames,
  because the outputs are named after the basename
- `--mode grip_daemon` accepts a single file
- `--daemon` works only with the `pandoc`, `pdf`, and `grip` modes

### Modes and Backends

- Modes:
  - `github`: open the file on GitHub, on the current branch
  - `pandoc`: convert to a standalone HTML with `pandoc`, with MathJax and
    embedded resources
  - `pdf`: convert to PDF with `pandoc` and `xelatex`
  - `grip`: export to HTML with `grip`
  - `grip_daemon`: start `grip` as a server for live preview
- Backends:
  - `global`: run `pandoc` and `grip` installed on the machine
  - `dockerized`: run `pandoc` in the Docker image `pandoc_only`, and `grip`
    through `uvx grip` (without Docker)
- The `pdf` mode needs a LaTeX distribution that provides `xelatex`

### Link Encoding

A link such as `[prd](/docs/prd.md#goal)` is relative to the root of the repo. It
works on GitHub but not in a page opened from disk, where `/docs/prd.md` is the
root of the file system. `--link_type` rewrites these links in the rendered copy
only:

- `local`: `file://` URL of the file in the working tree
- `branch`: GitHub URL of the file on the current branch
- `master`: GitHub URL of the file on the `master` branch

Images, links in fenced code blocks, and links with other targets are not
changed. Targets in a submodule (e.g., `helpers_root`) or behind a symlink are
resolved to the repo that owns them. The `grip_daemon` server uses HTTP, where
the browser blocks `file://` links: use `--link_type branch` or `master` there.

### Environment Variables

- None used directly by the script
- The tools it calls read their own variables (e.g., Docker settings)

## Output & Side Effects

### Files Created

All the files are created in the current dir, one set per input file. The mode
`github` creates no file.

- `tmp.open_md.<stem>.render_images.md`: copy of the input after
  `render_images.py` replaced the diagram code with images, and after the
  links were encoded
  - The commented-out diagram source is removed from this copy
  - The file is left in place after the run
- `tmp.<stem>.html`: output of the `pandoc` mode
- `tmp.<stem>.pdf`: output of the `pdf` mode
- `tmp.<stem>.grip.html`: output of the `grip` mode
- `<html file without .html>.build.js`: build id read by the page to reload
  itself, created only with `--live_reload`

Here `<stem>` is the basename of the input without the last extension, e.g.,
`docs/design.architecture.md` gives `design.architecture`.

The input file is never modified.

### Exit Codes

- `0`: success
- Non-zero: an assertion failed (e.g., no file selected, missing input file,
  invalid `--toc_depth`) or a called tool failed (`pandoc`, `grip`,
  `render_images.py`, `git`)

### Logging

- Logs go to stdout, at `INFO` level by default
- Use `-v DEBUG` to see more details, e.g., the repo root used for the links
- Each external command is logged before it runs

## Software Architecture

### Data Flow

1. **Input**: `_main()` parses the arguments and `_get_files_to_render()` selects
   the files, keeping only `.md` files for the git-based selections
2. **Pre-processing** (all modes but `github`):
   - `_run_render_images()` calls `render_images.py` and removes the commented
     diagram source with `_strip_rendered_source_blocks()`
   - `_encode_links()` rewrites the repo-root links in the processed copy
3. **Rendering**: `_render_file()` dispatches on `--mode` to `pandoc`, `pdf`,
   `grip`, or `grip_daemon`
4. **Post-processing**: with `--live_reload`, `_inject_live_reload()` adds a
   polling script to the HTML
5. **Output**: `_open_file()` opens the result with `open` or `xdg-open`
6. **Daemon**: with `--daemon`, `hdaemon.run_reactive_daemon_mode_multi()` watches
   the files and runs the script again on each changed file, with
   `--skip_open`

### Key Functions

- `_main(parser) -> None`
  - Validates the arguments, then either starts the daemon or renders each file
- `_get_files_to_render(args) -> List[str]`
  - Requires an explicit selection and checks that the basenames are distinct
- `_render_file(args, input_file, style_file) -> None`
  - Calls the renderer of the selected mode
- `_render_with_pandoc(input_file, *, backend, ...) -> None`
  - Runs `pandoc` to HTML with MathJax, embedded resources, the header style,
    and an optional TOC
- `_render_with_pdf(input_file, *, backend, ...) -> None`
  - Runs `pandoc` with `xelatex` and a margin of 1 inch
- `_render_with_grip(input_file, *, backend, ...) -> None`
  - Runs `grip --export` to HTML
- `_render_with_grip_daemon(input_file, *, backend, link_type) -> None`
  - Runs `grip -b`, which serves the page and opens the browser
- `_open_on_github(input_file) -> None`
  - Builds the GitHub URL from the `origin` remote, the current branch, and the
    path relative to the closest `.git` dir (handles subrepos)
- `_encode_links(file_path, input_file, link_type) -> None`
  - Rewrites inline links with a repo-root path, outside fenced blocks
- `_get_toc_depth(args, input_file) -> int`
  - Returns 0 (no TOC) for `--no_toc` or when the file has a `<!-- toc -->`
    marker, unless `--toc` is set
- `_inject_live_reload(html_file) -> None`
  - Adds the reload script before `</head>` and writes the build file last
- `_build_render_cmd(args, input_file) -> str`
  - Builds the command that renders one file, used by the daemon

### Design Patterns

- **Preview on a copy**: all transformations act on the `render_images.py` output,
  so the source file stays intact
- **One script call per file in daemon mode**: the daemon runs this script again
  for the changed file, so the render path is the same as without `--daemon`
- **Reload without a server**: Chrome does not re-read a `file://` page and the
  page cannot `fetch()` local files, but it can load a `<script src>`. The page
  polls the build file every second and reloads when the build id changes
  - The build id is the hash of the page before the injection, so re-rendering
    an unchanged file does not reload the tab
  - The build file is written after the HTML, so the browser never reloads onto a
    half-written page
- **Limits of the daemon**: changes to images, to the `--css` file, or to the
  list of files do not trigger a re-render, and the PDF reload depends on the
  PDF viewer
