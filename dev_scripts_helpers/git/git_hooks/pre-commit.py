#!/usr/bin/env python3
"""
This is a git commit-hook used to check that a commit follows certain
invariants.

In case of violations the script will exit non-zero and abort the
commit. User can ignore the checks with `git commit --no-verify '...'`.

One can run this hook to preview what `git commit` will do:
> pre-commit.py

Import as:

import dev_scripts_helpers.git.git_hooks.pre-commit as dsgghpr
"""

# NOTE: This file should depend only on Python standard libraries.
import logging
import os
import pathlib
import sys
from typing import List

import dev_scripts_helpers.git.git_hooks.utils as dshgghout

_LOG = logging.getLogger(__name__)


# #############################################################################


def _write_output_to_file(lines: List[str]) -> None:
    """
    Write the output of the pre-commit hook to temporary file.

    :param lines: pre-commit output lines
    """
    out_path = pathlib.Path("tmp.precommit_output.txt")
    with out_path.open("w") as f:
        for line in lines:
            f.write(line + "\n")


if __name__ == "__main__":
    print("# Running git pre-commit hook ...")
    lines = []
    lines.append("Pre-commit checks:")
    #
    dshgghout.check_master()
    lines.append("- 'check_master' passed")
    #
    dshgghout.check_author()
    lines.append("- 'check_author' passed")
    #
    dshgghout.check_file_size()
    lines.append("- 'check_file_size' passed")
    # TODO(gp): Disabled for now since it's too strict.
    # dshgghout.check_words()
    # lines.append("- 'check_words' passed")
    #
    dshgghout.check_python_compile()
    lines.append("- 'check_python_compile' passed")
    assert os.path.exists(".git")
    dshgghout.check_gitleaks()
    lines.append("- 'check_gitleaks' passed")
    print(
        "\n"
        + dshgghout.color_highlight(
            "##### All pre-commit hooks passed: committing ######", "purple"
        )
    )
    lines.append("All checks passed ✅")
    _write_output_to_file(lines)
    sys.exit(0)
