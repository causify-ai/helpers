#!/usr/bin/env python

"""
Import as:

import dev_scripts_helpers.remove_escape_chars as dsreesch
"""

import argparse
import logging

import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hseinout.add_input_output_args(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hseinout.init_logger_for_input_output_transform(args)
    #
    in_file_name, out_file_name = hseinout.parse_input_output_args(
        args, clear_screen=False
    )
    txt = hseinout.from_file(in_file_name)
    txt_tmp = "\n".join(txt)
    txt_tmp = hprint.remove_non_printable_chars(txt_tmp)
    txt_tmp = txt_tmp.split("\n")
    hseinout.to_file(txt_tmp, out_file_name)


if __name__ == "__main__":
    _main(_parse())
