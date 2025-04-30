#!/usr/bin/env python

"""
Import as:

import dev_scripts_helpers.git.git_hooks.commit-msg as dsgghoco
"""

import re
import sys

import dev_scripts_helpers.git.git_hooks.utils as dshgghout


def _main():
    message_file = sys.argv[1]
    try:
        f = open(message_file, "r")
        commit_message = f.read()
    finally:
        f.close()
    # We might not need every commit message to start with the issue number as
    # it is already in the branch and PR name.
    # regex = r"^Merge\sbranch|#(\d+)\s\S+"
    # Example: "E.g., '#101 Awesomely fix this and that' or 'Merge branch ...'"
    #
    # Every commit message should start with a capital letter.
    regex = r"^Merge\sbranch|^[A-Z].+"
    if not re.match(regex, commit_message):
        msg = dshgghout.color_highlight(
            "##### commit-msg hook failed ######", "red"
        )
        print(msg)
        print("Your commit message doesn't match regex '%s'" % regex)
        print("E.g., 'Awesomely fix this and that' or 'Merge branch ...'")
        print()
        print(
            "If you think there is a problem commit with --no-verify and "
            "file a bug with commit line and error"
        )
        sys.exit(1)
    # Read pre-commit output.
    precommit_output_path = f"tmp.precommit_output.txt"
    try:
        # We want to avoid using helpers here because we want to keep the
        # script decoupled from helpers.
        with open(precommit_output_path, "r") as f:
            precommit_output = f.read().strip()
    except FileNotFoundError:
        precommit_output = "No pre-commit output found."
    # Format metadata and append to commit message.
    metadata = "\n" + precommit_output
    with open(message_file, "a") as f:
        f.write(metadata)
    msg = dshgghout.color_highlight(
        "##### commit-msg hook passed: committing ######", "purple"
    )
    print(msg)


if __name__ == "__main__":
    print("\nRun git commit-msg hook ...\n")
    _main()
    sys.exit(0)
