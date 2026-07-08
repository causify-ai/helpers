#!/usr/bin/env python

"""
List every pytest test under a file or directory together with its pytest
marks and whether it is statically marked as skipped.

Examples

# Scan the whole repo.
> pytest_marks.py

# Scan only `helpers/`.
> pytest_marks.py --dir helpers

Creates the following file:
- tmp.pytest_marks.csv: nodeid, marks, skipped for every collected test
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hpytest as hpytest

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dir",
        action="store",
        default=".",
        help="File or directory to collect tests from",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Collect marks for every test under `args.dir` without running any test.
    _LOG.info("Collecting tests under '%s'", args.dir)
    marks_info = hpytest.collect_test_marks(args.dir)
    _LOG.info("Collected %d tests", len(marks_info))
    # Print a human-readable summary.
    print(hpytest.marks_to_str(marks_info))
    # Persist the full report to disk.
    csv_file = "tmp.pytest_marks.csv"
    hpytest.write_marks_csv(marks_info, csv_file)


if __name__ == "__main__":
    _main(_parse())
