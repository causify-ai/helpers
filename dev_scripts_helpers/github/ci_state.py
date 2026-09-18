#!/usr/bin/env python3

"""
Print the latest CI workflow status for a branch.

Shows a markdown table with the latest completed run for each GH Actions
workflow: status, time, duration, how long ago it ran, and, for a failed
workflow, the path to a downloaded copy of its failure log.

# Usage Example

- Print the CI state for `master`:
> ci_state.py

- Print the CI state for a feature branch:
> ci_state.py --branch HelpersTask1234_Foo

- Cap each table column to at most 40 chars:
> ci_state.py --max_col_width 40

Import as:

import dev_scripts_helpers.github.ci_state as dshgcist
"""

import argparse
import datetime
import json
import logging
from typing import Any, Dict, List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.htable as htable
import helpers.lib_tasks.lib_tasks_gh as hltltagh

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

# Fetched unfiltered (see `_get_gh_runs()`), so this needs to be large enough
# that, after filtering for `branch` client-side, it still covers workflows
# that run infrequently (e.g., weekly scheduled jobs).
_NUM_RUNS_TO_FETCH = 200
# `gh run list --json` timestamps look like `2026-07-28T22:08:19Z`.
_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


# #############################################################################
# Time formatting
# #############################################################################


def _parse_timestamp(iso_timestamp: str) -> datetime.datetime:
    """
    Parse a GH Actions ISO 8601 timestamp into a UTC `datetime`.

    :param iso_timestamp: e.g., `2026-07-28T22:08:19Z`
    :return: timezone-aware UTC `datetime`
    """
    dt = datetime.datetime.strptime(iso_timestamp, _TIMESTAMP_FORMAT)
    dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def _format_days_ago(dt: datetime.datetime) -> str:
    """
    Format how long ago `dt` was.

    :param dt: timezone-aware UTC `datetime` to compare against now
    :return: relative age in days, e.g., `0 days ago`, `3 days ago`
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    num_days = (now - dt).days
    return f"{num_days} days ago"


# #############################################################################
# GitHub data
# #############################################################################


def _get_gh_runs(branch: str) -> List[Dict[str, Any]]:
    """
    Fetch completed GH Actions runs for `branch`.

    `gh run list --branch=<branch>` filters server-side using a GH search
    index that can lag behind reality: it sometimes returns runs that are
    many days stale instead of the latest ones, even though the same runs
    show up immediately in the unfiltered list. To sidestep that, fetch the
    latest runs across all branches (like `_get_workflow_table()` in
    `helpers/lib_tasks/lib_tasks_gh.py`, used by `invoke gh_watch`, already
    does) and filter for `branch` client-side instead.

    :param branch: name of the branch to fetch the runs for
    :return: completed run objects with `name`, `status`, `conclusion`,
        `databaseId`, `updatedAt`, `createdAt`
    """
    _LOG.debug(hprint.to_str("branch"))
    cmd = [
        "gh run list",
        f"--limit={_NUM_RUNS_TO_FETCH}",
        "--json=name,status,conclusion,databaseId,updatedAt,createdAt,headBranch",
    ]
    cmd = " ".join(cmd)
    _, txt = hsystem.system_to_string(cmd)
    _LOG.debug(hprint.to_str("txt"))
    if not txt:
        return []
    all_runs = json.loads(txt)
    # Filter for completed runs on `branch`.
    runs = [
        run
        for run in all_runs
        if run["status"] == "completed" and run["headBranch"] == branch
    ]
    return runs


def _group_runs_by_workflow(
    runs: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Group runs by workflow name, keeping only the most recent for each.

    :param runs: run objects ordered by recency (as returned by `gh run list`)
    :return: workflow name -> its latest run object
    """
    workflows: Dict[str, Dict[str, Any]] = {}
    for run in runs:
        workflow_name = run["name"]
        if workflow_name not in workflows:
            workflows[workflow_name] = run
    return workflows


# #############################################################################
# Table
# #############################################################################


