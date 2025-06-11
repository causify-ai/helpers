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


def build_tree_lines(
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


def parse_comments(old_tree: List[str]) -> Dict[str, str]:
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
        candidates = dirnames + filenames
        for name in candidates:
            low = name.lower()
            full = pathlib.Path(dirpath) / name
            is_test = (
                low.startswith("test_")
                or low == "tests"
                or low.endswith("_test.py")
            )
            is_python = full.suffix in (".py", ".ipynb")
            if full.is_dir():
                # Always include directories.
                nodes.append(full.relative_to(dir_path))
                continue
            if only_dirs:
                # Include directories and test or python files when flagged.
                if is_test and include_tests:
                    # Include test files and directories.
                    nodes.append(full.relative_to(dir_path))
                elif is_python and include_python:
                    # Include python files.
                    nodes.append(full.relative_to(dir_path))
                continue
            if is_test and not include_tests:
                # Include test files and directories.
                continue
            if is_python and not include_python:
                # Include python files.
                continue
            nodes.append(full.relative_to(dir_path))
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
            try:
                idx_start = lines.index(start_marker)
                idx_end = lines.index(end_marker)
            except ValueError as exc:
                raise RuntimeError(
                    "Couldn't find tree markers in output file"
                ) from exc
            # Parse existing file.
            prefix = lines[:idx_start]
            old_tree = lines[idx_start + 1 : idx_end]
            suffix = lines[idx_end + 1 :]
            comments = parse_comments(old_tree)
        # Build the directory tree.
        tree_block = build_tree_lines(dir_path.name, nodes, comments)
        # Build the content of the file.
        content = (
            "\n".join(prefix + [start_marker, tree_block, end_marker] + suffix)
            + "\n"
        )
        output_path.write_text(content, encoding="utf-8")
    # Return tree without markers.
    tree_block = build_tree_lines(dir_path.name, nodes, {})
    return tree_block
