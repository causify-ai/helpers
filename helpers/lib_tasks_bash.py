"""
Import as:

import helpers.lib_tasks_find as hlitafin
"""

import functools
import glob
import logging
import os
import re
from typing import Iterator, List, Optional, Tuple

from invoke import task

# We want to minimize the dependencies from non-standard Python packages since
# this code needs to run with minimal dependencies and without Docker.
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# pylint: disable=protected-access

@task
def print_bash(ctx):  # type: ignore
    """
    Print the bash path.
    """
    cmd = r"echo $PATH | sed 's/:/\n/g'"
    _, ret = hsystem.system_to_string(cmd)
    # Check for duplicates.
    paths = ret.split("\n")
    paths.sort()
    # Find duplicates.
    duplicates = [path for path in paths if paths.count(path) > 1]
    if len(duplicates) > 0:
        _LOG.error("Found duplicates in the path: %s", duplicates)
    # Check for dirs that don't exist.
    for path in paths:
        if not os.path.exists(path):
            _LOG.error("Dir doesn't exist: %s", path)
    # Print the paths.
    for path in paths:
        print(path)
