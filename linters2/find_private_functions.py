#!/usr/bin/env python
"""
Find public Python functions that are only used inside their defining file.

The command reports module-level functions whose names do not start with an
underscore, which have at least one reference in their defining file, and
which have no statically-resolved reference from another scanned file.  It is
intentionally conservative around imports and exports.

Usage examples:

* Report candidates in the current repository:

  > find_private_functions.py .

* Return a failing status when candidates are found:

  > find_private_functions.py --check .

* Rename reported functions and their same-file references:

  > find_private_functions.py --fix .

Only Python identifier tokens are changed by ``--fix``.  Strings, comments,
and unrelated text are left untouched.

Import as:

import linters2.find_private_functions as lfindpriv
"""

import argparse
import ast
import io
import logging
import os
import tokenize
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# A source span is (start line, start column, end line, end column).  Python's
# AST and tokenize modules both use one-based lines and zero-based columns.
_SourceSpan = Tuple[int, int, int, int]

# These files contain framework hooks or package exports rather than ordinary
# module implementation functions.  Renaming functions in them is unsafe.
_EXCLUDED_FILE_NAMES = {
    "__init__.py",
    "conftest.py",
    "setup.py",
    "tasks.py",
}
_EXCLUDED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "outcomes",
    "tmp.scratch",
    "venv",
}


@dataclass(frozen=True)
class PrivateFunction:
    """A public function that can be made private safely by this tool."""

    file_path: str
    name: str
    lineno: int
    replacement: str
    _definition_span: _SourceSpan = field(repr=False, compare=False)
    _reference_spans: Tuple[_SourceSpan, ...] = field(
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class _FunctionDefinition:
    file_path: str
    name: str
    lineno: int
    name_span: _SourceSpan


@dataclass(frozen=True)
class _FunctionBinding:
    file_path: str
    name: str


@dataclass
class _ParsedFile:
    file_path: str
    module_name: str
    is_package: bool
    source: str
    tree: ast.Module
    definitions: Dict[str, _FunctionDefinition]
    exported_names: Set[str]
    ambiguous_names: Set[str] = field(default_factory=set)
    function_bindings: Dict[str, _FunctionBinding] = field(default_factory=dict)
    module_bindings: Dict[str, str] = field(default_factory=dict)
    wildcard_imports: List[str] = field(default_factory=list)


def _get_function_name_spans(source: str) -> Dict[Tuple[int, str], _SourceSpan]:
    """
    Get source spans for function names from Python tokens.

    ``ast.FunctionDef.col_offset`` points to ``def`` rather than the function
    name, so tokenization is used to identify the exact identifier to rename.

    :param source: Python source code
    :return: mapping from ``(line, function_name)`` to source span
    """
    ret: Dict[Tuple[int, str], _SourceSpan] = {}
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        token_list = list(tokens)
    except (IndentationError, SyntaxError, tokenize.TokenError):
        return ret
    for idx, token in enumerate(token_list[:-1]):
        if token.type != tokenize.NAME or token.string != "def":
            continue
        next_token = token_list[idx + 1]
        if next_token.type != tokenize.NAME:
            continue
        start = next_token.start
        end = next_token.end
        ret[(start[0], next_token.string)] = (
            start[0],
            start[1],
            end[0],
            end[1],
        )
    return ret


def _get_module_level_definitions(
    file_path: str,
    source: str,
    tree: ast.Module,
) -> Tuple[Dict[str, _FunctionDefinition], Set[str]]:
    """
    Extract module-level function definitions from an AST.

    Methods and nested functions are omitted because their public visibility
    can depend on runtime class and closure behavior that static imports do not
    describe reliably.

    :param file_path: source file path
    :param source: source code
    :param tree: parsed source tree
    :return: definitions keyed by function name and ambiguous names
    """
    name_spans = _get_function_name_spans(source)
    ret: Dict[str, _FunctionDefinition] = {}
    ambiguous_names: Set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        if node.name in ambiguous_names:
            continue
        # This should always be present for valid Python, but skipping the
        # definition is safer than attempting a textual replacement without a
        # precise identifier span.
        span = name_spans.get((node.lineno, node.name))
        if span is None:
            _LOG.warning(
                "Could not locate function name token for %s:%s",
                file_path,
                node.lineno,
            )
            continue
        # Duplicate module-level names are runtime-dependent and ambiguous.
        if node.name in ret:
            del ret[node.name]
            ambiguous_names.add(node.name)
            continue
        ret[node.name] = _FunctionDefinition(
            file_path=file_path,
            name=node.name,
            lineno=node.lineno,
            name_span=span,
        )
    return ret, ambiguous_names


def _extract_exported_names(tree: ast.Module) -> Set[str]:
    """Extract string names explicitly exported through ``__all__``."""
    ret: Set[str] = set()
    for node in tree.body:
        value: Optional[ast.AST] = None
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets: Iterable[ast.AST]
            if isinstance(node, ast.Assign):
                targets = node.targets
            else:
                targets = [node.target]
            if any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in targets
            ):
                value = node.value
        if value is None:
            continue
        for item in _iter_string_values(value):
            ret.add(item)
    return ret


