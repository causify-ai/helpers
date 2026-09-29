#!/usr/bin/env python3

"""
Run pytest targets or scripts across multiple build configurations.

Executes the same command or pytest target in 3 different build configurations:
- docker: Native docker engine
- apple: Apple engine
- dev_container: Docker container with local stage

For architecture overview, see `pytest_testing_system.README.md`.

# Usage Example

- Run pytest on a specific test file across all builds:
> pytest_multi_build.py --target "helpers/test/test_hunit_test.py"

- Run pytest on all tests in current directory, skipping cache clear:
> pytest_multi_build.py --target "." --no_delete_cache

- Run a custom script across all builds:
> pytest_multi_build.py --script ./pr_test.sh
"""

import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hnotify as hnotify
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hpytest as hpytest
import helpers.htmux as htmux

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--target",
        nargs="+",
        default=[],
        help="pytest targets to run (can be multiple)",
    )
    input_group.add_argument(
        "--script",
        type=str,
        default="",
        help="script to run (e.g., ./pr_test.sh)",
    )
    parser.add_argument(
        "--build_names",
        nargs="+",
        default=[],
        help="build names to run (e.g., docker apple dev_container). "
        "If not provided, runs all builds.",
    )
    parser.add_argument(
        "--no_delete_cache",
        action="store_true",
        help="skip manage_cache.py --action clear_all",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        default="tmp.pytest_multi_build",
        help="Directory storing the per-build log files. Not cleaned up "
        "before starting, so builds can be run piecemeal",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="timeout in seconds for hnotify.notify (default: 10)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _clear_cache() -> None:
    """
    Clear the cache using manage_cache.py.
    """
    _LOG.debug("_clear_cache called")
    _LOG.info("Clearing cache...")
    hsystem.system("manage_cache.py --action clear_all")
    _LOG.debug("cache cleared")


def _restart_docker_if_needed() -> None:
    """
    Restart Docker Desktop if it is hanging, using docker_restart_if_needed.py.
    """
    _LOG.debug("_restart_docker_if_needed called")
    _LOG.info("Checking Docker health...")
    hsystem.system("docker_restart_if_needed.py")
    _LOG.debug("Docker health check done")


def _build_pytest_cmd(targets: List[str]) -> str:
    """
    Build pytest command from targets.

    :param targets: list of pytest targets, e.g.,
        `['helpers/test/test_hunit_test.py', 'helpers/test/test_hio.py']`
    :return: command string to run, e.g.,
        `'pytest_log helpers/test/test_hunit_test.py helpers/test/test_hio.py'`
    """
    _LOG.debug("targets=%s", len(targets))
    targets_str = " ".join(targets)
    opts = "--no_clear_screen"
    cmd = f"pytest_log {opts} {targets_str}".strip()
    _LOG.debug("return=%s", cmd)
    return cmd


def _run_build(
    build_name: str,
    cmd: str,
    build_num: int,
    total_builds: int,
    *,
    output_dir: str = "tmp.pytest_multi_build",
) -> None:
    """
    Run a single build with specified command.

    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :param cmd: Command to run (e.g., 'pytest_log target1 target2' or './script.sh')
    :param build_num: Current build number (1-indexed)
    :param total_builds: Total number of builds to run
    :param output_dir: Directory storing the per-build log file
    """
    _LOG.debug(hprint.to_str("build_name output_dir"))
    output_file = os.path.join(output_dir, f"{build_name}.txt")
    # Print banner showing progress
    banner_msg = f"{build_num}/{total_builds}: Running build '{build_name}' -> '{output_file}'"
    _LOG.info("\n%s", hprint.frame(banner_msg))
    # Build full command with environment setup based on build configuration.
    docker_engine, use_docker_cmd = hpytest.BUILD_CONFIG[build_name]
    if use_docker_cmd:
        opts = "--stage=local -v 1.6.0"
        full_cmd = f'export CSFY_DOCKER_ENGINE="docker"; invoke docker_cmd {opts} --cmd "{cmd}"'
    else:
        full_cmd = f"export CSFY_DOCKER_ENGINE='{docker_engine}'; {cmd}"
    # Run command and capture output.
    _LOG.debug("Executing: %s", full_cmd)
    exit_code = hsystem.system(
        full_cmd,
        suppress_output=False,
        tee=True,
        output_file=output_file,
        abort_on_error=False,
    )
    _LOG.info("Build '%s' completed with exit code %d", build_name, exit_code)


def _summarize_results(build_names: List[str], output_dir: str) -> None:
    """
    Summarize test results by executing pytest_failed_multi_build.py.

    :param build_names: List of build names to summarize
    :param output_dir: Directory storing the per-build log files, passed
        along as `--input_dir` to `pytest_failed_multi_build.py`
    """
    _LOG.debug(hprint.to_str("build_names output_dir"))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pytest_failed_multi_build_script = os.path.join(
        script_dir, "pytest_failed_multi_build.py"
    )
    hdbg.dassert_file_exists(pytest_failed_multi_build_script)
    # Build command to execute pytest_failed_multi_build.py.
    build_names_str = " ".join(build_names)
    cmd = (
        f"{pytest_failed_multi_build_script} --build_names {build_names_str}"
        f" --input_dir {output_dir}"
    )
    _LOG.info("\n%s", hprint.frame("Summarizing test results"))
    _LOG.info("Executing: %s", cmd)
    hsystem.system(cmd, suppress_output=False)


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute pytest across multiple build configurations.
    """
    _LOG.debug("_main called")
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Create the output dir without deleting existing content, so builds can
    # be run piecemeal (e.g., a single build at a time) without losing the
    # logs from previous runs.
    hio.create_dir(args.output_dir, incremental=True)
    # Determine command to execute: either build pytest command from targets or use provided script.
    if args.target:
        cmd = _build_pytest_cmd(args.target)
    else:
        hdbg.dassert_ne(
            args.script, "", "Either --target or --script must be provided"
        )
        cmd = args.script
    _LOG.info("Command to run: %s", cmd)
    # Determine which builds to run.
    if args.build_names:
        build_names = args.build_names
        # Validate that all provided build names are valid.
        hdbg.dassert_is_subset(build_names, hpytest.BUILD_CONFIG.keys())
    else:
        build_names = list(hpytest.BUILD_CONFIG.keys())
    total_builds = len(build_names)
    docker_restarted = False
    for build_num, build_name in enumerate(build_names, 1):
        docker_engine, _ = hpytest.BUILD_CONFIG[build_name]
        if docker_engine == "docker" and not docker_restarted:
            _restart_docker_if_needed()
            docker_restarted = True
        if not args.no_delete_cache:
            _clear_cache()
        _run_build(
            build_name,
            cmd,
            build_num,
            total_builds,
            output_dir=args.output_dir,
        )
    _LOG.info("All builds completed")
    # Summarize results by calling pytest_failed_multi_build.py.
    _summarize_results(build_names, args.output_dir)


if __name__ == "__main__":
    parser = _parse()
    args = parser.parse_args()
    if args.target:
        window_name_str = f"pytest_multi_build: {' '.join(args.target)}"
    else:
        window_name_str = f"pytest_multi_build: {args.script}"
    with htmux.window_name(window_name_str):
        with hnotify.notify(title="pytest_multi_build", timeout=args.timeout):
            _main(parser)
