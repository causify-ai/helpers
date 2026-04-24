#!/usr/bin/env python
"""
Unified linter for Python, Jupyter, and Markdown files.

Selects files based on git state (modified, branch, etc.) or explicit paths,
then applies appropriate linting tools per file type.

Examples:

# Lint all modified Python files
> lint.py --modified --py

# Lint all files in branch vs master
> lint.py --branch

# Lint a specific directory (Python only)
> lint.py --dir ./tutorials --py

# Lint specific files
> lint.py --files foo.py bar.ipynb baz.md

# Lint from a file list, Jupyter only
> lint.py --from_file filelist.txt --ipynb

# Lint last commit
> lint.py --last_commit

# Lint markdown in modified files
> lint.py --modified --md

# Run only specific actions on modified files (pre-commit and normalize_import)
> lint.py --modified --action pre-commit normalize_import

# Run only jupytext sync on Jupyter notebooks
> lint.py --modified --ipynb --action sync_jupytext

# Run add_class_frames only on Python files
> lint.py --modified --py --action add_class_frames

# Run pyright type-checker on modified Python files (including paired jupytext)
> lint.py --modified --py --action pyright

# Run coverage for test files corresponding to modified Python files
> lint.py --modified --py --action coverage
"""

import argparse
import logging
import os
import sys
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters2.linter_utils as llinutil

_LOG = logging.getLogger(__name__)

_PYRIGHT_OPTIONS = ""


# #############################################################################
# Linting Functions
# #############################################################################


# TODO(ai_gp): Move this to ./helpers/hunit_test_utils.py and add unit tests.
def _get_test_file_for_source(source_file: str) -> Optional[str]:
	"""
	Map a source Python file to its corresponding test file.

	E.g., helpers/hdbg.py -> helpers/test/test_hdbg.py

	:param source_file: Path to a source Python file
	:return: Path to corresponding test file if it exists and source is not
	         already a test file; None otherwise
	"""
	if llinutil.is_test_code(source_file):
		return None
	dir_name = os.path.dirname(source_file)
	base_name = os.path.basename(source_file)
	test_file = os.path.join(dir_name, "test", f"test_{base_name}")
	if os.path.exists(test_file):
		return test_file
	return None


def _run_linting_actions(
    files_str: str,
    *,
    abort_on_error: bool = True,
    actions: List[str] | None = None,
) -> int:
    """
    Run common linting actions (pre-commit, normalize_import, add_class_frames).

    :param files_str: Space-separated string of file paths
    :param abort_on_error: whether to abort on first error
    :param actions: list of actions to perform; if None, all are performed
    :return: combined return code (OR of all command return codes)
    """
    # TODO(ai_gp): Add a DEFAULT_ACTIONS like in other files.
    if actions is None:
        actions = ["pre-commit", "normalize_import", "add_class_frames"]
    # TODO(ai_gp): Remove the processed actions and then assert if there is one
    # not processed, see code in other files.
    ret = 0
    if "pre-commit" in actions:
        ret |= hsystem.system(
            f"pre-commit run --files {files_str}",
            print_command=True,
            abort_on_error=abort_on_error,
            suppress_output=False,
        )
    if "normalize_import" in actions:
        ret |= hsystem.system(
            f"linters2/normalize_import.py {files_str}",
            print_command=True,
            abort_on_error=abort_on_error,
            suppress_output=False,
        )
    if "add_class_frames" in actions:
        ret |= hsystem.system(
            f"linters2/add_class_frames.py {files_str}",
            print_command=True,
            abort_on_error=abort_on_error,
            suppress_output=False,
        )
    if "pyright" in actions:
        ret |= hsystem.system(
            f"pyright {_PYRIGHT_OPTIONS} {files_str}",
            print_command=True,
            abort_on_error=abort_on_error,
            suppress_output=False,
        )
    return ret


def _run_coverage(
    file_paths: List[str],
    *,
    abort_on_error: bool = True,
) -> int:
	"""
	Run pytest coverage for test files corresponding to source Python files.

	Maps each source file to its corresponding test file and runs:
	> pytest --cov=. --cov-branch --cov-report term-missing --cov-report html

	:param file_paths: Source Python files to collect coverage for
	:param abort_on_error: whether to abort on first error
	:return: return code from pytest
	"""
	if not file_paths:
		return 0
	_LOG.info("Collecting coverage for %d Python files", len(file_paths))
	test_files = []
	for file_path in file_paths:
		test_file = _get_test_file_for_source(file_path)
		if test_file:
			test_files.append(test_file)
			_LOG.info("Source: %s -> Test: %s", file_path, test_file)
		else:
			_LOG.warning("No test file found for: %s", file_path)
	if not test_files:
		_LOG.warning("No test files found for any of the source files")
		return 0
	test_files_str = " ".join(test_files)
	cmd = f"pytest --cov=. --cov-branch --cov-report term-missing --cov-report html {test_files_str}",
	ret = hsystem.system(
        cmd,
		print_command=True,
		abort_on_error=abort_on_error,
		suppress_output=False,
	)
	return ret


