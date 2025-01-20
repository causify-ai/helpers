#!/usr/bin/env python
"""
Lint files.

E.g.,

```bash
# Lint all the files modified in the git client.
> base.py --modified

# Lint specific files.
> base.py -f "foo.py bar.md"
```
"""

import argparse
import itertools
import logging
import os
from typing import List, Tuple, Type

import joblib

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hlist as hlist
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import linters.action as liaction
import linters.add_python_init_files as lapyinfi
import linters.amp_add_class_frames as laadclfr
import linters.amp_add_toc_to_notebook as laattono
import linters.amp_autoflake as lampauto
import linters.amp_black as lampblac
import linters.amp_check_filename as lamchfil
import linters.amp_check_import as lamchimp
import linters.amp_check_merge_conflict as lachmeco
import linters.amp_class_method_order as laclmeor
import linters.amp_doc_formatter as lamdofor
import linters.amp_fix_md_links as lafimdli
import linters.amp_fix_whitespaces as lamfiwhi
import linters.amp_flake8 as lampflak
import linters.amp_format_separating_line as lafoseli
import linters.amp_isort as lampisor
import linters.amp_lint_md as lamlimd
import linters.amp_mypy as lampmypy
import linters.amp_normalize_import as lamnoimp
import linters.amp_processjupytext as lampproc
import linters.amp_pylint as lamppyli
import linters.amp_warn_incorrectly_formatted_todo as lawifoto
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################
# Files
# #############################################################################


def _filter_files(file_paths: List[str]) -> List[str]:
    """
    Filter the list of files to be linted.

    The following files are skipped:
    - Files that do not exist
    - Non-files (directories)
    - Ipynb checkpoints
    - Input and output files in unit tests

    :param file_paths: all the original files to be linted
    :return: files that passed the filters
    """
    file_paths_to_keep: List[str] = []
    for file_path in file_paths:
        # Skip files that do not exist.
        is_valid = os.path.exists(file_path)
        # Skip non-files.
        is_valid &= os.path.isfile(file_path)
        # Skip checkpoints.
        is_valid &= ".ipynb_checkpoints/" not in file_path
        # Skip input and output files used in unit tests.
        is_valid &= not liutils.is_test_input_output_file(file_path)
        if is_valid:
            file_paths_to_keep.append(file_path)
        else:
            _LOG.warning("Skipping %s", file_path)
    return file_paths_to_keep


def _get_files_to_lint(args: argparse.Namespace) -> List[str]:
    """
    Get the files to be processed by Linter.

    :param args: command line arguments
    :return: paths of the files to lint
    """
    file_paths: List[str] = []
    if args.files:
        # Get the files that were explicitly specified.
        file_paths = args.files
    elif args.modified:
        # Get all the modified files in the git client.
        file_paths = hgit.get_modified_files()
    elif args.last_commit:
        # Get all the files modified in the previous commit.
        file_paths = hgit.get_previous_committed_files()
    elif args.branch:
        # Get all the files modified in the branch.
        file_paths = hgit.get_modified_files_in_branch(dst_branch="master")
    elif args.dir_name:
        # Get the files in a specified dir.
        if args.dir_name == "$GIT_ROOT":
            dir_name = hgit.get_client_root(super_module=True)
        else:
            dir_name = args.dir_name
        dir_name = os.path.abspath(dir_name)
        _LOG.info("Looking for all files in '%s'", dir_name)
        hdbg.dassert_path_exists(dir_name)
        cmd = f"find {dir_name} -name '*' -type f"
        _, output = hsystem.system_to_string(cmd)
        file_paths = output.split("\n")
    # Remove files that should not be linted.
    file_paths = _filter_files(file_paths)
    if len(file_paths) < 1:
        _LOG.warning("No files that can be linted were found")
    return file_paths


# #############################################################################
# Actions
# #############################################################################

# Linter actions, listed in the order in which they are executed.
# The order should conform to the following principles:
# - `add_python_init_files` comes first because of its special status
#   (operating on a dir level instead of a file level).
# - Among modifying actions, the last two are `black` and `processjupytext`.
# - Among non-modifying actions, the last three are `flake8`, `pylint`, `mypy`.


