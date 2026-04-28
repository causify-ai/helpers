#!/usr/bin/env python
"""
Unified linter for Python, Jupyter, and Markdown files.

Selects files based on git state (modified, branch, etc.) or explicit paths,
then applies appropriate linting tools per file type.

Examples:

# Lint all modified files (default: Python and Jupyter)
> lint.py --modified

# Lint all files in branch vs master
> lint.py --branch

# Lint a specific directory
> lint.py --dir ./tutorials

# Lint specific files
> lint.py --files foo.py bar.ipynb baz.md

# Lint from a file list, Jupyter only
> lint.py --from_file filelist.txt --file_types "ipynb"

# Lint last commit
> lint.py --last_commit

# Lint only Markdown files in modified files
> lint.py --modified --file_types "md"

# Lint Markdown and Text files
> lint.py --modified --file_types "md,txt"

# Run only specific actions on modified files (pre-commit and normalize_import)
> lint.py --modified --action pre-commit normalize_import

# Run only jupytext sync on Jupyter notebooks
> lint.py --modified --file_types "ipynb" --action sync_jupytext

# Run add_class_frames only on Python files
> lint.py --modified --file_types "py" --action add_class_frames

# Run pyright type-checker on modified Python files (including paired jupytext)
> lint.py --modified --file_types "py" --action pyright

# Run coverage for test files corresponding to modified Python files
> lint.py --modified --file_types "py" --action coverage
"""

import argparse
import logging
import sys
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test_utils as hunteuti
import linters2.linter_utils as llinutil

_LOG = logging.getLogger(__name__)

_VALID_ACTIONS = set([
    "add_class_frames",
    "coverage",
    "fix_pyright",
    "normalize_import",
    "pre-commit",
    "pyright",
    "sync_jupytext",
]

# They are executed in the order given by the list.
_DEFAULT_ACTIONS = [
    "pre-commit",
    "normalize_import",
    "add_class_frames",
])

_PYRIGHT_OPTIONS = ""


# #############################################################################
# Linting Functions
# #############################################################################


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
    if actions is None:
        actions = list(_DEFAULT_ACTIONS)
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


def _is_test_file(file_path: str) -> bool:
    """Check if a file is a test file."""
    return (
        "/test/" in file_path
        or file_path.split("/")[-1].startswith("test_")
        or file_path.endswith("_test.py")
    )


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
    # Filter out test files (we only want source files)
    source_files = [f for f in file_paths if not _is_test_file(f)]
    if not source_files:
        _LOG.warning("No source files found (all files are test files)")
        return 0
    _LOG.info("Collecting coverage for %d Python files", len(source_files))
    test_files = []
    for file_path in source_files:
        test_file = hunteuti.get_test_file_for_source(file_path)
        if test_file:
            test_files.append(test_file)
            _LOG.info("Source: %s -> Test: %s", file_path, test_file)
        else:
            _LOG.warning("No test file found for: %s", file_path)
    if not test_files:
        _LOG.warning("No test files found for any of the source files")
        return 0
    test_files_str = " ".join(test_files)
    cmd = f"pytest --cov=. --cov-branch --cov-report term-missing --cov-report html {test_files_str}"
    ret = hsystem.system(
        cmd,
        print_command=True,
        abort_on_error=abort_on_error,
        suppress_output=False,
    )
    return ret


