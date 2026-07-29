#!/usr/bin/env python3

"""
Run local CI regression tests on a schedule.

This script runs regression tests for the current directory and helpers
subdirectory, either once or on a daily schedule.

Usage:
# TODO(ai_gp): Add a comment for each command line
> run_local_ci.py --start_time 2am
> run_local_ci.py --start_time 14:30 --daemon
> run_local_ci.py --pytest_target "helpers/test/"
> run_local_ci.py --pytest_target "." --daemon
> run_local_ci.py --no_master_check
> run_local_ci.py --pytest_target "helpers/test/" --no_master_check
"""

import argparse
import datetime
import logging
import os
import subprocess
import sys
import time

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


# #############################################################################
# Helper functions
# #############################################################################


def _run_command(
    cmd: str,
    cwd: str,
    *,
    log_file: str = "",
) -> int:
    """
    Run a shell command with optional logging to file.

    :param cmd: Command to execute
    :param cwd: Working directory for command execution
    :param log_file: File to append output to (if provided)
    :return: Exit code from command
    """
    _LOG.debug("Running command: '%s' in dir='%s'", cmd, cwd)
    # Build full command with environment setup.
    full_cmd = f"cd {cwd} && source setenv.sh && {cmd}"
    # Print command with green highlighting.
    print(f"> {hprint.color_highlight(full_cmd, 'green')}")
    # Run command and capture output.
    try:
        if log_file:
            with open(log_file, "a") as f:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"Command: {cmd}\n")
                f.write(f"Time: {datetime.datetime.now().isoformat()}\n")
                f.write(f"{'=' * 80}\n")
                result = subprocess.run(
                    full_cmd,
                    shell=True,
                    cwd=cwd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=3600,
                )
        else:
            result = subprocess.run(
                full_cmd,
                shell=True,
                cwd=cwd,
                capture_output=False,
                text=True,
                timeout=3600,
            )
        return result.returncode
    except Exception as e:
        _LOG.error("Error running command: %s", str(e))
        return -1


def _run_git_clean(target_dir: str, log_file: str) -> bool:
    """
    Run git clean -fd to remove untracked files.

    :param target_dir: Directory to clean
    :param log_file: File to log output to
    :return: True if successful, False otherwise
    """
    _LOG.info("Running 'git clean -fd' in '%s'", target_dir)
    exit_code = _run_command("git clean -fd", target_dir, log_file=log_file)
    return exit_code == 0


def _run_git_pull(target_dir: str, log_file: str) -> bool:
    """
    Run git pull to sync with remote.

    :param target_dir: Directory to sync
    :param log_file: File to log output to
    :return: True if successful, False otherwise
    """
    _LOG.info("Running 'git pull' in '%s' (log_file=%s)", target_dir, log_file)
    exit_code = _run_command("git pull", target_dir, log_file=log_file)
    return exit_code == 0


def _run_pytest_multi_build(
    target_dir: str, log_file: str, pytest_target: str = ""
) -> bool:
    """
    Run pytest_multi_build.py for regression testing.

    :param target_dir: Directory to test
    :param log_file: File to log output to
    :param pytest_target: pytest target to run (e.g., '.', 'helpers/test/')
    :return: True if successful, False otherwise
    """
    _LOG.info(
        "Running 'pytest_multi_build.py' in '%s' (log_file=%s)",
        target_dir,
        log_file,
    )
    if not pytest_target:
        pytest_target = "."
    # --timeout 0 so that it doesn't wait.
    cmd = f"pytest_multi_build.py --target {pytest_target} --build_names apple dev_container --timeout 0"
    exit_code = _run_command(cmd, target_dir, log_file=log_file)
    return exit_code == 0


def _run_pytest_failed_multi_build(target_dir: str, log_file: str) -> bool:
    """
    Run pytest_failed_multi_build.py to summarize failures.

    :param target_dir: Directory to test
    :param log_file: File to log output to
    :return: True if successful, False otherwise
    """
    _LOG.info(
        "Running 'pytest_failed_multi_build.py' in '%s' (log='%s')",
        target_dir,
        log_file,
    )
    exit_code = _run_command(
        "pytest_failed_multi_build.py", target_dir, log_file=log_file
    )
    return exit_code == 0


