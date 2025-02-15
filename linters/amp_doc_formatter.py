#!/usr/bin/env python
"""
Wrapper for docformatter.

> amp_doc_formatter.py sample_file1.py sample_file2.py

Import as:

import linters.amp_doc_formatter as lamdofor
"""
import argparse
import logging
import re
import uuid
from typing import Dict, List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hstring as hstring
import helpers.hsystem as hsystem
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################
# _DocFormatter
# #############################################################################


class _DocFormatter(liaction.Action):
    """
    Format docstrings to follow a subset of the PEP 257 conventions It relies
    on:

    - docformatter
    """

    def __init__(self) -> None:
        executable = "docformatter"
        super().__init__(executable)

    def check_if_possible(self) -> bool:
        """
        Check if action can run.
        """
        check: bool = hsystem.check_exec(self._executable)
        return check

    @staticmethod
    def _remove_ignored_docstrings(file_name: str) -> Dict[str, str]:
        """
        Replace ignored docstrings from the file with unique hashes and return
        dict with replacements.

        :param file_name: file to process
        :return: dictionary with hash as key and replaced docstring as a
            value
        """
        result: Dict[str, str] = {}
        contents = hio.from_file(file_name)
        # Example of text that is matched by the below pattern:
        # # docformatter: ignore
        # """Some comment."""
        pattern = r"""
        \#              # Literal symbol '#' that denotes a comment.
        \s*             # Any amount of space.
        docformatter:   # Literal string.
        \s*             # Any amount of space.
        ignore          # Literal string.
        [\s\v]+         # Any amount of space or new lines.
        (\'\'\'|\"\"\") # Either 3 single quotes, or 3 double quotes.
        [\w\W\v]+?      # Basically, any symbol.
        \1              # Either 3 single or double quotes, whichever was matched before.
        """
        while True:
            match = re.search(pattern, contents, re.VERBOSE)
            if match is None:
                break
            hash_id = str(uuid.uuid4())
            contents = (
                f"{contents[: match.start()]}# {hash_id}{contents[match.end() :]}"
            )
            result[hash_id] = match.group(0)
        hio.to_file(file_name, contents)
        return result

    @staticmethod
    def _remove_code_blocks(file_name: str) -> Dict[str, List[str]]:
        """
        Remove code blocks in triple backticks from docstrings.

        Code blocks such as the one below are temporarily removed.
        ```
        ABC
        ```
        This is done to preserve them as-is during the run of `docformatter`.

        :param file_name: file to process
        :return: storage of removed code blocks
        """
        lines = hio.from_file(file_name).split("\n")
        # Get lines within triple backticks.
        code_block_indices = hstring.get_code_block_line_indices(lines)
        updated_lines: List[str] = []
        skipped_id = 0
        removed_blocks_storage: Dict[str, List[str]] = {}
        for i, line in enumerate(lines):
            if i not in code_block_indices and i + 1 in code_block_indices:
                # Initialize objects for a new code block.
                skipped_id += 1
                skipped_lines = []
                updated_lines.append(line)
            elif i in code_block_indices or (
                i - 1 in code_block_indices and line.strip() == "```"
            ):
                # Replace the code block line with a placeholder.
                skipped_lines.append(line)
                indent = re.findall(r"^[\s]*", line)[0]
                num_repeat = int(80 - len(indent) / len(f"IDSKIP{skipped_id}"))
                updated_lines.append(indent + f"IDSKIP{skipped_id}" * num_repeat)
                if i not in code_block_indices:
                    # The end of the code block has been reached.
                    # Store the removed lines for adding them back later.
                    removed_blocks_storage[str(skipped_id)] = skipped_lines
            else:
                updated_lines.append(line)
        hio.to_file(file_name, "\n".join(updated_lines))
        return removed_blocks_storage

    @staticmethod
    def _restore_ignored_docstrings(
        file_name: str, store: Dict[str, str]
    ) -> None:
        """
        Restore docstrings that have been previously with unique hashes.

        :param file_name: file to process
        :param store: dictionary with hash as key and replaced docstring
            as a value
        """
        contents = hio.from_file(file_name)
        for key, value in store.items():
            contents = contents.replace(f"# {key}", value)
        hio.to_file(file_name, contents)

    @staticmethod
    def _restore_removed_code_blocks(
        file_name: str, removed_blocks_storage: Dict[str, List[str]]
    ) -> None:
        """
        Restore code blocks that have been previously removed.

        :param file_name: file to process
        :param removed_blocks_storage: original code blocks from the
            docstring
        """
        lines = hio.from_file(file_name).split("\n")
        updated_lines: List[str] = []
        restored_ids = []
        for line in lines:
            match = re.findall(r"IDSKIP(\d)", line)
            if match:
                # Get the id of the removed code block.
                skipped_id = match[0]
                if skipped_id in restored_ids:
                    continue
                for skipped_line in removed_blocks_storage[skipped_id]:
                    # Restore the previously removed line.
                    updated_lines.append(skipped_line)
                restored_ids.append(skipped_id)
            else:
                updated_lines.append(line)
        hio.to_file(file_name, "\n".join(updated_lines))

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        """
        Run docformatter on file.

        :param file_name: the name of the file
        :param pedantic: level of scrutiny in checking
        :return: lints
        """
        _ = pedantic
        # Applicable to only python file.
        if not liutils.is_py_file(file_name):
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        # Clear and store ignored docstrings and code.
        _ignored_docstrings = self._remove_ignored_docstrings(file_name)
        _removed_code = self._remove_code_blocks(file_name)
        # Execute docformatter.
        opts = "--make-summary-multi-line --pre-summary-newline --in-place"
        cmd = f"{self._executable} {opts} {file_name}"
        output: List[str] = []
        _, output = liutils.tee(cmd, self._executable, abort_on_error=False)
        # Restore ignored docstrings and code.
        self._restore_ignored_docstrings(file_name, _ignored_docstrings)
        self._restore_removed_code_blocks(file_name, _removed_code)
        return output


