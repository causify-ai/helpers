#!/usr/bin/env python
r"""
Wrapper for pylint.

> amp_pylint.py sample_file1.py sample_file2.py

Import as:

import linters.amp_pylint as lamppyli
"""
import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################


# #############################################################################
# _Pylint
# #############################################################################


class _Pylint(liaction.Action):

    def __init__(self) -> None:
        executable = "pylint"
        super().__init__(executable)

    def check_if_possible(self) -> bool:
        check: bool = hsystem.check_exec(self._executable)
        return check

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        if self.skip_if_not_py(file_name):
            # Apply only to Python files.
            return []
        #
        is_test_code_tmp = liutils.is_under_test_dir(file_name)
        _LOG.debug("is_test_code_tmp=%s", is_test_code_tmp)
        #
        is_jupytext_code = liutils.is_paired_jupytext_file(file_name)
        _LOG.debug("is_jupytext_code=%s", is_jupytext_code)
        #
        opts = []
        ignore = []
        if pedantic < 2:
            # We ignore these errors as too picky.
            ignore.extend(
                [
                    # [C0302(too-many-lines), ] Too many lines in module (/1000)
                    "C0302",
                    # TODO(gp): Re-enable?
                    # [C0304(missing-final-newline), ] Final newline missing.
                    "C0304",
                    ## [C0411(wrong-import-order), ]
                    # Pylint's import order check is based fully on `isort` that
                    # we use separately (see https://github.com/PyCQA/pylint/issues/3551),
                    # but is less configurable, which leads to false positives (not
                    # recognizing `helpers` as a first-party module).
                    "C0411",
                    ## [C0412(ungrouped-imports), ] Imports from package ... are not
                    ##   grouped.
                    # TODO(gp): Re-enable?
                    "C0412",
                    # [C0415(import-outside-toplevel), ] Import outside toplevel.
                    # - Sometimes we import inside a function.
                    "C0415",
                    # [R0402(consider-using-from-import)] Use 'from %s import %s' instead
                    # This rule contradicts our internal guidelines.
                    "R0402",
                    # [R0902(too-many-instance-attributes)] Too many instance attributes (/7)
                    "R0902",
                    # [R0903(too-few-public-methods), ] Too few public methods (/2)
                    "R0903",
                    # [R0904(too-many-public-methods), ] Too many public methods (/20)
                    "R0904",
                    # [R0912(too-many-branches), ] Too many branches (/12)
                    "R0912",
                    # R0913(too-many-arguments), ] Too many arguments (/5)
                    "R0913",
                    # [R0914(too-many-locals), ] Too many local variables (/15)
                    "R0914",
                    # [R0915(too-many-statements), ] Too many statements (/50)
                    "R0915",
                    # [W0123(eval-used), ] Use of eval.
                    # - We assume that we are mature enough to use `eval` properly.
                    "W0123",
                    ## [W0125(using-constant-test), ] Using a conditional statement
                    ##   with a constant value:
                    # - E.g., we use sometimes `if True:` or `if False:`.
                    "W0125",
                    # [W0201(attribute-defined-outside-init)]
                    ## - If the constructor calls a method (e.g., `reset()`) to
                    ##   initialize the state, we have all these errors.
                    "W0201",
                    # [W0511(fixme), ]
                    "W0511",
                    # [W0603(global-statement), ] Using the global statement.
                    # - We assume that we are mature enough to use `global` properly.
                    "W0603",
                    # [W0640(cell-var-from-loop): Cell variable  defined in loop.
                    "W0640",
                    ## [W1113(keyword-arg-before-vararg), ] Keyword argument before variable
                    ##   positional arguments list in the definition of.
                    # - TODO(gp): Not clear what is the problem.
                    "W1113",
                    # Ignoring import errors till we figure out how to fix those in docker.
                    # ref: https://github.com/alphamatic/amp/issues/695
                    # TODO(amr): Figure out a better way, as I think this also disables the
                    # `no-member` errors.
                    "E0401",
                ]
            )
            # Unit test.
            if is_test_code_tmp:
                ignore.extend(
                    [
                        ## [C0103(invalid-name), ] Class name "Test_dassert_eq1"
                        ##   doesn't conform to PascalCase naming style.
                        "C0103",
                        ## [W0212(protected-access), ] Access to a protected member
                        ##   _get_default_tempdir of a client class.
                        "W0212",
                    ]
                )
            # Jupytext.
            if is_jupytext_code:
                ignore.extend(
                    [
                        ## [W0104(pointless-statement), ] Statement seems to
                        ## have no effect.
                        ## - This is disabled since we use just variable names
                        ##   to print.
                        "W0104",
                        ## [W0106(expression-not-assigned), ] Expression ... is
                        ## assigned to nothing.
                        "W0106",
                        ## [W0621(redefined-outer-name), ] Redefining name ...
                        ## from outer scope.
                        "W0621",
                    ]
                )
        if pedantic < 1:
            ignore.extend(
                [
                    ## [C0103(invalid-name), ] Constant name "..." doesn't
                    ##   conform to UPPER_CASE naming style.
                    "C0103",
                    # [C0111(missing - docstring), ] Missing module docstring.
                    "C0111",
                    # [C0301(line-too-long), ] Line too long (/100)
                    # "C0301",
                ]
            )
        if ignore:
            opts.append("--disable " + ",".join(ignore))
        # Allow short variables, as long as they are camel-case.
        opts.append('--variable-rgx="[a-z0-9_]{1,30}$"')
        opts.append('--argument-rgx="[a-z0-9_]{1,30}$"')
        # TODO(gp): Not sure this is needed anymore.
        opts.append("--ignored-modules=pandas")
        opts.append("--output-format=parseable")
        # TODO(gp): Does -j 4 help?
        opts.append("-j 4")
        # pylint crashed due to lack of memory.
        # A fix according to https://github.com/PyCQA/pylint/issues/2388 is:
        opts.append('--init-hook="import sys; sys.setrecursionlimit(2000);')
        # Enforce that we lint the code in `/src` and not the code of the linter
        # itself (see DevToolsTask406). This is equivalent to prepending
        # `export PYTHONPATH=/src:$PYTHONPATH;` to `pylint`.
        opts.append('''sys.path.insert(0, '/src')"''')
        hdbg.dassert_list_of_strings(opts)
        opts_as_str = " ".join(opts)
        cmd = " ".join([self._executable, opts_as_str, file_name])
        _, output = liutils.tee(cmd, self._executable, abort_on_error=False)
        # Remove some errors.
        output_tmp: List[str] = []
        for line in output:
            if is_jupytext_code:
                # [E0602(undefined-variable), ] Undefined variable 'display'
                if "E0602" in line and "Undefined variable 'display'" in line:
                    continue
            if line.startswith("Your code has been rated"):
                # Your code has been rated at 10.00/10 (previous run: ...
                continue
            output_tmp.append(line)
        output = output_tmp
        # Remove decorator lines.
        output = [
            line
            for line in output
            if ("-" * 20) not in line and not line.startswith("*" * 13)
        ]
        # Remove empty lines.
        output = [line for line in output if line.rstrip().lstrip() != ""]
        return output


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
    verbosity = os.environ.get("DBG_VERBOSITY", None) or args.log_level
    hdbg.init_logger(verbosity=verbosity)
    action = _Pylint()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
