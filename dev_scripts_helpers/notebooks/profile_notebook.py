#!/usr/bin/env python

"""
Run a notebook, generate its HTML export, and write per-cell execution time
statistics to a JSON file, to find which cell is slow.

The notebook is executed once, inside Docker via a `docker_cmd.sh` sitting
next to it if one is found, otherwise directly on the host. The HTML export
is rendered from that same executed notebook, without re-running any cell.

# Usage Example

- Profile a tutorial notebook (runs inside Docker if `docker_cmd.sh` sits
  next to it), writing the profile to the default
  `L05_01_01_hoeffding_inequality.profile.json`:
> profile_notebook.py -i msml610/tutorials/L05_statistical_learning/L05_01_01_hoeffding_inequality.ipynb

- Write the profile to a specific file:
> profile_notebook.py -i path/to/notebook.ipynb -o path/to/profile.json

- Print the profile to stdout instead of writing a file:
> profile_notebook.py -i path/to/notebook.ipynb -o -

- Print the commands that would run, without executing the notebook:
> profile_notebook.py -i path/to/notebook.ipynb --dry_run

Import as:

import dev_scripts_helpers.notebooks.profile_notebook as dsnoprno
"""

import argparse
import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional

import nbformat
import pandas as pd

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hselect_input_output as hseinout
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Constants
# #############################################################################


# Disable the per-cell timeout: some notebook cells (e.g., simulations) can
# legitimately run for minutes.
_NO_TIMEOUT = -1
# Timestamp pair that `nbclient` records in `cell.metadata.execution` to
# bracket the wall-clock time a cell took to run.
_START_KEY = "iopub.status.busy"
_END_KEY = "iopub.status.idle"
# Relative path (from the Git root) to the template used to render the HTML
# export, matching `run_nbconvert.sh` / `helpers.hdocker_tests`.
_TEMPLATE_REL_DIR = (
    "helpers_root/dev_scripts_helpers/notebooks/nbconvert_templates"
)
# Number of leading characters of a cell's source kept in the profile.
_SOURCE_PREVIEW_LEN = 200


# #############################################################################
# Helper functions
# #############################################################################


def _get_docker_cmd_script(notebook_dir: str) -> str:
    """
    Return the path to `docker_cmd.sh` next to the notebook, if any.

    :param notebook_dir: directory containing the notebook
    :return: path to `docker_cmd.sh`, or `""` if the notebook is not run
        inside a per-project Docker container
    """
    docker_cmd_script = os.path.join(notebook_dir, "docker_cmd.sh")
    if not os.path.exists(docker_cmd_script):
        docker_cmd_script = ""
    return docker_cmd_script


def _get_container_path(host_path: str, git_root: str) -> str:
    """
    Map a host path under `git_root` to its path inside the container.

    :param host_path: absolute path on the host, inside `git_root`
    :param git_root: absolute path to the Git root, mounted at
        `/git_root` inside the container
    :return: equivalent absolute path inside the container
    """
    rel_path = os.path.relpath(host_path, git_root)
    container_path = f"/git_root/{rel_path}"
    return container_path


def _run_cmd(
    cmd: str, *, docker_cmd_script: str, notebook_dir: str, dry_run: bool
) -> None:
    """
    Run `cmd`, inside Docker via `docker_cmd_script` if one was given.

    :param cmd: shell command to run (built with container-absolute paths
        when `docker_cmd_script` is set)
    :param docker_cmd_script: path to `docker_cmd.sh`, or `""` to run on
        the host directly
    :param notebook_dir: directory to `cd` into before invoking
        `docker_cmd_script`
    :param dry_run: if `True`, print the command instead of running it
    """
    if docker_cmd_script:
        cmd = f"cd {notebook_dir} && bash {docker_cmd_script} '{cmd}'"
    if dry_run:
        _LOG.warning("[DRY_RUN] Would run:\n%s", cmd)
        return
    hsystem.system(cmd, suppress_output=False)