def _build_table_rows(
    workflows: Dict[str, Dict[str, Any]], branch: str
) -> List[List[str]]:
    """
    Build the CI status table rows, downloading the log for each failure.

    Sharing `hltltagh._download_failed_run_log()` and
    `hltltagh._colorize_status()` with `invoke gh_watch` (i.e.,
    `gh_workflow_list()`) keeps the log file naming convention
    (`tmp.ci_state.<workflow>.<branch>.txt`) and the status colors in one
    place.

    :param workflows: workflow name -> its latest run object
    :param branch: branch the runs belong to, used to name the log files
    :return: table rows, with the header as the first row
    """
    header = ["Workflow", "Status", "Time", "Duration", "Date", "Log"]
    rows = [header]
    for workflow_name in sorted(workflows.keys()):
        run = workflows[workflow_name]
        conclusion = run["conclusion"]
        created_at = _parse_timestamp(run["createdAt"])
        updated_at = _parse_timestamp(run["updatedAt"])
        duration_min = int((updated_at - created_at).total_seconds() / 60)
        # Download the log of a failed run and reference it in the table.
        log_file_name = "-"
        if conclusion == "failure":
            log_file_name = hltltagh._download_failed_run_log(
                str(run["databaseId"]),
                workflow_name,
                branch,
                prefix="ci_state",
            )
            _LOG.info(
                "Downloaded log for '%s' to '%s'", workflow_name, log_file_name
            )
        row = [
            workflow_name,
            hltltagh._colorize_status(conclusion),
            updated_at.strftime("%H:%M"),
            f"{duration_min}m",
            _format_days_ago(updated_at),
            log_file_name,
        ]
        rows.append(row)
    return rows


def _format_table(rows: List[List[str]], *, max_col_width: int = -1) -> str:
    """
    Format `rows` as a markdown table sized to fit each column's content.

    :param rows: table rows, with the header as the first row
    :param max_col_width: max number of chars for a column, see
        `htable.compute_column_widths()`
        - `-1`: no limit
    :return: markdown formatted table
    """
    widths = htable.compute_column_widths(rows, max_width=max_col_width)
    lines = []
    for row_idx, row in enumerate(rows):
        cells = []
        for cell, width in zip(row, widths):
            content_width = width - 2
            # Pad/truncate using the visible length, ignoring ANSI color
            # codes (e.g., from `hltltagh._colorize_status()`), since those
            # don't count towards the rendered width.
            visible_len = len(hprint.remove_non_printable_chars(cell))
            if visible_len > content_width and "\033[" not in cell:
                cell = cell[:content_width]
                visible_len = content_width
            padding = " " * (content_width - visible_len)
            cells.append(f"{cell}{padding}")
        lines.append("| " + " | ".join(cells) + " |")
        if row_idx == 0:
            # Header separator row.
            sep = "|".join("-" * width for width in widths)
            lines.append(f"|{sep}|")
    return "\n".join(lines)


def _print_summary(workflows: Dict[str, Dict[str, Any]]) -> None:
    """
    Print a summary of any failed or cancelled workflows.

    :param workflows: workflow name -> its latest run object
    """
    failed = []
    cancelled = []
    for workflow_name, run in workflows.items():
        conclusion = run["conclusion"]
        if conclusion == "failure":
            failed.append(workflow_name)
        elif conclusion == "cancelled":
            cancelled.append(workflow_name)
    # Print issues if any.
    if failed or cancelled:
        _LOG.info("Issues found:")
        if failed:
            _LOG.info("  Failed: %s", ", ".join(failed))
        if cancelled:
            _LOG.info("  Cancelled: %s", ", ".join(cancelled))


# #############################################################################
# Main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--branch",
        action="store",
        default="master",
        help="Name of the branch to report the CI state for",
    )
    parser.add_argument(
        "--max_col_width",
        action="store",
        type=int,
        default=-1,
        help="Max number of chars for a table column (-1 for no limit)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.debug(hprint.to_str("args.branch args.max_col_width"))
    # Fetch runs from GitHub CLI.
    runs = _get_gh_runs(args.branch)
    _LOG.debug("Fetched %d completed runs", len(runs))
    # Group by workflow, keeping only the latest run for each.
    workflows = _group_runs_by_workflow(runs)
    _LOG.debug("Found %d unique workflows", len(workflows))
    # Build and print the table.
    rows = _build_table_rows(workflows, args.branch)
    table_str = _format_table(rows, max_col_width=args.max_col_width)
    print(table_str)
    # Print summary of issues.
    _print_summary(workflows)


if __name__ == "__main__":
    _main(_parse())
