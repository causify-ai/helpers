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
import sys

import dev_scripts_helpers.git.git_hooks.utils as dshgghout

_LOG = logging.getLogger(__name__)


# #############################################################################


if __name__ == "__main__":
    print("# Running git pre-commit hook ...")
    dshgghout.check_master()
    dshgghout.check_author()
    dshgghout.check_file_size()
    dshgghout.check_words()
    dshgghout.check_python_compile()
    dshgghout.check_gitleaks()
    print(
        "\n"
        + dshgghout.color_highlight(
            "##### All pre-commit hooks passed: committing ######", "purple"
        )
    )
    sys.exit(0)
