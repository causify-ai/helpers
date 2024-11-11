#!/usr/bin/env python3

"""
This is a skeleton example for a script that reads value from stdin or file,
transforms it, and writes it to stdout or file.

This pattern is useful for integrating with editors (e.g., vim).
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hparser as hparser

import snippets

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(parser)
    parser.add_argument(
        "-t", "--transform", required=True, type=str, help="Type of transform"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Parse files.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    _ = in_file_name, out_file_name
    # Read file.
    txt = hparser.read_file(in_file_name)
    # Transform.
    txt_tmp = "\n".join(txt)
    transform = args.transform
    if transform == "comment":
        txt_tmp = snippets.add_comments_one_shot_learning1(txt_tmp)
    elif transform == "docstring":
        txt_tmp = snippets.add_docstring_one_shot_learning1(txt_tmp)
    elif transform == "typehints":
        txt_tmp = snippets.add_type_hints(txt_tmp)
    else:
        raise ValueError("Invalid transform=%s" % transform)
    # Write file.
    hparser.write_file(txt_tmp.split("\n"), out_file_name)


if __name__ == "__main__":
    _main(_parse())