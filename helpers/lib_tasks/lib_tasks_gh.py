"""
Import as:

import helpers.lib_tasks.lib_tasks_gh as hltltagh
"""

import datetime
import json
import logging
import os
import re
import shlex
import subprocess
from typing import Any, Dict, List, Optional, Set, Tuple

import invoke.exceptions as invexc
from invoke import task

# We want to minimize the dependencies from non-standard Python packages since
# this code needs to run with minimal dependencies and without Docker.
import helpers.hdaemon as hdaemon
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hplayback as hplayba
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.htable as htable
import helpers.lib_tasks.lib_tasks_utils as hltltaut
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)

# Fixture file used by `@hplayba.record` on `_gh_run_and_get_json()` and by the
# `MockDict` replay in unit tests. The path resolves to a location under the
# `helpers` package so the file moves with the repo.
_GH_FIXTURE_FILE = os.path.join(
    os.path.dirname(__file__),
    "test",
    "input",
    "test_lib_tasks_gh",
    "_gh_run_and_get_json.json",
)

# pylint: disable=protected-access

# #############################################################################
# GitHub CLI.
# #############################################################################


@task
def gh_login(  # type: ignore
    ctx,
    account="",
    print_status=False,
):
    hltltaut.report_task()
    if not account:
        # Retrieve the name of the repo, e.g., "alphamatic/amp".
        full_repo_name = hgit.get_repo_full_name_from_dirname(
            ".", include_host_name=False
        )
        _LOG.debug(hprint.to_str("full_repo_name"))
        account = full_repo_name.split("/")[0]
    _LOG.info(hprint.to_str("account"))
    ssh_filename = os.path.expanduser(f"~/.ssh/id_rsa.{account}.github")
    _LOG.debug(hprint.to_str("ssh_filename"))
    if os.path.exists(ssh_filename):
        cmd = f"export GIT_SSH_COMMAND='ssh -i {ssh_filename}'"
        print(cmd)
    else:
        _LOG.warning("Can't find file '%s'", ssh_filename)
    if print_status:
        cmd = "gh auth status"
        hltltaut.run(ctx, cmd)
    github_pat_filename = os.path.expanduser(f"~/.ssh/github_pat.{account}.txt")
    if os.path.exists(github_pat_filename):
        cmd = f"gh auth login --with-token <{github_pat_filename}"
        hltltaut.run(ctx, cmd)
    else:
        _LOG.warning("Can't find file '%s'", github_pat_filename)
    if print_status:
        cmd = "gh auth status"
        hltltaut.run(ctx, cmd)


# #############################################################################


def _get_branch_name(branch_mode: str) -> Optional[str]:
    if branch_mode == "current_branch":
        branch_name: Optional[str] = hgit.get_branch_name()
    elif branch_mode == "master":
        branch_name = "master"
    elif branch_mode == "all":
        branch_name = None
    else:
        raise ValueError(f"Invalid branch='{branch_mode}'")
    return branch_name


def _get_org_name(org_name: str) -> str:
    """
    Get organization name, inferring from current repo if not provided.

    :param org_name: organization name or empty string
    :return: organization name
    """
    if not org_name:
        # Infer organization from current repo.
        full_repo_name = hgit.get_repo_full_name_from_dirname(
            ".", include_host_name=False
        )
        org_name = full_repo_name.split("/")[0]
    return org_name


# #############################################################################
# Latest CI state per workflow.
# #############################################################################


def parse_timestamp(iso_timestamp: str) -> datetime.datetime:
    """
    Parse a GH Actions ISO 8601 timestamp into a UTC `datetime`.

    :param iso_timestamp: timestamp as returned by `gh run list --json`
        - E.g., `2026-07-28T22:08:19Z`
    :return: timezone-aware UTC `datetime`
    """
    dt = datetime.datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    dt = dt.replace(tzinfo=datetime.UTC)
    return dt


def format_days_ago(dt: datetime.datetime) -> str:
    """
    Format how long ago `dt` was.

    :param dt: timezone-aware UTC `datetime` to compare against now
    :return: relative age in days, e.g., `0 days ago`, `3 days ago`
    """
    now = datetime.datetime.now(datetime.UTC)
    num_days = (now - dt).days
    return f"{num_days} days ago"


def fetch_runs(
    *, repo_full_name_with_host: str = "", limit: int = 200
) -> List[Dict[str, Any]]:
    """
    Fetch the most recent GH Actions runs across all the branches.

    The runs are not filtered by branch on the GH side: callers filter on the
    `headBranch` field.

    :param repo_full_name_with_host: e.g., `github.com/causify-ai/helpers`
        - If empty, use the repo that the CWD is in (`gh`'s default)
    :param limit: max number of runs to fetch
        - `gh run list` returns only the 20 most recent runs by default, so the
          runs of a branch (or of a workflow that runs rarely, e.g., a weekly
          job) are missed when other branches have been more active
    :return: run objects ordered newest-first (as returned by `gh`), each with
        the keys `name`, `status`, `conclusion`, `databaseId`, `updatedAt`,
        `createdAt`, `headBranch`
    """
    _LOG.debug(hprint.to_str("repo_full_name_with_host limit"))
    hdbg.dassert_lt(0, limit, "The number of runs to fetch must be positive")
    # Check of the claim "`gh run list --branch=<branch>` can return stale
    # runs", which the old `ci_state.py` script made. Checked on 2026-11-01 for
    # `master` of `causify-ai/helpers`:
    # > gh run list --branch master --limit 20 --json ...
    # > gh run list --limit 200 --json ...
    # Both gave the same newest `master` run for every workflow (e.g.,
    # `Fast tests` 41303654964): the claim was NOT reproduced. The only
    # difference was that the 20-run window of the filtered list was too short
    # to reach the old `Scheduled` run. So a stale server-side filter is not
    # proven. We still fetch unfiltered and filter on `headBranch` in Python
    # (see `get_latest_runs_per_workflow()`), at the cost that the `limit` runs
    # are shared among all the branches.
    cmd = [
        "gh run list",
        f"--limit {limit}",
        "--json=name,status,conclusion,databaseId,updatedAt,createdAt,headBranch",
    ]
    if repo_full_name_with_host:
        cmd.append(f"--repo {repo_full_name_with_host}")
    cmd = " ".join(cmd)
    _, txt = hsystem.system_to_string(cmd)
    _LOG.debug(hprint.to_str("txt"))
    # `gh` prints nothing when there are no runs.
    runs: List[Dict[str, Any]] = json.loads(txt) if txt.strip() else []
    return runs


