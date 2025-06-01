"""
Import as:

import helpers.lib_tasks_find as hlitafin
"""

import logging
import os
import re
from typing import Iterator, List, Optional, Tuple

from invoke import task

# We want to minimize the dependencies from non-standard Python packages since
# this code needs to run with minimal dependencies and without Docker.
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