def _execute_notebook(
    notebook_path: str,
    executed_notebook_path: str,
    *,
    docker_cmd_script: str,
    git_root: str,
    dry_run: bool,
) -> None:
    """
    Execute `notebook_path`, saving outputs and per-cell timing metadata to
    `executed_notebook_path`.

    :param notebook_path: path to the source notebook
    :param executed_notebook_path: path where the executed notebook
        (outputs + timing metadata) is saved
    :param docker_cmd_script: path to `docker_cmd.sh`, or `""` to run on
        the host
    :param git_root: absolute path to the Git root
    :param dry_run: if `True`, print the command instead of running it
    """
    notebook_dir = os.path.dirname(notebook_path)
    if docker_cmd_script:
        in_path = _get_container_path(notebook_path, git_root)
        out_path = _get_container_path(executed_notebook_path, git_root)
    else:
        in_path, out_path = notebook_path, executed_notebook_path
    cmd = " ".join(
        [
            "jupyter nbconvert",
            "--execute",
            "--to notebook",
            f"--ExecutePreprocessor.timeout={_NO_TIMEOUT}",
            f"--output {out_path}",
            in_path,
        ]
    )
    _LOG.info("Executing '%s'", notebook_path)
    _run_cmd(
        cmd,
        docker_cmd_script=docker_cmd_script,
        notebook_dir=notebook_dir,
        dry_run=dry_run,
    )


def _convert_to_html(
    executed_notebook_path: str,
    html_path: str,
    *,
    docker_cmd_script: str,
    git_root: str,
    dry_run: bool,
) -> None:
    """
    Render the already-executed `executed_notebook_path` to HTML.

    This does not pass `--execute`, so it only exports the outputs already
    stored in the notebook: no cell is re-run (or re-timed).

    :param executed_notebook_path: path to the notebook with outputs
        already saved
    :param html_path: path to the HTML file to generate
    :param docker_cmd_script: path to `docker_cmd.sh`, or `""` to run on
        the host
    :param git_root: absolute path to the Git root
    :param dry_run: if `True`, print the command instead of running it
    """
    notebook_dir = os.path.dirname(html_path)
    if docker_cmd_script:
        in_path = _get_container_path(executed_notebook_path, git_root)
        out_path = _get_container_path(html_path, git_root)
        template_dir = f"/git_root/{_TEMPLATE_REL_DIR}"
    else:
        in_path, out_path = executed_notebook_path, html_path
        template_dir = os.path.join(git_root, _TEMPLATE_REL_DIR)
    cmd = " ".join(
        [
            "jupyter nbconvert",
            "--to html",
            "--template html_anchorfix",
            f"--TemplateExporter.extra_template_basedirs={template_dir}",
            f"--output {out_path}",
            in_path,
        ]
    )
    _LOG.info("Generating HTML '%s'", html_path)
    _run_cmd(
        cmd,
        docker_cmd_script=docker_cmd_script,
        notebook_dir=notebook_dir,
        dry_run=dry_run,
    )


def _get_cell_duration(cell: Dict[str, Any]) -> Optional[float]:
    """
    Compute a cell's wall-clock execution time from its timing metadata.

    :param cell: notebook cell, as read by `nbformat`
    :return: duration in seconds, or `None` if the cell was not executed
        (e.g., a markdown cell, or a code cell that was skipped)
    """
    execution = cell.get("metadata", {}).get("execution", {})
    start = execution.get(_START_KEY)
    end = execution.get(_END_KEY)
    duration = None
    if start and end:
        start_ts = datetime.datetime.fromisoformat(start)
        end_ts = datetime.datetime.fromisoformat(end)
        duration = (end_ts - start_ts).total_seconds()
    return duration


def _get_cell_rows(executed_notebook_path: str) -> List[Dict[str, Any]]:
    """
    Build a per-cell timing record for an executed notebook, in notebook order.

    :param executed_notebook_path: path to the notebook with outputs and
        timing metadata already saved
    :return: one record per cell, in original notebook order, each with:
        - `cell_index`: 0-based position in the notebook
        - `duration_sec`: wall-clock execution time in seconds, `None` for
          cells with no timing (e.g., markdown)
        - `source_preview`: first `_SOURCE_PREVIEW_LEN` characters of the
          cell's source, verbatim (may contain newlines)
    """
    hdbg.dassert_file_exists(executed_notebook_path)
    nb = nbformat.read(executed_notebook_path, as_version=4)
    rows = []
    for idx, cell in enumerate(nb.cells):
        row = {
            "cell_index": idx,
            "duration_sec": _get_cell_duration(cell),
            "source_preview": cell.get("source", "")[:_SOURCE_PREVIEW_LEN],
        }
        rows.append(row)
    return rows


