"""
Extract the symbols and the call graph from a directory of Python code.

The extraction has two passes:
1. `ast` collects the definitions (modules, classes, functions, methods) with
   signatures, docstrings, and line ranges, and records the position of every
   call site, base class, and attribute type
2. `jedi` resolves each recorded position to the definition it refers to, so
   `self.foo()`, `hdbg.dassert()`, and aliased imports resolve correctly

The result is a `CallGraph`, a plain data model that the HTML renderer (v1) and a
local server (v2) can both consume. See `call_graph_viewer.README.md`.

Import as:

import dev_scripts_helpers.coding_tools.call_graph.extract as dsccgex
"""

import ast
import copy
import dataclasses
import logging
import os
from typing import Any, Union

import jedi
import networkx as nx
import tqdm

from helpers import hdbg, hprint

_LOG = logging.getLogger(__name__)

# AST nodes that define a symbol.
_FuncNode = Union[ast.FunctionDef, ast.AsyncFunctionDef]
_DefNode = Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]

# #############################################################################
# Data model
# #############################################################################


@dataclasses.dataclass
class Symbol:
    """
    A named code entity: a module, a class, a function, or a method.
    """

    # Qualified name, e.g., `helpers.hdbg.dassert_eq` or `pkg.mod.Class.method`.
    id: str
    # One of `module`, `class`, `function`, `method`.
    kind: str
    # Short name, e.g., `dassert_eq`.
    name: str
    # Id of the enclosing module or class (empty for a module).
    parent: str
    # Path of the defining file, relative to the project root.
    file: str
    # 1-based inclusive line range of the definition.
    line_start: int
    line_end: int
    # Arguments and return type, e.g., `(a: int, *, b: str = '') -> str`.
    signature: str = ""
    doc: str = ""
    decorators: list[str] = dataclasses.field(default_factory=list)
    # Base classes as written in the source (classes only).
    bases: list[str] = dataclasses.field(default_factory=list)
    # Attributes as `name` or `name: type` (classes only).
    attrs: list[str] = dataclasses.field(default_factory=list)
    # UML visibility: `+` public, `#` protected (`_x`), `-` private (`__x`).
    visibility: str = "+"


@dataclasses.dataclass
class Edge:
    """
    A directed relation between two symbols.
    """

    src: str
    dst: str
    # One of `call`, `instantiate`, `inherit`, `compose`.
    kind: str
    # Lines of the source file where the relation occurs (call sites).
    lines: list[int] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class CallGraph:
    """
    The symbols and the relations extracted from a directory.
    """

    # Directory that was analyzed.
    root_dir: str
    # Directory used to name modules and to resolve absolute imports.
    project_root: str
    symbols: dict[str, Symbol] = dataclasses.field(default_factory=dict)
    edges: list[Edge] = dataclasses.field(default_factory=list)
    # Counters, e.g., resolved / unresolved / external call sites.
    stats: dict[str, int] = dataclasses.field(default_factory=dict)


# A reference found by `ast` and still to be resolved by `jedi`.
@dataclasses.dataclass
class _Ref:
    # Absolute path of the file containing the reference.
    path: str
    # Symbol that owns the reference (the caller, the subclass, the owner class).
    src: str
    # One of `call`, `inherit`, `compose`.
    kind: str
    # 1-based line and 0-based character column of the referenced name.
    line: int
    col: int


# #############################################################################
# File discovery
# #############################################################################


def get_project_root(root_dir: str) -> str:
    """
    Find the directory used to resolve absolute imports.

    Walk up from `root_dir` to the closest directory containing `.git` (a dir or
    a file, as in a submodule), so that `import helpers.hdbg` resolves when
    `root_dir` is `<repo>/helpers`. Fall back to `root_dir`.

    :param root_dir: directory of code to analyze
    :return: absolute path of the project root
    """
    _LOG.debug(hprint.to_str("root_dir"))
    root_dir = os.path.realpath(root_dir)
    curr_dir = root_dir
    project_root = root_dir
    while True:
        if os.path.exists(os.path.join(curr_dir, ".git")):
            project_root = curr_dir
            break
        parent_dir = os.path.dirname(curr_dir)
        # Stop at the filesystem root.
        if parent_dir == curr_dir:
            break
        curr_dir = parent_dir
    _LOG.debug("return=%s", project_root)
    return project_root


