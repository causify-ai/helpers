"""
Inventory statically defined Python tests without importing test modules.

Import as:

import helpers.hpytest_sanity_inventory as hpysainv
"""

import ast
import dataclasses
import fnmatch
import logging
import os
import tokenize
from typing import Dict, List, Optional, Sequence, Tuple, Union

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)
_Function = Union[ast.FunctionDef, ast.AsyncFunctionDef]


# #############################################################################
# SourceTest
# #############################################################################


@dataclasses.dataclass
class SourceTest:
    """Represent one source definition, before parametrization produces cases."""

    nodeid: str
    path: str
    line: int
    excluded_reason: str
    uncertain_reason: str = ""


# #############################################################################
# SourceInventory
# #############################################################################


@dataclasses.dataclass
class SourceInventory:
    """Keep source candidates separate from files that could not be analyzed."""

    tests: Dict[str, SourceTest]
    errors: Dict[str, str]
    uncertainties: Dict[str, str] = dataclasses.field(default_factory=dict)


# #############################################################################
# AST inspection
# #############################################################################


def _matches(name: str, patterns: Sequence[str]) -> bool:
    """Apply pytest's prefix-or-glob naming convention."""
    return any(
        fnmatch.fnmatchcase(name, pattern)
        if any(char in pattern for char in "*?[")
        else name.startswith(pattern)
        for pattern in patterns
    )


