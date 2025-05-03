#!/usr/bin/env python

"""
This script extracts the file name from a cfile.

Example:
> jackmd DataPull | extract_cfile.py -i - -o -
"""

import argparse
import logging
import re
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    hparser.add_input_output_args(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _parse_input_cfile(txt: List[str]) -> List[str]:
    files = []
    for line in txt:
        # Extract the file name from the `filename:line:text`.
        # E.g.,
        # ```
        # docs/all.workflow.explanation.md:396:- Add QA for a `DataPull` source
        # ````
        pattern = r"^(\S+):\d+:.*$"
        match = re.match(pattern, line)
        if match:
            filename = match.group(1)
            files.append(filename)
        else:
            _LOG.warning("Can't parse line: '%s", line)
    return files


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hparser.init_logger_for_input_output_transform(args)
    # Parse files.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    # Read file.
    txt = hparser.read_file(in_file_name)
    # Transform.
    files = _parse_input_cfile(txt)
    files = sorted(list(set(files)))
    # Write file.
    txt_out = "\n".join(files)
    hparser.write_file(txt_out, out_file_name)


if __name__ == "__main__":
    _main(_parse())
