#!/usr/bin/env python
"""
Check if a Markdown file is referenced in the README.

Assumption:
    - The `README.md` file is in the root of the repository.

Steps:
1. Parse the README file to extract references.
2. Check if the current Markdown file is referenced in the README.
3. Generate warnings if the current file is not referenced.
"""

import argparse
import logging
import os
import re
from typing import List

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction

_LOG = logging.getLogger(__name__)

MARKDOWN_LINK_REGEX = r"\[.*?\]\((.*?)\)"


def check_file_reference(readme_path: str, file_name: str) -> List[str]:
    """
    Check if the given file is referenced in the README.

    :param readme_path: the path to the README file
    :param file_name: the path to the file being linted
    :return: warnings
    """
    references = set()
    warnings = []
    if os.path.exists(readme_path):
        lines = hio.from_file(readme_path).split("\n")
        for _, line in enumerate(lines, start=1):
            markdown_links = re.findall(MARKDOWN_LINK_REGEX, line)
            references.update(markdown_links)
        normalized_file_name = os.path.normpath(file_name)
        is_referenced = any(
            os.path.normpath(ref.split("#")[0]) == normalized_file_name
            for ref in references
        )
        if not is_referenced:
            warnings.append(
                f"{file_name}: '{file_name}' is not referenced in README.md"
            )
    else:
        _LOG.warning("README.md not found. Skipping check for '%s'", file_name)
    return warnings


# #############################################################################
# _ReadmeLinter
# #############################################################################


class _ReadmeLinter(liaction.Action):
    """
    Linter action to check if a Markdown file is referenced in README.
    """

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_markdown(file_name):
            # Apply only to Markdown files.
            return []
        # Find the repository root.
        repo_root = hgit.find_git_root()
        # Define the path to README.md.
        readme_path = os.path.join(repo_root, "README.md")
        warnings = check_file_reference(readme_path, file_name)
        return warnings


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "files",
        nargs="+",
        action="store",
        type=str,
        help="Markdown file(s) to lint",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _ReadmeLinter()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
