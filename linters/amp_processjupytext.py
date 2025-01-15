#!/usr/bin/env python
r"""
Wrapper for process_jupytext.

> amp_processjupytext.py sample_file1.py sample_file2.py

Import as:

import linters.amp_processjupytext as lampproc
"""
import argparse
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################


# #############################################################################
# _ProcessJupytext
# #############################################################################


class _ProcessJupytext(liaction.Action):

    def __init__(self, jupytext_action: str) -> None:
        executable = "$(find -wholename '*dev_scripts_helpers/notebooks/process_jupytext.py')"
        super().__init__(executable)
        self._jupytext_action = jupytext_action

    def check_if_possible(self) -> bool:
        check: bool = hsystem.check_exec(self._executable)
        return check

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        output: List[str] = []
        # TODO(gp): Use the usual idiom of these functions.
        if (
            liutils.is_py_file(file_name) or liutils.is_ipynb_file(file_name)
        ) and liutils.is_paired_jupytext_file(file_name):
            cmd_opts = f"-f {file_name} --action {self._jupytext_action}"
            cmd = self._executable + " " + cmd_opts
            rc, output = liutils.tee(cmd, self._executable, abort_on_error=False)
            if rc != 0:
                error = f"process_jupytext failed with command `{cmd}`\n"
                output.append(error)
                _LOG.error(output)
        else:
            _LOG.debug("Skipping file_name='%s'", file_name)
        return output


# #############################################################################
# _SyncJupytext
# #############################################################################


class _SyncJupytext(_ProcessJupytext):

    def __init__(self) -> None:
        super().__init__("sync")


# #############################################################################
# _TestJupytext
# #############################################################################


class _TestJupytext(_ProcessJupytext):

    def __init__(self) -> None:
        super().__init__("test")


# #############################################################################
# _JupytextAction
# #############################################################################


class _JupytextAction(liaction.CompositeAction):
    """
    An action that groups all jupyter text linter actions.
    """

    def __init__(self) -> None:
        super().__init__([_SyncJupytext(), _TestJupytext()])


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
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _JupytextAction()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
