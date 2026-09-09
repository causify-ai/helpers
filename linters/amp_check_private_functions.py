#!/usr/bin/env python
"""
Find public functions that are only used within their defining file.

A public module-level function (i.e., a function whose name does not start
with "_") that is never referenced outside of the file where it is defined
should be private, meaning that its name should start with "_".

The check is static and conservative:

- definitions and usages are collected through `ast` parsing;
- a function is flagged only when every usage of its name within the
  searched code is inside its defining file; a function with no usage at
  all is flagged as well;
- any identifier with the same name in another file counts as a usage, so
  that dynamic references cause false negatives instead of false positives.

Note: usages are searched in the repository of the linted file (or in the
dirs passed through `--search_dirs`), so a function that is used only by
other repos is still reported; in that case the function should remain
public.

# Usage example

- Find the functions that should be private:
> amp_check_private_functions.py sample_file1.py sample_file2.py

- Search for usages also in other dirs:
> amp_check_private_functions.py --search_dirs "/src/repo1,/src/repo2" sample_file1.py

- Rename the flagged functions (and their usages within the defining file)
  to make them private:
> amp_check_private_functions.py --fix sample_file1.py

Import as:

import linters.amp_check_private_functions as lamchprfu
"""

import argparse
import ast
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)

# Map of usages by name: name -> file -> [(line number, column)].
_UsageMap = Dict[str, Dict[str, List[Tuple[int, int]]]]


# #############################################################################
# Functions that should be private
# #############################################################################


def _is_public_function(name: str) -> bool:
    """
    Return whether a function name is considered public.
    """
    ret = not name.startswith("_") and name != "main"
    return ret


def _is_dynamically_called(node: ast.AST) -> bool:
    """
    Return whether a function node is invoked dynamically through a
    decorator.

    E.g., the functions decorated with `@task` are called by `invoke` and
    not (only) from the code, so they must stay public.
    """
    for decorator in getattr(node, "decorator_list", []):
        target: Optional[ast.AST] = decorator
        if isinstance(target, ast.Call):
            target = target.func
        if isinstance(target, ast.Name) and target.id == "task":
            return True
        if isinstance(target, ast.Attribute) and target.attr == "task":
            return True
    return False


def _is_exported(tree: ast.Module, name: str) -> bool:
    """
    Return whether a name is listed in the `__all__` of a module.
    """
    for node in tree.body:
        targets: List[ast.AST] = []
        value: Optional[ast.AST] = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        if value is None:
            continue
        if not any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in targets
        ):
            continue
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            for elem in value.elts:
                if (
                    isinstance(elem, ast.Constant)
                    and isinstance(elem.value, str)
                    and elem.value == name
                ):
                    return True
    return False


def _get_public_functions(file_name: str) -> List[Tuple[str, int]]:
    """
    Get the public module-level functions defined in a file.

    :return: list of (function name, line number of the definition)
    """
    source = hio.from_file(file_name)
    tree = ast.parse(source)
    funcs = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not _is_public_function(node.name):
            continue
        if _is_dynamically_called(node):
            continue
        if _is_exported(tree, node.name):
            continue
        funcs.append((node.name, node.lineno))
    return funcs


# #############################################################################
# Usages
# #############################################################################


def _get_py_files(search_dir: str) -> List[str]:
    """
    Get all the Python files under a directory, skipping hidden dirs.

    Note: the files in the `tmp.scratch` dirs are skipped since they are
    temporary.
    """
    py_files = []
    for root, dirs, file_names in os.walk(search_dir):
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".")
            and d != "tmp.scratch"
            and not d.endswith(".egg-info")
        ]
        for file_name in file_names:
            if file_name.endswith(".py"):
                py_files.append(os.path.join(root, file_name))
    return py_files


