"""
Utilities for dockerized CLI scripts.

Import as:

import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
"""

import logging
import os
from typing import Any

import helpers.hio as hio
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


def create_test_file(self_: Any, txt: str, extension: str) -> str:
    """
    Create a scratch file with the given content and extension for testing.

    :param self_: test instance (needs `get_scratch_space()`)
    :param txt: file contents (leading/trailing blank lines are stripped)
    :param extension: file extension without leading dot
    :return: absolute path to the created file
    """
    file_path = os.path.join(self_.get_scratch_space(), f"input.{extension}")
    txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
    _LOG.debug("txt=\n%s", txt)
    hio.to_file(file_path, txt)
    return file_path