def find_python_files(
    root_dir: str, *, exclude_tests: bool = False
) -> list[str]:
    """
    Find the Python files under a directory.

    Skip hidden dirs, caches, virtual envs, `tmp.*` dirs, and (optionally) tests.

    :param root_dir: directory to scan
    :param exclude_tests: skip `test/` dirs and `test_*.py` files
    :return: sorted absolute paths
    """
    _LOG.debug(hprint.to_str("root_dir exclude_tests"))
    hdbg.dassert_dir_exists(root_dir)
    # Dirs that never hold the code of the project.
    skip_dirs = {"__pycache__", "node_modules", "site-packages", "build", "dist"}
    files = []
    for dir_path, dir_names, file_names in os.walk(root_dir):
        # Prune in place so that `os.walk()` does not descend into them.
        dir_names[:] = [
            d
            for d in dir_names
            if d not in skip_dirs
            and not d.startswith(".")
            and not d.startswith("tmp.")
            and not d.endswith("venv")
            and not (exclude_tests and d in ("test", "tests"))
        ]
        for file_name in file_names:
            if not file_name.endswith(".py"):
                continue
            if exclude_tests and file_name.startswith("test_"):
                continue
            files.append(os.path.realpath(os.path.join(dir_path, file_name)))
    files = sorted(files)
    _LOG.debug("return=%d files", len(files))
    return files


def _get_module_id(project_root: str, file_path: str) -> str:
    """
    Convert a file path into a dotted module name.

    E.g., `<root>/helpers/hdbg.py` -> `helpers.hdbg`, `<root>/pkg/__init__.py` ->
    `pkg`.

    :param project_root: directory used to name the modules
    :param file_path: path of the Python file
    :return: dotted module name
    """
    _LOG.debug(hprint.to_str("project_root file_path"))
    rel_path = os.path.relpath(file_path, project_root)
    base, _ = os.path.splitext(rel_path)
    parts = base.split(os.sep)
    if parts[-1] == "__init__" and len(parts) > 1:
        parts = parts[:-1]
    module_id = ".".join(parts)
    _LOG.debug("return=%s", module_id)
    return module_id


# #############################################################################
# AST helpers
# #############################################################################


def _byte_to_char_col(line_txt: str, byte_col: int) -> int:
    """
    Convert an `ast` column (UTF-8 byte offset) into a character column.

    `jedi` expects character columns, so the two differ on non-ASCII lines.

    :param line_txt: source line containing the column
    :param byte_col: UTF-8 byte offset of the column
    :return: character offset of the same column
    """
    char_col = len(line_txt.encode("utf-8")[:byte_col].decode("utf-8", "ignore"))
    return char_col


def _get_name_position(node: ast.AST) -> tuple[int, int] | None:
    """
    Get the position of the name that identifies a callee or a type.

    - `foo(...)` -> position of `foo`
    - `a.b.foo(...)` -> position of the last attribute `foo`
    - Anything else (e.g., `f()()`, `x[0]()`) has no name to resolve

    :param node: expression naming a callee or a type
    :return: (1-based line, byte column) or `None`
    """
    pos = None
    if isinstance(node, ast.Name):
        pos = (node.lineno, node.col_offset)
    elif (
        isinstance(node, ast.Attribute)
        and node.end_lineno is not None
        and node.end_col_offset is not None
    ):
        # The attribute name ends where the whole node ends.
        pos = (node.end_lineno, node.end_col_offset - len(node.attr))
    return pos


