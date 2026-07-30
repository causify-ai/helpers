#!/usr/bin/env python3
"""
Print the last completed CI workflow status for master branch.

Shows a table with the latest completed test for each workflow, including
the workflow name, conclusion status (success/failure/cancelled), and when
it was last updated.

Usage:
    > print_master_ci_state.py
"""

import json
import logging
import subprocess
# TODO(ai_gp): Use `import datetime` and not the `from ... import`
from datetime import datetime
from typing import Any, Dict, List

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_BRANCH = "master"
_NUM_RUNS_TO_FETCH = 50
# ANSI color codes for terminal output.
_COLOR_GREEN = "\033[92m"
_COLOR_RED = "\033[91m"
_COLOR_YELLOW = "\033[93m"
_COLOR_GRAY = "\033[90m"
_COLOR_RESET = "\033[0m"
_STATUS_COLORS = {
    "success": _COLOR_GREEN,
    "failure": _COLOR_RED,
    "cancelled": _COLOR_YELLOW,
    "skipped": _COLOR_GRAY,
}

# #############################################################################
# Helper functions
# #############################################################################


def _get_gh_runs() -> List[Dict[str, Any]]:
    """
    Fetch GitHub Actions runs for master branch.

    Retrieves completed runs from the GitHub CLI and filters for the
    master branch.

    :return: List of completed GitHub run objects with fields:
        `name`, `status`, `conclusion`, `updatedAt`, `createdAt`
    """
    # Use subprocess with list args to avoid shell escaping issues.
    cmd = [
        "gh",
        "run",
        "list",
        f"--branch={_BRANCH}",
        f"--limit={_NUM_RUNS_TO_FETCH}",
        "--json=name,status,conclusion,updatedAt,createdAt",
    ]
    _LOG.debug("Running gh run list for branch='%s'", _BRANCH)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    hdbg.dassert_eq(
        result.returncode,
        0,
        "Failed to fetch GitHub runs",
    )
    # Parse JSON output.
    output = result.stdout.strip()
    if not output:
        return []
    all_runs = json.loads(output)
    # Filter for completed runs.
    runs = [r for r in all_runs if r["status"] == "completed"]
    return runs


def _group_runs_by_workflow(
    runs: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Group runs by workflow name, keeping only the most recent for each.

    Filters for the latest (most recent) completed run for each workflow.

    :param runs: List of GitHub run objects ordered by recency
    :return: Dict mapping workflow name to its latest run object
    """
    workflows = {}
    for run in runs:
        workflow_name = run["name"]
        if workflow_name not in workflows:
            workflows[workflow_name] = run
    return workflows


def _extract_time(iso_timestamp: str) -> str:
    """
    Extract HH:MM time from ISO timestamp.

    :param iso_timestamp: ISO 8601 timestamp (e.g., '2026-07-28T22:08:19Z')
    :return: Time in HH:MM format
    """
    time_part = iso_timestamp.split("T")[1].split("Z")[0]
    return time_part[:5]


def _compute_duration_minutes(created_at: str, updated_at: str) -> int:
    """
    Compute duration in minutes between two ISO timestamps.

    :param created_at: ISO 8601 start timestamp
    :param updated_at: ISO 8601 end timestamp
    :return: Duration in minutes
    """
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    created = datetime.strptime(created_at, fmt)
    updated = datetime.strptime(updated_at, fmt)
    delta = updated - created
    return int(delta.total_seconds() / 60)


def _format_table(
    workflows: Dict[str, Dict[str, Any]],
) -> List[str]:
    """
    Format workflow data as a table with headers and rows.

    Creates a markdown table showing workflow name, conclusion status,
    last update time, and duration for each workflow.

    :param workflows: Dict mapping workflow name to run object
    :return: List of formatted table lines (header, separator, rows)
    """
    lines = []
    # Header.
    lines.append("| Workflow | Status | Time | Duration |")
    lines.append("|----------|--------|------|----------|")
    # Sort by workflow name for consistency.
    for workflow_name in sorted(workflows.keys()):
        run = workflows[workflow_name]
        conclusion = run["conclusion"]
        updated_at = run["updatedAt"]
        created_at = run["createdAt"]
        # Extract time and compute duration.
        time_hm = _extract_time(updated_at)
        duration_min = _compute_duration_minutes(created_at, updated_at)
        # Format conclusion with color.
        color = _STATUS_COLORS.get(conclusion, _COLOR_RESET)
        status_str = f"{color}{conclusion}{_COLOR_RESET}"
        # Format row.
        row = f"| {workflow_name} | {status_str} | {time_hm} | {duration_min}m |"
        lines.append(row)
    return lines


def _print_summary(workflows: Dict[str, Dict[str, Any]]) -> None:
    """
    Print a summary of any failed or cancelled workflows.

    Identifies and lists workflows that did not complete successfully.

    :param workflows: Dict mapping workflow name to run object
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


def main() -> None:
    """
    Print the latest CI state for master branch.

    Fetches GitHub Actions workflow runs, groups them by workflow name,
    and displays a formatted table of the latest status for each.
    """
    hdbg.init_logger(use_exec_path=True)
    _LOG.debug("Fetching GitHub Actions runs for '%s'", _BRANCH)
    # Fetch runs from GitHub CLI.
    runs = _get_gh_runs()
    _LOG.debug("Fetched %d completed runs", len(runs))
    # Group by workflow, keeping only latest for each.
    workflows = _group_runs_by_workflow(runs)
    _LOG.debug("Found %d unique workflows", len(workflows))
    # Format and print table.
    table_lines = _format_table(workflows)
    for line in table_lines:
        print(line)
    # Print summary of issues.
    _print_summary(workflows)


if __name__ == "__main__":
    main()
