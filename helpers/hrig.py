"""
Import as:

import helpers.hrig as hrig

Examples:
# Search for pattern in current directory
> rig.py TODO

# Search in specific directory
> rig.py import src

# Filter by single file type
> rig.py class . --file_types py

# Filter by multiple file types
> rig.py def . --file_types "py,md,ipynb"
"""

import subprocess
import sys
from typing import List, Optional

import dev_scripts_helpers.system_tools.lib_rig as dshstliri


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for rig utility.

    :param args: Command-line arguments (defaults to sys.argv[1:])
    :return: Exit code (0 for success, 1 for error)
    """
    if args is None:
        args = sys.argv[1:]
    parser = dshstliri.parse()
    parsed = parser.parse_args(args)
    parsed = dshstliri._parse_arguments(parsed)
    try:
        if not parsed.pattern:
            parser.print_help()
            return 0
        rg_opts = dshstliri._get_default_rg_opts()
        cmd = dshstliri._build_ripgrep_command(
            pattern=parsed.pattern,
            directory=parsed.directory,
            extensions=parsed.extensions,
            rg_opts=rg_opts,
        )
        subprocess.run(cmd)
        return 0
    except FileNotFoundError:
        return 1