def _get_annotation_positions(annotation: ast.AST) -> list[tuple[int, int]]:
    """
    Get the positions of all the type names inside an annotation.

    E.g., `Dict[str, Foo]` -> positions of `Dict`, `str`, `Foo`.

    :param annotation: type annotation expression
    :return: list of (1-based line, byte column)
    """
    positions = []
    for node in ast.walk(annotation):
        pos = _get_name_position(node)
        # An `Attribute` such as `a.B` also contains the `Name` `a`, which
        # resolves to a module and is dropped later.
        if pos is not None:
            positions.append(pos)
    return positions


def _unparse(node: ast.AST | None) -> str:
    """
    Convert an AST node back into source text.

    :param node: AST node, or `None` for a missing node
    :return: source text, `""` for `None`
    """
    return "" if node is None else ast.unparse(node)


def _get_decorators(node: _DefNode) -> list[str]:
    """
    Get the decorators of a definition as written in the source.

    :param node: function or class definition
    :return: one source text per decorator, e.g., `['staticmethod']`
    """
    decorators = [_unparse(d) for d in node.decorator_list]
    return decorators


def _get_visibility(name: str) -> str:
    """
    Get the UML visibility of a name from the Python naming convention.

    :param name: short name of a symbol
    :return: `+` public, `#` protected (`_x`), `-` private (`__x`)
    """
    is_dunder = name.startswith("__") and name.endswith("__")
    if name.startswith("__") and not is_dunder:
        visibility = "-"
    elif name.startswith("_") and not is_dunder:
        visibility = "#"
    else:
        visibility = "+"
    return visibility


def _get_signature(node: _FuncNode, is_method: bool) -> str:
    """
    Format the signature of a function, dropping `self` / `cls` for methods.

    E.g., `def f(self, a: int, *, b: str = "x") -> str` ->
    `(a: int, *, b: str = 'x') -> str`.

    :param node: function definition
    :param is_method: whether the function is defined inside a class
    :return: arguments and return type
    """
    args = copy.copy(node.args)
    decorators = _get_decorators(node)
    if is_method and "staticmethod" not in decorators:
        # Drop the implicit first argument.
        if args.posonlyargs:
            args.posonlyargs = args.posonlyargs[1:]
        elif args.args:
            args.args = args.args[1:]
        # Defaults align with the last positional args.
        num_pos = len(args.posonlyargs) + len(args.args)
        if len(args.defaults) > num_pos:
            args.defaults = args.defaults[len(args.defaults) - num_pos :]
    signature = f"({ast.unparse(args)})"
    if node.returns is not None:
        signature += f" -> {ast.unparse(node.returns)}"
    return signature


def _get_doc(node: ast.Module | _DefNode) -> str:
    """
    Get the docstring, capped to keep the output small.

    :param node: module, function, or class definition
    :return: docstring, `""` if missing
    """
    doc = ast.get_docstring(node) or ""
    max_chars = 2000
    if len(doc) > max_chars:
        doc = doc[:max_chars] + "..."
    return doc


