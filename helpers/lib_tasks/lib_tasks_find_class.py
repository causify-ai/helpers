"""
Parse Python class declarations for test discovery without importing
modules.

Import as:

import helpers.lib_tasks.lib_tasks_find_class as hltltficl
"""

import ast
import logging
from typing import Iterator, List, Tuple

import helpers.hio as hio

_LOG = logging.getLogger(__name__)


def _iter_class_paths(
    node: ast.AST, parents: Tuple[str, ...] = ()
) -> Iterator[Tuple[str, ...]]:
    """
    Yield syntactic class paths outside local function scopes.
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        return
    if isinstance(node, ast.ClassDef):
        parents += (node.name,)
        yield parents
        # Bases and decorators cannot contain class declarations. Walking only
        # the body also keeps every nested node under its full class ancestry.
        children = node.body
    else:
        children = ast.iter_child_nodes(node)
    for child in children:
        yield from _iter_class_paths(child, parents)


def find_class_paths(source: str, file_name: str) -> List[Tuple[str, ...]]:
    """
    Return syntactic class paths parsed from Python `source`.
    """
    module = ast.parse(source, filename=file_name)
    return list(_iter_class_paths(module))


def find_test_classes(
    class_name: str, file_names: List[str], exact_match: bool
) -> List[str]:
    """
    Find matching classes and return deterministic pytest node IDs.
    """
    result = []
    for file_name in file_names:
        source = hio.from_file(file_name)
        try:
            class_paths = find_class_paths(source, file_name)
        except SyntaxError as error:
            _LOG.warning(
                "Skipping malformed Python file '%s': %s (line %s)",
                file_name,
                error.msg,
                error.lineno,
            )
            continue
        for class_path in class_paths:
            found_class_name = class_path[-1]
            matches = (
                found_class_name == class_name
                if exact_match
                else class_name in found_class_name
            )
            if matches:
                pytest_path = "::".join(class_path)
                result.append(f"{file_name}::{pytest_path}")
    return sorted(set(result))