_MODIFYING_ACTIONS: List[Tuple[str, str, Type[liaction.Action]]] = [
    (
        "add_python_init_files",
        "Adds missing __init__.py files to directories",
        lapyinfi._AddPythonInitFiles,  # pylint: disable=protected-access
    ),
    (
        "add_toc_to_notebook",
        "Adds a table of contents to a notebook",
        laattono._AddTOC,  # pylint: disable=protected-access
    ),
    (
        "fix_md_links",
        "Regularizes links in Markdown files",
        lafimdli._LinkFixer,  # pylint: disable=protected-access
    ),
    (
        "lint_md",
        "Cleans up Markdown files and update the table of contents",
        lamlimd._LintMarkdown,  # pylint: disable=protected-access
    ),
    (
        "autoflake",
        "Removes unused imports and variables",
        lampauto._Autoflake,  # pylint: disable=protected-access
    ),
    (
        "fix_whitespaces",
        "Standardizes the use of whitespace characters",
        lamfiwhi._FixWhitespaces,  # pylint: disable=protected-access
    ),
    (
        "doc_formatter",
        "Formats docstrings to follow a subset of the PEP 257 conventions",
        lamdofor._DocFormatterAction,  # pylint: disable=protected-access
    ),
    (
        "isort",
        "Sorts imports alphabetically, by section and type",
        lampisor._ISort,  # pylint: disable=protected-access
    ),
    (
        "class_method_order",
        "Sorts methods in classes",
        laclmeor._ClassMethodOrder,  # pylint: disable=protected-access
    ),
    (
        "normalize_imports",
        "Normalizes imports in the code and in the docstring",
        lamnoimp._NormalizeImports,  # pylint: disable=protected-access
    ),
    (
        "format_separating_line",
        "Normalizes separating lines in the code",
        lafoseli._FormatSeparatingLine,  # pylint: disable=protected-access
    ),
    (
        "add_class_frames",
        "Adds frames with class names",
        laadclfr._ClassFramer,  # pylint: disable=protected-access
    ),
    # Not stable; see, e.g., its performance on `linters/amp_pylint.py`.
    # (
    #    "fix_comments",
    #    "Reflows, capitalizes and adds punctuation to comment lines",
    #    lamficom._FixComment,  # pylint: disable=protected-access
    # ),
    (
        "black",
        "Runs `black` to format the code",
        lampblac._Black,  # pylint: disable=protected-access
    ),
    (
        "process_jupytext",
        "Keeps paired .ipynb and .py files synchronized",
        lampproc._JupytextAction,  # pylint: disable=protected-access
    ),
]

_NON_MODIFYING_ACTIONS: List[Tuple[str, str, Type[liaction.Action]]] = [
    (
        "check_filename",
        "Checks if file names conform to our standards",
        lamchfil._CheckFilename,  # pylint: disable=protected-access
    ),
    (
        "check_merge_conflict",
        "Checks for git merge conflict markers",
        lachmeco._CheckMergeConflict,  # pylint: disable=protected-access
    ),
    # Does not work with Docker on Mac, see DevToolsTask97.
    # (
    #    "check_shebang",
    #    "Checks if executable Python files start with a shebang",
    #    lamchshe._CheckShebang,  # pylint: disable=protected-access
    # ),
    (
        "check_import",
        "Checks if imports conform to our standards",
        lamchimp._CheckImport,  # pylint: disable=protected-access
    ),
    (
        "warn_incorrectly_formatted_todo",
        "Checks if TODO comments are correctly formatted",
        lawifoto._WarnIncorrectlyFormattedTodo,  # pylint: disable=protected-access
    ),
    (
        "flake8",
        "Checks if the code conforms to coding style standards according to Flake8",
        lampflak._Flake8,  # pylint: disable=protected-access
    ),
    (
        "pylint",
        "Checks if the code conforms to coding style standards according to Pylint",
        lamppyli._Pylint,  # pylint: disable=protected-access
    ),
    (
        "mypy",
        "Checks if types and type hints are used correctly",
        lampmypy._Mypy,  # pylint: disable=protected-access
    ),
]


def _get_actions(
    args: argparse.Namespace,
) -> Tuple[List[str], List[Type[liaction.Action]]]:
    """
    Get Linter actions to run on files.

    :param args: command line arguments
    :return: action names and classes
    """
    # Get the Linter actions to run.
    if args.only_format:
        # Select only modifying.
        action_names, _, action_classes = list(zip(*_MODIFYING_ACTIONS))
    elif args.only_check:
        # Select only non-modifying.
        action_names, _, action_classes = list(zip(*_NON_MODIFYING_ACTIONS))
    else:
        # Select all.
        action_names, _, action_classes = list(
            zip(*_MODIFYING_ACTIONS + _NON_MODIFYING_ACTIONS)
        )
    action_names_out, action_classes_out = [], []
    for i, action_name in enumerate(action_names):
        if action_name == "normalize_imports":
            # To initialize, Import Normalizer needs a list of all Python files in the directory.
            root_dir = hgit.get_client_root(super_module=False)
            py_files = liutils.get_python_files_to_lint(root_dir)
            action_class = action_classes[i](py_files)
        else:
            action_class = action_classes[i]()
        # Drop actions that cannot be executed.
        is_possible = action_class.check_if_possible()
        if not is_possible:
            _LOG.warning("Cannot execute action '%s': skipping", action_name)
        else:
            action_names_out.append(action_name)
            action_classes_out.append(action_class)
    return action_names_out, action_classes_out


# #############################################################################


