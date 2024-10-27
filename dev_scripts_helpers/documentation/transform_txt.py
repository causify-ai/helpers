#!/usr/bin/env python

"""
Perform one of several transformations on a txt file, e.g.,

    1) `toc`: create table of context from the current file, with 1 level
        > transform_txt.py -a toc -i % -l 1

    2) `format`: format the current file with 3 levels
        :!transform_txt.py -a format -i % --max_lev 3
        > transform_txt.py -a format -i notes/ABC.txt --max_lev 3

        - In vim
        :!transform_txt.py -a format -i % --max_lev 3
        :%!transform_txt.py -a format -i - --max_lev 3

    3) `increase`: increase level
        :!transform_txt.py -a increase -i %
        :%!transform_txt.py -a increase -i -

- The input or output can be filename or stdin (represented by '-')
- If output file is not specified then we assume that the output file is the
  same as the input
"""

# TODO(gp):
#  - Compute index number
#  - Add unit tests
#  - Make functions private


import argparse
import logging
import re

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _skip_comments(line, skip_block):
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


# #############################################################################


def table_of_content(file_name, max_lev):
    skip_block = False
    txt = hparser.read_file(file_name)
    for line in txt:
        # Skip comments.
        skip_this_line, skip_block = _skip_comments(line, skip_block)
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
                    print("%s%s" % ("    " * (i - 1), line))
                break


# #############################################################################


def format_text(in_file_name, out_file_name, max_lev):
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


# #############################################################################


def increase_chapter(in_file_name, out_file_name):
    """
    Increase the level of chapters by one for text in stdin.
    """
    skip_block = False
    txt = hparser.read_file(in_file_name)
    #
    txt_tmp = []
    for line in txt:
        skip_this_line, skip_block = _skip_comments(line, skip_block)
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


from typing import List, Dict
import pprint

# Define data structure for nested items.
class MarkdownItem:
    def __init__(self, text: str, children: List['MarkdownItem'] = None):
        self.text = text
        self.children = children or []

    def __str__(self, depth: int = 0) -> str:
        """
        Recursively convert a MarkdownItem structure to a formatted markdown string.

        :param item: The MarkdownItem object to convert.
        :param depth: The current depth level for indentation.
        :return: A string representing the nested MarkdownItem structure.

        Example:
        item = MarkdownItem("Title",
                [MarkdownItem("Subitem 1",
                    [MarkdownItem("Subsubitem 1.1")])])
        print(markdown_item_to_string(item))
            * Title
              * Subitem 1
                * Subsubitem 1.1
        """
        # Initialize the string with the current item's text and appropriate
        # indentation.
        result = "  " * depth + f"* {self.text}\n"
        # Recursively add each child item's string representation.
        for child in self.children:
            result += child.__str__(depth + 1) + "\n"
        result = result.rstrip()
        return result


def MarkdownItems_to_str(items: List[MarkdownItem]) -> str:
    hdbg.dassert_isinstance(items, list)
    txts = []
    for item in items:
        hdbg.dassert_isinstance(item, MarkdownItem)
        txts.append(str(item))
    txt = "\n".join(txts)
    return txt


def _parse_markdown(markdown: List[str], depth: int = 0) -> List[MarkdownItem]:
    """
    Recursively parse a list of markdown lines into a nested structure of
    MarkdownItems.

    :param markdown: A list of markdown lines.
    :param depth: Current depth level for nested items.
    :return: A list of MarkdownItem instances representing the nested list structure.

    Example:
        >>> _parse_markdown([
            "* Title",
            "  * Item 1",
            "    * Subitem 1",
            "  * Item 2"])
        [MarkdownItem("Title",
            [MarkdownItem("Item 1", [
                MarkdownItem("Subitem 1")
            ]),
            MarkdownItem("Item 2")
            ])
        ]
    """
    # Initialize list to hold parsed items at the current depth.
    items = []

    while markdown:
        line = markdown.pop(0).strip()

        # Check for itemized list character at current depth level.
        if line.startswith("*"):
            # Create a new item for the current line.
            current_item = MarkdownItem(text=line[1:].strip())
            # Recursively parse children if the next line has more indentation.
            if markdown and markdown[0].startswith(" " * (depth + 2) + "*"):
                current_item.children = _parse_markdown(markdown, depth + 2)
            # Append the item to the current level's list.
            items.append(current_item)
        elif line.startswith(" " * (depth - 2) + "*"):
            # Un-read the line by adding it back and exit recursion if depth mismatch.
            markdown.insert(0, line)
            break

    return items


def render_latex(items: List[MarkdownItem], depth: int = 0,
                 frame_title: str = "") -> str:
    """
    Convert a list of MarkdownItem instances into LaTeX format, with nested structures.

    :param items: A list of MarkdownItem instances representing the nested list structure.
    :param depth: Current depth level for LaTeX itemization.
    :param frame_title: Title of the frame if applicable.
    :return: A LaTeX formatted string for the nested list.
    """
    # Base LaTeX block with or without frame depending on depth and frame_title.
    if depth == 0 and frame_title:
        latex = f"\\begin{{frame}}{{{frame_title}}}\n"
    else:
        latex = ""

    # Begin itemize environment at the current depth.
    latex += "  " * depth + "\\begin{itemize}\n"

    for item in items:
        # Add item text.
        latex += "  " * (depth + 1) + f"\\item {item.text}\n"

        # Recursively add children if any.
        if item.children:
            latex += render_latex(item.children, depth + 1)

    # End itemize environment at the current depth.
    latex += "  " * depth + "\\end{itemize}\n"

    # Close frame if it's the top level with a frame title.
    if depth == 0 and frame_title:
        latex += "\\end{frame}\n"

    return latex


def markdown_to_latex(markdown: str) -> str:
    """
    Convert a nested markdown list into LaTeX format, wrapped in a frame if the list starts with "*".

    :param markdown: A list of markdown lines.
    :return: LaTeX formatted string for the nested list.

    Example:
        >>> markdown_to_latex([
            "* Title of Frame",
            "  * First item",
            "    * Subitem 1",
            "* Second item"])
        "\\begin{frame}{Title of Frame}\n
        \\begin{itemize}\n
        \\item Title of Frame\n
        \\item First item\n
        \\item Subitem 1\n
        \\item Second item\n
        \\end{itemize}\n
        \\end{frame}\n"
    """
    hdbg.dassert_isinstance(markdown, str)
    markdown = markdown.split("\n")
    # Parse markdown into a structured list.
    items = _parse_markdown(markdown)
    # Determine if the top-level item is a frame.
    if items and items[0].text.startswith("*"):
        frame_title = items[0].text
    else:
        frame_title = ""
    # Render LaTeX output from the structured list.
    txt = render_latex(items, frame_title=frame_title)
    return txt


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-a", "--action", choices=["toc", "format", "increase"], required=True
    )
    hparser.add_input_output_args(parser)
    parser.add_argument("-l", "--max_lev", default=5)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    print("cmd line: %s" % hdbg.get_command_line())
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
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
    else:
        assert 0, "Invalid cmd='%s'" % cmd


if __name__ == "__main__":
    _main(_parse())
