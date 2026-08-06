#!/usr/bin/env python3

"""
Run local CI regression tests on a schedule.

This script runs regression tests for the current directory and helpers
subdirectory, either once or on a daily schedule.

# Usage Example

- Run once immediately, starting at 2am (the default):
> run_local_ci.py --start_time 2am

- Run as a daemon, triggering a run daily at 14:30:
> run_local_ci.py --start_time 14:30 --daemon

- Run once immediately, restricting pytest to the `helpers/test/` dir:
> run_local_ci.py --pytest_target "helpers/test/"

- Run as a daemon over the entire repo, starting at the default time:
> run_local_ci.py --pytest_target "." --daemon

- Run once immediately, skipping the check that the repo is at master:
> run_local_ci.py --no_abort_if_not_master

- Run once immediately, restricting pytest to `helpers/test/` and skipping
  the master branch check:
> run_local_ci.py --pytest_target "helpers/test/" --no_abort_if_not_master
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
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=3600,
                )
        else:
            result = subprocess.run(
                full_cmd,
                shell=True,
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
    target_dir: str, log_file: str, pytest_target: str = "", nice_level: int = 10
) -> bool:
    """
    Run pytest_multi_build.py for regression testing.

    :param target_dir: Directory to test
    :param log_file: File to log output to
    :param pytest_target: pytest target to run (e.g., '.', 'helpers/test/')
    :param nice_level: Nice level for process priority (default: 10)
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
    if nice_level is not None:
        cmd = f"nice -n {nice_level} {cmd}"
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
    target_dir: str,
    *,
    pytest_target: str = "",
    no_abort_if_not_master: bool = False,
    nice_level: int = 10,
    no_clean_check: bool = False,
) -> bool:
    """
    Run full CI pipeline for a target directory.

    :param target_dir: Target directory to run CI for
    :param pytest_target: pytest target to run (e.g., '.', 'helpers/test/')
    :param no_abort_if_not_master: Skip aborting if repository is not at master branch
    :param nice_level: Nice level for process priority (default: 10)
    :param no_clean_check: Skip checking if working directory is clean
    :return: True if all steps succeeded, False otherwise
    """
    _LOG.info("Starting CI run for target='%s'", target_dir)
    # Ensure target directory exists.
    hdbg.dassert_dir_exists(target_dir, "Target directory must exist")
    # Check that we're at master.
    if not no_abort_if_not_master:
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
    if not no_clean_check:
        _LOG.debug("Checking if '%s' has clean working directory", target_dir)
        if not hgit.is_client_clean(target_dir):
            _LOG.error("Working directory not clean in '%s'", target_dir)
            return False
        _LOG.info("Working directory is clean")
    else:
        _LOG.warning("Skipping clean working directory check")
    # Run git pull.
    if not _run_git_pull(target_dir, log_file_pytest):
        _LOG.error("git pull failed in '%s'", target_dir)
        return False
    # Run pytest_multi_build.
    _run_pytest_multi_build(
        target_dir, log_file_pytest, pytest_target, nice_level
    )
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
    pytest_target: str = "",
    no_abort_if_not_master: bool = False,
    repo_dirs: list[str] | None = None,
    nice_level: int = 10,
    no_clean_check: bool = False,
) -> bool:
    """
    Run CI for all target directories.

    :param pytest_target: pytest target to run (e.g., '.', 'helpers/test/')
    :param no_abort_if_not_master: Skip aborting if repository is not at master branch
    :param repo_dirs: List of repo directories to test (if None, auto-discover)
    :param nice_level: Nice level for process priority (default: 10)
    :param no_clean_check: Skip checking if working directory is clean
    :return: True if all targets succeeded, False otherwise
    """
    if repo_dirs is None:
        repo_dirs = _get_target_dirs()
    _LOG.info("Starting full CI run for all targets: %s", repo_dirs)
    all_passed = True
    for target_dir in repo_dirs:
        if not os.path.isdir(target_dir):
            _LOG.warning(
                "Skipping target='%s' (directory does not exist)", target_dir
            )
            continue
        _LOG.info("\n%s", hprint.frame(f"target='{target_dir}'"))
        success = _run_ci_for_target(
            target_dir,
            pytest_target,
            no_abort_if_not_master,
            nice_level,
            no_clean_check,
        )
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
    no_abort_if_not_master: bool = False,
    repo_dirs: list[str] | None = None,
    nice_level: int = 10,
    no_clean_check: bool = False,
) -> None:
    """
    Run CI on a daily schedule at the specified start time.

    :param start_time: Time to run CI each day
    :param pytest_target: pytest target to run (e.g., '.', 'helpers/test/')
    :param no_abort_if_not_master: Skip aborting if repository is not at master branch
    :param repo_dirs: List of repo directories to test (if None, auto-discover)
    :param nice_level: Nice level for process priority (default: 10)
    :param no_clean_check: Skip checking if working directory is clean
    """
    _LOG.info(
        "Running in daemon mode. CI will run daily at %s",
        start_time.strftime("%H:%M"),
    )
    while True:
        if _should_run_now(start_time):
            _LOG.info("Scheduled CI run starting at '%s'", start_time)
            _run_all_ci(
                pytest_target,
                no_abort_if_not_master,
                repo_dirs,
                nice_level,
                no_clean_check,
            )
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
        formatter_class=hparser.CustomHelpFormatter,
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
        "--no_abort_if_not_master",
        action="store_true",
        help="Skip checking if repository is at master branch",
    )
    parser.add_argument(
        "--no_clean_check",
        action="store_true",
        help="Skip checking if working directory is clean",
    )
    parser.add_argument(
        "--repo_dirs",
        type=str,
        nargs="+",
        default=None,
        help="Directories to test (space-separated). If not provided, auto-discovers from git submodules",
    )
    parser.add_argument(
        "--nice",
        type=int,
        default=10,
        help="Nice level for pytest_multi_build process priority (default: 10, range: -20 to 19)",
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
    if args.no_abort_if_not_master:
        _LOG.info("Master branch check is disabled")
    # Log if skipping clean check.
    if args.no_clean_check:
        _LOG.info("Clean directory check is disabled")
    # Log repo directories if specified.
    if args.repo_dirs:
        _LOG.info("Using provided repo_dirs: %s", args.repo_dirs)
    # Log nice level.
    _LOG.info("Nice level: %d", args.nice)
    # Run CI.
    if args.daemon:
        _run_daemon_mode(
            start_time,
            args.pytest_target,
            args.no_abort_if_not_master,
            args.repo_dirs,
            args.nice,
            args.no_clean_check,
        )
    else:
        # Run once immediately.
        _LOG.info("Running CI once (non-daemon mode)")
        success = _run_all_ci(
            args.pytest_target,
            args.no_abort_if_not_master,
            args.repo_dirs,
            args.nice,
            args.no_clean_check,
        )
        exit_code = 0 if success else 1
        sys.exit(exit_code)


if __name__ == "__main__":
    parser = _parse()
    args = parser.parse_args()
    _main(args)