def _iter_defs(body: list[ast.stmt]) -> list[_DefNode]:
    """
    List the function and class definitions in a body.

    Look inside `if` / `try` / `with` / `for` / `while` blocks (e.g., `if
    TYPE_CHECKING:`) but never inside a definition, since nested functions are
    not symbols.

    :param body: statements of a module or of a class
    :return: definitions in source order
    """
    defs: list[_DefNode] = []
    for stmt in body:
        if isinstance(
            stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            defs.append(stmt)
        else:
            # Collect the statements nested in the compound statement.
            for field in ("body", "orelse", "finalbody", "handlers"):
                children = getattr(stmt, field, [])
                if field == "handlers":
                    children = [s for h in children for s in h.body]
                defs.extend(_iter_defs(children))
    return defs


def _collect_call_positions(node: ast.AST) -> list[tuple[int, int]]:
    """
    Get the callee positions of all the calls inside a function body.

    Nested functions and lambdas are attributed to the enclosing function.

    :param node: function definition
    :return: list of (1-based line, byte column)
    """
    positions = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            pos = _get_name_position(child.func)
            if pos is not None:
                positions.append(pos)
    return positions


# #############################################################################
# Symbol collection (pass 1)
# #############################################################################


def _add_refs(
    refs: list[_Ref],
    path: str,
    lines: list[str],
    src: str,
    kind: str,
    positions: list[tuple[int, int]],
) -> None:
    """
    Record positions to resolve, converting byte columns to character columns.

    :param refs: references collected so far, extended in place
    :param path: absolute path of the file containing the positions
    :param lines: source lines of the file
    :param src: id of the symbol that owns the references
    :param kind: one of `call`, `inherit`, `compose`
    :param positions: list of (1-based line, byte column)
    """
    for line, byte_col in positions:
        col = _byte_to_char_col(lines[line - 1], byte_col)
        refs.append(_Ref(path=path, src=src, kind=kind, line=line, col=col))


def _get_self_attr_name(target: ast.AST) -> str:
    """
    Get `x` from the target `self.x`, or `""` if the target is not a `self` attr.

    :param target: assignment target
    :return: attribute name, `""` if the target is not `self.<name>`
    """
    name = ""
    if (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "self"
    ):
        name = target.attr
    return name


def _collect_class_attrs(
    class_node: ast.ClassDef,
    class_id: str,
    path: str,
    lines: list[str],
    refs: list[_Ref],
) -> list[str]:
    """
    Collect the attributes of a class and the types they refer to.

    Attributes come from class-level assignments and from `self.x = ...` in
    `__init__()` / `__post_init__()`. A type that is the annotation or the
    constructor call on the right-hand side becomes a `compose` reference.

    :param class_node: class definition
    :param class_id: id of the class symbol
    :param path: absolute path of the file defining the class
    :param lines: source lines of the file
    :param refs: references collected so far, extended in place
    :return: attributes as `name` or `name: type`
    """
    attrs: dict[str, str] = {}

    def _add(name: str, annotation: ast.AST | None) -> None:
        """
        Record an attribute, keeping the first type seen for it.

        :param name: attribute name
        :param annotation: type annotation, `None` if the attribute has none
        """
        if name not in attrs or (annotation is not None and not attrs[name]):
            attrs[name] = _unparse(annotation)

    # Class-level attributes, e.g., dataclass fields.
    for stmt in class_node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            _add(stmt.target.id, stmt.annotation)
            positions = _get_annotation_positions(stmt.annotation)
            _add_refs(refs, path, lines, class_id, "compose", positions)
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    _add(target.id, None)
    # Instance attributes assigned in the initializers.
    for stmt in class_node.body:
        is_init = isinstance(stmt, ast.FunctionDef) and stmt.name in (
            "__init__",
            "__post_init__",
        )
        if not is_init:
            continue
        for node in ast.walk(stmt):
            if isinstance(node, ast.AnnAssign):
                name = _get_self_attr_name(node.target)
                if name:
                    _add(name, node.annotation)
                    positions = _get_annotation_positions(node.annotation)
                    _add_refs(refs, path, lines, class_id, "compose", positions)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    name = _get_self_attr_name(target)
                    if name:
                        _add(name, None)
                        # `self.x = Foo(...)` composes `Foo`.
                        if isinstance(node.value, ast.Call):
                            pos = _get_name_position(node.value.func)
                            if pos is not None:
                                _add_refs(
                                    refs, path, lines, class_id, "compose", [pos]
                                )
    attr_strs = [f"{n}: {t}" if t else n for n, t in attrs.items()]
    return attr_strs


def _collect_def(
    node: _DefNode,
    parent: Symbol,
    path: str,
    rel_path: str,
    lines: list[str],
    symbols: dict[str, Symbol],
    refs: list[_Ref],
) -> None:
    """
    Add the symbol for a function or class definition, and recurse into classes.

    :param node: function or class definition
    :param parent: symbol of the enclosing module or class
    :param path: absolute path of the file containing the definition
    :param rel_path: path of the file relative to the project root
    :param lines: source lines of the file
    :param symbols: symbols collected so far, extended in place
    :param refs: references collected so far, extended in place
    """
    sym_id = f"{parent.id}.{node.name}"
    _LOG.debug("Collecting the definition '%s' in '%s'", sym_id, rel_path)
    # Classes have bases and a bare name, functions have a signature.
    if isinstance(node, ast.ClassDef):
        kind = "class"
        signature = ""
        bases = [_unparse(b) for b in node.bases]
    else:
        is_method = parent.kind == "class"
        kind = "method" if is_method else "function"
        signature = _get_signature(node, is_method)
        bases = []
    # Build the symbol.
    symbol = Symbol(
        id=sym_id,
        kind=kind,
        name=node.name,
        parent=parent.id,
        file=rel_path,
        line_start=node.lineno,
        line_end=node.end_lineno or node.lineno,
        signature=signature,
        doc=_get_doc(node),
        decorators=_get_decorators(node),
        bases=bases,
        visibility=_get_visibility(node.name),
    )
    symbols[sym_id] = symbol
    if isinstance(node, ast.ClassDef):
        # Inheritance: resolve each base expression.
        for base in node.bases:
            pos = _get_name_position(base)
            if pos is not None:
                _add_refs(refs, path, lines, sym_id, "inherit", [pos])
        symbol.attrs = _collect_class_attrs(node, sym_id, path, lines, refs)
        # Members and nested classes.
        for child in _iter_defs(node.body):
            _collect_def(child, symbol, path, rel_path, lines, symbols, refs)
    else:
        # Calls inside the body, resolved later.
        positions = _collect_call_positions(node)
        _add_refs(refs, path, lines, sym_id, "call", positions)


def _collect_module(
    path: str,
    project_root: str,
    symbols: dict[str, Symbol],
    refs: list[_Ref],
) -> None:
    """
    Parse a file and add its symbols and unresolved references.

    :param path: absolute path of the Python file
    :param project_root: directory used to name the modules
    :param symbols: symbols collected so far, extended in place
    :param refs: references collected so far, extended in place
    """
    _LOG.debug(hprint.to_str("path project_root"))
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=path)
    # Split like `ast` does: only on `\n`, since the text mode of `open()`
    # already converted the other line terminators.
    lines = source.split("\n")
    rel_path = os.path.relpath(path, project_root)
    module_id = _get_module_id(project_root, path)
    # Build the symbol of the module.
    module = Symbol(
        id=module_id,
        kind="module",
        name=module_id.split(".")[-1],
        parent="",
        file=rel_path,
        line_start=1,
        line_end=max(len(lines) - (1 if source.endswith("\n") else 0), 1),
        doc=_get_doc(tree),
    )
    symbols[module_id] = module
    # Collect the definitions of the module.
    for node in _iter_defs(tree.body):
        _collect_def(node, module, path, rel_path, lines, symbols, refs)


