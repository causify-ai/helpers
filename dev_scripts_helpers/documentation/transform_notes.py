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

- The input or output can be filename or stdin (represented by '-')
- If output file is not specified then we assume that the output file is the
  same as the input
"""

# TODO(gp):
#  - Compute index number
#  - Separate code into a library
#  - Add unit tests
#  - Make functions private


import argparse
import logging
import re
from typing import Tuple

import helpers.hdbg as hdbg
import helpers.hpandoc as hpandoc
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


# TODO(gp): Move all these transforms in helpers/transform_text.py

def skip_comments(line: str, skip_block: bool) -> Tuple[bool, bool]:
    """
    Skip comments in the given line and handle comment blocks.

    Comments are like:
    - Single line: %% This is a comment
    - Block: <!-- This is a comment -->

    :param line: The line of text to check for comments
    :param skip_block: A flag indicating if currently inside a comment block
    :return: A tuple containing a flag indicating if the line should be skipped and the updated skip_block flag
    """
    skip_this_line = False
    # Handle comment block.
    if line.startswith("<!--"):
        # Start skipping comments.
        skip_block = True
        skip_this_line = True
    if skip_block:
        skip_this_line = True
        if line.startswith("-->"):
            # End skipping comments.
            skip_block = False
        else:
            # Skip comment.
            _LOG.debug("  -> skip")
    else:
        # Handle single line comment.
        if line.startswith("%%"):
            _LOG.debug("  -> skip")
            skip_this_line = True
    return skip_this_line, skip_block


def table_of_content(file_name: str, max_lev: int) -> None:
    """
    Generate a table of contents from the given file, considering the specified
    maximum level of headings.

    :param file_name: The name of the file to read and generate the table of contents from
    :param max_lev: The maximum level of headings to include in the table of contents
    """
    skip_block = False
    txt = hparser.read_file(file_name)
    for line in txt:
        # Skip comments.
        skip_this_line, skip_block = skip_comments(line, skip_block)
        if False and skip_this_line:
            continue
        #
        for i in range(1, max_lev + 1):
            if line.startswith("#" * i + " "):
                if (
                    ("#########" not in line)
                    and ("///////" not in line)
                    and ("-------" not in line)
                    and ("======" not in line)
                ):
                    if i == 1:
                        print()
                    print(f"{'    ' * (i - 1)}{line}")
                break


# TODO(gp): -> format_headers
def format_text(in_file_name: str, out_file_name: str, max_lev: int) -> None:
    """
    Format the headers in the input file and write the formatted text to the
    output file.

    :param in_file_name: The name of the input file to read
    :param out_file_name: The name of the output file to write the formatted text to
    :param max_lev: The maximum level of headings to include in the formatted text
    """
    txt = hparser.read_file(in_file_name)
    #
    for line in txt:
        m = re.search(r"max_level=(\d+)", line)
        if m:
            max_lev = int(m.group(1))
            _LOG.warning("Inferred max_level=%s", max_lev)
            break
    hdbg.dassert_lte(1, max_lev)
    # Remove all headings.
    txt_tmp = []
    for line in txt:
        # Keep the comments.
        if not (
            re.match("#+ ####+", line)
            or re.match("#+ /////+", line)
            or re.match("#+ ------+", line)
            or re.match("#+ ======+", line)
        ):
            txt_tmp.append(line)
    txt = txt_tmp[:]
    # Add proper heading of the correct length.
    txt_tmp = []
    for line in txt:
        # Keep comments.
        found = False
        for i in range(1, max_lev + 1):
            if line.startswith("#" * i + " "):
                row = "#" * i + " " + "#" * (79 - 1 - i)
                txt_tmp.append(row)
                txt_tmp.append(line)
                txt_tmp.append(row)
                found = True
        if not found:
            txt_tmp.append(line)
    # TODO(gp): Remove all empty lines after a heading.
    # TODO(gp): Format title (first line capital and then small).
    hparser.write_file(txt_tmp, out_file_name)


# TODO(gp): Generalize this to also decrease the header level
# TODO(gp): -> modify_header_level
def increase_chapter(in_file_name: str, out_file_name: str) -> None:
    """
    Increase the level of chapters by one for text in stdin.

    :param in_file_name: The name of the input file to read
    :param out_file_name: The name of the output file to write the modified text to
    :return: None
    """
    skip_block = False
    txt = hparser.read_file(in_file_name)
    #
    txt_tmp = []
    for line in txt:
        skip_this_line, skip_block = skip_comments(line, skip_block)
        if skip_this_line:
            continue
        #
        line = line.rstrip(r"\n")
        for i in range(1, 5):
            if line.startswith("#" * i + " "):
                line = line.replace("#" * i + " ", "#" * (i + 1) + " ")
                break
        txt_tmp.append(line)
    #
    hparser.write_file(txt_tmp, out_file_name)


# #############################################################################


def markdown_list_to_latex(markdown: str) -> str:
    """
    Convert a markdown list to LaTeX format.

    :param markdown: The markdown text to convert
    :return: The converted LaTeX text
    """
    hdbg.dassert_isinstance(markdown, str)
    markdown = hprint.dedent(markdown)
    # Remove the first line if it's a title.
    markdown = markdown.split("\n")
    m = re.match("^(\*+ )(.*)", markdown[0])
    if m:
        title = m.group(2)
        markdown = markdown[1:]
    else:
        title = ""
    markdown = "\n".join(markdown)
    # Convert.
    txt = hpandoc.convert_pandoc_md_to_latex(markdown)
    # Remove \tightlist and empty lines.
    lines = txt.splitlines()
    lines = [line for line in lines if "\\tightlist" not in line]
    lines = [line for line in lines if line.strip() != ""]
    txt = "\n".join(lines)
    # Add the title frame.
    if title:
        txt = "\\begin{frame}{%s}" % title + "\n" + txt + "\n" + "\\end{frame}"
    return txt


# #############################################################################


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
        table_of_content(in_file_name, max_lev)
    elif cmd == "format":
        format_text(in_file_name, out_file_name, max_lev)
    elif cmd == "increase":
        increase_chapter(in_file_name, out_file_name)
    elif cmd == "md_list_to_latex":
        txt = hparser.read_file(in_file_name)
        txt = "\n".join(txt)
        txt = markdown_list_to_latex(txt)
        hparser.write_file(txt, out_file_name)
    else:
        assert 0, f"Invalid cmd='{cmd}'"


if __name__ == "__main__":
    _main(_parse())
