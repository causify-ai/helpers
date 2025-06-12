"""
Import as:

import helpers.hfile_tree as hfiltree
"""

import logging
import os
import pathlib
import re
from typing import Dict, List

_LOG = logging.getLogger(__name__)


def _build_tree_lines(
    dir_name: str,
    nodes: List[pathlib.Path],
    comments: Dict[str, str],
) -> str:
    """
    Build the text lines for the directory tree while preserving inline
    comments.

    :param dir_name: the directory name
    :param nodes: relative paths under the given directory
    :param comments: inline comments from existing file
    :return: a formatted tree

    Example output:
    ```
    devops
    - __init__.py
    - compose
      - __init__.py
      - tmp.docker-compose.yml
    - docker_build
      - create_users.sh
      - dev.Dockerfile
      - dockerignore.dev
      - dockerignore.prod
      - etc_sudoers
      - fstab
      - install_cprofile.sh
      - install_dind.sh
      - install_os_packages.sh
      - install_publishing_tools.sh
      - install_python_packages.sh
      - pip_list.txt
      - poetry.lock
      - poetry.toml
      - prod.Dockerfile
      - pyproject.python_data_stack.toml
      - pyproject.toml
      - update_os.sh
      - utils.sh
    - docker_run
      - bashrc
      - docker_setenv.sh
      - entrypoint.sh
      - run_jupyter_server.sh
    - env
      - default.env
    ```
    """
    lines = [dir_name]
    for rel in nodes:
        indent = "  " * (len(rel.parts) - 1)
        key = "/".join(rel.parts)
        suffix = comments.get(key, "")
        lines.append(f"{indent}- {rel.name}{suffix}".rstrip())
    return "\n".join(lines)


def _parse_comments(old_tree: List[str]) -> Dict[str, str]:
    """
    Parse existing tree lines to extract inline comments.

    :param old_tree: the existing tree block
    :return: inline comments and indentations
    """
    comments: Dict[str, str] = {}
    stack: List[str] = []
    for line in old_tree:
        # Find indents, bullet points, name, and inline comments.
        match = re.match(r"^(\s*)-\s+([^\s#]+)(\s*#.*)?$", line)
        if not match:
            continue
        indent, name, suffix = match.groups()
        level = len(indent) // 2
        stack = stack[:level]
        stack.append(name)
        key = "/".join(stack)
        comments[key] = suffix or ""
    return comments


def get_tree_nodes(
    dir_path: pathlib.Path,
    depth: int,
    include_tests: bool,
    include_python: bool,
    only_dirs: bool,
) -> List[pathlib.Path]:
    """
    Get relative paths under the given directory based on filters.

    Filters include:
    - Test files and directories
    - Python files

    :param dir_path: the directory path
    :param depth: maximum depth to traverse
    :param include_tests: include test files or directories
    :param include_python: only show python files
    :param only_dirs: only show directories
    :return: all relative paths that match the specified flags
    """
    nodes: List[pathlib.Path] = []
    for dirpath, dirnames, filenames in os.walk(dir_path):
        rel_dir = pathlib.Path(dirpath).relative_to(dir_path)
        level = len(rel_dir.parts)
        if 0 < depth <= level:
            # Stop pruning on given depth.
            dirnames[:] = []
            continue
        if not include_tests:
            # Prune out test directories.
            filtered = []
            for d in dirnames:
                dir_lower = d.lower()
                if not (
                    dir_lower.startswith("test_")
                    or dir_lower in {"test", "tests"}
                ):
                    filtered.append(d)
            dirnames[:] = filtered
        candidates = dirnames + filenames
        for name in candidates:
            full_path = pathlib.Path(dirpath) / name
            rel_path = full_path.relative_to(dir_path)
            name_lower = name.lower()
            is_dir = full_path.is_dir()
            is_test_name = name_lower.startswith("test_") or name_lower in {
                "test",
                "tests",
            }
            is_test = is_test_name or name_lower.endswith("_test.py")
            is_python = full_path.suffix in {".py", ".ipynb"}
            if is_dir:
                # Always include directories.
                nodes.append(rel_path)
                continue
            # Flag filter to include test or python files.
            allowed_by_flag = (include_tests and is_test) or (
                include_python and is_python
            )
            if only_dirs:
                include_file = allowed_by_flag
            else:
                include_file = allowed_by_flag or (
                    not is_test
                    and not is_python
                    and not include_tests
                    and not include_python
                )
            if include_file:
                nodes.append(rel_path)
    nodes.sort()
    return nodes


def generate_tree(
    path: str,
    depth: int,
    include_tests: bool,
    include_python: bool,
    only_dirs: bool,
    output: str,
) -> str:
    """
    Generate a directory tree, and optionally update or create a markdown file.

    :param path: directory path to traverse
    :param depth: maximum depth to traverse
    :param include_tests: include test files or directories
    :param include_python: include show python files
    :param only_dirs: only show directories
    :param output: path of the markdown file to create or update
    """
    dir_path = pathlib.Path(path).resolve()
    nodes = get_tree_nodes(
        dir_path, depth, include_tests, include_python, only_dirs
    )
    _LOG.debug("Collected %d nodes under '%s'", len(nodes), dir_path)
    if output:
        output_path = pathlib.Path(output)
        start_marker = f"<!-- tree:start:{dir_path.name} -->"
        end_marker = "<!-- tree:end -->"
        prefix = []
        suffix = []
        comments = {}
        if output_path.exists():
            # Parse inline comments.
            file = output_path.read_text(encoding="utf-8")
            lines = file.splitlines()
            _LOG.debug("Reading existing file '%s' for markers", output_path)
            try:
                idx_start = lines.index(start_marker)
                idx_end = lines.index(end_marker)
                _LOG.debug("Markers found at lines %d–%d", idx_start, idx_end)
            except ValueError as exc:
                raise RuntimeError(
                    "Couldn't find tree markers in output file."
                ) from exc
            # Parse existing file.
            prefix = lines[:idx_start]
            old_tree = lines[idx_start + 1 : idx_end]
            suffix = lines[idx_end + 1 :]
            comments = _parse_comments(old_tree)
        # Build the directory tree.
        tree_block = _build_tree_lines(dir_path.name, nodes, comments)
        # Build the content of the file.
        content = (
            "\n".join(prefix + [start_marker, tree_block, end_marker] + suffix)
            + "\n"
        )
        output_path.write_text(content, encoding="utf-8")
        _LOG.debug("Writing updated tree to '%s'", output_path)
    # Return tree without markers.
    tree_block = _build_tree_lines(dir_path.name, nodes, {})
    return tree_block