# #############################################################################
# Reference resolution (pass 2)
# #############################################################################


def _resolve_refs(
    project_root: str,
    symbols: dict[str, Symbol],
    refs: list[_Ref],
) -> tuple[list[Edge], dict[str, int]]:
    """
    Resolve the recorded references with `jedi` and build the edges.

    A reference is resolved by jumping to the definition of the name at its
    position. The definition is then mapped back to a symbol by (file, line).
    References resolving outside the analyzed code (stdlib, third party,
    builtins) are counted as `external`, the ones `jedi` cannot infer as
    `unresolved`.

    :param project_root: directory used to resolve absolute imports
    :param symbols: symbols collected by pass 1
    :param refs: references collected by pass 1
    :return: edges (one per distinct (src, dst, kind)) and the counters
    """
    _LOG.debug(hprint.to_str("project_root len(symbols) len(refs)"))
    # Map the definition site of each symbol to its id.
    def_index: dict[tuple[str, int], str] = {}
    for sym in symbols.values():
        if sym.kind != "module":
            abs_path = os.path.realpath(os.path.join(project_root, sym.file))
            def_index[(abs_path, sym.line_start)] = sym.id
    # Group references by file so that each file is parsed by `jedi` once.
    refs_by_path: dict[str, list[_Ref]] = {}
    for ref in refs:
        refs_by_path.setdefault(ref.path, []).append(ref)
    project = jedi.Project(path=project_root)
    edges: dict[tuple[str, str, str], Edge] = {}
    stats = {"resolved": 0, "unresolved": 0, "external": 0}
    for path, path_refs in tqdm.tqdm(
        sorted(refs_by_path.items()), desc="Resolving references"
    ):
        with open(path, "r", encoding="utf-8") as f:
            script = jedi.Script(code=f.read(), path=path, project=project)
        for ref in path_refs:
            # Jump to the definition of the name at the reference position.
            names = script.goto(
                ref.line,
                ref.col,
                follow_imports=True,
                follow_builtin_imports=False,
            )
            # Map each definition found to a symbol of the analyzed code.
            targets = []
            for name in names:
                if name.module_path is None:
                    continue
                key = (os.path.realpath(str(name.module_path)), name.line)
                if key in def_index:
                    targets.append(def_index[key])
            if not targets:
                stats["external" if names else "unresolved"] += 1
                continue
            stats["resolved"] += 1
            # Add one edge per target, merging the call sites of equal edges.
            for dst in targets:
                kind = ref.kind
                dst_kind = symbols[dst].kind
                # Only classes are meaningful targets of the type relations.
                if kind in ("inherit", "compose") and dst_kind != "class":
                    continue
                # Calling a class creates an instance.
                if kind == "call" and dst_kind == "class":
                    kind = "instantiate"
                edge = edges.setdefault(
                    (ref.src, dst, kind), Edge(ref.src, dst, kind)
                )
                if ref.line not in edge.lines:
                    edge.lines.append(ref.line)
    edge_list = list(edges.values())
    _LOG.debug("return=%d edges, stats=%s", len(edge_list), stats)
    return edge_list, stats


