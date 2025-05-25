# Tool Code Breakdown
<!-- toc -->

- [Tool Dockerized Components Guide](#tool-dockerized-components-guide)

  - [1 · Dockerized Graphviz](#1--dockerized-graphviz)

  - [2 · Dockerized LaTeX](#2--dockerized-latex)

  - [3 · Dockerized Mermaid](#3--dockerized-mermaid)

  - [4 · Dockerized Pandoc](#4--dockerized-pandoc)

  - [5 · Dockerized Prettier](#5--dockerized-prettier)

<!-- tocstop -->

## 1 · Dockerized Graphviz

### What

Converts Graphviz DOT files into PNG images that are later inserted into slides.

### Why

- Removes manual dependency installation across systems.

- Ensures version consistency of Graphviz.

- Provides high-level abstraction and hides complex code.

### How

Two key functions:

- _parse():

  - Creates a parser object for CLI execution.

  - Adds required input and output arguments.

  - Appends Docker and verbosity arguments.

- main():

  - Parses known and unknown arguments.

  - Initializes logger.

  - Calls Graphviz Docker function with:

    - `args.input`

    - `cmd_opts`

    - `args.output`

    - `force_rebuild`

    - `use_sudo`

### Dependency – `run_dockerized_graphviz()` in `hdocker.py`

- Calls `build_container_image()`.

- Converts paths to Docker format.

- Constructs full Docker command string.

- Optionally uses `sudo` for Docker execution.

- Final command is run with `hsystem.system()`.

### Dependency – `build_container_image()`

- Defines the container image.

- Checks for image existence and rebuild flag.

- If needed:

   - Creates temp Dockerfile directory.

   - Constructs Docker command string.

   - Executes via `hsystem.system()`.

---

## 2 · Dockerized LaTeX

### What

Runs LaTeX using `pdflatex` inside Docker to produce PDF output.

### Why

- Provides clean abstraction.

- Hides system-level LaTeX setup complexity.

### How

Two main functions:

- `parser()`:

  - Creates CLI object.

  - Adds file paths and Docker args.

- `main()`:

  - Parses known and unknown args.

  - Initializes logging.

  - Calls `run_basic_latex()`.

### Dependency – `run_basic_latex()` in `hdocker.py`

- Validates file paths and extensions.

- Builds `pdflatex` command string.

- Calls `run_dockerized_latex()` (twice if needed).

- Changes output extension to PDF and moves file if needed.

### Dependency – `run_dockerized_latex()`

1. Sets container image and Dockerfile.
2. Calls `build_container_image()`.
3. Converts paths to Docker format.
4. Prepares param dictionary.
5. Converts all paths in params to Docker format.
6. Ensures input is at command end (bug workaround).
7. Appends `sudo` if needed.
8. Cleans spacing and runs command using `hsystem.system()`.

---

## 3 · Dockerized Mermaid

### What

Runs Mermaid chart/diagram rendering inside Docker.

### How

Acts as a lightweight placeholder for calling `run_dockerized_mermaid()`.

### Dependency – `run_dockerized_mermaid()` in `hdocker.py`

1. Defines the container image.
2. Retrieves input/output paths.
3. Uses sibling container.
4. Converts paths to Docker format.
5. Constructs CLI command.
6. Prepends `sudo` if needed.
7. Executes with `process_docker_cmd()`.

---

## 4 · Dockerized Pandoc

### What

Provides a high-level abstraction for running Pandoc inside Docker.

### How

Two functions:

- `_parse()`:

  - Builds CLI parser.

  - Adds Docker, file path, verbosity options.

- `_main()`:

  - Parses args.

  - Defaults `args.output` if needed.

  - Constructs Pandoc command string.

  - Calls `run_dockerized_pandoc()`.

### Dependency – `run_dockerized_pandoc()` in `hdocker.py`

1. Handles container type:
   - `pandoc_only`: Lightweight.

   - `pandoc_latex`: Custom build with TeXLive.

   - `pandoc_texlive`: Uses texlive/texlive + apt.

2. Builds container.
3. Converts paths.
4. Mounts volumes.
5. Prepares command and arguments.
6. Assembles final Docker command.
7. Executes via `hsystem.system()`.

---

## 5 · Dockerized Prettier

### What

Formats `.md`, `.txt`, `.tex` using Prettier via Docker.

### Why

- Ensures consistent formatting across environments.

- Avoids need to install plugins manually.

### How

Two key functions:

- `_parse()`:

  - Adds input/output, Docker, verbosity args to parser.

- `_main()`:

  - Parses args and logs.

  - Handles empty `cmd_opts`.

  - Calls `run_dockerized_prettier()`.

### Dependency – `run_dockerized_prettier()` in `hdocker.py`

1. Defines container image.
2. Chooses image per `file_type` (`md`, `txt`, `tex`).
3. Uses sibling container.
4. Converts paths to Docker format.
5. If output = input, adds `--write`.
6. Chooses executable based on file type.
7. Constructs bash command with redirection if needed.
8. Builds and executes Docker command.

---