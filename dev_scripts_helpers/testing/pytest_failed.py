#!/usr/bin/env python

"""
Parse the failed tests out of a pytest log, print them, save a repro script,
and copy the test names to the clipboard.

Examples

# Parse failed tests from `tmp.pytest_script.txt`.
> pytest_failed.py

# Parse failed tests from a specific log file, keeping only the file names.
> pytest_failed.py --file_name tmp.log --only_file
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hpytest as hpytest
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input",
        action="store",
        # This is the output from pytest_log.
        default="tmp.pytest_script.txt",
        help="Pytest log file to parse for failed tests",
    )
    parser.add_argument(
        "--only_file",
        action="store_true",
        help="Return only the file name for each failed test",
    )
    parser.add_argument(
        "--only_class",
        action="store_true",
        help="Return only the class name for each failed test",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Read file.
    _LOG.info("Reading '%s'", args.input)
    txt = hio.from_file(args.input)
    # Extract info.
    _LOG.info("Parsing '%s'", args.input)
    info = hpytest.parse_failed_tests(txt, args.only_file, args.only_class)
    failed_tests = info["failed_tests"]
    print("\n".join(failed_tests))
    # Write the repro in a file.
    repro_file_name = "tmp.pytest_failed.sh"
    repro_txt = "pytest_log " + " ".join(failed_tests) + " $*"
    hio.create_executable_script(repro_file_name, repro_txt)
    _LOG.warning("To run the failed tests run: %s", repro_file_name)
    # Save to clipboard.
    txt = " ".join(failed_tests)
    hsystem.to_pbcopy(txt, pbcopy=True)


if __name__ == "__main__":
    _main(_parse())