def _collect_usages(search_dir: str) -> _UsageMap:
    """
    Collect the identifier usages of all the Python files under a dir.

    Usages are both plain names (e.g., a call `foo()`) and attributes
    (e.g., a call `module.foo()`).

    :return: map of usages in the format `_UsageMap`
    """
    usages: _UsageMap = {}
    for py_file in _get_py_files(search_dir):
        py_file = os.path.abspath(py_file)
        source = hio.from_file(py_file)
        try:
            tree = ast.parse(source)
        except SyntaxError as ex:
            _LOG.debug("Could not parse file '%s': %s", py_file, ex)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                name = node.id
            elif isinstance(node, ast.Attribute):
                name = node.attr
            else:
                continue
            file_usages = usages.setdefault(name, {})
            file_usages.setdefault(py_file, []).append(
                (node.lineno, node.col_offset)
            )
    return usages


def _find_private_function_candidates(
    file_name: str, usages: _UsageMap
) -> List[Tuple[str, int]]:
    """
    Find the public functions of a file that are only used within it.

    A function is a candidate when every usage of its name within the
    searched code is inside its defining file; functions with no usage at
    all are candidates as well.

    :param usages: map of usages in the format `_UsageMap`
    :return: list of (function name, line number of the definition)
    """
    file_name = os.path.abspath(file_name)
    candidates = []
    for name, line_num in _get_public_functions(file_name):
        locs = usages.get(name, {})
        is_used_externally = any(loc_file != file_name for loc_file in locs)
        if is_used_externally:
            continue
        candidates.append((name, line_num))
    return candidates


# #############################################################################
# _CheckPrivateFunctions
# #############################################################################


class _CheckPrivateFunctions(liaction.Action):
    """
    Check for public functions that are only used within their defining
    file.
    """

    def __init__(self, search_dirs: Optional[List[str]] = None) -> None:
        super().__init__()
        self._search_dirs = search_dirs
        self._usages: Optional[_UsageMap] = None

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_py(file_name):
            # Apply only to Python files.
            return []
        if liutils.is_init_py(file_name) or liutils.is_test_code(file_name):
            return []
        if self._usages is None:
            search_dirs = self._search_dirs
            if search_dirs is None:
                search_dirs = [_get_repo_root(file_name)]
            _LOG.debug("Collecting usages from %s dir(s)", len(search_dirs))
            usages: _UsageMap = {}
            for search_dir in search_dirs:
                cur_usages = _collect_usages(search_dir)
                for name, locs in cur_usages.items():
                    file_usages = usages.setdefault(name, {})
                    for loc_file, positions in locs.items():
                        file_usages.setdefault(loc_file, []).extend(positions)
            self._usages = usages
        candidates = _find_private_function_candidates(file_name, self._usages)
        output = [
            f"{file_name}:{line_num}: the function '{name}' is only used"
            f" within this file and should be renamed to '_{name}'"
            for name, line_num in candidates
        ]
        return output


def _get_repo_root(file_name: str) -> str:
    """
    Return the dir to search for usages of a file.

    This is the root of the repository containing the file, or the dir of
    the file when the repository can't be determined (e.g., the file is in
    a tmp dir).
    """
    try:
        repo_root = hgit.find_git_root(file_name)
    except Exception as ex:  # pylint: disable=broad-except
        _LOG.debug("Could not find the git root of '%s': %s", file_name, ex)
        repo_root = os.path.dirname(os.path.abspath(file_name))
    return repo_root


# #############################################################################
# Fix mode
# #############################################################################