def _lint_python_files(
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
        actions = list(_DEFAULT_ACTIONS)
    _LOG.info(
        "Linting %d Python files with actions: %s", len(file_paths), actions
    )
    ret = 0
    files_str = " ".join(file_paths)
    ret |= _run_linting_actions(
        files_str,
        abort_on_error=abort_on_error,
        actions=actions,
    )
    # Pyright and coverage run on all Python files including paired jupytext.
    if "pyright" in actions:
        files_str = " ".join(file_paths)
        ret |= _run_linting_actions(
            files_str,
            abort_on_error=abort_on_error,
            actions=["pyright"],
        )
    if "coverage" in actions:
        ret |= _run_coverage(
            file_paths,
            abort_on_error=abort_on_error,
        )
    return ret


def _lint_jupyter_files(
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
        actions = list(_DEFAULT_ACTIONS)
    _LOG.info(
        "Linting %d Jupyter notebooks with actions: %s", len(file_paths), actions
    )
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


def _lint_markdown_files(
    file_paths: List[str],
    *,
    abort_on_error: bool = True,
    actions: Optional[List[str]] = None,
) -> int:
    """
    Lint Markdown files using lint_txt.py.

    :param file_paths: Markdown files to lint
    :param abort_on_error: whether to abort on first error
    :param actions: list of actions to perform (passed to lint_txt.py)
    :return: combined return code (OR of all command return codes)
    """
    if not file_paths:
        return 0
    _LOG.info("Linting %d Markdown files", len(file_paths))
    files_str = " ".join(file_paths)
    lint_txt_script = hsystem.find_file_in_repo("lint_txt.py")
    ret = hsystem.system(
        f"{lint_txt_script} --files {files_str}",
        print_command=True,
        abort_on_error=abort_on_error,
        suppress_output=False,
    )
    return ret


def _filter_files_by_type(
    file_paths: List[str],
    file_extensions: List[str],
    *,
    skip_dassert_exists: bool = False,
) -> tuple:
    """
    Filter files by type (Python, Jupyter, Markdown, Text).

    :param file_paths: files to filter
    :param file_extensions: list of file extensions to include (e.g., ["py", "ipynb", "md", "txt"])
    :param skip_dassert_exists: skip file existence checks
    :return: tuple of (python_files, jupyter_files, markdown_files)
    """
    python_files = []
    jupyter_files = []
    markdown_files = []
    # Categorize all files by type.
    for f in file_paths:
        if llinutil.is_ipynb_file(f):
            if "ipynb" not in file_extensions:
                continue
            paired_python_file = llinutil.from_ipynb_to_python_file(f)
            if not skip_dassert_exists:
                hdbg.dassert_file_exists(
                    paired_python_file,
                    "Paired Jupyter notebook file '%s' not found for Python file '%s'",
                    f,
                    paired_python_file,
                )
            jupyter_files.append(f)
        elif llinutil.is_py_file(f):
            if "py" not in file_extensions:
                continue
            if not llinutil.is_paired_jupytext_file(f):
                python_files.append(f)
        elif f.endswith(".md"):
            if "md" not in file_extensions:
                continue
            markdown_files.append(f)
        elif f.endswith(".txt"):
            if "txt" not in file_extensions:
                continue
            markdown_files.append(f)
        else:
            _LOG.warning("File type for '%s' not recognized", f)
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
        formatter_class=argparse.RawTextHelpFormatter,
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
    # File type filters.
    parser.add_argument(
        "--file_types",
        type=str,
        default="py,ipynb",
        help="Comma-separated list of file extensions to process (e.g., 'py,ipynb,md,txt')\n"
        "  Available: py (Python), ipynb (Jupyter), md (Markdown), txt (Text)\n"
        "  Default: 'py,ipynb'",
    )
    # Other options.
    parser.add_argument(
        "--action",
        nargs="+",
        type=str,
        choices=_VALID_ACTIONS,
        help="Specific actions to perform (default: all applicable actions).\n"
        "  pre-commit: Run pre-commit linters\n"
        "  normalize_import: Normalize import statements\n"
        "  add_class_frames: Add class frame decorators\n"
        "  sync_jupytext: Sync Jupyter notebooks with paired Python files\n"
        "  pyright: Run pyright type checker\n"
        "  coverage: Run pytest coverage for test files",
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
    # Parse file_types into a list of extensions
    file_extensions = [ext.strip() for ext in args.file_types.split(",")]
    _LOG.info("File extensions to process: %s", file_extensions)
    # Get files based on selection mode.
    file_paths = llinutil.get_files_to_check(
        args.files,
        args.from_file,
        args.skip_files,
        args.dir,
        args.modified,
        args.last_commit,
        args.branch,
    )
    _LOG.info("Found %d files for linting", len(file_paths))
    python_files, jupyter_files, markdown_files = _filter_files_by_type(
        file_paths,
        file_extensions,
    )
    # Report file types being selected.
    selected_types = []
    unprocessed_types = set(file_extensions)
    if "py" in file_extensions:
        selected_types.append("python")
        unprocessed_types.discard("py")
    if "ipynb" in file_extensions:
        selected_types.append("jupyter")
        unprocessed_types.discard("ipynb")
    if "md" in file_extensions:
        selected_types.append("markdown")
        unprocessed_types.discard("md")
    if "txt" in file_extensions:
        selected_types.append("text")
        unprocessed_types.discard("txt")
    # Ensure all requested file types are processed.
    hdbg.dassert_eq(
        len(unprocessed_types),
        0,
        msg=f"Unprocessed file types: {unprocessed_types}",
    )
    print(hprint.frame(f"Selecting files: {', '.join(selected_types)}"))
    all_files = python_files + jupyter_files + markdown_files
    breakdown = f"Python: {len(python_files)}, Jupyter: {len(jupyter_files)}, Markdown: {len(markdown_files)}"
    print(
        hprint.frame(
            f"Selected {len(all_files)} files for linting ({breakdown})"
        )
    )
    # Print file listings by type
    if python_files:
        print(f"\n# Python files ({len(python_files)})")
        for f in python_files:
            print(f"  {f}")
    if jupyter_files:
        print(f"\n# Jupyter files ({len(jupyter_files)})")
        for f in jupyter_files:
            print(f"  {f}")
    if markdown_files:
        print(f"\n# Markdown files ({len(markdown_files)})")
        for f in markdown_files:
            print(f"  {f}")
    # If dry_run, print files and exit.
    if args.dry_run:
        _LOG.warning("Aborting as per user request")
        return 0
    # Lint each file type and collect return codes.
    ret = 0
    if python_files:
        print(hprint.frame("Processing Python files"))
        ret |= _lint_python_files(
            python_files,
            abort_on_error=args.abort_on_error,
            actions=args.action,
        )
    if jupyter_files:
        print(hprint.frame("Processing Jupyter notebooks"))
        ret |= _lint_jupyter_files(
            jupyter_files,
            abort_on_error=args.abort_on_error,
            actions=args.action,
        )
    if markdown_files:
        print(hprint.frame("Processing Markdown files"))
        ret |= _lint_markdown_files(
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
