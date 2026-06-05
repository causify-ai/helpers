#!/usr/bin/env python

"""
Read a pickle file and pretty print its contents.

This script loads a pickle file and displays its contents in a readable format
using pprint.

# Print contents of a pickle file:
> ./print_pickle.py --input file.pkl

# Print contents with increased depth:
> ./print_pickle.py --input file.pkl --depth 5

Import as:

import dev_scripts_helpers.coding_tools.print_pickle as dsctoprpi
"""

import argparse
import logging
import os
import pickle
import pprint
from typing import Any

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# #############################################################################


def _load_pickle(file_path: str) -> Any:
    """
    Load and return contents from a pickle file.

    :param file_path: path to the pickle file
    :return: the unpickled object
    """
    _LOG.info("Loading pickle file: %s", file_path)
    with open(file_path, "rb") as f:
        data = pickle.load(f)
    _LOG.info("Successfully loaded pickle file")
    return data


def _pretty_print_data(data: Any, *, depth: int) -> None:
    """
    Pretty print the data with appropriate formatting.

    :param data: the data to print
    :param depth: maximum depth for nested structures
    """
    # Print type information.
    type_str = type(data).__name__
    _LOG.info("Data type: %s", type_str)
    print(hprint.frame(f"Type: {type_str}"))
    # Print the data.
    print(hprint.frame("Contents"))
    txt = pprint.pformat(data, depth=depth, width=100)
    print(txt)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        required=True,
        type=str,
        help="Path to the pickle file to read",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Maximum depth for nested structures (default: 3)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate input file exists.
    input_file = args.input
    hdbg.dassert(
        os.path.exists(input_file),
        "Input file does not exist:",
        input_file,
    )
    # Load and print pickle contents.
    data = _load_pickle(input_file)
    _pretty_print_data(data, depth=args.depth)


if __name__ == "__main__":
    _main(_parse())