def _write_json_profile(rows: List[Dict[str, Any]], json_path: str) -> None:
    """
    Write the per-cell profile to `json_path`, or print it if `json_path` is `-`.

    :param rows: per-cell records from `_get_cell_rows()`
    :param json_path: destination JSON file, or `-` to print to stdout
    """
    payload = {"cells": rows}
    if json_path == "-":
        print(json.dumps(payload, indent=2))
    else:
        hio.to_json(json_path, payload)
        _LOG.info("Saved per-cell profile to '%s'", json_path)


def _print_summary(rows: List[Dict[str, Any]], *, top_n: int) -> None:
    """
    Print the slowest cells and the overall execution time.

    :param rows: per-cell records from `_get_cell_rows()`
    :param top_n: number of slowest cells to print; `0` prints all of them
    """
    stats = pd.DataFrame(rows)
    total_duration = stats["duration_sec"].sum()
    num_executed = stats["duration_sec"].notna().sum()
    print(
        f"Total execution time: {total_duration:.1f}s across "
        f"{num_executed} executed cell(s) ({len(stats)} cell(s) total)"
    )
    stats = stats.sort_values(
        "duration_sec", ascending=False, na_position="last"
    )
    to_print = stats if top_n == 0 else stats.head(top_n)
    # Collapse embedded newlines so the table stays aligned; the JSON
    # profile keeps the verbatim source.
    to_print = to_print.assign(
        source_preview=to_print["source_preview"].str.replace(
            "\n", "\\n", regex=False
        )
    )
    print(f"\nSlowest {len(to_print)} cell(s):")
    with pd.option_context("display.max_colwidth", None):
        print(to_print.to_string(index=False))


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    # `-i` is the notebook to profile; `-o` is the JSON profile file (`-`
    # prints it to stdout instead), defaulting to `<notebook>.profile.json`.
    hseinout.add_input_output_args(parser, in_required=True, out_required=False)
    parser.add_argument(
        "--top_n",
        action="store",
        type=int,
        default=10,
        help="Number of slowest cells to print; 0 prints all cells",
    )
    hparser.add_bool_arg(
        parser,
        "generate_html",
        default_value=True,
        help_="Generate the notebook's HTML export",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print the commands instead of running them",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    notebook_path = os.path.abspath(args.input)
    hdbg.dassert_file_exists(notebook_path)
    notebook_dir = os.path.dirname(notebook_path)
    notebook_name = os.path.splitext(os.path.basename(notebook_path))[0]
    git_root = hgit.find_git_root(notebook_dir)
    # Decide whether to run inside Docker.
    docker_cmd_script = _get_docker_cmd_script(notebook_dir)
    if docker_cmd_script:
        _LOG.info(
            "Found '%s': running the notebook inside Docker", docker_cmd_script
        )
    else:
        _LOG.info("No 'docker_cmd.sh' next to the notebook: running on the host")
    # Execute the notebook once, capturing per-cell timing metadata. Use a
    # `tmp.` prefix per the repo convention for debuggable scratch files: no
    # need to clean it up.
    executed_notebook_path = os.path.join(
        notebook_dir, f"tmp.profile_notebook.{notebook_name}.ipynb"
    )
    _execute_notebook(
        notebook_path,
        executed_notebook_path,
        docker_cmd_script=docker_cmd_script,
        git_root=git_root,
        dry_run=args.dry_run,
    )
    # Export the already-executed notebook to HTML, without re-running it.
    if args.generate_html:
        html_path = os.path.join(notebook_dir, f"{notebook_name}.html")
        _convert_to_html(
            executed_notebook_path,
            html_path,
            docker_cmd_script=docker_cmd_script,
            git_root=git_root,
            dry_run=args.dry_run,
        )
    # Write the per-cell timing profile.
    if args.dry_run:
        _LOG.warning(
            "[DRY_RUN] Skipping the profile: the notebook was not executed"
        )
        return
    json_path = args.output or os.path.join(
        notebook_dir, f"{notebook_name}.profile.json"
    )
    rows = _get_cell_rows(executed_notebook_path)
    _write_json_profile(rows, json_path)
    _print_summary(rows, top_n=args.top_n)


if __name__ == "__main__":
    _main(_parse())
