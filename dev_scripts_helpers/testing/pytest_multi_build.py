#!/usr/bin/env python3

"""
Run pytest targets or scripts across multiple build configurations.

For architecture overview, see pytest_testing_system.README.md

Executes the same command or pytest target in 3 different build configurations:
- docker: Native docker engine
- apple: Apple engine
- dev_container: Docker container with local stage

Examples:
> pytest_multi_build.py --target "helpers/test/test_hunit_test.py"
> pytest_multi_build.py --target "." --no_delete_cache
> pytest_multi_build.py --script ./pr_test.sh
"""

import argparse
import logging
import os
import subprocess
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
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
    _LOG.info("Clearing cache...")
    hsystem.system("manage_cache.py --action clear_all")


def _build_pytest_cmd(targets: List[str]) -> str:
    """
    Build pytest command from targets.

    :param targets: list of pytest targets
    :return: command string to run
    """
    targets_str = " ".join(targets)
    cmd = f"pytest_log {targets_str}"
    return cmd


def _run_build(
    build_name: str,
    cmd: str,
) -> None:
    """
    Run a single build with specified command.

    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :param cmd: Command to run (e.g., 'pytest_log target1 target2' or './script.sh')
    """
    output_file = f"tmp.pytest_multi_build.{build_name}.txt"
    _LOG.info(
        "Running build '%s' -> '%s'",
        build_name,
        output_file,
    )
    # Build full command with environment setup based on build config.
    docker_engine, use_docker_cmd = hpytest.BUILD_CONFIG[build_name]
    if use_docker_cmd:
        opts = "--stage=local -v 1.6.0"
        full_cmd = f'invoke docker_cmd {opts} --cmd "{cmd}"'
    else:
        full_cmd = f"export CSFY_DOCKER_ENGINE='{docker_engine}'; {cmd}"
    # Run command and tee output to file.
    shell_cmd = f"({full_cmd}) 2>&1 | tee {output_file}"
    _LOG.debug("Executing: %s", shell_cmd)
    result = subprocess.run(
        shell_cmd,
        shell=True,
        check=False,
    )
    _LOG.info(
        "Build '%s' completed with exit code %d", build_name, result.returncode
    )


def _cleanup_old_files() -> None:
    """
    Clean up old build output files.
    """
    for build_name in hpytest.BUILD_CONFIG.keys():
        output_file = f"tmp.pytest_multi_build.{build_name}.txt"
        if os.path.exists(output_file):
            _LOG.debug("Removing old file: %s", output_file)
            os.remove(output_file)


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute pytest across multiple build configurations.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Clean up old files.
    _cleanup_old_files()
    # Determine command to run.
    if args.target:
        cmd = _build_pytest_cmd(args.target)
    else:
        hdbg.dassert_ne(
            args.script, "", "Either --target or --script must be provided"
        )
        cmd = args.script
    _LOG.info("Command to run: %s", cmd)
    # Run all configured builds.
    for build_name in hpytest.BUILD_CONFIG.keys():
        if not args.no_delete_cache:
            _clear_cache()
        _run_build(build_name, cmd)
    _LOG.info("All builds completed")


if __name__ == "__main__":
    _main(_parse())
