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
"""

import argparse
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters2.linter_utils as llinutil

_LOG = logging.getLogger(__name__)


# #############################################################################
# Linting Functions
# #############################################################################


def _lint_python(file_paths: List[str]) -> None:
    """
    Lint Python files using pre-commit, normalize_import, and add_class_frames.

    :param file_paths: Python files to lint
    """
    if not file_paths:
        return
    _LOG.info("Linting %d Python files", len(file_paths))
    files_str = " ".join(file_paths)
    hsystem.system(f"pre-commit run --files {files_str}")
    hsystem.system(f"linters2/normalize_import.py {files_str}")
    hsystem.system(f"linters2/add_class_frames.py {files_str}")


def _lint_jupyter(file_paths: List[str]) -> None:
    """
    Lint Jupyter notebooks (same as Python) then sync with jupytext.

    :param file_paths: Jupyter notebook files to lint
    """
    if not file_paths:
        return
    _LOG.info("Linting %d Jupyter notebooks", len(file_paths))
    files_str = " ".join(file_paths)
    hsystem.system(f"pre-commit run --files {files_str}")
    hsystem.system(f"linters2/normalize_import.py {files_str}")
    hsystem.system(f"linters2/add_class_frames.py {files_str}")
    for file_path in file_paths:
        _LOG.debug("Syncing jupytext: %s", file_path)
        hsystem.system(f"jupytext --sync {file_path}")


def _lint_markdown(file_paths: List[str]) -> None:
    """
    Lint Markdown files using lint_txt.py.

    :param file_paths: Markdown files to lint
    """
    if not file_paths:
        return
    _LOG.info("Linting %d Markdown files", len(file_paths))
    for file_path in file_paths:
        _LOG.debug("Linting markdown: %s", file_path)
        hsystem.system(
            f"dev_scripts_helpers/documentation/lint_txt.py -i {file_path}"
        )


def _filter_files_by_type(
    file_paths: List[str],
    *,
    py: bool,
    ipynb: bool,
    md: bool,
) -> tuple:
    """
    Filter files by type (Python, Jupyter, Markdown).

    If no type filters are provided (all False), returns all files grouped
    by detected type.

    :param file_paths: files to filter
    :param py: include Python files
    :param ipynb: include Jupyter notebooks
    :param md: include Markdown files
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
                if not llinutil.is_paired_jupytext_file(f):
                    python_files.append(f)
            elif f.endswith(".md"):
                markdown_files.append(f)
    else:
        # Filters specified; include only requested types.
        for f in file_paths:
            if py and llinutil.is_py_file(f):
                if not llinutil.is_paired_jupytext_file(f):
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
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # File selection arguments (mutually exclusive)
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

    # File type filters (can be combined)
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

    # Other options
    parser.add_argument(
        "--skip_files",
        nargs="+",
        type=str,
        help="Files to skip during linting",
    )

    hparser.add_verbosity_arg(parser)

    return parser


# #############################################################################
# Main
# #############################################################################


def _main(args: argparse.Namespace) -> None:
    """
    Main entry point.
    """
    hdbg.init_logger(args.log_level)

    # Validate that at least one file selection option is provided
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

    # Get files based on selection mode
    file_paths = llinutil.get_files_to_check(
        files=args.files,
        from_file=args.from_file,
        skip_files=args.skip_files,
        dir_name=args.dir,
        modified=args.modified,
        last_commit=args.last_commit,
        branch=args.branch,
    )

    _LOG.info("Selected %d files for linting", len(file_paths))

    # Filter by file type
    python_files, jupyter_files, markdown_files = _filter_files_by_type(
        file_paths,
        py=args.py,
        ipynb=args.ipynb,
        md=args.md,
    )

    # Lint each file type
    if python_files:
        _lint_python(python_files)
    if jupyter_files:
        _lint_jupyter(jupyter_files)
    if markdown_files:
        _lint_markdown(markdown_files)

    if not (python_files or jupyter_files or markdown_files):
        _LOG.warning("No files matched the selection and type filters")


if __name__ == "__main__":
    parser_ = _parse()
    args_ = parser_.parse_args()
    _main(args_)
