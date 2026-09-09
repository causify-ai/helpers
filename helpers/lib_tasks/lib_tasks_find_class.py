"""Parse Python class declarations for test discovery without importing
modules.

Import as:

import helpers.lib_tasks.lib_tasks_find_class as hltltficl
"""

import ast
import logging
from typing import Iterator, List, Sequence, Tuple

import helpers.hio as hio

_LOG = logging.getLogger(__name__)


def _iter_class_paths(
    statements: Sequence[ast.stmt], parents: Tuple[str, ...] = ()
) -> Iterator[Tuple[str, ...]]:
    """Yield module and class-nested class paths in source order."""
    for statement in statements:
        if not isinstance(statement, ast.ClassDef):
            continue
        class_path = parents + (statement.name,)
        yield class_path
        # Pytest can collect nested classes, but not classes local to a
        # function. Recurse only through class bodies to preserve that rule.
        yield from _iter_class_paths(statement.body, class_path)


def find_class_paths(source: str, file_name: str) -> List[Tuple[str, ...]]:
    """Return collectible class paths parsed from Python `source`."""
    module = ast.parse(source, filename=file_name)
    return list(_iter_class_paths(module.body))


def find_test_classes(
    class_name: str, file_names: List[str], exact_match: bool
) -> List[str]:
    """Find matching classes and return deterministic pytest node IDs."""
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