def group_runs_by_workflow(
    runs: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Group runs by workflow name, keeping only the most recent for each.

    :param runs: run objects ordered newest-first (as returned by
        `fetch_runs()`)
    :return: workflow name -> its newest run object, in the order the
        workflows first appear in `runs`
    """
    workflows: Dict[str, Dict[str, Any]] = {}
    for run in runs:
        workflow_name = run["name"]
        if workflow_name not in workflows:
            workflows[workflow_name] = run
    return workflows


def get_latest_runs_per_workflow(
    branch: str,
    *,
    repo_full_name_with_host: str = "",
    limit: int = 200,
) -> Tuple[Dict[str, Dict[str, Any]], Set[str]]:
    """
    Get the latest completed run of each GH Actions workflow on a branch.

    The verdict of a workflow comes from its latest *completed* run, even when
    a newer run is queued or running. The run can have any conclusion
    (`success`, `failure`, `cancelled`, `skipped`, `startup_failure`, ...): the
    caller decides which ones count as a failure.

    :param branch: name of the branch to report, e.g., `master`
    :param repo_full_name_with_host: see `fetch_runs()`
    :param limit: see `fetch_runs()`
    :return: pair `(latest_runs, in_progress)`
        - `latest_runs`: workflow name -> latest completed run on `branch`,
          ordered newest-first
        - `in_progress`: names of the workflows whose newest run on `branch`
          is not completed yet
            - If the workflow is also in `latest_runs`, a newer run than the
              one in `latest_runs` is in flight
            - If the workflow is not in `latest_runs`, it has no verdict yet
    """
    _LOG.debug(hprint.to_str("branch repo_full_name_with_host limit"))
    hdbg.dassert_ne(branch, "", "A branch name is needed to select the runs")
    runs = fetch_runs(
        repo_full_name_with_host=repo_full_name_with_host, limit=limit
    )
    # Filter on the branch client-side, see `fetch_runs()`.
    runs = [run for run in runs if run["headBranch"] == branch]
    # The verdict comes from the latest completed run of each workflow.
    completed_runs = [run for run in runs if run["status"] == "completed"]
    latest_runs = group_runs_by_workflow(completed_runs)
    # A workflow is in progress when its newest run, completed or not, is not
    # completed.
    newest_runs = group_runs_by_workflow(runs)
    in_progress = {
        workflow_name
        for workflow_name, run in newest_runs.items()
        if run["status"] != "completed"
    }
    _LOG.debug(hprint.to_str("latest_runs in_progress"))
    return latest_runs, in_progress


def get_failed_workflows(latest_runs: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Get the workflows whose latest completed run has `conclusion == "failure"`.

    The conclusions `cancelled`, `skipped` and `startup_failure` do not count
    as a failure.

    :param latest_runs: workflow name -> its latest completed run, as returned
        by `get_latest_runs_per_workflow()`
    :return: sorted names of the failed workflows
    """
    failed = [
        workflow_name
        for workflow_name, run in latest_runs.items()
        if run["conclusion"] == "failure"
    ]
    return sorted(failed)


# #############################################################################
# Failure logs and status formatting.
# #############################################################################


def download_failed_run_log(
    workload_id: str, workflow: str, branch_name: str
) -> str:
    """
    Download the log of a failed GH run to a local file.

    The log is saved to `tmp.failure.<workflow>.<branch>.txt`, which is the name
    that `.claude/skills/pytest.fix_ci_tests/SKILL.md` relies on.

    :param workload_id: GH run id, e.g., `1477484584`
    :param workflow: workflow name, e.g., `Fast tests`
    :param branch_name: name of the branch the run belongs to
    :return: name of the file the log was saved to
    """
    # > gh run view 1477484584 --log-failed
    log_file_name = f"tmp.failure.{workflow}.{branch_name}.txt"
    log_file_name = log_file_name.replace(" ", "_").lower()
    cmd = f"gh run view {workload_id} --log-failed >{log_file_name}"
    hsystem.system(cmd)
    # Remove non-printable chars.
    # TODO(heanh): Consider adding all the helpers util scripts to the `PATH`
    # (when inside the container) so we can just use them without specifying
    # the full path.
    helpers_root_dir = hgit.find_helpers_root()
    file_path = f"{helpers_root_dir}/dev_scripts_helpers/system_tools"
    cmd = f"{file_path}/remove_escape_chars.py -i {log_file_name}"
    hsystem.system(cmd)
    return log_file_name


def download_failure_logs(
    latest_runs: Dict[str, Dict[str, Any]], branch_name: str
) -> Dict[str, str]:
    """
    Download the log of each workflow whose latest completed run failed.

    :param latest_runs: workflow name -> its latest completed run, as returned
        by `get_latest_runs_per_workflow()`
    :param branch_name: name of the branch the runs belong to
    :return: workflow name -> name of the file with its failure log, only for
        the failed workflows
    """
    log_files: Dict[str, str] = {}
    for workflow_name in get_failed_workflows(latest_runs):
        run = latest_runs[workflow_name]
        log_file_name = download_failed_run_log(
            str(run["databaseId"]), workflow_name, branch_name
        )
        _LOG.info(
            "Downloaded log for '%s' to '%s'", workflow_name, log_file_name
        )
        log_files[workflow_name] = log_file_name
    return log_files


# Map a workflow status to the color used to highlight it.
_STATUS_COLOR_MAP = {
    "success": "green",
    "failure": "red",
    "in progress": "yellow",
}


def colorize_status(status: str) -> str:
    """
    Highlight `status` with its color from `_STATUS_COLOR_MAP`.

    :param status: workflow status/conclusion, e.g., `success`, `failure`
    :return: `status` wrapped in ANSI color codes, or unchanged if `status`
        has no entry in `_STATUS_COLOR_MAP`
    """
    if status in _STATUS_COLOR_MAP:
        status = hprint.color_highlight(status, _STATUS_COLOR_MAP[status])
    return status


# #############################################################################
# Tables.
# #############################################################################


def _get_run_time_cells(run: Dict[str, Any]) -> List[str]:
    """
    Get the time, duration and age cells of a run.

    :param run: run object with the keys `createdAt`, `updatedAt`
    :return: cells `[time, duration, age]`, e.g.,
        `["22:08", "12m", "3 days ago"]`
    """
    created_at = parse_timestamp(run["createdAt"])
    updated_at = parse_timestamp(run["updatedAt"])
    duration_min = int((updated_at - created_at).total_seconds() / 60)
    cells = [
        updated_at.strftime("%H:%M"),
        f"{duration_min}m",
        format_days_ago(updated_at),
    ]
    return cells


def build_table_rows(
    latest_runs: Dict[str, Dict[str, Any]],
    in_progress: Set[str],
    log_files: Dict[str, str],
) -> List[List[str]]:
    """
    Build the rows of the table with the latest state of each workflow.

    :param latest_runs: workflow name -> its latest completed run, as returned
        by `get_latest_runs_per_workflow()`
    :param in_progress: workflows with a newer run in progress, as returned by
        `get_latest_runs_per_workflow()`; they get a marker in the status
    :param log_files: workflow name -> failure log file, as returned by
        `download_failure_logs()`
    :return: table rows with the header as the first row, one row per workflow
        sorted by name
    """
    header = ["Workflow", "Status", "Time", "Duration", "Date", "Log"]
    rows = [header]
    for workflow_name in sorted(latest_runs):
        run = latest_runs[workflow_name]
        status = colorize_status(run["conclusion"])
        # The verdict is still the latest completed run, but a newer one is
        # running and can change it.
        if workflow_name in in_progress:
            status += " (newer run in progress)"
        row = [workflow_name, status]
        row += _get_run_time_cells(run)
        row.append(log_files.get(workflow_name, "-"))
        rows.append(row)
    return rows


def build_runs_table_rows(runs: List[Dict[str, Any]]) -> List[List[str]]:
    """
    Build the rows of a table listing every run, with no verdict.

    :param runs: run objects, as returned by `fetch_runs()`
    :return: table rows with the header as the first row, one row per run in
        the order of `runs`
    """
    header = ["Workflow", "Branch", "Status", "Time", "Duration", "Date"]
    rows = [header]
    for run in runs:
        # A run that is not completed has no conclusion yet: show its status.
        status = run["conclusion"] or run["status"].replace("_", " ")
        row = [run["name"], run["headBranch"], colorize_status(status)]
        row += _get_run_time_cells(run)
        rows.append(row)
    return rows


def format_table(rows: List[List[str]], *, max_col_width: int = -1) -> str:
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
            # codes (e.g., from `colorize_status()`), since those don't count
            # towards the rendered width.
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


def print_summary(
    latest_runs: Dict[str, Dict[str, Any]], in_progress: Set[str]
) -> None:
    """
    Print a summary of the workflows that need attention.

    Only `failure` counts as a failure for the exit code, but the other
    non-green conclusions and the workflows without a verdict are reported too.

    :param latest_runs: workflow name -> its latest completed run, as returned
        by `get_latest_runs_per_workflow()`
    :param in_progress: workflows with a newer run in progress, as returned by
        `get_latest_runs_per_workflow()`
    """
    issues = {
        "failure": "Failed",
        "cancelled": "Cancelled",
        "skipped": "Skipped",
        "startup_failure": "Startup failure",
    }
    lines = []
    for conclusion, label in issues.items():
        names = [
            workflow_name
            for workflow_name, run in latest_runs.items()
            if run["conclusion"] == conclusion
        ]
        if names:
            lines.append("  %s: %s" % (label, ", ".join(sorted(names))))
    # A workflow with only runs in progress has no verdict yet.
    no_verdict = sorted(in_progress - set(latest_runs))
    if no_verdict:
        lines.append("  No completed run yet: %s" % ", ".join(no_verdict))
    if lines:
        _LOG.info("Issues found:")
        for line in lines:
            _LOG.info(line)


# #############################################################################
# GH workflow report.
# #############################################################################


def _report_workflow_status(
    ctx: Any,
    *,
    filter_by_branch: str,
    filter_by_completed: str,
    report_only_status: bool,
    show_stack_trace: bool,
    print_table: bool,
    repo_short_name: str,
) -> int:
    """
    Report the status of the GH workflows once.

    See `gh_workflow_list()` for the meaning of the parameters.

    :return: number of workflows whose latest completed run failed, always 0
        when the runs are only listed (no verdict is computed)
    """
    _LOG.debug(
        hprint.to_str(
            "filter_by_branch filter_by_completed report_only_status "
            "show_stack_trace print_table repo_short_name"
        )
    )
    # Login.
    gh_login(ctx)
    repo_full_name_with_host, _ = _get_repo_full_name_from_cmd(repo_short_name)
    # Keep the branch that was asked for in all the messages and in the log file
    # names, even when it is not the current Git branch.
    branch_name = _get_branch_name(filter_by_branch)
    num_failed = 0
    if branch_name is None or not report_only_status:
        # List the runs without a verdict.
        runs = fetch_runs(repo_full_name_with_host=repo_full_name_with_host)
        if branch_name is not None:
            runs = [run for run in runs if run["headBranch"] == branch_name]
        if filter_by_completed != "all":
            runs = [
                run
                for run in runs
                if filter_by_completed in (run["status"], run["conclusion"])
            ]
        if not runs:
            _LOG.warning(
                "No workflow runs found for filter_by_branch=%s "
                "filter_by_completed=%s",
                filter_by_branch,
                filter_by_completed,
            )
        else:
            print(format_table(build_runs_table_rows(runs)))
    else:
        # Get the verdict of each workflow from its latest completed run.
        latest_runs, in_progress = get_latest_runs_per_workflow(
            branch_name, repo_full_name_with_host=repo_full_name_with_host
        )
        if filter_by_completed != "all":
            latest_runs = {
                workflow_name: run
                for workflow_name, run in latest_runs.items()
                if filter_by_completed in (run["status"], run["conclusion"])
            }
        if not latest_runs and not in_progress:
            _LOG.warning(
                "No workflow runs found for filter_by_branch=%s "
                "filter_by_completed=%s",
                filter_by_branch,
                filter_by_completed,
            )
        else:
            log_files = download_failure_logs(latest_runs, branch_name)
            if print_table:
                rows = build_table_rows(latest_runs, in_progress, log_files)
                print(format_table(rows))
            for workflow_name in sorted(latest_runs):
                conclusion = latest_runs[workflow_name]["conclusion"]
                if conclusion == "success":
                    print(
                        f"Workflow '{workflow_name}' for '{branch_name}' is ok"
                    )
                elif conclusion == "failure":
                    _LOG.error(
                        "Workflow '%s' for '%s' is broken",
                        workflow_name,
                        branch_name,
                    )
                    log_file_name = log_files[workflow_name]
                    print(f"# Log is in '{log_file_name}'")
                    # Run_fast_tests  Run fast tests  2021-12-19T00:19:38.3394316Z FAILED data
                    # cmd = rf"grep 'Z FAILED ' {log_file_name}"
                    workflow_as_str = workflow_name.lower().replace(" ", "_")
                    script_name = f"./tmp.pytest_repro.{workflow_as_str}.sh"
                    cmd = f"invoke pytest_repro --file-name {log_file_name} --script-name {script_name}"
                    if show_stack_trace:
                        cmd += " -s"
                    hsystem.system(
                        cmd, suppress_output=False, abort_on_error=False
                    )
                else:
                    # `cancelled`, `skipped` and `startup_failure` give no
                    # verdict: they are shown in the table and the summary.
                    _LOG.debug(
                        "Workflow '%s' for '%s' has conclusion '%s', no verdict",
                        workflow_name,
                        branch_name,
                        conclusion,
                    )
            print_summary(latest_runs, in_progress)
            num_failed = len(get_failed_workflows(latest_runs))
    _LOG.debug(hprint.to_str("num_failed"))
    return num_failed


@task
def gh_workflow_list(  # type: ignore
    ctx,
    filter_by_branch="current_branch",
    filter_by_completed="all",
    report_only_status=True,
    show_stack_trace=False,
    print_table=True,
    daemon=False,
    interval=60,
    repo_short_name="current",
):
    """
    Report the status of the GH workflows.

    The verdict of each workflow comes from its latest completed run. A newer
    run in progress is marked in the table. The task exits with code 1 if the
    latest completed run of a workflow has `conclusion == "failure"`. The
    conclusions `cancelled`, `skipped` and `startup_failure` are shown but do
    not count as a failure.

    :param filter_by_branch: name of the branch to check
        - `current_branch` for the current Git branch
        - `master` for master branch
        - `all` for all branches: list the runs, with no verdict
    :param filter_by_completed: keep only the workflows (or the runs, when
        listing runs) whose status or conclusion has this value
        - E.g., "failure", "success", "completed"
    :param report_only_status: if True, report only the status of the workflows
        - If False, list the runs with no verdict
    :param show_stack_trace: in case of error run `pytest_repro` reporting also
        the stack trace
    :param print_table: if True, print the table with the status of the workflows
    :param daemon: if True, periodically clear the screen and re-run this
        same report every `interval` seconds instead of running once (this
        is what `invoke gh_watch` does)
        - The task never exits in this mode
    :param interval: seconds between periodic runs in daemon mode
    :param repo_short_name: `current` refer to the repo where we are in,
        otherwise a `repo_short_name` (e.g., "amp")
    """
    # `report_task()` prints the name of its caller, so call it here and not
    # from `_report_workflow_status()`.
    hltltaut.report_task(
        txt=hprint.to_str("filter_by_branch filter_by_completed")
    )

    def _report() -> int:
        num_failed = _report_workflow_status(
            ctx,
            filter_by_branch=filter_by_branch,
            filter_by_completed=filter_by_completed,
            report_only_status=report_only_status,
            show_stack_trace=show_stack_trace,
            print_table=print_table,
            repo_short_name=repo_short_name,
        )
        return num_failed

    if daemon:
        # Periodically re-run the report. A failure must not stop the loop, so
        # the number of failures is ignored.
        def _run() -> None:
            subprocess.run("clear", shell=True, check=False)
            _report()

        hdaemon.run_periodic_daemon_mode(
            _run, interval, window_name_str="*GH_WATCH*"
        )
        return
    num_failed = _report()
    if num_failed > 0:
        # Exit with a non-zero code so that a script can gate on it.
        raise invexc.Exit(
            f"{num_failed} workflow(s) failed for '{filter_by_branch}'", code=1
        )


@task
def gh_watch(ctx, *, interval=60):  # type: ignore
    """
    Watch GitHub workflow status with periodic updates.

    Alias of `invoke gh_workflow_list --daemon`. If running in tmux,
    temporarily renames the window to "*GH_WATCH*" for visibility and restores it
    on exit.

    :param interval: Update interval in seconds
    """
    gh_workflow_list(ctx, daemon=True, interval=interval)


@task
def gh_workflow_run(  # type: ignore
    ctx, branch="current_branch", workflows="all", repo_short_name="current"
):
    """
    Run GH workflows in a branch.

    :param repo_short_name: `current` refer to the repo where we are in,
        otherwise a `repo_short_name` (e.g., "amp")
    """
    hltltaut.report_task(txt=hprint.to_str("branch workflows"))
    # Login.
    gh_login(ctx)
    # Get the branch name.
    if branch == "current_branch":
        branch_name = hgit.get_branch_name()
    elif branch == "master":
        branch_name = "master"
    else:
        raise ValueError(f"Invalid branch='{branch}'")
    _LOG.debug(hprint.to_str("branch_name"))
    # Get the workflows.
    if workflows == "all":
        gh_tests = ["fast_tests", "slow_tests"]
    else:
        gh_tests = [workflows]
    _LOG.debug(hprint.to_str("workflows"))
    repo_full_name_with_host, _ = _get_repo_full_name_from_cmd(repo_short_name)
    # Run.
    for gh_test in gh_tests:
        gh_test += ".yml"
        # gh workflow run fast_tests.yml --ref AmpTask1251_Update_GH_actions_for_amp
        cmd = (
            f"gh workflow run {gh_test} --ref {branch_name}"
            f" --repo {repo_full_name_with_host}"
        )
        hltltaut.run(ctx, cmd)


# #############################################################################


# TODO(gp): Remove repo_short_name.
def _get_repo_full_name_from_cmd(repo_short_name: str) -> Tuple[str, str]:
    """
    Convert the `repo_short_name` from command line (e.g., "current", "amp",
    "lm") to the repo_short_name full name without host name.
    """
    repo_full_name_with_host: str = ""
    ret_repo_short_name: str = ""
    if repo_short_name == "current":
        # Get the repo name from the current repo.
        repo_full_name_with_host = hgit.get_repo_full_name_from_dirname(
            ".", include_host_name=True
        )
        hdbg.dassert_eq(
            repo_full_name_with_host,
            hrecouti.get_repo_config().get_repo_full_name_with_hostname(),
        )
        ret_repo_short_name = hrecouti.get_repo_config().get_repo_short_name()
    else:
        hdbg.dfatal("This code path is obsolete")
    _LOG.debug(
        "repo_short_name=%s -> repo_full_name_with_host=%s ret_repo_short_name=%s",
        repo_short_name,
        repo_full_name_with_host,
        ret_repo_short_name,
    )
    return repo_full_name_with_host, ret_repo_short_name


def _dassert_no_duplicate_open_issue(
    repo_full_name_with_host: str, title: str
) -> None:
    """
    Assert that no open issue titled exactly `title` already exists.

    Guards against creating duplicate issues when a caller (e.g.,
    `git_create_issue_and_branch.py`) is re-run after a later step (e.g.,
    branch creation) failed, since a naive retry would otherwise create a
    fresh issue every time instead of reusing the one already created.

    :param repo_full_name_with_host: e.g., "github.com/org/repo"
    :param title: exact issue title to check for
    """
    cmd = (
        "gh issue list"
        + f" --repo {repo_full_name_with_host}"
        + " --state open"
        + " --json number,title"
        + " --limit 200"
    )
    _, output = hsystem.system_to_string(cmd)
    issues = json.loads(output)
    duplicate_ids = [
        str(issue["number"]) for issue in issues if issue["title"] == title
    ]
    hdbg.dassert(
        not duplicate_ids,
        "An open issue titled '%s' already exists: #%s. Pass "
        "--gh_issue_id to reuse it instead of creating a duplicate.",
        title,
        ", #".join(duplicate_ids),
    )


def _get_gh_issue_title(issue_id: int, repo_short_name: str) -> Tuple[str, str]:
    """
    Get the title of a GitHub issue.

    :param repo_short_name: `current` refer to the repo where we are in,
        otherwise a `repo_short_name` (e.g., "amp")
    """
    # TODO(gp): I don't see applications where we need to pass the repo_short_name.
    # One should always operate in the dir corresponding to a repo.
    hdbg.dassert_eq(repo_short_name, "current")
    repo_full_name_with_host, repo_short_name = _get_repo_full_name_from_cmd(
        repo_short_name
    )
    # > (export NO_COLOR=1; gh issue view 1251 --json title)
    # {"title":"Update GH actions for amp"}
    hdbg.dassert_lte(1, issue_id)
    cmd = f"gh issue view {issue_id} --repo {repo_full_name_with_host} --json title,url"
    _, txt = hsystem.system_to_string(cmd)
    _LOG.debug("txt=\n%s", txt)
    # Parse json.
    dict_ = json.loads(txt)
    _LOG.debug("dict_=\n%s", dict_)
    title = dict_["title"]
    _LOG.debug("title=%s", title)
    url = dict_["url"]
    _LOG.debug("url=%s", url)
    # Remove some annoying chars.
    for char in [":", "+", "(", ")", "/", "`", "*"]:
        title = title.replace(char, "")
    # Replace multiple spaces with one.
    title = re.sub(r"\s+", " ", title)
    title = title.replace(" ", "_")
    # Replace problematic branch name chars with underscore.
    for char in [".", "-", "'", "`", '"', ";", "<", ">", "!"]:
        title = title.replace(char, "_")
    # Add the prefix `AmpTaskXYZ_...`
    task_prefix = hrecouti.get_repo_config().get_issue_prefix()
    # task_prefix = hgit.get_task_prefix_from_repo_short_name(repo_short_name)
    _LOG.debug("task_prefix=%s", task_prefix)
    title = f"{task_prefix}{issue_id}_{title}"
    return title, url


@task
def gh_issue_title(ctx, issue_id, repo_short_name="current", pbcopy=True):  # type: ignore
    """
    Print the title that corresponds to the given issue and repo_short_name.
    E.g., AmpTask1251_Update_GH_actions_for_amp.

    Before running the invoke, one must check their login status on GH
    by running `gh auth status`.

    :param issue_id: id number of the issue to create the branch for
    :param repo_short_name: short name of the repo to use for the branch
        name building. "current" refers to the repo where the call is
        implemented
    :param pbcopy: save the result into the system clipboard (only on
        macOS)
    """
    hltltaut.report_task(txt=hprint.to_str("issue_id repo_short_name"))
    # Login.
    gh_login(ctx)
    issue_id = int(issue_id)
    hdbg.dassert_lte(1, issue_id)
    title, url = _get_gh_issue_title(issue_id, repo_short_name)
    # Print or copy to clipboard.
    msg = f"{title}: {url}"
    hsystem.to_pbcopy(msg, pbcopy=pbcopy)


@task
def gh_issue_create(  # type: ignore
    ctx,
    title="",
    body="",
    labels="",
    assignees="",
    project="",
    repo_short_name="current",
    suffix="",
):
    """
    Create a new GitHub issue in the specified repository.

    ```
    # Create a simple issue
    > invoke gh_issue_create --title "Fix bug in parser"

    # Create an issue with body and labels
    > invoke gh_issue_create --title "Add new feature" --body "Description here" --labels "enhancement,priority-high"

    # Create an issue with assignees
    > invoke gh_issue_create --title "Review PR" --assignees "user1,user2"

    # Create an issue and add to a project
    > invoke gh_issue_create --title "Implement feature" --project "Development Board"

    # Create an issue and, in one shot, the first branch (and draft PR) for it,
    # e.g., `AmpTask1234_Fix_bug_in_parser_1`
    > invoke gh_issue_create --title "Fix bug in parser" --suffix 1
    ```

    :param title: title of the issue (required)
    :param body: body/description of the issue
    :param labels: comma-separated list of labels to apply
    :param assignees: comma-separated list of GitHub usernames to assign
    :param project: GitHub project name or number to add the issue to
    :param repo_short_name: `current` refer to the repo where we are in,
        otherwise a `repo_short_name` (e.g., "amp")
    :param suffix: if specified (e.g., "1"), also create the corresponding
        branch (and a draft PR for it) via `git_branch_create`, named
        `<Base>_<suffix>` (e.g., `AmpTask1234_..._1`)
    :return: issue ID (integer) of the created issue
    """
    hltltaut.report_task(txt=hprint.to_str("title repo_short_name"))
    # Login.
    gh_login(ctx)
    hdbg.dassert(title, "Title is required")
    hdbg.dassert_eq(repo_short_name, "current")
    repo_full_name_with_host, repo_short_name = _get_repo_full_name_from_cmd(
        repo_short_name
    )
    # Avoid creating a duplicate issue, e.g., when a caller is re-run after a
    # later step (like branch creation) failed.
    _dassert_no_duplicate_open_issue(repo_full_name_with_host, title)
    _LOG.info(
        "Creating issue with title '%s' in %s",
        title,
        repo_full_name_with_host,
    )
    # Write the body to a temp file and pass it to `gh` via `--body-file`
    # instead of interpolating it inline as `--body "{body}"`: `hsystem.system*`
    # runs the command through a shell, so an inline double-quoted body with
    # backticks or `$(...)` (e.g., a body listing shell commands or code
    # snippets) gets executed as command substitution instead of being passed
    # through literally.
    body_file_name = "tmp.gh_issue_create.body.txt"
    hio.to_file(body_file_name, body)
    try:
        # Build the command.
        cmd = [
            "gh issue create",
            f"--repo {repo_full_name_with_host}",
            f"--title {shlex.quote(title)}",
            f"--body-file {shlex.quote(body_file_name)}",
        ]
        if labels:
            cmd.append(f"--label {shlex.quote(labels)}")
        if assignees:
            cmd.append(f"--assignee {shlex.quote(assignees)}")
        if project:
            cmd.append(f"--project {shlex.quote(project)}")
        cmd = " ".join(cmd)
        # Execute the command and capture output.
        # gh issue create outputs the URL of the created issue, e.g.,
        # https://github.com/cryptokaizen/csfy/issues/7572
        _, output = hsystem.system_to_string(cmd)
    finally:
        os.remove(body_file_name)
    _LOG.debug("gh issue create output: %s", output)
    # Extract the issue ID from the URL.
    # The URL format is: https://github.com/org/repo/issues/123
    match = re.search(r"/issues/(\d+)", output)
    hdbg.dassert(match, f"Could not extract issue ID from output: {output}")
    issue_id = int(match.group(1))
    _LOG.info("Created issue #%s", issue_id)
    if suffix:
        # Also create the corresponding branch (and a draft PR for it).
        # Import locally to avoid a circular import, since
        # `lib_tasks_git.py` imports this module.
        import helpers.lib_tasks.lib_tasks_git as hltltagi

        hltltagi.git_branch_create(
            ctx,
            issue_id=issue_id,
            suffix=suffix,
            repo_short_name=repo_short_name,
        )
    return issue_id


# #############################################################################


def _check_if_pr_exists(title: str) -> bool:
    """
    Return whether a PR exists or not.
    """
    # > gh pr diff AmpTask1955_Lint_20211219
    # no pull requests found for branch "AmpTask1955_Lint_20211219"
    cmd = f"gh pr diff {title}"
    rc = hsystem.system(cmd, abort_on_error=False)
    pr_exists: bool = rc == 0
    return pr_exists


# TODO(ai_gp2): Factor out this in a script.
@task
def gh_create_pr(  # type: ignore
    ctx,
    body="",
    draft=True,
    auto_merge=False,
    repo_short_name="current",
    title="",
    reviewer="",
    labels="",
    assignee="",
    dry_run=False,
):
    """
    Create a draft PR for the current branch in the corresponding
    repo_short_name.

    ```
    # To open a PR in the web browser
    > gh pr view --web

    # To see the status of the checks
    > gh pr checks
    ```

    :param body: the body of the PR
    :param draft: draft or ready-to-review PR
    :param auto_merge: enable auto merging PR
    :param repo_short_name: `current` refer to the repo where we are in,
        otherwise a `repo_short_name` (e.g., "amp")
    :param title: title of the PR or the branch name, if title is empty
    :param reviewer: GitHub username to request review from
    :param labels: comma-separated list of labels to apply
    :param assignee: GitHub username to assign the PR to
    :param dry_run: if True, log the `gh pr create`/`gh pr ready`/
        `gh pr merge` commands without running them
    """
    hltltaut.report_task()
    # Login.
    gh_login(ctx)
    branch_name = hgit.get_branch_name()
    if not title:
        # Use the branch name as title.
        title = branch_name
    repo_full_name_with_host, repo_short_name = _get_repo_full_name_from_cmd(
        repo_short_name
    )
    _LOG.info(
        "Creating PR with title '%s' for '%s' in %s",
        title,
        branch_name,
        repo_full_name_with_host,
    )
    if auto_merge:
        hdbg.dassert(
            not draft, "The PR can't be a draft in order to auto merge it"
        )
    pr_exists = _check_if_pr_exists(title)
    _LOG.debug(hprint.to_str("pr_exists"))
    if pr_exists:
        _LOG.warning("PR '%s' already exists: skipping creation", title)
    else:
        # Link the PR automatically to the branch, if possible.
        issue_id = hgit.extract_gh_issue_number_from_branch(branch_name)
        _LOG.debug(hprint.to_str("issue_id"))
        if issue_id and str(issue_id) not in body:
            body += f"\n\n#{issue_id}"
            _LOG.info("Added issue id %s to the PR body", issue_id)
        # Write the body to a temp file and pass it to `gh` via `--body-file`
        # instead of interpolating it inline as `--body "{body}"`: `ctx.run()`
        # runs the command through a shell, so an inline double-quoted body
        # with backticks or `$(...)` (e.g., a body listing shell commands or
        # code snippets) gets executed as command substitution instead of
        # being passed through literally.
        body_file_name = "tmp.gh_create_pr.body.txt"
        hio.to_file(body_file_name, body)
        try:
            cmd = [
                "gh pr create",
                f"--repo {repo_full_name_with_host}",
                "--draft" if draft else "",
                f"--title {shlex.quote(title)}",
                f"--body-file {shlex.quote(body_file_name)}",
            ]
            if reviewer:
                cmd.append(f"--reviewer {reviewer}")
                _LOG.info("Added reviewer %s to the PR", reviewer)
            if labels:
                cmd.append(f"--label {shlex.quote(labels)}")
                _LOG.info("Added labels %s to the PR", labels)
            if assignee:
                cmd.append(f"--assignee {assignee}")
            cmd = " ".join(part for part in cmd if part)
            # TODO(gp): Use _to_single_line_cmd
            hltltaut.run(ctx, cmd, dry_run=dry_run)
        finally:
            os.remove(body_file_name)
    if auto_merge:
        cmd = f"gh pr ready {title}"
        hltltaut.run(ctx, cmd, dry_run=dry_run)
        cmd = f"gh pr merge {title} --auto --delete-branch --squash"
        hltltaut.run(ctx, cmd, dry_run=dry_run)


# TODO(Grisha): probably the section deserves a separate lib.
# #############################################################################
# Buildmeister dashboard
# #############################################################################


# TODO(Grisha): consider moving to cmamp as we run the workflow from cmamp.
@task
def gh_publish_buildmeister_dashboard_to_s3(  # type: ignore
    ctx, mark_as_latest=True, repo_short_name="current"
):
    """
    Run the buildmeister dashboard notebook and publish it to S3.

    :param mark_as_latest: if True, mark the dashboard as `latest`, otherwise
        just publish a timestamped copy
    :param repo_short_name: `current` refer to the repo where we are in,
        otherwise a `repo_short_name` (e.g., "amp")
    """
    hltltaut.report_task()
    # Resolve the repo (used only for consistency/validation: this task has
    # no other repo-scoped `gh` command to thread it into beyond the login
    # step below).
    _get_repo_full_name_from_cmd(repo_short_name)
    # Login to GH CLI.
    if hserver.is_inside_ci():
        _LOG.info("Skipping login since running inside CI")
    else:
        gh_login(ctx)
    # Run and publish the Buildmeister dashboard Jupyter notebook locally.
    run_notebook_script_path = hgit.find_file_in_git_tree("run_notebook.py")
    amp_abs_path = hgit.get_amp_abs_path()
    notebook_path = os.path.join(
        amp_abs_path, "devops/notebooks/Master_buildmeister_dashboard.ipynb"
    )
    dst_local_dir = os.path.join(amp_abs_path, "tmp.notebooks")
    cmd_run_txt = [
        run_notebook_script_path,
        f"--notebook {notebook_path}",
        # The notebook does not require a config, so using a random dummy config.
        # TODO(Grisha): consider creating a separate config builder for the notebook.
        "--config_builder 'datapull.optima.common.qa.qa_check.build_dummy_data_reconciliation_config()'",
        f"--dst_dir '{dst_local_dir}'",
        "--publish",
        "--num_threads serial",
    ]
    cmd_run_txt = " ".join(cmd_run_txt)
    hsystem.system(cmd_run_txt)
    # To avoid the dependency on `helpers.hs3`.
    import helpers.hs3 as hs3

    # Get HTML file name.
    tmp_local_dir_name = os.path.join(amp_abs_path, "tmp.notebooks")
    pattern = "Master_buildmeister_dashboard.0*.html"
    only_files = True
    use_relative_paths = False
    local_html_files = hio.listdir(
        tmp_local_dir_name,
        pattern,
        only_files=only_files,
        use_relative_paths=use_relative_paths,
    )
    # Assert if more than 1 file is returned.
    hdbg.dassert_eq(
        len(local_html_files),
        1,
        f"Found more than one file in {tmp_local_dir_name} - {local_html_files}",
    )
    local_html_file = local_html_files[0]
    s3_build_path = os.path.join(
        hrecouti.get_repo_config().get_html_bucket_path(),
        "build/buildmeister_dashboard",
    )
    aws_profile = "ck"
    if mark_as_latest:
        # Copy the dashboard notebook to S3 as latest build.
        s3_latest_build_path = os.path.join(
            s3_build_path, "Master_buildmeister_dashboard.latest.html"
        )
        hs3.copy_file_to_s3(local_html_file, s3_latest_build_path, aws_profile)
    # Copy the timestamped version of the dashboard notebook to S3.
    # Need to add a trailing slash to the path to copy the file into the folder.
    # https://docs.python.org/3/library/os.path.html#os.path.join
    s3_build_path_folder = os.path.join(s3_build_path, "")
    hs3.copy_file_to_s3(local_html_file, s3_build_path_folder, aws_profile)


@hplayba.record(_GH_FIXTURE_FILE)
def _gh_run_and_get_json(cmd: str) -> List[Dict[str, Any]]:
    """
    Run a `gh` command and remove colors when running inside a notebook.

    :param cmd: `gh` command to run
    :return: parsed JSON output of a command
    """
    _, _txt = hsystem.system_to_string(cmd)
    if hsystem.is_running_in_ipynb():
        # Remove the colors from the text.
        _txt = re.sub(r"\x1b\[((1;)*[0-9]{2})*m", "", _txt)
    _LOG.debug(hprint.to_str("_txt"))
    ret: List[Dict[str, Any]] = json.loads(_txt)
    return ret


def gh_get_open_prs(repo: str) -> List[Dict[str, Any]]:
    """
    Return a list of open PRs.

    :param repo: repo name in the format "organization/repo", e.g.,
        "cryptokaizen/cmamp"
    """
    cmd = f"gh pr list --state 'open' --json id --repo {repo}"
    pull_requests = _gh_run_and_get_json(cmd)
    return pull_requests


def _get_best_workflow_run(
    workflow_name: str,
    workflow_runs: List[Dict[str, Any]],
    *,
    preferred_event: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Pick the best available workflow run:
    - If `preferred_event` is specified (e.g., "schedule"), try that first.
    - Otherwise, return the most recent success/failure run.

    :param workflow_name: GitHub Actions workflow name
    :param workflow_runs: run metadata, sorted most-recent-first
    :param preferred_event: trigger type to prioritize (e.g., "schedule")
    :return: best-matching run
        e.g.,
        ```
        {
            'conclusion': 'success',
            'status': 'completed',
            'url': 'https://github.com/cryptokaizen/cmamp/actions/runs/8714881296',
            'workflowName': 'Allure fast tests'
        }
    """
    run_status = None
    if preferred_event:
        for run in workflow_runs:
            if run.get("event") == preferred_event and run["conclusion"] in [
                "success",
                "failure",
            ]:
                run_status = run
                break
        if run_status is None:
            _LOG.warning(
                "No '%s' run found for workflow '%s'",
                preferred_event,
                workflow_name,
            )
    if run_status is None:
        for run in workflow_runs:
            if run["conclusion"] in ["success", "failure"]:
                run_status = run
                break
    return run_status


def gh_get_workflows(
    repo_name: str, *, sort: bool = True
) -> List[Dict[str, str]]:
    """
    Get a list of workflows for a given repo.

    :param repo_name: git repo name in the format "organization/repo",
        e.g., "cryptokaizen/cmamp"
    :param sort: if True, sort the list of workflow names
    :return: list of workflows, e.g., [{"id": "12520125", "name": "Fast
        tests"}, {"id": "12520124", "name": "Slow tests"}]
    """
    hdbg.dassert_isinstance(repo_name, str)
    _LOG.debug(hprint.to_str("repo_name"))
    # Get the workflow list.
    cmd = f"gh workflow list --json id,name --repo {repo_name}"
    workflows = _gh_run_and_get_json(cmd)
    workflows = [
        {"id": str(workflow["id"]), "name": workflow["name"]}
        for workflow in workflows
    ]
    # sort workflow by name
    if sort:
        workflows = sorted(workflows, key=lambda workflow: workflow["name"])
    return workflows


def gh_get_workflow_details(
    repo_name: str, workflow_id: str, fields: List[str], limit: int
) -> List[Dict[str, Any]]:
    """
    Return the stats for a given workflow.

    :param repo_name: git repo name in the format "organization/repo",
        e.g., "cryptokaizen/cmamp"
    :param workflow_id: workflow id, e.g., "12520125"
    :param fields: list of fields to return, e.g., ["workflowName", "status"]
    :param limit: number of runs to return
    :return: workflow stats
        Example output:
        ```
        [
            {
                "conclusion": "success",
                "status": "completed",
                "url": "https://github.com/cryptokaizen/cmamp/actions/runs/7757345960",
                "workflowName": "Slow tests"
            }
        ]
        ```
    """
    hdbg.dassert_isinstance(repo_name, str)
    hdbg.dassert_isinstance(workflow_id, str)
    hdbg.dassert_container_type(fields, List, str)
    _LOG.debug(hprint.to_str("repo_name workflow_id fields"))
    # Fetch the latest `limit` runs for status calculation.
    cmd = f"""
    gh run list \
        --json {",".join(fields)} \
        --repo {repo_name} \
        --branch master \
        --limit {limit} \
        --workflow "{workflow_id}"
    """
    workflow_statuses = _gh_run_and_get_json(cmd)
    # We still want to return the statuses even there are less runs than requested. E.g., there is a new workflow with a few runs or there is a workflow that was never run.
    hdbg.dassert_eq(len(workflow_statuses), limit, only_warning=True)
    _LOG.debug("workflow_statuses=\n%s", workflow_statuses)
    return workflow_statuses


def gh_get_details_for_all_workflows(
    repo_list: List[str],
) -> "pd.DataFrame":  # noqa: F821
    """
    Get status for all the workflows.

    :param repo_list: list of repos to get the status for e.g.,
        ["cryptokaizen/cmamp", "cryptokaizen/orange"]
    :return: a table with the status of all the workflows, e.g.,
    ```
    Repo                workflowName       url                                                status
    cryptokaizen/cmamp  Allure fast tests  https://github.com/cryptokaizen/cmamp/actions/...  completed
    cryptokaizen/cmamp  Allure slow tests  https://github.com/cryptokaizen/cmamp/actions/...  completed
    ```
    """
    import pandas as pd

    # TODO(Grisha): expose cols to the interface, i.e. a caller decides what to do.
    gh_cols = ["workflowName", "url", "status", "conclusion", "event"]
    # Import locally in order not to introduce external dependencies to the lib.
    repo_dfs = []
    for repo_name in repo_list:
        # Get all workflows for the given repo.
        workflows = gh_get_workflows(repo_name)
        # For each workflow find the last run.
        for workflow in workflows:
            # Get at least a few runs to compute the status; this is useful when
            # the latest run is not completed, in this case the run before the
            # latest one tells the status for a workflow.
            limit = 10
            workflow_id = workflow["id"]
            workflow_name = workflow["name"]
            workflow_statuses = gh_get_workflow_details(
                repo_name, workflow_id, gh_cols, limit
            )
            if len(workflow_statuses) < limit:
                # TODO(Grisha): should we just insert empty rows as placeholders so that
                # we know that such workflows exist?
                _LOG.warning(
                    "Not enough runs to compute status for '%s', repo '%s', skipping the workflow",
                    workflow_name,
                    repo_name,
                )
                continue
            # Get the latest successful or failed workflow run (prioritize scheduled run if available).
            SCHEDULED_WORKFLOWS = {
                "Gitleaks Scan",
            }
            preferred_event = (
                "schedule" if workflow_name in SCHEDULED_WORKFLOWS else None
            )
            workflow_status = _get_best_workflow_run(
                workflow_name, workflow_statuses, preferred_event=preferred_event
            )
            if workflow_status is None:
                _LOG.warning(
                    "No successful or failed runs found for '%s', repo '%s', skipping the workflow",
                    workflow_name,
                    repo_name,
                )
                continue
            # Access the info of latest workflow run.
            workflow_status = pd.DataFrame([workflow_status])
            workflow_status["repo_name"] = repo_name
            repo_dfs.append(workflow_status)
    # Collect per-repo tables into a single DataFrame.
    df = pd.concat(repo_dfs, ignore_index=True)
    # Rename the columns.
    df = df.drop(columns=["status"])
    df = df.rename(columns={"workflowName": "workflow_name"})
    return df


def gh_get_overall_build_status_for_repo(
    repo_df: "pd.Dataframe",  # noqa: F821
    *,
    use_colors: bool = True,
) -> str:
    """
    Return the overall status of the workflows for a repo.

    :param repo_df: table with the status of the workflows for a repo
    :param use_colors: if True, return the status with colors
    :return: overall status of the build for a repo
    """
    if use_colors:
        hdbg.dassert(
            hsystem.is_running_in_ipynb(),
            msg="The use_colors option is applicable only when running inside a Jupyter notebook",
        )
        # See: https://stackoverflow.com/questions/19746350/how-to-change-color-in-markdown-cells-ipython-jupyter-notebook
        failed_status = '<span style="color:red">Failed</span>'
        success_status = '<span style="color:green">Success</span>'
    else:
        failed_status = "Failed"
        success_status = "Success"
    if "failure" in repo_df["conclusion"].values:
        # The build is failed if at least one workflow is failed.
        overall_status = failed_status
    else:
        overall_status = success_status
    return overall_status


def gh_get_workflow_type_names(
    repo_name: str, *, sort: bool = True
) -> List[str]:
    """
    Get a list of workflow names for a given repo.

    :param repo_name: git repo name in the format "organization/repo",
        e.g., "cryptokaizen/cmamp"
    :param sort: if True, sort the list of workflow names
    :return: list of workflow names, e.g., ["Fast tests", "Slow tests"]
    """
    hdbg.dassert_isinstance(repo_name, str)
    _LOG.debug(hprint.to_str("repo_name"))
    # Get the workflow list.
    cmd = f"gh workflow list --json name --repo {repo_name}"
    workflow_types = _gh_run_and_get_json(cmd)
    workflow_names = [workflow["name"] for workflow in workflow_types]
    if sort:
        workflow_names = sorted(workflow_names)
    # Check for duplicate workflow names.
    hdbg.dassert_no_duplicates(
        workflow_names,
        f"Found duplicate workflow names in repo '{repo_name}'",
    )
    return workflow_names


def gh_get_org_team_names(org_name: str = "", *, sort: bool = True) -> List[str]:
    """
    Get a list of team names for a GitHub organization.

    :param org_name: organization name, e.g., "causify-ai". If empty,
        infers from the current repo
    :param sort: if True, sort team names alphabetically
    :return: list of team names (slugs)
        Example output:
        ```
        ["dev_system", "dev_frontend", "qa_team"]
        ```
    """
    org_name = _get_org_name(org_name)
    _LOG.debug(hprint.to_str("org_name"))
    # Get the team list using GitHub API.
    cmd = f"gh api /orgs/{org_name}/teams --paginate"
    teams_data = _gh_run_and_get_json(cmd)
    # Extract team slugs from the response.
    team_names = [team["slug"] for team in teams_data]
    # Sort team names if requested.
    if sort:
        team_names = sorted(team_names)
    _LOG.debug("Found %s teams for org '%s'", len(team_names), org_name)
    return team_names


def gh_get_team_member_names(team_slug: str, *, org_name: str = "") -> List[str]:
    """
    Get a list of member usernames for a specific team in a GitHub
    organization.

    :param team_slug: team slug (URL-friendly team name), e.g., "dev_system"
    :param org_name: organization name, e.g., "causify-ai". If empty,
        infers from the current repo
    :return: list of member usernames (login names)
        Example output:
        ```
        ["username1", "username2", "username3"]
        ```
    """
    org_name = _get_org_name(org_name)
    hdbg.dassert_isinstance(team_slug, str)
    _LOG.debug(hprint.to_str("org_name team_slug"))
    # Get the team members using GitHub API.
    cmd = f"gh api /orgs/{org_name}/teams/{team_slug}/members --paginate"
    members_data = _gh_run_and_get_json(cmd)
    # Extract usernames from the response.
    usernames = [member["login"] for member in members_data]
    _LOG.debug(
        "Found %s members in team '%s' (org: '%s')",
        len(usernames),
        team_slug,
        org_name,
    )
    return usernames


def make_clickable(url: str) -> str:
    """
    Wrap a URL as an HTML anchor tag.

    :param url: URL to wrap (e.g., "https://github.com/causify-ai/cmamp/actions/...")
    :return: HTML anchor string that makes the URL clickable in rendered Markdown
    """
    anchor = f'<a href="{url}" target="_blank">{url}</a>'
    return anchor


def color_format(val: str, status_color_mapping: Dict[str, str]) -> str:
    """
    Return a background-color style for DataFrame.style.map based on status.

    :param val: value to evaluate for status-based styling (e.g.,
        "success" or "failure")
    :param status_color_mapping: map status strings to color values,
        e.g.: { "success": "green", "failure": "red" }
    :return: CSS string to apply as a style, e.g., "background-color:
        green"
    """
    color = status_color_mapping.get(val, "grey")
    style = f"background-color: {color}"
    return style


def render_repo_workflow_status_table(
    workflow_df: "pd.DataFrame",  # noqa: F821
    status_color_mapping: Dict[str, str],
    timezone: str = "America/New_York",
) -> None:
    """
    Render a dashboard summary of workflow statuses grouped by repo.

    :param workflow_df: data with columns ["repo_name", "workflow_name",
        "conclusion", "url"]
    :param status_color_mapping: color for outcomes {"success": "green",
        "failure": "red"}
    :param timezone: timezone for timestamp display
    """
    import pandas as pd
    from IPython.display import Markdown, display

    workflow_df["url"] = workflow_df["url"].apply(make_clickable)
    repos = workflow_df["repo_name"].unique()
    display(Markdown("## Overall Status"))
    current_timestamp = pd.Timestamp.now(tz=timezone)
    display(Markdown(f"**Last run: {current_timestamp}**"))
    for repo in repos:
        repo_df = workflow_df[workflow_df["repo_name"] == repo]
        overall_status = gh_get_overall_build_status_for_repo(repo_df)
        display(Markdown(f"## {repo}: {overall_status}"))
        repo_df = repo_df.drop(columns=["repo_name"])
        display(
            repo_df.style.map(
                color_format,
                status_color_mapping=status_color_mapping,
                subset=["conclusion"],
            )
        )


def get_workflow_run_ids(
    repo_path: str, workflow_id: str, *, older_than_days: Optional[int] = None
) -> List[str]:
    """
    Get workflow run IDs, optionally filtering by age.

    :param repo_path: repository path in format "org/repo"
    :param workflow_id: GitHub workflow ID
    :param older_than_days: if specified, only return runs older than
        this many days
    :return: list of run IDs
    """
    # See GitHub CLI API documentation: https://cli.github.com/manual/gh_api
    # We use the -q/--jq option to filter results using jq syntax.
    if older_than_days is not None:
        # Use jq to filter runs by age directly in the gh api command.
        # jq date filtering breakdown:
        # - `fromdateiso8601` converts ISO 8601 date to Unix timestamp (seconds since epoch)
        # - `now` returns current Unix timestamp
        # - Days are converted to seconds (days * 86400 seconds/day)
        # - Example: if older_than_days=30, cutoff = now - (30 * 86400)
        #   Only runs where created_at timestamp < cutoff are selected
        cutoff_seconds = older_than_days * 86400
        # Log the cutoff date for debugging.
        cutoff_date = datetime.datetime.now(datetime.UTC) - datetime.timedelta(
            days=older_than_days
        )
        _LOG.debug("Filtering runs created before: %s", cutoff_date.isoformat())
        jq_filter = (
            f".workflow_runs[] | "
            f"select((.created_at | fromdateiso8601) < (now - {cutoff_seconds})) | "
            f".id"
        )
        # WARNING: Using --paginate to fetch all workflow runs can be slow
        # for workflows with a large number of runs (e.g., 1000+ runs).
        # The GitHub API paginates results, and jq filters each page.
        cmd = (
            f"gh api /repos/{repo_path}/actions/workflows/{workflow_id}/runs "
            f"--paginate -q '{jq_filter}'"
        )
    else:
        # Get all run IDs without date filtering.
        # Example API output (one ID per line):
        # 11758293857
        # 11758293856
        # 11758293855
        cmd = (
            f"gh api /repos/{repo_path}/actions/workflows/{workflow_id}/runs "
            "--paginate -q '.workflow_runs[].id'"
        )
    # Execute command and parse output.
    _, run_ids_output = hsystem.system_to_string(cmd)
    run_ids = [
        run_id.strip()
        for run_id in run_ids_output.strip().split("\n")
        if run_id.strip()
    ]
    return run_ids


@task
def gh_delete_workflow_runs(  # type: ignore
    ctx,
    workflow_name,
    older_than_days=None,
    dry_run=False,
    confirmation=True,
    repo_short_name="current",
):
    """
    Delete all workflow runs for a given workflow.

    :param workflow_name: name of the workflow to delete runs for
    :param older_than_days: only delete runs older than this many days
        (optional). If None, delete all runs. Example:
        older_than_days=30 deletes runs created more than 30 days ago
    :param dry_run: if True, show what would be deleted without actually
        deleting
    :param confirmation: if True, prompt user for confirmation before
        deletion (default: True)
    :param repo_short_name: `current` refer to the repo where we are in,
        otherwise a `repo_short_name` (e.g., "amp")
    """
    hltltaut.report_task(
        txt=hprint.to_str("workflow_name older_than_days dry_run confirmation")
    )
    # Convert older_than_days to int if provided (invoke passes strings).
    if older_than_days is not None:
        older_than_days = int(older_than_days)
        hdbg.dassert_lte(1, older_than_days)
    # Login.
    gh_login(ctx)
    repo_full_name_with_host, _ = _get_repo_full_name_from_cmd(repo_short_name)
    # Get workflow ID by name.
    repo_path = repo_full_name_with_host.replace("github.com/", "")
    workflows = gh_get_workflows(repo_path)
    workflow_id = None
    for workflow in workflows:
        if workflow["name"] == workflow_name:
            workflow_id = workflow["id"]
            break
    if not workflow_id:
        available_workflows = [w["name"] for w in workflows]
        raise ValueError(
            f"Workflow '{workflow_name}' not found. "
            f"Available workflows: {available_workflows}"
        )
    _LOG.info("Found workflow '%s' with ID: %s", workflow_name, workflow_id)
    # Get all run IDs for this workflow, optionally filtering by date.
    run_ids = get_workflow_run_ids(
        repo_path, workflow_id, older_than_days=older_than_days
    )
    # Check if any runs were found.
    age_filter_msg = (
        f" older than {older_than_days} days"
        if older_than_days is not None
        else ""
    )
    if not run_ids:
        _LOG.info(
            "No workflow runs%s found for '%s'", age_filter_msg, workflow_name
        )
        return
    _LOG.info("Found %d workflow runs%s to delete", len(run_ids), age_filter_msg)
    # Prompt for confirmation if required.
    if confirmation and not dry_run:
        confirmation_msg = (
            f"\nAre you sure you want to delete {len(run_ids)} workflow run(s)"
            f"{age_filter_msg} for '{workflow_name}'?\n"
            f"Repository: {repo_full_name_with_host}\n"
            f"Type 'yes' or 'y' to confirm: "
        )
        user_input = input(confirmation_msg).strip().lower()
        if user_input not in ("yes", "y"):
            _LOG.info("Deletion cancelled by user")
            return
        _LOG.info("User confirmed deletion, proceeding...")
    # Delete each run.
    deleted_count = 0
    failed_count = 0
    for run_id in run_ids:
        try:
            cmd = f"gh api -X DELETE /repos/{repo_path}/actions/runs/{run_id}"
            _LOG.info("Deleting run %s", run_id)
            hltltaut.run(ctx, cmd, dry_run=dry_run)
            deleted_count += 1
        except (invexc.UnexpectedExit, RuntimeError) as e:
            _LOG.error("Failed to delete run %s: %s", run_id, str(e))
            failed_count += 1
    _LOG.info(
        "Deletion complete: %d successful, %d failed out of %d total runs",
        deleted_count,
        failed_count,
        len(run_ids),
    )


# #############################################################################


@task
def gh_create_mock_fixture(ctx):  # type: ignore
    """
    Record live calls to `_gh_run_and_get_json()` into the test fixture.

    Run this with real GitHub access whenever `gh`'s output schema changes.
    The resulting fixture at `_GH_FIXTURE_FILE` is consumed by the unit
    tests in `test_lib_tasks_gh.py` via `MockDict`, so they run offline.
    The fixture is committed to the repo; the git diff after a refresh is
    the documented schema change.
    """
    hltltaut.report_task()
    gh_login(ctx)
    repo_full_name = hgit.get_repo_full_name_from_dirname(
        ".", include_host_name=False
    )
    _LOG.info("Recording fixture for repo '%s'", repo_full_name)
    with hplayba.recording(_gh_run_and_get_json):
        # Each call below adds one record to the fixture. Keep this in sync
        # with the helpers that unit tests need to mock.
        gh_get_open_prs(repo_full_name)
        gh_get_workflow_type_names(repo_full_name)
        workflows = gh_get_workflows(repo_full_name)
        if workflows:
            gh_get_workflow_details(
                repo_full_name,
                workflows[0]["id"],
                ["conclusion", "status", "url", "workflowName"],
                1,
            )
    _LOG.info("Fixture written to '%s'", _GH_FIXTURE_FILE)


# #############################################################################

# def gh_get_pr_title(pr_url: str) -> str:
# > gh pr view https://github.com/causify-ai/helpers/pull/754 --json title -q .title
# HelpersTask705_Extend_coverage_in_pytest_to_cover_when_we_run_through_system
