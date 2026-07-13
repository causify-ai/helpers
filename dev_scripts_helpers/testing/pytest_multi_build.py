#!/usr/bin/env python3

"""
Run pytest targets or scripts across multiple build configurations.

Executes the same command or pytest target in 3 different build configurations:
- docker: Native docker engine
- apple: Apple engine
- dev_container: Docker container with local stage

For architecture overview, see `pytest_testing_system.README.md`.

Examples:
> pytest_multi_build.py --target "helpers/test/test_hunit_test.py"
> pytest_multi_build.py --target "." --no_delete_cache
> pytest_multi_build.py --script ./pr_test.sh
"""

import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hpytest as hpytest

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        "--no_delete_cache",
        action="store_true",
        help="skip manage_cache.py --action clear_all",
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
    cmd = f"pytest_log {targets_str}"
    _LOG.debug("return=%s", cmd)
    return cmd


def _run_build(
    build_name: str,
    cmd: str,
    build_num: int,
    total_builds: int,
) -> None:
    """
    Run a single build with specified command.

    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :param cmd: Command to run (e.g., 'pytest_log target1 target2' or './script.sh')
    :param build_num: Current build number (1-indexed)
    :param total_builds: Total number of builds to run
    """
    _LOG.debug("build_name=%s", build_name)
    output_file = f"tmp.pytest_multi_build.{build_name}.txt"
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


def _cleanup_old_files() -> None:
    """
    Clean up old build output files.
    """
    _LOG.debug("_cleanup_old_files called")
    # Remove stale output files from previous runs.
    for build_name in hpytest.BUILD_CONFIG.keys():
        output_file = f"tmp.pytest_multi_build.{build_name}.txt"
        if os.path.exists(output_file):
            _LOG.debug("Removing old file: %s", output_file)
            os.remove(output_file)


def _summarize_results(build_names: List[str]) -> None:
    """
    Summarize test results by executing pytest_failed_multi_build.py.

    :param build_names: List of build names to summarize
    """
    _LOG.debug("_summarize_results called")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pytest_failed_multi_build_script = os.path.join(
        script_dir, "pytest_failed_multi_build.py"
    )
    hdbg.dassert_file_exists(pytest_failed_multi_build_script)
    # Build command to execute pytest_failed_multi_build.py.
    build_names_str = " ".join(build_names)
    cmd = f"{pytest_failed_multi_build_script} --build_names {build_names_str}"
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
    # Clean up old output files from previous runs.
    _cleanup_old_files()
    # Determine command to execute: either build pytest command from targets or use provided script.
    if args.target:
        cmd = _build_pytest_cmd(args.target)
    else:
        hdbg.dassert_ne(
            args.script, "", "Either --target or --script must be provided"
        )
        cmd = args.script
    _LOG.info("Command to run: %s", cmd)
    # Run the same command across all configured build environments.
    build_names = list(hpytest.BUILD_CONFIG.keys())
    total_builds = len(build_names)
    for build_num, build_name in enumerate(build_names, 1):
        if not args.no_delete_cache:
            _clear_cache()
        _run_build(build_name, cmd, build_num, total_builds)
    _LOG.info("All builds completed")
    # Summarize results by calling pytest_failed_multi_build.py.
    _summarize_results(build_names)


if __name__ == "__main__":
    _main(_parse())
