"""
Import as:

import helpers.lib_tasks_bash as hlitabas
"""

import logging
import os

from invoke import task

# We want to minimize the dependencies from non-standard Python packages since
# this code needs to run with minimal dependencies and without Docker.
import helpers.hfile_tree as hfiltree
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# TODO(gp): GFI: Unit test.
@task
def bash_print_path(ctx):  # type: ignore
    """
    Print the bash path.
    """
    _ = ctx
    cmd = r"echo $PATH | sed 's/:/\n/g'"
    _, ret = hsystem.system_to_string(cmd)
    paths = ret.split("\n")
    paths.sort()
    #
    all_paths = []
    # Remove empty lines.
    for path in paths:
        if path.strip() == "":
            _LOG.error("Empty path: '%s'", path)
            continue
        if not os.path.exists(path):
            _LOG.error("Dir doesn't exist: '%s'", path)
            continue
        if not os.path.isdir(path):
            _LOG.error("Not a dir: '%s'", path)
            continue
        # TODO(gp): Make it efficient.
        if paths.count(path) > 1:
            _LOG.error("Duplicate path: '%s'", path)
            continue
        all_paths.append(path)
    # Print the paths.
    _LOG.info("Valid paths:")
    for path in all_paths:
        print(path)


@task
def bash_print_tree(
    ctx,
    path=".",
    depth=0,
    include_tests=False,
    include_python=False,
    only_dirs=False,
    output="",
):
    """
    Print a directory tree, and optionally update or create a markdown file.

    ```
    # To print tree for current directory:
    > i bash_print_tree

    # Limit depth to 2 and include test files:
    > i bash_print_tree --path="devops" --depth=2 --include-tests

    # Include python files:
    > i bash_print_tree --path="devops" --include-python

    # Only show directories:
    > i bash_print_tree --path="devops" --only-dirs

    # Write the tree to file, preserving comments:
    > i bash_print_tree  --path="devops" --output="README.md"
    ```

    :param path: directory path to traverse
    :param depth: maximum depth to traverse
    :param include_tests: include test files or directories
    :param include_python: include python files
    :param only_dirs: only show directories
    :param output: path of the markdown file to create or update
    """
    _ = ctx
    tree = hfiltree.generate_tree(
        path, depth, include_tests, include_python, only_dirs, output
    )
    print(tree)