def _lint(
    file_path: str,
    action_names: List[str],
    action_classes: List[Type[liaction.Action]],
    pedantic: int,
) -> List[str]:
    """
    Execute all Linter actions on a single file.

    This is the unit of parallelization. All the actions are run one by one
    to ensure that they are executed in a proper order.

    :param file_path: path to the file to be linted
    :param action_names: names of Linter actions
    :param action_classes: classes executing Linter actions
    :param pedantic: how pedantic Linter should be (0 - min, 2 - max)
    :return: lint messages for the input file
    """
    lints: List[str] = []
    _LOG.info("\nLinting file: '%s'", file_path)
    for i, action_name in enumerate(action_names):
        # Run a single Linter action.
        _LOG.debug("\nRunning action:'%s'", action_name)
        action_class = action_classes[i]
        cur_action_lints = action_class.execute(file_path, pedantic)
        hdbg.dassert_list_of_strings(cur_action_lints)
        # Annotate each lint with a [tag] specifying the action name.
        cur_action_lints = [lnt + f" [{action_name}]" for lnt in cur_action_lints]
        lints.extend(cur_action_lints)
    return lints


def _run_linter(
    file_paths: List[str],
    action_names: List[str],
    action_classes: List[Type[liaction.Action]],
    args: argparse.Namespace,
) -> List[str]:
    """
    Run Linter on the input files.

    :param file_paths: files to be linted
    :param action_names: names of Linter actions
    :param action_classes: classes executing Linter actions
    :param args: command line arguments
    :return: lint messages for all the files
    """
    num_threads = args.num_threads
    if len(file_paths) == 1:
        # Use serial mode if there is only one file to lint.
        num_threads = "serial"
        _LOG.info(
            "Using num_threads='%s' since there is only one file to lint",
            num_threads,
        )
    lints: List[str] = []
    if num_threads == "serial":
        # Lint the files one by one.
        for file_path in file_paths:
            cur_file_lints = _lint(
                file_path, action_names, action_classes, args.pedantic
            )
            lints.extend(cur_file_lints)
    else:
        # Lint the files in parallel.
        num_threads = int(num_threads)
        _LOG.info("Using %s threads", num_threads if num_threads > 0 else "all")

        lints_tmp = joblib.Parallel(n_jobs=num_threads, verbose=50)(
            joblib.delayed(_lint)(
                file_path, action_names, action_classes, args.pedantic
            )
            for file_path in file_paths
        )
        lints.extend(list(itertools.chain.from_iterable(lints_tmp)))
    lints = hprint.remove_empty_lines_from_string_list(lints)
    return lints  # type: ignore


# #############################################################################
# Main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # File selection.
    parser.add_argument(
        "-f", "--files", nargs="+", type=str, help="Files to process"
    )
    parser.add_argument(
        "-d",
        "--dir_name",
        action="store",
        help="Select all the files in a dir. 'GIT_ROOT' to select git root",
    )
    parser.add_argument(
        "--modified",
        action="store_true",
        help="Select files modified in the current git client",
    )
    parser.add_argument(
        "--last_commit",
        action="store_true",
        help="Select files modified in the previous commit",
    )
    parser.add_argument(
        "--branch",
        action="store_true",
        help="Select files modified in the current branch with respect to master",
    )
    # Action selection.
    parser.add_argument(
        "--only_format",
        action="store_true",
        help="Run only modifying Linter actions",
    )
    parser.add_argument(
        "--only_check",
        action="store_true",
        help="Run only non-modifying Linter actions",
    )
    # Run parameters.
    parser.add_argument(
        "--pedantic",
        action="store",
        type=int,
        default=0,
        help="0 - min, 2 - max (all the lints)",
    )
    parser.add_argument(
        "--num_threads",
        action="store",
        default="-1",
        help="Number of threads to use ('serial' to run serially, -1 to use "
        "all CPUs)",
    )
    parser.add_argument(
        "--linter_log",
        default="./linter_warnings.txt",
        help="File for storing the warnings",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(args: argparse.Namespace) -> None:
    hdbg.init_logger(args.log_level)
    # Get the files to be linted.
    file_paths = _get_files_to_lint(args)
    _LOG.debug(
        "Linting %s files; file_paths=%s", len(file_paths), " ".join(file_paths)
    )
    # Get Linter actions.
    action_names, action_classes = _get_actions(args)
    _LOG.debug(
        "Running %s actions; action_names=%s",
        len(action_names),
        " ".join(action_names),
    )
    # Run.
    lints = _run_linter(file_paths, action_names, action_classes, args)
    hdbg.dassert_list_of_strings(lints)
    lints = sorted(lints)
    lints = hlist.remove_duplicates(lints)
    # Write the output into a file.
    output: List[str] = []
    output.append(f"cmd line='{hdbg.get_command_line()}'")
    output.append(f"file_paths={len(file_paths)} {file_paths}")
    output.append(f"actions={len(action_names)} {action_names}")
    output.append(hprint.line(char="/"))
    output.extend(lints)
    hio.to_file(args.linter_log, "\n".join(output))
    # Print the output.
    output_from_file = hio.from_file(args.linter_log)
    print(hprint.frame(args.linter_log, char1="/").rstrip("\n"))
    print(output_from_file + "\n")
    print(hprint.line(char="/").rstrip("\n"))


if __name__ == "__main__":
    parser_ = _parse()
    args_ = parser_.parse_args()
    _main(args_)