# #############################################################################


# #############################################################################
# _Pydocstyle
# #############################################################################


class _Pydocstyle(liaction.Action):

    def __init__(self) -> None:
        executable = "pydocstyle"
        super().__init__(executable)

    def check_if_possible(self) -> bool:
        """
        Check if action can run.
        """
        check: bool = hsystem.check_exec(self._executable)
        return check

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        """
        Run pydocstyle on file.

        :param file_name: the name of the file
        :param pedantic: level of scrutiny in checking
        :return: lints
        """
        # Applicable to only python file.
        if not liutils.is_py_file(file_name):
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        ignore = []
        # Error codes: http://www.pydocstyle.org/en/2.1.1/error_codes.html.
        if pedantic < 2:
            # TODO(gp): Review all of these.
            ignore.extend(
                [
                    # D105: Missing docstring in magic method.
                    "D105",
                    # D200: One-line docstring should fit on one line with quotes.
                    "D200",
                    # D202: No blank lines allowed after function docstring.
                    "D202",
                    # D212: Multi-line docstring summary should start at the first line.
                    # Demanding that the docstrings look like this:
                    # ```
                    # def func():
                    #     """Do this.
                    #
                    #     Continue explanation.
                    #     """
                    # ```
                    "D212",
                    # D213: Multi-line docstring summary should start at the second line.
                    "D213",
                    # D209: Multi-line docstring closing quotes should be on a separate line.
                    "D209",
                    # D203: 1 blank line required before class docstring (found 0)
                    "D203",
                    # D205: 1 blank line required between summary line and description.
                    "D205",
                    # D400: First line should end with a period (not ':')
                    "D400",
                    # D402: First line should not be the function's "signature"
                    "D402",
                    # D407: Missing dashed underline after section.
                    "D407",
                    # D413: Missing dashed underline after section.
                    "D413",
                    ## D415: First line should end with a period, question mark,
                    ## or exclamation point.
                    "D415",
                ]
            )
        if pedantic < 1:
            # Disable some lints that are hard to respect.
            ignore.extend(
                [
                    # D100: Missing docstring in public module.
                    "D100",
                    # D101: Missing docstring in public class.
                    "D101",
                    # D102: Missing docstring in public method.
                    "D102",
                    # D103: Missing docstring in public function.
                    "D103",
                    # D104: Missing docstring in public package.
                    "D104",
                    # D107: Missing docstring in __init__
                    "D107",
                ]
            )
        cmd_opts = ""
        if ignore:
            cmd_opts += "--ignore " + ",".join(ignore)
        #
        cmd = []
        cmd.append(self._executable)
        cmd.append(cmd_opts)
        cmd.append(file_name)
        cmd_as_str = " ".join(cmd)
        ## We don't abort on error on pydocstyle, since it returns error if there
        ## is any violation.
        _, file_lines_as_str = hsystem.system_to_string(
            cmd_as_str, abort_on_error=False
        )
        ## Process lint_log transforming:
        ##   linter_v2.py:1 at module level:
        ##       D400: First line should end with a period (not ':')
        ## into:
        ##   linter_v2.py:1: at module level: D400: First line should end with a
        ##   period (not ':')
        #
        output: List[str] = []
        #
        file_lines = file_lines_as_str.split("\n")
        lines = ["", ""]
        for cnt, line in enumerate(file_lines):
            line = line.rstrip("\n")
            # _log.debug("line=%s", line)
            if cnt % 2 == 0:
                regex = r"(\s(at|in)\s)"
                subst = r":\1"
                line = re.sub(regex, subst, line)
            else:
                line = line.lstrip()
            # _log.debug("-> line=%s", line)
            lines[cnt % 2] = line
            if cnt % 2 == 1:
                line = "".join(lines)
                output.append(line)
        return output


# #############################################################################


# #############################################################################
# _Pyment
# #############################################################################


# TODO(gp): Fix this.
# Not installable through conda.
class _Pyment(liaction.Action):

    def __init__(self) -> None:
        executable = "pyment"
        super().__init__(executable)

    def check_if_possible(self) -> bool:
        """
        Check if action can run.
        """
        check: bool = hsystem.check_exec(self._executable)
        return check

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        """
        Run pyment on file.

        :param file_name: the name of the file
        :param pedantic: level of scrutiny in checking
        :return: lints
        """
        _ = pedantic
        # Applicable to only python file.
        if not liutils.is_py_file(file_name):
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        opts = "-w --first-line False -o reST"
        cmd = self._executable + f" {opts} {file_name}"
        output: List[str]
        _, output = liutils.tee(cmd, self._executable, abort_on_error=False)
        return output


# #############################################################################


# #############################################################################
# _DocFormatterAction
# #############################################################################


class _DocFormatterAction(liaction.CompositeAction):
    """
    An action that groups all docstring linter actions.
    """

    def __init__(self) -> None:
        super().__init__(
            [
                _DocFormatter(),
                _Pydocstyle(),
                ## Pyment's config doesn't play well with other formatters,
                ## possible problems I see so far:
                ##  1. it adds a lot of trailing white spaces.
                ##  2. it reads already existing arguments in the docstring (very weird)
                ##  3. it moves start of multi-line doc strings to 2nd line, which conflicts
                ##     with docformatter (possibly can be configured)
                # _Pyment(),
            ]
        )


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "files",
        nargs="+",
        action="store",
        type=str,
        help="Files to process",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Run _DocFormatterAction.

    :param parser: argparse.ArgumentParser:
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _DocFormatterAction()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