def _iter_string_values(node: ast.AST) -> Iterable[str]:
    """Yield string constants from a simple export expression."""
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for item in node.elts:
            yield from _iter_string_values(item)
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
        yield node.value


def _get_scan_root(file_paths: Sequence[str]) -> str:
    """Get a stable root used to derive importable module names."""
    absolute_paths = [os.path.abspath(path) for path in file_paths]
    current_dir = os.path.abspath(os.getcwd())
    try:
        if all(
            os.path.commonpath([current_dir, path]) == current_dir
            for path in absolute_paths
        ):
            return current_dir
    except ValueError:
        pass
    directories = [
        path if os.path.isdir(path) else os.path.dirname(path)
        for path in absolute_paths
    ]
    return os.path.commonpath(directories)


def _module_name_from_path(file_path: str, scan_root: str) -> str:
    """Convert a Python file path to its import-style module name."""
    relative_path = os.path.relpath(file_path, scan_root)
    path_without_suffix = os.path.splitext(relative_path)[0]
    parts = path_without_suffix.replace(os.sep, "/").split("/")
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(part for part in parts if part)


def _should_skip_file(file_path: str) -> bool:
    """Return whether a discovered file is outside the analysis scope."""
    path_parts = set(os.path.normpath(file_path).split(os.sep))
    return bool(path_parts & _EXCLUDED_DIR_NAMES)


def _is_candidate_file(file_path: str) -> bool:
    """Return whether definitions in a file can be suggested for renaming."""
    if os.path.basename(file_path) in _EXCLUDED_FILE_NAMES:
        return False
    path_parts = set(os.path.normpath(file_path).split(os.sep))
    if "tmp.scratch" in path_parts:
        return True
    return not bool(path_parts & {"test", "tests"})


def _collect_python_files(paths: Sequence[str]) -> List[str]:
    """Expand files and directories into a sorted list of Python files."""
    ret: Set[str] = set()
    for path in paths:
        absolute_path = os.path.abspath(path)
        if os.path.isfile(absolute_path):
            # An explicitly named file is an intentional request, including
            # fixtures under a test scratch directory.
            if absolute_path.endswith(".py"):
                ret.add(absolute_path)
            continue
        if not os.path.isdir(absolute_path):
            _LOG.warning("Skipping path that does not exist: %s", path)
            continue
        for root, dir_names, file_names in os.walk(absolute_path):
            dir_names[:] = [
                name
                for name in dir_names
                if name not in _EXCLUDED_DIR_NAMES
            ]
            for file_name in file_names:
                file_path = os.path.join(root, file_name)
                if (
                    file_name.endswith(".py")
                    and not _should_skip_file(file_path)
                ):
                    ret.add(os.path.abspath(file_path))
    return sorted(ret)


