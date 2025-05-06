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
import hashlib
import logging

import dev_scripts_helpers.documentation.lint_notes as dshdlino
import helpers.hdbg as hdbg
import helpers.hlatex as hlatex
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser
import helpers.hprint as hprint

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
    hparser.init_logger_for_input_output_transform(args)
    #
    cmd = args.action
    if cmd == "list":
        txt = r"""
        test: compute the hash of a string to test the flow
        format_headers: format the headers of the current file
        increase_headers_level: increase the level of the headers of the current file
        md_list_to_latex: convert a markdown list to a latex list
        md_remove_formatting: remove the formatting of the current file
        md_clean_up: clean up the current file
        md_format: format the current file
        md_format_compressed: format the current file
        md_colorize_bold_text: colorize the bold text of the current file
        """
        txt = hprint.dedent(txt)
        print(txt)
        return

    max_lev = int(args.max_lev)
    #
    in_file_name, out_file_name = hparser.parse_input_output_args(
        args, clear_screen=True
    )
    if cmd == "test":
        # Compute the hash of a string to test the flow.
        txt = hparser.read_file(in_file_name)
        txt = "\n".join(txt)
        txt = hashlib.sha256(txt.encode("utf-8")).hexdigest()
        hparser.write_file(txt, out_file_name)
    elif cmd == "format_headers":
        hmarkdo.format_headers(in_file_name, out_file_name, max_lev)
    elif cmd == "increase_headers_level":
        hmarkdo.modify_header_level(in_file_name, out_file_name, mode="increase")
    else:
        txt = hparser.read_file(in_file_name)
        txt = "\n".join(txt)
        if cmd == "toc":
            max_level = 3
            header_list = hmarkdo.extract_headers_from_markdown(
                txt, max_level=max_level
            )
            mode = "list"
            txt = hmarkdo.header_list_to_markdown(header_list, mode)
        elif cmd == "md_list_to_latex":
            txt = hlatex.markdown_list_to_latex(txt)
        elif cmd == "md_remove_formatting":
            txt = hmarkdo.remove_formatting(txt)
        elif cmd == "md_clean_up":
            txt = hmarkdo.md_clean_up(txt)
        elif cmd == "md_format":
            #txt = dshdlino.prettier_on_str(txt)
            pass
        elif cmd == "md_format_compressed":
            txt = hmarkdo.format_compressed_markdown(txt)
        elif cmd == "md_colorize_bold_text":
            txt = hmarkdo.colorize_bold_text(txt)
        else:
            raise ValueError(f"Invalid cmd='{cmd}'")
        # Format the output.
        txt = dshdlino.prettier_on_str(txt)
        hparser.write_file(txt, out_file_name)


if __name__ == "__main__":
    _main(_parse())
