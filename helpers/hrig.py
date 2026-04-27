# """
# Wrapper around ripgrep (rg) to search files by pattern and extension.
# Core logic module that can be imported and tested.
# """

import os
import subprocess
import sys
from typing import List, Optional


def build_ripgrep_command(
    *,
    pattern: str,
    directory: str,
    extension: Optional[str],
    rg_opts: List[str],
) -> List[str]:
    """
    Build ripgrep command with given parameters.

    :param pattern: Search pattern (supports regex)
    :param directory: Directory to search in
    :param extension: File extension filter (without dot), optional
    :param rg_opts: Additional ripgrep options
    :return: Command list ready for subprocess
    """
    cmd = ["rg"]
    if extension:
        cmd.extend(["-g", f"*.{extension}"])
    cmd.append(pattern)
    cmd.append(directory)
    cmd.extend(rg_opts)
    return cmd


def get_default_rg_opts() -> List[str]:
    """
    Get default ripgrep options.

    :return: List of default options
    """
    return ["-n", "--no-heading", "--color=never"]