def _resolve_relative_module(
    module_name: str,
    imported_module: Optional[str],
    level: int,
    *,
    is_package: bool,
) -> str:
    """Resolve an absolute or relative import against ``module_name``."""
    if level == 0:
        return imported_module or ""
    package_parts = module_name.split(".") if module_name else []
    # A module's package is everything before its final component.  An
    # __init__.py module name already denotes the package itself.
    if package_parts and not is_package:
        package_parts = package_parts[:-1]
    if level > len(package_parts) + 1:
        return ""
    keep = len(package_parts) - (level - 1)
    base_parts = package_parts[:max(keep, 0)]
    imported_parts = (imported_module or "").split(".")
    return ".".join(part for part in base_parts + imported_parts if part)


def _build_module_index(
    file_paths: Sequence[str],
) -> Tuple[Dict[str, _ParsedFile], Dict[str, _ParsedFile]]:
    """
    Parse source files and build indexes by module name and path.

    :param file_paths: Python source files to parse
    :return: indexes keyed by module name and absolute path
    """
    scan_root = _get_scan_root(file_paths)
    by_module: Dict[str, _ParsedFile] = {}
    by_path: Dict[str, _ParsedFile] = {}
    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                source = file_handle.read()
            tree = ast.parse(source, filename=file_path)
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            _LOG.warning("Skipping %s: %s", file_path, exc)
            continue
        module_name = _module_name_from_path(file_path, scan_root)
        definitions, ambiguous_names = _get_module_level_definitions(
            file_path,
            source,
            tree,
        )
        parsed_file = _ParsedFile(
            file_path=file_path,
            module_name=module_name,
            is_package=os.path.basename(file_path) == "__init__.py",
            source=source,
            tree=tree,
            definitions=definitions,
            exported_names=_extract_exported_names(tree),
            ambiguous_names=ambiguous_names,
        )
        if module_name in by_module:
            _LOG.warning(
                "Duplicate module name '%s'; imports will be treated as "
                "ambiguous",
                module_name,
            )
        else:
            by_module[module_name] = parsed_file
        by_path[file_path] = parsed_file
    # Add unqualified aliases for explicitly scanned files.  This supports
    # small standalone source trees (for example ``source.py`` importing
    # ``from source import helper``) while keeping duplicate basenames
    # ambiguous.
    simple_names: Dict[str, Optional[_ParsedFile]] = {}
    for parsed_file in by_path.values():
        simple_name = os.path.splitext(
            os.path.basename(parsed_file.file_path)
        )[0]
        if simple_name == "__init__":
            continue
        if simple_name in simple_names:
            simple_names[simple_name] = None
        else:
            simple_names[simple_name] = parsed_file
    for simple_name, parsed_file in simple_names.items():
        if parsed_file is not None and simple_name not in by_module:
            by_module[simple_name] = parsed_file
    return by_module, by_path