def _lint_python(
    file_paths: List[str],
    *,
    abort_on_error: bool = True,
    actions: List[str] | None = None,
) -> int:
    """
    Lint Python files using specified actions.

    :param file_paths: Python files to lint
    :param abort_on_error: whether to abort on first error
    :param actions: list of actions to perform (pre-commit, normalize_import,
    add_class_frames, pyright, coverage)
        - If None, all actions except coverage are performed
    :return: combined return code (OR of all command return codes)
    """
    if not file_paths:
        return 0
    if actions is None:
        actions = ["pre-commit", "normalize_import", "add_class_frames"]
    _LOG.info("Linting %d Python files with actions: %s", len(file_paths), actions)
    ret = 0
    files_str = " ".join(file_paths)
    ret |= _run_linting_actions(
        files_str,
        abort_on_error=abort_on_error,
        actions=actions,
    )
    if "coverage" in actions:
        ret |= _run_coverage(
            file_paths,
            abort_on_error=abort_on_error,
        )
    return ret


def _lint_jupyter(
    file_paths: List[str],
    *,
    abort_on_error: bool = True,
    actions: List[str] | None = None,
) -> int:
    """
    Lint Jupyter notebooks with specified actions.

    :param file_paths: Jupyter notebook files to lint
    :param abort_on_error: whether to abort on first error
    :param actions: list of actions to perform (pre-commit, normalize_import, add_class_frames, sync_jupytext);
                   if None, all actions are performed
    :return: combined return code (OR of all command return codes)
    """
    if not file_paths:
        return 0
    if actions is None:
        actions = ["pre-commit", "normalize_import", "add_class_frames", "sync_jupytext"]
    _LOG.info("Linting %d Jupyter notebooks with actions: %s", len(file_paths), actions)
    files_str = " ".join(file_paths)
    ret = _run_linting_actions(
        files_str,
        abort_on_error=abort_on_error,
        actions=actions,
    )
    if "sync_jupytext" in actions:
        for file_path in file_paths:
            _LOG.debug("Syncing jupytext: %s", file_path)
            ret |= hsystem.system(
                f"jupytext --sync {file_path}",
                print_command=True,
                abort_on_error=abort_on_error,
                suppress_output=False,
            )
    return ret


def _lint_markdown(
    file_paths: List[str],
    *,
    abort_on_error: bool = True,
) -> int:
    """
    Lint Markdown files using lint_txt.py.

    :param file_paths: Markdown files to lint
    :param abort_on_error: whether to abort on first error
    :return: combined return code (OR of all command return codes)
    """
    if not file_paths:
        return 0
    _LOG.info("Linting %d Markdown files", len(file_paths))
    files_str = " ".join(file_paths)
    lint_txt_script = hsystem.find_file_in_repo("lint_txt.py")
    ret = hsystem.system(
        f"{lint_txt_script} -i {files_str}",
        print_command=True,
        abort_on_error=abort_on_error,
        suppress_output=False,
    )
    return ret


def _filter_files_by_type(
    file_paths: List[str],
    *,
    py: bool,
    ipynb: bool,
    md: bool,
    include_paired_jupytext: bool = False,
) -> tuple:
    """
    Filter files by type (Python, Jupyter, Markdown).

    If no type filters are provided (all False), returns all files grouped
    by detected type.

    :param file_paths: files to filter
    :param py: include Python files
    :param ipynb: include Jupyter notebooks
    :param md: include Markdown files
    :param include_paired_jupytext:
        - if True, include .py files that are paired with Jupyter notebooks
          (normally excluded)
    :return: tuple of (python_files, jupyter_files, markdown_files)
    """
    python_files = []
    jupyter_files = []
    markdown_files = []
    if not (py or ipynb or md):
        # No filters specified; categorize all files by type.
        for f in file_paths:
            if llinutil.is_ipynb_file(f):
                jupyter_files.append(f)
            elif llinutil.is_py_file(f):
                if not (not include_paired_jupytext and
                        llinutil.is_paired_jupytext_file(f)):
                    python_files.append(f)
            elif f.endswith(".md"):
                markdown_files.append(f)
    else:
        # Filters specified; include only requested types.
        for f in file_paths:
            if py and llinutil.is_py_file(f):
                if not (not include_paired_jupytext and
                        llinutil.is_paired_jupytext_file(f)):
                    python_files.append(f)
            if ipynb and llinutil.is_ipynb_file(f):
                jupyter_files.append(f)
            if md and f.endswith(".md"):
                markdown_files.append(f)
    return python_files, jupyter_files, markdown_files