def _get_rename_edits(
    file_name: str, name: str
) -> List[Tuple[int, int, int, str]]:
    """
    Get the position-exact edits to rename a function within its file.

    :return: list of (line number, start col, end col, new text) edits
    """
    new_name = "_" + name
    source = hio.from_file(file_name)
    tree = ast.parse(source)
    lines = source.split("\n")
    edits = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name != name:
                continue
            line = lines[node.lineno - 1]
            m = re.search(r"\bdef\s+", line)
            hdbg.dassert(
                m is not None,
                "Can't find 'def' for '%s' in line '%s'",
                name,
                line,
            )
            start = m.end()  # type: ignore[union-attr]
            hdbg.dassert(
                line.startswith(name, start),
                "Expected '%s' right after 'def' in line '%s'",
                name,
                line,
            )
            edits.append((node.lineno, start, start + len(name), new_name))
        elif isinstance(node, ast.Name):
            if node.id == name:
                edits.append(
                    (
                        node.lineno,
                        node.col_offset,
                        node.col_offset + len(name),
                        new_name,
                    )
                )
        elif isinstance(node, ast.Attribute):
            if node.attr == name:
                end_lineno = node.end_lineno
                end_col = node.end_col_offset
                hdbg.dassert(end_lineno is not None)
                hdbg.dassert(end_col is not None)
                # The attribute name is at the end of the node.
                edits.append(
                    (
                        end_lineno,  # type: ignore[arg-type]
                        end_col - len(name),  # type: ignore[operator]
                        end_col,
                        new_name,
                    )
                )
    # Ensure that there are no overlapping edits.
    by_line: Dict[int, List[Tuple[int, int, int, str]]] = {}
    for edit in edits:
        by_line.setdefault(edit[0], []).append(edit)
    for line_edits in by_line.values():
        line_edits.sort(key=lambda e: e[1])
        for prev, cur in zip(line_edits, line_edits[1:]):
            hdbg.dassert_lte(prev[2], cur[1])
    return edits


def _fix_file(file_name: str, search_dirs: List[str]) -> List[str]:
    """
    Rename the flagged public functions of a file to make them private.

    The functions and their usages within the defining file are renamed;
    the files other than the defining file are never touched.

    :param search_dirs: dirs to search for usages
    :return: list of messages describing the renames
    """
    file_name = os.path.abspath(file_name)
    usages: _UsageMap = {}
    for search_dir in search_dirs:
        cur_usages = _collect_usages(search_dir)
        for name, locs in cur_usages.items():
            file_usages = usages.setdefault(name, {})
            for loc_file, positions in locs.items():
                file_usages.setdefault(loc_file, []).extend(positions)
    candidates = _find_private_function_candidates(file_name, usages)
    all_edits = []
    for name, line_num in candidates:
        all_edits.extend(_get_rename_edits(file_name, name))
        _LOG.debug("Renaming function '%s' in '%s'", name, file_name)
    if all_edits:
        lines = hio.from_file(file_name).split("\n")
        # Apply the edits bottom-up so that the positions stay valid.
        for line_num, start, end, new_text in sorted(all_edits, reverse=True):
            line = lines[line_num - 1]
            lines[line_num - 1] = line[:start] + new_text + line[end:]
        source = "\n".join(lines)
        # Verify that the file is still valid Python code.
        ast.parse(source)
        hio.to_file(file_name, source)
    output = [
        f"{file_name}:{line_num}: renamed '{name}' to '_{name}'"
        for name, line_num in candidates
    ]
    return output


# #############################################################################
# Command line
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "files",
        nargs="+",
        action="store",
        type=str,
        help="Files to process",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Rename the flagged functions to make them private",
    )
    parser.add_argument(
        "--search_dirs",
        action="store",
        type=str,
        default=None,
        help="Comma-separated list of dirs to search for usages; by default"
        " only the repo of the linted file is searched",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    search_dirs: Optional[List[str]] = None
    if args.search_dirs is not None:
        search_dirs = args.search_dirs.split(",")
    if args.fix:
        if search_dirs is None:
            # Without explicit search dirs, search the dir of each file.
            search_dirs = []
            for file_name in args.files:
                file_dir = os.path.dirname(os.path.abspath(file_name))
                if file_dir not in search_dirs:
                    search_dirs.append(file_dir)
        for file_name in args.files:
            msgs = _fix_file(file_name, search_dirs)
            print("\n".join(msgs))
    else:
        action = _CheckPrivateFunctions(search_dirs=search_dirs)
        action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
