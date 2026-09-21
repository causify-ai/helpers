#!/usr/bin/env python
r"""
Execute notebooks top to bottom and convert them to HTML inside Docker.

Each notebook runs in the container defined by the `docker_cmd.sh` and
`docker_name.sh` files in the dir of the notebook, since each tutorial dir has
its own Docker setup. The HTML is written next to the notebook and uses the
`html_anchorfix` template so that section anchors work.

`--execute` re-runs every cell instead of reusing the outputs saved in the
`.ipynb` file, so this verifies that a notebook still runs end-to-end.

Each cell has a timeout (`--cell_timeout`, 300 seconds by default) so that a
hung kernel fails with the name of the stuck cell instead of blocking forever.
Use `--cell_timeout -1` to disable the timeout.

`--progress` prints one line per executed cell (e.g., `cell 5/37: <first line
of the cell>`) instead of staying silent until the notebook is done.

For config-driven runs on the host use `run_notebook.py`.

# Usage Example

- Execute a notebook and convert it to HTML:
> run_nbconvert.py \
    -i msml610/tutorials/L03_knowledge_representation/L03_01_entailment_implication_inference.ipynb

- Execute several notebooks, one after the other:
> run_nbconvert.py \
    --files msml610/tutorials/L03_knowledge_representation/L03_01_entailment_implication_inference.ipynb,msml610/tutorials/L03_knowledge_representation/L03_02_wumpus_world.ipynb

- Show which cell is running, allowing 10 minutes per cell:
> run_nbconvert.py -i L03_01_entailment_implication_inference.ipynb \
    --progress --cell_timeout 600

- Show the commands without running them:
> run_nbconvert.py -i L03_01_entailment_implication_inference.ipynb --dry_run

Import as:

import dev_scripts_helpers.notebooks.run_nbconvert as dsnorunb
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hselect_input_output as hseinout
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Name of the nbconvert template that gives working section anchors.
_TEMPLATE_NAME = "html_anchorfix"

# Default time limit in seconds for a single cell.
_DEFAULT_CELL_TIMEOUT = 300

# `awk` filter that turns the `nbconvert` DEBUG log into one line per cell.
# `nbclient` logs `Executing cell:` followed by the source of the cell, so:
# - Print the counter and the first line of the source and skip the rest of the
#   source
# - Drop the other DEBUG lines (all start with `[NbConvertApp]`), except the
#   ones that report the start, the end, or a problem
# - Pass through everything else (e.g., the error of a failed cell)
# `fflush()` is needed since `awk` buffers its output when writing to a pipe.
_PROGRESS_AWK = r"""
/^\[NbConvertApp\] Executing cell:$/ {
    n++
    getline first
    printf "[NbConvertApp] cell %d/%d: %s\n", n, TOTAL, first
    fflush()
    skip = 1
    next
}
/^\[NbConvertApp\] / {
    skip = 0
    if ($0 ~ /^\[NbConvertApp\] (Converting notebook|Writing [0-9]+ bytes|Executing notebook|WARNING \||ERROR \||CRITICAL \|)/) {
        print
        fflush()
    }
    next
}
skip { next }
{ print; fflush() }
"""


# #############################################################################
# Docker path helpers
# #############################################################################


def _get_docker_git_root(notebook_dir: str) -> str:
    """
    Return the git root that `docker_cmd.sh` mounts at `/git_root`.

    `docker_cmd.sh` mounts the output of `git rev-parse --show-toplevel` run
    from the notebook dir, i.e., the root of the innermost repo. This is not the
    super module root returned by `hgit.find_git_root()`, so use the same
    definition to translate the host paths into container paths.

    :param notebook_dir: dir of the notebook
    :return: absolute path of the git root
    """
    _LOG.debug(hprint.to_str("notebook_dir"))
    cmd = f"cd {notebook_dir} && git rev-parse --show-toplevel"
    _, git_root = hsystem.system_to_one_line(cmd)
    git_root = os.path.realpath(git_root)
    _LOG.debug("return=%s", git_root)
    return git_root


def _to_container_path(path: str, git_root: str) -> str:
    """
    Translate a host path into the path seen inside the Docker container.

    Only the git root is mounted in the container, so a path outside of it is
    not visible there.

    :param path: absolute host path
        - E.g., `/home/user/repo/tutorials/L01`
    :param git_root: absolute path of the git root mounted in the container
        - E.g., `/home/user/repo`
    :return: path inside the container
        - E.g., `/git_root/tutorials/L01`
    """
    _LOG.debug(hprint.to_str("path git_root"))
    rel_path = os.path.relpath(path, git_root)
    hdbg.dassert_ne(
        rel_path.split(os.sep)[0],
        "..",
        "Path '%s' is outside of the git root '%s' mounted in the container",
        path,
        git_root,
    )
    # Use `normpath()` so that the git root itself maps to `/git_root`.
    container_path = os.path.normpath(os.path.join("/git_root", rel_path))
    _LOG.debug("return=%s", container_path)
    return container_path


# #############################################################################
# Command building
# #############################################################################


def _build_nbconvert_cmd(
    notebook_file: str,
    *,
    template_base_dir: str,
    git_root: str,
    cell_timeout: int = _DEFAULT_CELL_TIMEOUT,
    progress: bool = False,
) -> str:
    """
    Build the `jupyter nbconvert` command to run inside the container.

    :param notebook_file: absolute host path of the notebook
    :param template_base_dir: absolute host path of the dir containing the
        `html_anchorfix` template
    :param git_root: absolute host path of the git root mounted in the
        container
    :param cell_timeout: max seconds for a single cell, or -1 for no limit
    :param progress: log each executed cell (DEBUG level of `nbconvert`)
    :return: shell command to run in the container
    """
    _LOG.debug(
        hprint.to_str(
            "notebook_file template_base_dir git_root cell_timeout progress"
        )
    )
    hdbg.dassert(
        cell_timeout == -1 or cell_timeout > 0,
        "`cell_timeout` must be positive or -1, got %s",
        cell_timeout,
    )
    notebook_dir = os.path.dirname(notebook_file)
    notebook_name = os.path.basename(notebook_file)
    container_notebook_dir = _to_container_path(notebook_dir, git_root)
    container_template_dir = _to_container_path(template_base_dir, git_root)
    # `cd` into the notebook dir first: `docker_cmd.sh` does not start the
    # container there, so a relative notebook name would match no files.
    # `--ExecutePreprocessor.timeout` is per cell: without it a hung kernel
    # blocks forever. `-1` disables it.
    cmd = [
        f"cd {container_notebook_dir} &&",
        "jupyter nbconvert",
        "--execute",
        "--to html",
    ]
    if progress:
        # `nbclient` logs the source of each cell it executes at DEBUG level.
        cmd.append("--log-level=DEBUG")
    cmd.extend(
        [
            f"--ExecutePreprocessor.timeout={cell_timeout}",
            f"--template {_TEMPLATE_NAME}",
            f"--TemplateExporter.extra_template_basedirs={container_template_dir}",
            notebook_name,
        ]
    )
    cmd = " ".join(cmd)
    # `docker_cmd.sh` wraps the command in single quotes, so a quote inside it
    # would silently end the string early.
    hdbg.dassert_not_in(
        "'", cmd, "The command cannot contain single quotes: %s", cmd
    )
    _LOG.debug("return=%s", cmd)
    return cmd


def _count_executed_cells(notebook_file: str) -> int:
    """
    Count the cells that `nbclient` executes.

    `nbclient` skips markdown cells and code cells with an empty source.

    :param notebook_file: path to the `.ipynb` file
    :return: number of cells that log `Executing cell:`
    """
    _LOG.debug(hprint.to_str("notebook_file"))
    notebook = hio.from_json(notebook_file)
    cells = notebook.get("cells", [])
    num_cells = sum(
        1
        for cell in cells
        if cell["cell_type"] == "code" and "".join(cell["source"]).strip()
    )
    _LOG.debug("return=%s", num_cells)
    return num_cells


def _build_progress_filter(num_cells: int) -> str:
    """
    Build the shell filter that reduces the `nbconvert` log to a line per cell.

    :param num_cells: total number of executed cells, used for the counter
    :return: shell command reading the log from stdin
    """
    _LOG.debug(hprint.to_str("num_cells"))
    hdbg.dassert_lte(0, num_cells)
    hdbg.dassert_not_in("'", _PROGRESS_AWK)
    cmd = f"awk -v TOTAL={num_cells} '{_PROGRESS_AWK}'"
    return cmd


# #############################################################################
# Notebook execution
# #############################################################################


def _run_notebook_in_docker(
    notebook_file: str,
    template_base_dir: str,
    cell_timeout: int,
    progress: bool,
    dry_run: bool,
) -> None:
    """
    Execute a notebook and convert it to HTML in its own Docker container.

    :param notebook_file: path to the `.ipynb` file
    :param template_base_dir: absolute path of the dir containing the
        `html_anchorfix` template
    :param cell_timeout: max seconds for a single cell, or -1 for no limit
    :param progress: if True, print one line per executed cell
    :param dry_run: if True, show the command without running it
    """
    _LOG.debug(
        hprint.to_str(
            "notebook_file template_base_dir cell_timeout progress dry_run"
        )
    )
    hdbg.dassert_file_extension(notebook_file, "ipynb")
    # Resolve symlinks so that the dir matches what `git` reports.
    notebook_dir = os.path.realpath(os.path.dirname(notebook_file))
    notebook_file = os.path.join(notebook_dir, os.path.basename(notebook_file))
    # Each tutorial dir has its own Docker setup.
    docker_cmd_script = os.path.join(notebook_dir, "docker_cmd.sh")
    hdbg.dassert_file_exists(
        docker_cmd_script, "Notebook dir needs its own `docker_cmd.sh`"
    )
    # Build the command to run inside the container.
    git_root = _get_docker_git_root(notebook_dir)
    nbconvert_cmd = _build_nbconvert_cmd(
        notebook_file,
        template_base_dir=template_base_dir,
        git_root=git_root,
        cell_timeout=cell_timeout,
        progress=progress,
    )
    # Run from the notebook dir so that `docker_cmd.sh` finds the right git root
    # and `docker_name.sh`.
    # Read stdin from `/dev/null`: `docker_cmd.sh` attaches stdin to the
    # container (`container run -i`), and with a live stdin (e.g., a terminal)
    # the notebook hangs at a random cell, with `nbconvert` and the kernel both
    # idle, so even the cell timeout does not always fire.
    cmd = (
        f"cd {notebook_dir} && "
        f"bash {docker_cmd_script} '{nbconvert_cmd}' < /dev/null"
    )
    if progress:
        # `nbconvert` logs to stderr, so merge it into the pipe. `pipefail`
        # keeps the exit code of the notebook run instead of the one of `awk`.
        num_cells = _count_executed_cells(notebook_file)
        progress_filter = _build_progress_filter(num_cells)
        cmd = f"set -o pipefail; {cmd} 2>&1 | {progress_filter}"
    _LOG.info("Running notebook '%s'", notebook_file)
    # Show the output while the notebook runs since it can take minutes.
    hsystem.system(cmd, suppress_output=False, dry_run=dry_run)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hseinout.add_multi_file_args(parser)
    parser.add_argument(
        "--cell_timeout",
        type=int,
        default=_DEFAULT_CELL_TIMEOUT,
        help="Max seconds for a single cell before failing, -1 for no limit",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Print one line per executed cell instead of staying silent",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    notebook_files = hseinout.parse_multi_file_args(args)
    # `extra_template_basedirs` wants the dir holding the template dir.
    template_dir = hgit.find_file_in_git_tree(_TEMPLATE_NAME)
    template_base_dir = os.path.dirname(template_dir)
    # Run the notebooks one at a time: `docker_cmd.sh` names the container after
    # the image, so two concurrent runs would collide.
    for notebook_file in notebook_files:
        _run_notebook_in_docker(
            notebook_file,
            template_base_dir,
            args.cell_timeout,
            args.progress,
            args.dry_run,
        )


if __name__ == "__main__":
    _main(_parse())