# #############################################################################
# Argument Parsing
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments for linting file selection and type filtering.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # File selection arguments (mutually exclusive).
    file_selection = parser.add_mutually_exclusive_group()
    file_selection.add_argument(
        "--modified",
        action="store_true",
        help="Lint files modified in current git client",
    )
    file_selection.add_argument(
        "--branch",
        action="store_true",
        help="Lint files modified in current branch vs master",
    )
    file_selection.add_argument(
        "-d",
        "--dir",
        type=str,
        help="Lint all files in a directory",
    )
    file_selection.add_argument(
        "-f",
        "--files",
        nargs="+",
        type=str,
        help="Explicit list of files to lint",
    )
    file_selection.add_argument(
        "--from_file",
        type=str,
        help="Read file list from a file",
    )
    file_selection.add_argument(
        "--last_commit",
        action="store_true",
        help="Lint files from last commit",
    )
    # File type filters (can be combined).
    parser.add_argument(
        "--py",
        action="store_true",
        help="Lint only Python files (exclude paired jupytext)",
    )
    parser.add_argument(
        "--ipynb",
        action="store_true",
        help="Lint only Jupyter notebooks (and sync with jupytext)",
    )
    parser.add_argument(
        "--md",
        action="store_true",
        help="Lint only Markdown files",
    )
    # Other options.
    parser.add_argument(
        "--action",
        nargs="+",
        type=str,
        # TODO(ai_gp): Use a constant with valid actions like other files.
        choices=["pre-commit", "normalize_import", "add_class_frames",
                 "sync_jupytext", "pyright", "coverage"],
        help="Specific actions to perform (default: all applicable actions). "
    )
    parser.add_argument(
        "--skip_files",
        nargs="+",
        type=str,
        help="Files to skip during linting",
    )
    parser.add_argument(
        "--abort_on_error",
        action="store_true",
        help="Abort on first linting error (default: collect all errors and exit with combined code)",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Only select files without processing them (print list of files)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


# #############################################################################
# Main
# #############################################################################


def _main(args: argparse.Namespace) -> int:
    """
    Main entry point for the linter.

    :return: combined return code from all linting operations
    """
    hdbg.init_logger(args.log_level)
    # Validate that at least one file selection option is provided.
    has_selection = any(
        [
            args.modified,
            args.branch,
            args.dir,
            args.files,
            args.from_file,
            args.last_commit,
        ]
    )
    hdbg.dassert(
        has_selection,
        "Must specify one of: --modified, --branch, --dir, --files, "
        "--from_file, --last_commit",
    )
    # Get files based on selection mode.
    file_paths = llinutil.get_files_to_check(
        files=args.files,
        from_file=args.from_file,
        skip_files=args.skip_files,
        dir_name=args.dir,
        modified=args.modified,
        last_commit=args.last_commit,
        branch=args.branch,
    )
    _LOG.info("Found %d files for linting", len(file_paths))
    # Determine if we should include paired jupytext files.
    # TODO(ai_gp): This should be done to filter only in pyright and coverage
    # since these actions work only on Python files.
    include_paired_jupytext = (
        args.action is not None
        and ("pyright" in args.action or "coverage" in args.action)
    )
    # Filter by file type.
    python_files, jupyter_files, markdown_files = _filter_files_by_type(
        file_paths,
        py=args.py,
        ipynb=args.ipynb,
        md=args.md,
        include_paired_jupytext=include_paired_jupytext,
    )
    all_files = python_files + jupyter_files + markdown_files
    _LOG.info(
        "Selected %d files for linting: %s", len(all_files), "\n".join(all_files)
    )
    # If dry_run, print files and exit.
    if args.dry_run:
        _LOG.warning("Aborting as per user request")
        return 0
    # Lint each file type and collect return codes.
    ret = 0
    if python_files:
        ret |= _lint_python(
            python_files,
            abort_on_error=args.abort_on_error,
            actions=args.action,
        )
    if jupyter_files:
        ret |= _lint_jupyter(
            jupyter_files,
            abort_on_error=args.abort_on_error,
            actions=args.action,
        )
    if markdown_files:
        ret |= _lint_markdown(
            markdown_files,
            abort_on_error=args.abort_on_error,
        )
    if not (python_files or jupyter_files or markdown_files):
        _LOG.warning("No files matched the selection and type filters")
    return ret


if __name__ == "__main__":
    parser_ = _parse()
    args_ = parser_.parse_args()
    ret_ = _main(args_)
    sys.exit(ret_)