def _resolve_import_bindings(
    parsed_file: _ParsedFile,
    modules: Dict[str, _ParsedFile],
) -> None:
    """Resolve statically identifiable imports in one parsed file."""
    for node in ast.walk(parsed_file.tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    local_name = alias.asname
                    imported_module = alias.name
                else:
                    local_name = alias.name.split(".")[0]
                    imported_module = local_name
                if imported_module in modules:
                    parsed_file.module_bindings[local_name] = imported_module
        elif isinstance(node, ast.ImportFrom):
            module_name = _resolve_relative_module(
                parsed_file.module_name,
                node.module,
                node.level,
                is_package=parsed_file.is_package,
            )
            source_module = modules.get(module_name)
            for alias in node.names:
                if alias.name == "*":
                    if source_module is not None:
                        parsed_file.wildcard_imports.append(
                            source_module.file_path
                        )
                    continue
                local_name = alias.asname or alias.name
                if (
                    source_module is not None
                    and alias.name in source_module.definitions
                ):
                    parsed_file.function_bindings[local_name] = _FunctionBinding(
                        file_path=source_module.file_path,
                        name=alias.name,
                    )
                    continue
                nested_module_name = (
                    f"{module_name}.{alias.name}" if module_name else alias.name
                )
                if nested_module_name in modules:
                    parsed_file.module_bindings[local_name] = nested_module_name


def _flatten_attribute(node: ast.AST) -> Optional[List[str]]:
    """Convert ``pkg.module.function`` into its component names."""
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        parent = _flatten_attribute(node.value)
        if parent is not None:
            return parent + [node.attr]
    return None


def _resolve_attribute_binding(
    node: ast.Attribute,
    parsed_file: _ParsedFile,
    modules: Dict[str, _ParsedFile],
) -> Optional[_FunctionBinding]:
    """Resolve an imported module attribute to a function definition."""
    parts = _flatten_attribute(node)
    if parts is None or not parts or parts[0] not in parsed_file.module_bindings:
        return None
    module_name = parsed_file.module_bindings[parts[0]]
    for component in parts[1:]:
        nested_module_name = f"{module_name}.{component}"
        if nested_module_name in modules:
            module_name = nested_module_name
            continue
        source_module = modules.get(module_name)
        if source_module is not None and component in source_module.definitions:
            return _FunctionBinding(
                file_path=source_module.file_path,
                name=component,
            )
        return None
    return None


def _add_external_reference(
    external_references: Set[Tuple[str, str]],
    parsed_file: _ParsedFile,
    binding: _FunctionBinding,
) -> None:
    """Record a reference if it originates outside the definition's file."""
    if parsed_file.file_path != binding.file_path:
        external_references.add((binding.file_path, binding.name))


def _collect_references(
    modules: Dict[str, _ParsedFile],
    files_by_path: Dict[str, _ParsedFile],
) -> Tuple[Dict[Tuple[str, str], List[_SourceSpan]], Set[Tuple[str, str]]]:
    """
    Collect local and external references for all parsed files.

    :param modules: parsed files indexed by module name
    :param files_by_path: parsed files indexed by path
    :return: local reference spans and external function references
    """
    local_references: Dict[Tuple[str, str], List[_SourceSpan]] = {}
    external_references: Set[Tuple[str, str]] = set()
    for parsed_file in files_by_path.values():
        # An explicit import is an API dependency even if its imported name is
        # not subsequently loaded.  This prevents --fix from breaking imports
        # that are used for re-exporting or registration side effects.
        for binding in parsed_file.function_bindings.values():
            _add_external_reference(external_references, parsed_file, binding)
        for wildcard_path in parsed_file.wildcard_imports:
            if wildcard_path == parsed_file.file_path:
                continue
            source_module = files_by_path.get(wildcard_path)
            if source_module is not None:
                external_references.update(
                    (wildcard_path, name)
                    for name in source_module.definitions
                )

        class _ReferenceVisitor(ast.NodeVisitor):
            def visit_Import(self, node: ast.Import) -> None:
                _ = node

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                _ = node

            def visit_Name(self, node: ast.Name) -> None:
                if not isinstance(node.ctx, ast.Load):
                    return
                if node.id in parsed_file.definitions:
                    span = (
                        node.lineno,
                        node.col_offset,
                        node.end_lineno,
                        node.end_col_offset,
                    )
                    key = (parsed_file.file_path, node.id)
                    local_references.setdefault(key, []).append(span)
                binding = parsed_file.function_bindings.get(node.id)
                if binding is not None:
                    _add_external_reference(
                        external_references,
                        parsed_file,
                        binding,
                    )

            def visit_Attribute(self, node: ast.Attribute) -> None:
                binding = _resolve_attribute_binding(node, parsed_file, modules)
                if binding is not None:
                    _add_external_reference(
                        external_references,
                        parsed_file,
                        binding,
                    )
                # Avoid visiting the module alias as a plain Name (for
                # example, ``pkg`` in ``pkg.module.function``).  Visit
                # computed expressions such as ``get_module().function``.
                if not isinstance(node.value, (ast.Name, ast.Attribute)):
                    self.visit(node.value)

        _ReferenceVisitor().visit(parsed_file.tree)
    return local_references, external_references


def _build_candidates(
    files_by_path: Dict[str, _ParsedFile],
    local_references: Dict[Tuple[str, str], List[_SourceSpan]],
    external_references: Set[Tuple[str, str]],
) -> List[PrivateFunction]:
    """Build conservative private-function candidates from collected refs."""
    ret: List[PrivateFunction] = []
    for parsed_file in files_by_path.values():
        if not _is_candidate_file(parsed_file.file_path):
            continue
        for name, definition in parsed_file.definitions.items():
            if name.startswith("_"):
                continue
            if name in parsed_file.ambiguous_names:
                continue
            key = (parsed_file.file_path, name)
            references = local_references.get(key, [])
            if not references:
                continue
            if key in external_references:
                continue
            if name in parsed_file.exported_names:
                continue
            # Do not make a fix that would collide with an existing private
            # function.  The report remains useful only when the replacement is
            # unambiguous, so skip it there as well.
            replacement = f"_{name}"
            if replacement in parsed_file.definitions:
                continue
            ret.append(
                PrivateFunction(
                    file_path=parsed_file.file_path,
                    name=name,
                    lineno=definition.lineno,
                    replacement=replacement,
                    _definition_span=definition.name_span,
                    _reference_spans=tuple(references),
                )
            )
    return sorted(ret, key=lambda item: (item.file_path, item.lineno, item.name))


def find_private_functions(paths: Sequence[str]) -> List[PrivateFunction]:
    """
    Find public functions referenced only from their defining file.

    :param paths: Python files or directories to scan
    :return: sorted private-function candidates
    """
    file_paths = _collect_python_files(paths)
    if not file_paths:
        return []
    modules, files_by_path = _build_module_index(file_paths)
    for parsed_file in files_by_path.values():
        _resolve_import_bindings(parsed_file, modules)
    local_references, external_references = _collect_references(
        modules,
        files_by_path,
    )
    return _build_candidates(
        files_by_path,
        local_references,
        external_references,
    )


def _replace_spans(
    source: str,
    spans: Iterable[_SourceSpan],
    replacement: str,
) -> str:
    """Replace identifier spans from right to left without touching text."""
    lines = source.splitlines(keepends=True)
    for start_line, start_col, end_line, end_col in sorted(
        set(spans),
        reverse=True,
    ):
        if start_line != end_line:
            raise ValueError("Function identifier spans must be one line")
        line = lines[start_line - 1]
        lines[start_line - 1] = (
            line[:start_col] + replacement + line[end_col:]
        )
    return "".join(lines)


def fix_private_functions(
    candidates: Sequence[PrivateFunction],
) -> List[PrivateFunction]:
    """
    Rename candidate functions and their same-file references.

    :param candidates: candidates returned by :func:`find_private_functions`
    :return: candidates whose files were changed
    """
    candidates_by_file: Dict[str, List[PrivateFunction]] = {}
    for candidate in candidates:
        candidates_by_file.setdefault(candidate.file_path, []).append(candidate)
    changed: List[PrivateFunction] = []
    for file_path, file_candidates in candidates_by_file.items():
        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                source = file_handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            _LOG.warning("Could not read %s: %s", file_path, exc)
            continue
        updated_source = source
        for candidate in sorted(
            file_candidates,
            key=lambda item: item._definition_span,
            reverse=True,
        ):
            spans = [candidate._definition_span, *candidate._reference_spans]
            updated_source = _replace_spans(
                updated_source,
                spans,
                candidate.replacement,
            )
            changed.append(candidate)
        if updated_source != source:
            with open(
                file_path,
                "w",
                encoding="utf-8",
                newline="",
            ) as file_handle:
                file_handle.write(updated_source)
    return changed


def _parse() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Python files or directories to scan (default: current directory)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with status 1 when candidates are found",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Rename candidates and same-file references",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> int:
    """Run the private-function finder from the command line."""
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    candidates = find_private_functions(args.paths)
    if args.fix:
        candidates = fix_private_functions(candidates)
        for candidate in candidates:
            print(
                f"Fixed {candidate.file_path}:{candidate.lineno}: "
                f"{candidate.name} -> {candidate.replacement}"
            )
        return 0
    for candidate in candidates:
        print(
            f"{candidate.file_path}:{candidate.lineno}: "
            f"{candidate.name} -> {candidate.replacement}"
        )
    if args.check and candidates:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(_parse()))