# #############################################################################
# Public API
# #############################################################################


def extract_call_graph(
    root_dir: str, *, project_root: str = "", exclude_tests: bool = False
) -> CallGraph:
    """
    Extract the symbols and the call graph from a directory of Python code.

    :param root_dir: directory of code to analyze
    :param project_root: directory used to name modules and resolve absolute
        imports
        - Default: closest ancestor of `root_dir` containing `.git`
    :param exclude_tests: skip `test/` dirs and `test_*.py` files
    :return: the symbols and the edges
    """
    _LOG.debug(hprint.to_str("root_dir project_root exclude_tests"))
    root_dir = os.path.realpath(root_dir)
    if not project_root:
        project_root = get_project_root(root_dir)
    project_root = os.path.realpath(project_root)
    hdbg.dassert(
        root_dir == project_root or root_dir.startswith(project_root + os.sep),
        "The dir to analyze '%s' must be inside the project root '%s'",
        root_dir,
        project_root,
    )
    # Pass 1: definitions and positions to resolve.
    files = find_python_files(root_dir, exclude_tests=exclude_tests)
    hdbg.dassert_lt(0, len(files), "No Python files found in '%s'", root_dir)
    symbols: dict[str, Symbol] = {}
    refs: list[_Ref] = []
    for path in tqdm.tqdm(files, desc="Collecting symbols"):
        _collect_module(path, project_root, symbols, refs)
    _LOG.info(
        "Found %d files, %d symbols, %d references",
        len(files),
        len(symbols),
        len(refs),
    )
    # Pass 2: resolve references with `jedi`.
    edges, stats = _resolve_refs(project_root, symbols, refs)
    # Summarize the extraction in the counters.
    stats["files"] = len(files)
    for kind in ("module", "class", "function", "method"):
        stats["num_" + kind] = sum(1 for s in symbols.values() if s.kind == kind)
    cg = CallGraph(
        root_dir=root_dir,
        project_root=project_root,
        symbols=symbols,
        edges=edges,
        stats=stats,
    )
    _LOG.info("Extracted %d edges, stats=%s", len(edges), stats)
    return cg


