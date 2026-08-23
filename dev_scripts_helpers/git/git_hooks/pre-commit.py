#!/usr/bin/env python3
"""
This is a git commit-hook used to check that a commit follows certain
invariants.

In case of violations the script will exit non-zero and abort the
commit. User can ignore the checks with `git commit --no-verify '...'`.

One can run this hook to preview what `git commit` will do:
> pre-commit.py

To debug a single check, run only that phase with `--check`:
> pre-commit.py --check gitleaks

Import as:

import dev_scripts_helpers.git.git_hooks.pre-commit as dsgghpr
"""

# NOTE: This file should depend only on Python standard libraries.
import argparse
import logging
import os
import pathlib
import sys
from typing import Callable, Dict, List

import dev_scripts_helpers.git.git_hooks.utils as dshgghout

_LOG = logging.getLogger(__name__)


# #############################################################################


def _run_gitleaks_check() -> None:
    assert os.path.exists(".git")
    dshgghout.check_gitleaks()


# Map the name used with `--check` to the corresponding check phase. The
# order of this dict is also the order in which the phases run when no
# `--check` is specified.
_CHECKS: Dict[str, Callable[[], None]] = {
    "master": dshgghout.check_master,
    "merged_branch": dshgghout.check_merged_branch,
    "merge_conflict_markers": dshgghout.check_merge_conflict_markers,
    "author": dshgghout.check_author,
    "file_size": dshgghout.check_file_size,
    # TODO(gp): Disabled for now since it's too strict.
    # "words": dshgghout.check_words,
    "python_compile": dshgghout.check_python_compile,
    "gitleaks": _run_gitleaks_check,
}


def _write_output_to_file(lines: List[str]) -> None:
    """
    Write the output of the pre-commit hook to temporary file.

    :param lines: pre-commit output lines
    """
    out_path = pathlib.Path("tmp.precommit_output.txt")
    with out_path.open("w") as f:
        for line in lines:
            f.write(line + "\n")


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check",
        action="store",
        choices=sorted(_CHECKS.keys()),
        default=None,
        help="Run only this check phase instead of the full pre-commit "
        "sequence (useful to debug a single check)",
    )
    return parser


if __name__ == "__main__":
    args = _parse().parse_args()
    if args.check is not None:
        # Run only the requested check phase.
        _CHECKS[args.check]()
        sys.exit(0)
    # Run the full pre-commit sequence.
    print("# Running git pre-commit hook ...")
    lines = []
    lines.append("Pre-commit checks:")
    for check_fn in _CHECKS.values():
        check_fn()
    print(
        "\n"
        + dshgghout.color_highlight(
            "##### All pre-commit hooks passed ######", "purple"
        )
    )
    lines.append("All checks passed ✅")
    _write_output_to_file(lines)
    sys.exit(0)