def _get_log_file_path(target_dir: str, step: str) -> str:
    """
    Get the log file path for a given target directory and step.

    :param target_dir: Target directory (. or helpers)
    :param step: Step name (pytest_multi_build or pytest_failed_multi_build)
    :return: Log file path
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    repo_name = os.path.basename(os.path.abspath(target_dir))
    if repo_name == ".":
        repo_name = "current"
    log_filename = f"local_ci.{step}.{timestamp}.{repo_name}.txt"
    log_path = os.path.join("..", log_filename)
    return log_path


# #############################################################################
# Main CI execution
# #############################################################################


def _run_ci_for_target(
    target_dir: str, pytest_target: str = "", no_master_check: bool = False
) -> bool:
    """
    Run full CI pipeline for a target directory.

    :param target_dir: Target directory to run CI for
    :param pytest_target: pytest target to run (e.g., '.', 'helpers/test/')
    :param no_master_check: Skip checking if repository is at master branch
    :return: True if all steps succeeded, False otherwise
    """
    _LOG.info("Starting CI run for target='%s'", target_dir)
    # Ensure target directory exists.
    hdbg.dassert_dir_exists(target_dir, "Target directory must exist")
    # Check that we're at master.
    if not no_master_check:
        _LOG.debug("Checking if '%s' is at master branch", target_dir)
        branch = hgit.get_branch_name(target_dir)
        if branch != "master":
            _LOG.error(
                "Target '%s' is not at master branch (current: %s)",
                target_dir,
                branch,
            )
            return False
        _LOG.info("Repository is at master branch")
    else:
        _LOG.warning("Skipping master branch check")
    # Get log file paths.
    log_file_pytest = _get_log_file_path(target_dir, "pytest_multi_build")
    log_file_failed = _get_log_file_path(target_dir, "pytest_failed_multi_build")
    # Run git clean.
    if not _run_git_clean(target_dir, log_file_pytest):
        _LOG.error("git clean failed in '%s'", target_dir)
        return False
    # Check working directory is clean.
    _LOG.debug("Checking if '%s' has clean working directory", target_dir)
    if not hgit.is_client_clean(target_dir):
        _LOG.error("Working directory not clean in '%s'", target_dir)
        return False
    _LOG.info("Working directory is clean")
    # Run git pull.
    if not _run_git_pull(target_dir, log_file_pytest):
        _LOG.error("git pull failed in '%s'", target_dir)
        return False
    # Run pytest_multi_build.
    _run_pytest_multi_build(target_dir, log_file_pytest, pytest_target)
    _LOG.info("Test output logged to '%s'", log_file_pytest)
    # Run pytest_failed_multi_build.
    _run_pytest_failed_multi_build(target_dir, log_file_failed)
    _LOG.info("Summary logged to '%s'", log_file_failed)
    _LOG.info("CI run completed for target='%s'", target_dir)
    return True


def _get_target_dirs() -> list[str]:
    """
    Get target directories for regression testing.

    Discovers git subrepos from .gitmodules and includes current dir.

    :return: List of target directories
    """
    # Start with current directory.
    targets = ["."]
    # Add any git submodules.
    submodules = hgit.get_submodule_paths()
    _LOG.debug("Discovered submodules: %s", submodules)
    targets.extend(submodules)
    _LOG.info("Target directories: %s", targets)
    return targets


def _run_all_ci(
    pytest_target: str = "", no_master_check: bool = False, repo_dirs: list[str] | None = None
) -> bool:
    """
    Run CI for all target directories.

    :param pytest_target: pytest target to run (e.g., '.', 'helpers/test/')
    :param no_master_check: Skip checking if repository is at master branch
    :param repo_dirs: List of repo directories to test (if None, auto-discover)
    :return: True if all targets succeeded, False otherwise
    """
    if repo_dirs is None:
        repo_dirs = _get_target_dirs()
    _LOG.info("Starting full CI run for all targets: %s", repo_dirs)
    all_passed = True
    for target_dir in repo_dirs:
        if not os.path.isdir(target_dir):
            _LOG.warning("Skipping target='%s' (directory does not exist)", target_dir)
            continue
        _LOG.info("\n%s", hprint.frame(f"target='{target_dir}'"))
        success = _run_ci_for_target(target_dir, pytest_target, no_master_check)
        if not success:
            all_passed = False
            _LOG.error("CI failed for target='%s'", target_dir)
    return all_passed


# #############################################################################
# Scheduling
# #############################################################################


def _parse_start_time(start_time_str: str) -> datetime.time:
    """
    Parse start time string to datetime.time object.

    Supports formats like "2am", "14:30", "2:00am", etc.

    :param start_time_str: Start time string to parse
    :return: datetime.time object
    """
    start_time_str = start_time_str.lower().strip()
    # Try common formats.
    formats = [
        "%I%p",  # 2am, 3pm
        "%I:%M%p",  # 2:00am, 3:30pm
        "%H:%M",  # 14:30, 2:30
        "%H",  # 14, 2
    ]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(start_time_str, fmt)
            return dt.time()
        except ValueError:
            continue
    # If none of the formats matched, raise an error.
    raise ValueError(
        f"Cannot parse start time '{start_time_str}'. "
        "Use formats like '2am', '14:30', '2:00am'"
    )


def _should_run_now(start_time: datetime.time) -> bool:
    """
    Check if current time matches the scheduled start time.

    :param start_time: Target time to run at
    :return: True if current time is within a minute of start time, False otherwise
    """
    now = datetime.datetime.now().time()
    # Check if we're within 1 minute of the start time.
    start_dt = datetime.datetime.combine(datetime.date.today(), start_time)
    now_dt = datetime.datetime.combine(datetime.date.today(), now)
    time_diff = abs((now_dt - start_dt).total_seconds())
    # Run if within 60 seconds of start time.
    return time_diff < 60


def _run_daemon_mode(
    start_time: datetime.time,
    pytest_target: str = "",
    no_master_check: bool = False,
    repo_dirs: list[str] | None = None,
) -> None:
    """
    Run CI on a daily schedule at the specified start time.

    :param start_time: Time to run CI each day
    :param pytest_target: pytest target to run (e.g., '.', 'helpers/test/')
    :param no_master_check: Skip checking if repository is at master branch
    :param repo_dirs: List of repo directories to test (if None, auto-discover)
    """
    _LOG.info(
        "Running in daemon mode. CI will run daily at %s",
        start_time.strftime("%H:%M"),
    )
    while True:
        if _should_run_now(start_time):
            _LOG.info("Scheduled CI run starting at '%s'", start_time)
            _run_all_ci(pytest_target, no_master_check, repo_dirs)
            # Sleep for a minute to avoid running multiple times.
            time.sleep(60)
        else:
            # Check every 30 seconds.
            time.sleep(30)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Create and return argument parser.

    :return: Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "--start_time",
        type=str,
        default="2am",
        help="Time to run CI (e.g., '2am', '14:30')",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run CI on a daily schedule (without this flag, runs once and exits)",
    )
    parser.add_argument(
        "--pytest_target",
        type=str,
        default="",
        help="pytest target to run (e.g., '.', 'helpers/test/'). If not provided, defaults to '.'",
    )
    parser.add_argument(
        "--no_master_check",
        action="store_true",
        help="Skip checking if repository is at master branch",
    )
    parser.add_argument(
        "--repo_dirs",
        type=str,
        nargs="+",
        default=None,
        help="Directories to test (space-separated). If not provided, auto-discovers from git submodules",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(args: argparse.Namespace) -> None:
    """
    Main entry point for the script.

    :param args: Parsed command line arguments
    """
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Parse start time.
    start_time = _parse_start_time(args.start_time)
    _LOG.info("Parsed start_time as '%s'", start_time.strftime("%H:%M"))
    # Log pytest target if specified.
    if args.pytest_target:
        _LOG.info("pytest_target: '%s'", args.pytest_target)
    # Log if skipping master check.
    if args.no_master_check:
        _LOG.info("Master branch check is disabled")
    # Log repo directories if specified.
    if args.repo_dirs:
        _LOG.info("Using provided repo_dirs: %s", args.repo_dirs)
    # Run CI.
    if args.daemon:
        _run_daemon_mode(start_time, args.pytest_target, args.no_master_check, args.repo_dirs)
    else:
        # Run once immediately.
        _LOG.info("Running CI once (non-daemon mode)")
        success = _run_all_ci(args.pytest_target, args.no_master_check, args.repo_dirs)
        exit_code = 0 if success else 1
        sys.exit(exit_code)


if __name__ == "__main__":
    parser = _parse()
    args = parser.parse_args()
    _main(args)