def _name(node: ast.AST) -> str:
    """Read a dotted name without evaluating arbitrary expressions."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name(node.value)}.{node.attr}"
    return ""


def _is_disabled(body: List[ast.stmt]) -> bool:
    """Recognize an explicit local `__test__ = False` assignment."""
    disabled = False
    for statement in body:
        if isinstance(statement, ast.Assign):
            names = [_name(target) for target in statement.targets]
            if "__test__" in names:
                disabled = (
                    isinstance(statement.value, ast.Constant)
                    and statement.value.value is False
                )
    return disabled


def _class_test_flag(
    node: ast.ClassDef,
    classes: Dict[str, ast.ClassDef],
    visited: Tuple[str, ...],
) -> Optional[bool]:
    """Resolve literal local or inherited `__test__` flags for simple class
    trees.
    """
    if node.name in visited:
        return None
    local = None
    for statement in node.body:
        if isinstance(statement, ast.Assign):
            if any(_name(target) == "__test__" for target in statement.targets):
                if isinstance(statement.value, ast.Constant):
                    local = bool(statement.value.value)
    if local is not None:
        return local
    for base in node.bases:
        base_name = _name(base)
        if base_name in classes:
            flag = _class_test_flag(
                classes[base_name], classes, (*visited, node.name)
            )
            if flag is not None:
                return flag
    return None


def _conditional_definitions(body: List[ast.stmt]) -> List[ast.stmt]:
    """Enumerate definitions inside control flow, never inside function
    bodies.
    """
    definitions = []
    for statement in body:
        if isinstance(
            statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            definitions.append(statement)
        else:
            # Inspect statement-list children such as if/else and try/except.
            # Expressions cannot contain Python test definitions.
            for child in ast.iter_child_nodes(statement):
                if isinstance(child, ast.stmt):
                    definitions.extend(_conditional_definitions([child]))
                elif isinstance(child, (ast.ExceptHandler, ast.match_case)):
                    definitions.extend(_conditional_definitions(child.body))
    return definitions


def _class_methods(
    node: ast.ClassDef,
    classes: Dict[str, ast.ClassDef],
    visited: Tuple[str, ...],
) -> Tuple[Dict[str, _Function], bool]:
    """Resolve local inherited methods, allowing subclasses to override them."""
    methods: Dict[str, _Function] = {}
    is_unittest = False
    if node.name in visited:
        return methods, is_unittest
    visited = (*visited, node.name)
    # Reverse bases so Python's leftmost base wins for simple inheritance.
    # Runtime node IDs remain authoritative for more complex dynamic MROs.
    for base in reversed(node.bases):
        base_name = _name(base)
        is_unittest = is_unittest or base_name.split(".")[-1] == "TestCase"
        if base_name in classes:
            inherited, base_is_unittest = _class_methods(
                classes[base_name], classes, visited
            )
            methods.update(inherited)
            is_unittest = is_unittest or base_is_unittest
    for statement in node.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods[statement.name] = statement
        elif isinstance(statement, ast.Assign):
            # A non-callable override masks an inherited test as well.
            for target in statement.targets:
                methods.pop(_name(target), None)
        else:
            for definition in _conditional_definitions([statement]):
                if isinstance(
                    definition, (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    methods[definition.name] = definition
    return methods, is_unittest


def _inventory_module(
    tree: ast.Module,
    path: str,
    class_patterns: Sequence[str],
    function_patterns: Sequence[str],
) -> Dict[str, SourceTest]:
    """Inventory top-level functions and methods, including nested test
    classes.
    """
    _LOG.debug("Inventorying path='%s'", path)
    tests: Dict[str, SourceTest] = {}
    definitions = _conditional_definitions(tree.body)
    classes = {
        statement.name: statement
        for statement in definitions
        if isinstance(statement, ast.ClassDef)
    }
    conditional_ids = {id(node) for node in definitions if node not in tree.body}
    module_reason = "module __test__ = False" if _is_disabled(tree.body) else ""

    def add(function: _Function, prefix: str, reason: str) -> None:
        """Store a test candidate and explicit exclusion evidence."""
        nodeid = f"{path}::{prefix}{function.name}"
        for decorator in function.decorator_list:
            target = (
                decorator.func if isinstance(decorator, ast.Call) else decorator
            )
            if _name(target).split(".")[-1] == "fixture":
                reason = reason or "fixture definition"
        uncertainty = (
            "conditional source definition"
            if id(function) in conditional_ids
            else ""
        )
        tests[nodeid] = SourceTest(
            nodeid, path, function.lineno, reason, uncertainty
        )

    def visit_class(node: ast.ClassDef, prefix: str, reason: str) -> None:
        """Inspect a class without descending into method bodies."""
        methods, is_unittest = _class_methods(node, classes, ())
        if not (is_unittest or _matches(node.name, class_patterns)):
            return
        if id(node) in conditional_ids:
            conditional_ids.update(id(method) for method in methods.values())
        conditional_ids.update(
            id(method)
            for method in _conditional_definitions(node.body)
            if method not in node.body
        )
        reason = reason or (
            "class __test__ = False"
            if _class_test_flag(node, classes, ()) is False
            else ""
        )
        if not is_unittest and "__init__" in methods:
            reason = reason or "pytest class defines __init__"
        if not is_unittest and "__new__" in methods:
            reason = reason or "pytest class defines __new__"
        class_prefix = f"{prefix}{node.name}::"
        # unittest uses its own testMethodPrefix, not python_functions.
        patterns = ("test",) if is_unittest else function_patterns
        for name, method in methods.items():
            if _matches(name, patterns):
                add(method, class_prefix, reason)
        if not is_unittest:
            for statement in node.body:
                if isinstance(statement, ast.ClassDef):
                    visit_class(statement, class_prefix, reason)

    for statement in definitions:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _matches(statement.name, function_patterns):
                add(statement, "", module_reason)
        elif isinstance(statement, ast.ClassDef):
            visit_class(statement, "", module_reason)
    return tests


def _source_uncertainties(tree: ast.Module, path: str) -> Dict[str, str]:
    """Expose constructs whose runtime test inventory cannot be proven
    statically.
    """
    uncertainties = {}
    definitions = _conditional_definitions(tree.body)
    local_classes = {
        node.name for node in definitions if isinstance(node, ast.ClassDef)
    }
    pending: List[ast.AST] = [tree]
    while pending:
        node = pending.pop()
        # Function bodies run after collection and do not define module tests.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        pending.extend(ast.iter_child_nodes(node))
        if isinstance(node, ast.ClassDef):
            external = [
                _name(base) or "computed base"
                for base in node.bases
                if _name(base) not in local_classes
                and _name(base) not in ("object", "unittest.TestCase")
            ]
            if external or len(node.bases) > 1 or node.keywords:
                uncertainties[f"{path}:{node.lineno}"] = (
                    "Class inheritance or metaclass requires runtime resolution: "
                    + node.name
                )
        if isinstance(node, ast.Call) and _name(node.func) in (
            "exec",
            "eval",
            "setattr",
            "globals",
            "locals",
            "type",
        ):
            uncertainties[f"{path}:{node.lineno}"] = (
                "Potential dynamic test definition: " + _name(node.func)
            )
    return uncertainties


# #############################################################################
# Public inventory API
# #############################################################################


def collect_source_tests(
    root: str,
    file_patterns: Sequence[str],
    class_patterns: Sequence[str],
    function_patterns: Sequence[str],
    excluded_dirs: Sequence[str],
) -> SourceInventory:
    """
    Scan test source independently of pytest's collection exclusions.

    :param root: code directory used as the relative node-ID root
    :param file_patterns: pytest `python_files` glob patterns
    :param class_patterns: pytest `python_classes` prefixes or globs
    :param function_patterns: pytest `python_functions` prefixes or globs
    :param excluded_dirs: inventory-only directory globs, relative to `root`
    :return: source candidates and explicit parse/read error diagnostics
    """
    _LOG.debug("Scanning source root='%s'", root)
    hdbg.dassert_dir_exists(root, "Source inventory requires a directory")
    tests: Dict[str, SourceTest] = {}
    errors = {}
    uncertainties = {}
    for directory, directories, files in os.walk(root, followlinks=False):
        # Do not silently mirror pytest norecursedirs: omitted tests are the
        # very evidence this inventory is intended to discover.
        directories[:] = sorted(
            name
            for name in directories
            if not any(
                fnmatch.fnmatchcase(
                    os.path.relpath(os.path.join(directory, name), root), pattern
                )
                for pattern in excluded_dirs
            )
        )
        for filename in sorted(files):
            if not any(
                fnmatch.fnmatchcase(filename, pat) for pat in file_patterns
            ):
                continue
            full_path = os.path.join(directory, filename)
            path = os.path.relpath(full_path, root).replace(os.sep, "/")
            # Syntax failures are reported as missing evidence, never treated
            # as an empty module. No source code is executed during the scan.
            try:
                with tokenize.open(full_path) as stream:
                    tree = ast.parse(stream.read(), filename=path)
            except (SyntaxError, UnicodeError, OSError) as error:
                errors[path] = str(error)
                continue
            tests.update(
                _inventory_module(tree, path, class_patterns, function_patterns)
            )
            uncertainties.update(_source_uncertainties(tree, path))
    return SourceInventory(tests, errors, uncertainties)