def build_nx_graph(cg: CallGraph) -> nx.MultiDiGraph:
    """
    Build a `networkx` graph with a node per symbol and an edge per relation.

    :param cg: extracted call graph
    :return: multigraph, since two symbols can be related in more than one way
        (e.g., a class inherits from and composes another)
    """
    _LOG.debug(hprint.to_str("len(cg.symbols) len(cg.edges)"))
    graph = nx.MultiDiGraph()
    # One node per symbol.
    for sym in cg.symbols.values():
        graph.add_node(sym.id, kind=sym.kind)
    # One edge per relation, keyed by its kind.
    for edge in cg.edges:
        graph.add_edge(edge.src, edge.dst, key=edge.kind, kind=edge.kind)
    return graph


def find_symbol_id(cg: CallGraph, query: str) -> str:
    """
    Resolve a user-provided name into the id of a symbol.

    :param cg: extracted call graph
    :param query: full id (e.g., `helpers.hdbg.dassert`) or any unique dotted
        suffix (e.g., `hdbg.dassert`, `dassert`)
    :return: symbol id
    """
    _LOG.debug(hprint.to_str("query"))
    if query in cg.symbols:
        symbol_id = query
    else:
        # Match any symbol whose id ends with the query on a dot boundary.
        matches = [
            s for s in cg.symbols if s == query or s.endswith("." + query)
        ]
        hdbg.dassert_lt(0, len(matches), "No symbol matches '%s'", query)
        hdbg.dassert_eq(
            len(matches),
            1,
            "Ambiguous symbol '%s', candidates: %s",
            query,
            matches[:10],
        )
        symbol_id = matches[0]
    _LOG.debug("return=%s", symbol_id)
    return symbol_id


def prune_call_graph(cg: CallGraph, focus: str, radius: int) -> CallGraph:
    """
    Keep only the symbols within `radius` connections of `focus`.

    Connections are followed in both directions. The seeds of a class are the
    class and its methods. Enclosing classes and modules of every kept symbol
    are also kept so the result is self-contained.

    :param cg: extracted call graph
    :param focus: symbol to center on (see `find_symbol_id()`)
    :param radius: max number of connections, `0` keeps everything
    :return: new call graph
    """
    _LOG.debug(hprint.to_str("focus radius"))
    hdbg.dassert_lte(0, radius, "Radius must be non-negative")
    if radius == 0:
        pruned = cg
    else:
        focus_id = find_symbol_id(cg, focus)
        graph = build_nx_graph(cg)
        seeds = [focus_id]
        if cg.symbols[focus_id].kind == "class":
            seeds += [s.id for s in cg.symbols.values() if s.parent == focus_id]
        # Union of the balls around each seed.
        keep: set[str] = set()
        for seed in seeds:
            ball = nx.ego_graph(graph, seed, radius=radius, undirected=True)
            keep |= set(ball.nodes)
        # Add the ancestors, since a method is shown inside its class.
        for sym_id in list(keep):
            parent = cg.symbols[sym_id].parent
            while parent:
                keep.add(parent)
                parent = cg.symbols[parent].parent
        pruned = CallGraph(
            root_dir=cg.root_dir,
            project_root=cg.project_root,
            symbols={k: v for k, v in cg.symbols.items() if k in keep},
            edges=[e for e in cg.edges if e.src in keep and e.dst in keep],
            stats=dict(cg.stats),
        )
    return pruned


def call_graph_to_dict(cg: CallGraph) -> dict[str, Any]:
    """
    Convert a call graph into a JSON-serializable dict.

    :param cg: extracted call graph
    :return: dict with `root_dir`, `stats`, `symbols` (list), `edges` (list)
    """
    _LOG.debug(hprint.to_str("len(cg.symbols) len(cg.edges)"))
    data = {
        "root_dir": cg.root_dir,
        "stats": cg.stats,
        "symbols": [dataclasses.asdict(s) for s in cg.symbols.values()],
        "edges": [dataclasses.asdict(e) for e in cg.edges],
    }
    return data
