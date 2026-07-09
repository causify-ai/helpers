#!/usr/bin/env python3

"""
Run pytest targets or scripts across multiple build configurations.

Executes the same command or pytest target in 3 different build configurations:
- Build 1: Native docker engine
- Build 2: Apple engine
- Build 3: Docker container with local stage

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
    build_num: int,
    cmd: str,
    docker_engine: str,
    *,
    use_docker_cmd: bool = False,
) -> None:
    """
    Run a single build with specified configuration.

    :param build_num: Build number (1, 2, or 3)
    :param cmd: Command to run
    :param docker_engine: Value for CSFY_DOCKER_ENGINE environment variable
    :param use_docker_cmd: Whether to wrap command in docker_cmd
    """
    output_file = f"tmp.pytest_multi_build{build_num}.txt"
    _LOG.info(
        "Running build %d with CSFY_DOCKER_ENGINE='%s' -> '%s'",
        build_num,
        docker_engine,
        output_file,
    )
    # Build full command with environment variable via export.
    full_cmd = cmd
    if use_docker_cmd:
        # TODO(gp): Generalize this.
        opts = "--stage=local -v 1.6.0"
        full_cmd = f'invoke docker_cmd {opts} --cmd "{cmd}"'
    # Run command and tee output to file.
    shell_cmd = f"export CSFY_DOCKER_ENGINE='{docker_engine}'; ({full_cmd}) 2>&1 | tee {output_file}"
    _LOG.debug("Executing: %s", shell_cmd)
    result = subprocess.run(
        shell_cmd,
        shell=True,
        check=False,
    )
    _LOG.info("Build %d completed with exit code %d", build_num, result.returncode)


def _cleanup_old_files() -> None:
    """
    Clean up old build output files.
    """
    for build_num in range(1, 4):
        output_file = f"tmp.pytest_multi_build{build_num}.txt"
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
        hdbg.dassert_ne(args.script, "", "Either --target or --script must be provided")
        cmd = args.script
    _LOG.info("Command to run: %s", cmd)
    # Run 3 builds.
    for build_num in range(1, 4):
        if not args.no_delete_cache:
            _clear_cache()
        if build_num == 1:
            _run_build(build_num, cmd, docker_engine="docker", use_docker_cmd=False)
        elif build_num == 2:
            _run_build(build_num, cmd, docker_engine="apple", use_docker_cmd=False)
        elif build_num == 3:
            _run_build(build_num, cmd, docker_engine="docker", use_docker_cmd=True)
    _LOG.info("All builds completed")


if __name__ == "__main__":
    _main(_parse())
