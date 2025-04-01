#!/usr/bin/env python

"""
Perform one of several transformations on a txt file, e.g.,

1) `toc`: create table of context from the current file, with 1 level
    > transform_notes.py -a toc -i % -l 1

2) `format`: format the current file with 3 levels
    :!transform_notes.py -a format -i % --max_lev 3
    > transform_notes.py -a format -i notes/ABC.txt --max_lev 3

    - In vim
    :!transform_notes.py -a format -i % --max_lev 3
    :%!transform_notes.py -a format -i - --max_lev 3

3) `increase`: increase level
    :!transform_notes.py -a increase -i %
    :%!transform_notes.py -a increase -i -

4) `md_list_to_latex`: convert a markdown list to a latex list
    :!transform_notes.py -a md_list_to_latex -i %
    :%!transform_notes.py -a md_list_to_latex -i -

- The input or output can be filename or stdin (represented by '-')
- If output file is not specified then we assume that the output file is the
  same as the input
"""

import argparse
import logging
import re

import helpers.hdbg as hdbg
import helpers.hlatex as hlatex
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-a", "--action", required=True)
    hparser.add_input_output_args(parser)
    parser.add_argument("-l", "--max_lev", default=5)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=logging.ERROR, use_exec_path=True, force_white=False
    )
    #
    cmd = args.action
    max_lev = int(args.max_lev)
    #
    in_file_name, out_file_name = hparser.parse_input_output_args(
        args, clear_screen=True
    )
    if cmd == "toc":
        txt = hparser.read_file(in_file_name)
        max_level = 3
        header_list = hmarkdo.extract_headers_from_markdown(
            txt, max_level=max_level
        )
        mode = "list"
        txt_out = hmarkdo.header_list_to_markdown(header_list, mode)
        hparser.write_file(txt_out, out_file_name)
    elif cmd == "format":
        hmarkdo.format_headers(in_file_name, out_file_name, max_lev)
    elif cmd == "increase":
        hmarkdo.increase_chapter(in_file_name, out_file_name)
    elif cmd == "md_list_to_latex":
        txt = hparser.read_file(in_file_name)
        txt = "\n".join(txt)
        txt = hlatex.markdown_list_to_latex(txt)
        hparser.write_file(txt, out_file_name)
    elif cmd == "md_remove_formatting":
        txt = hparser.read_file(in_file_name)
        # TODO(gp): Move to hmarkdo
        txt = "\n".join(txt)
        # Replace bold markdown syntax with plain text.
        txt = re.sub(r"\*\*(.*?)\*\*", r"\1", txt)
        # Replace italic markdown syntax with plain text.
        txt = re.sub(r"\*(.*?)\*", r"\1", txt)
        # Replace \( ... \) math syntax with $ ... $.
        txt = re.sub(r"\\\(\s*(.*?)\s*\\\)", r"$\1$", txt)
        hparser.write_file(txt, out_file_name)
    else:
        assert 0, f"Invalid cmd='{cmd}'"


if __name__ == "__main__":
    _main(_parse())
