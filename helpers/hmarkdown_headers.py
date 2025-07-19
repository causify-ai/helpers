"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import dataclasses
import logging
import re
from typing import List, Optional, Tuple, cast

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

_TRACE = False


# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.


def is_markdown_line_separator(line: str, min_repeats: int = 5) -> bool:
    """
    Check if the given line is a Markdown separator.

    This function determines if a line consists of repeated characters (`#`,
    `/`, `-`, `=`) that would indicate a markdown separator.

    :param line: current line of text being processed
    :param min_repeats: minimum number of times the characters have to be
        repeated to be considered a separator, e.g., if `min_repeats = 2`, then
        `##`, `###`, `//` are considered to be line separators, but `#`, `/` are
        not
    :return: whether the line is a separator
    """
    separator_pattern = rf"""
    \#*\s*                            # Optional leading `#` and whitespace.
    ([#/=\-])\1{{{min_repeats - 1},}} # Capture a character, then repeat it
                                      #   (`min_repeats` - 1) times.
    \s*$                              # Match only whitespace characters
                                      #   until the end of the line.
    """
    res = bool(re.match(separator_pattern, line, re.VERBOSE))
    return res


def is_header(line: str) -> Tuple[bool, int, str]:
    """
    Check if the given line is a Markdown header.

    :param line: line to check
    :return: tuple containing:
        - boolean indicating if the line is a header
        - level of the header (`0` if not a header)
        - title of the header (empty string if not a header)
    """
    # hdbg.dassert(not is_markdown_line_separator(line), "line='%s'", line)
    m = re.match(r"(#+)\s+(.*)", line)
    is_header_ = bool(m)
    if m:
        level = len(m.group(1))
        title = m.group(2)
    else:
        level = 0
        title = ""
    return is_header_, level, title


# #############################################################################
# Header processing
# #############################################################################


# TODO(gp): This could be done by processing `HeaderList`.
def extract_section_from_markdown(content: str, header_name: str) -> str:
    """
    Extract a section of text from a Markdown document based on the header
    name.

    The function identifies a section by locating the specified header
    and captures all lines until encountering another header of the same
    or higher level. Headers are identified by the '#' prefix, and their
    level is determined by the number of '#' characters.

    :param content: markdown content as a single string
    :param header_name: exact header name to extract (excluding `#`
        symbols)
    :return: extracted section as a string, including the header
        line itself and all lines until the next header of the same or
        higher level
    """
    lines = content.splitlines()
    _LOG.debug(hprint.to_str("lines"))
    extracted_lines = []
    # Level of the current header being processed.
    current_level: Optional[int] = None
    # Flag to indicate if we're inside the desired section.
    inside_section: bool = False
    found = False
    # Process each line in the markdown content.
    for line in lines:
        _LOG.debug(hprint.to_str("line"))
        # Check if the line is a markdown header.
        if line.strip().startswith("#"):
            # Determine the level of the header by counting leading '#'
            # characters.
            header_level = len(line) - len(line.lstrip("#"))
            # Extract the actual header text by stripping '#' and surrounding
            # whitespace.
            header_text = line.strip("#").strip()
            _LOG.debug(hprint.to_str("header_level, header_text"))
            # Handle the end of the desired section when encountering another
            # header.
            if inside_section:
                hdbg.dassert_is_not(current_level, None)
                current_level = cast(int, current_level)
                if header_level <= current_level:
                    break
            # Check if the current line is the desired header.
            if header_text == header_name:
                found = True
                # Set the level of the matched header.
                current_level = header_level
                # Mark that we are now inside the desired section.
                inside_section = True
        # Add the line to the output if inside the desired section.
        if inside_section:
            extracted_lines.append(line)
            _LOG.debug(hprint.to_str("extracted_lines"))
    if not found:
        raise ValueError(f"Header '{header_name}' not found")
    return "\n".join(extracted_lines)


# #############################################################################
# HeaderInfo
# #############################################################################


@dataclasses.dataclass
class HeaderInfo:
    """
    Store the header level, the description, and the line number in the
    original file.

    E.g., `(1, "Chapter 1", 5)` and `(2, "Section 1.1", 10)`
    """

    level: int
    description: str
    line_number: int

    def __init__(self, level: int, description: str, line_number: int):
        hdbg.dassert_isinstance(level, int)
        hdbg.dassert_lte(1, level)
        self.level = level
        #
        hdbg.dassert_isinstance(description, str)
        hdbg.dassert_ne(
            description,
            "",
            "Invalid HeaderInfo: %s, %s, %s",
            level,
            description,
            line_number,
        )
        self.description = description
        #
        hdbg.dassert_isinstance(line_number, int)
        hdbg.dassert_lte(1, line_number)
        self.line_number = line_number
        #
        self.children: List[HeaderInfo] = []

    def __repr__(self) -> str:
        return (
            f"HeaderInfo({self.level}, '{self.description}', {self.line_number})"
        )

    def as_tuple(self) -> Tuple[int, str, int]:
        return (self.level, self.description, self.line_number)


HeaderList = List[HeaderInfo]


def sanity_check_header_list(header_list: HeaderList) -> None:
    """
    Check that the header list is valid.

    1) The first header should be level 1.
    2) All level 1 headers are unique.
    3) Check that consecutive elements in the header list only increase by at
       most one level at a time (even if it can decrease by multiple levels).
       - E.g., the following is valid:
         ```
         # Header 1
         # Header 2
         ## Header 2.1
         ## Header 2.2
         # Header 3
         ```
       - E.g., the following is valid:
         ```
         # Header1
         ## Header 1.1
         ### Header 1.1.1
         # Header 2
         ```
       - E.g., the following is not valid:
         ```
         # Header 1
         ### Header 1.0.1
         # Header 2
         ```

    :param header_list: list of headers to validate
    """
    # 1) The first header should be level 1.
    if header_list and header_list[0].level > 1:
        _LOG.warning(
            "First header '%s' at line %s is not level 1, but %s",
            header_list[0].description,
            header_list[0].line_number,
            header_list[0].level,
        )
    # 2) All level 1 headers are unique.
    level_1_headers = [
        header.description for header in header_list if header.level == 1
    ]
    hdbg.dassert_no_duplicates(level_1_headers)
    # 3) Check that consecutive elements in the header list only increase by at
    #    most one level at a time (even if it can decrease by multiple levels).
    if len(header_list) > 1:
        for i in range(1, len(header_list)):
            hdbg.dassert_isinstance(header_list[i - 1], HeaderInfo)
            hdbg.dassert_isinstance(header_list[i], HeaderInfo)
            if header_list[i].level - header_list[i - 1].level > 1:
                msg = []
                msg.append(
                    "Consecutive headers increase by more than one level:"
                )
                msg.append(f"  {header_list[i - 1]}")
                msg.append(f"  {header_list[i]}")
                msg = "\n".join(msg)
                raise ValueError(msg)


# TODO(gp): Move sanity check outside?
def extract_headers_from_markdown(
    txt: str, max_level: int, *, sanity_check: bool = True
) -> HeaderList:
    """
    Extract headers from Markdown file and return an `HeaderList`.

    :param txt: content of the input Markdown file
    :param max_level: maximum header levels to parse (e.g., '3' parses all levels
        included `###`, but not `####`)
    :param sanity_check: whether to check that the header list is valid
    :return: generated `HeaderList`, e.g.,
        ```
        [
            (1, "Chapter 1", 5),
            (2, "Section 1.1", 10), ...]
        ```
    """
    hdbg.dassert_isinstance(txt, str)
    hdbg.dassert_lte(1, max_level)
    header_list: HeaderList = []
    # Process the input file to extract headers.
    for line_number, line in enumerate(txt.splitlines(), start=1):
        # TODO(gp): Use the iterator.
        # Skip the visual separators.
        if is_markdown_line_separator(line):
            continue
        # Get the header level and title.
        is_header_, level, title = is_header(line)
        if is_header_ and level <= max_level:
            header_info = HeaderInfo(level, title, line_number)
            header_list.append(header_info)
    # Check the header list.
    if sanity_check:
        sanity_check_header_list(header_list)
    else:
        _LOG.debug("Skipping sanity check")
    return header_list


# TODO(gp): Should it go to markdown_slides?
def extract_slides_from_markdown(
    txt: str,
) -> Tuple[HeaderList, int]:
    """
    Extract slides (i.e., sections prepended by `*`) from Markdown file and
    return an `HeaderList`.

    :param txt: content of the input Markdown file
    :return: tuple containing:
        - generated `HeaderList`
            ```
            [
                (1, "Slide 1", 5),
                (1, "Slide 2", 10), ...]
            ```
        - last line number of the file, e.g., '100'
    """
    hdbg.dassert_isinstance(txt, str)
    header_list: HeaderList = []
    # Process the input file to extract headers.
    for line_number, line in enumerate(txt.splitlines(), start=1):
        _LOG.debug("%d: %s", line_number, line)
        # TODO(gp): Use the iterator.
        # Skip the visual separators.
        if is_markdown_line_separator(line):
            continue
        # Get the header level and title.
        m = re.match(r"^\* (.*)$", line)
        is_slide = m is not None
        if is_slide:
            title = m.group(1)
            header_info = HeaderInfo(1, title, line_number)
            header_list.append(header_info)
    last_line_number = len(txt.splitlines())
    return header_list, last_line_number


def header_list_to_vim_cfile(markdown_file: str, header_list: HeaderList) -> str:
    """
    Convert a list of headers into a Vim cfile format.

    Use the generated file in Vim as:
        `:cfile <output_file>`
        Use `:cnext` and `:cprev` to navigate between headers.

    :param markdown_file: path to the input Markdown file
    :param header_list: list of headers, where each header is a tuple containing
        the line number, level, and title
    :return: generated cfile content as a string in the format:
        ```
        ...
        <file path>:<line number>:<header title>
        ...
        ```
    """
    hdbg.dassert_isinstance(header_list, list)
    _LOG.debug(hprint.to_str("markdown_file header_list"))
    output_lines = [
        f"{markdown_file}:{header_info.line_number}:{header_info.description}"
        for header_info in header_list
    ]
    output_content = "\n".join(output_lines)
    return output_content


def header_list_to_markdown(header_list: HeaderList, mode: str) -> str:
    """
    Convert a list of headers into a Markdown format.

    :param header_list: list of headers, where each header is a tuple
        containing the level, title, and line number
    :param mode: format of the output:
        - `list`: indents headers to create a nested list
        - `headers`: uses Markdown header syntax (e.g., '#', '##', '###')
    :return: generated Markdown content as a string
    """
    hdbg.dassert_isinstance(header_list, list)
    _LOG.debug(hprint.to_str("header_list mode"))
    output_lines = []
    for header_info in header_list:
        level, title, line_number = header_info.as_tuple()
        _ = line_number
        if mode == "list":
            header_prefix = "  " * (level - 1) + "-"
        elif mode == "headers":
            header_prefix = "#" * level
        else:
            raise ValueError(f"Invalid mode '{mode}'")
        output_lines.append(f"{header_prefix} {title}")
    output_content = "\n".join(output_lines)
    return output_content


# #############################################################################
# Process headers.
# #############################################################################


def format_headers(in_file_name: str, out_file_name: str, max_lev: int) -> None:
    """
    Format the headers in the input file and write the formatted text to the
    output file.

    :param in_file_name: name of the input file to read
    :param out_file_name: name of the output file to write the
        formatted text to
    :param max_lev: maximum level of headings to include in the
        formatted text
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
        if not is_markdown_line_separator(line):
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


def modify_header_level(input_text: str, level: int) -> str:
    """
    Increase or decrease the level of headings by the specified amount.

    :param input_text: input text to modify
    :param level: amount to adjust header levels (positive
        increases, negative decreases)
    :return: modified text with header levels adjusted
    """
    lines = input_text.split("\n")
    #
    txt_tmp = []
    for line in lines:
        # TODO(gp): Use the iterator.
        line = line.rstrip(r"\n")
        is_header_, current_level, title = is_header(line)
        if is_header_:
            modified_level = current_level + level
            # Ensure modified level is within valid range (1-6 for markdown headers).
            hdbg.dassert_lte(1, modified_level)
            hdbg.dassert_lte(modified_level, 6)
            line = "#" * modified_level + " " + title
        txt_tmp.append(line)
    #
    return "\n".join(txt_tmp)


# #############################################################################
# _HeaderTreeNode
# #############################################################################


# This is a different representation of the data than the one in `HeaderList`
# because it is a tree structure. So we use a different type hint.
_HeaderTree = List[HeaderInfo]


def build_header_tree(header_list: HeaderList) -> _HeaderTree:
    """
    Build a tree (list of Node objects) from the flat list.

    We assume that the level changes never jump by more than 1.

    :param header_list: flat list of headers
    :return: tree structure of headers
    """
    tree: _HeaderTree = []
    stack: _HeaderTree = []
    for node in header_list:
        if node.level == 1:
            tree.append(node)
            stack = [node]
        else:
            # Pop until we find the proper parent: one with level < current
            # level.
            while stack and stack[-1].level >= node.level:
                stack.pop()
            if stack:
                stack[-1].children.append(node)
            else:
                tree.append(node)
            stack.append(node)
    # hdbg.dassert_eq(len(header_list), len(tree))
    # hdbg.dassert_eq(len(stack), 0)
    return tree


def _find_header_tree_ancestry(
    tree: _HeaderTree, level: int, description: str
) -> Optional[_HeaderTree]:
    """
    Recursively search for the node matching (level, description).

    If found, return the ancestry as a list from the root down to that
    node. Otherwise return None.

    :param tree: header tree to search
    :param level: header level to match
    :param description: header description to match
    :return: ancestry list from root to matching node, or None if not found
    """
    for node in tree:
        if node.level == level and node.description == description:
            return [node]
        result = _find_header_tree_ancestry(node.children, level, description)
        if result:
            return [node] + result
    return None


def header_tree_to_str(
    tree: _HeaderTree,
    ancestry: Optional[_HeaderTree],
    *,
    open_modifier: str = "**",
    close_modifier: str = "**",
    indent: int = 0,
) -> str:
    """
    Return the tree as a string.

    Only expand (i.e. recursively include children) for a node if it is part of
    the ancestry of the selected node.

    :param tree: tree to convert to a string
    :param ancestry: ancestry of the selected node
    :param open_modifier: modifier to use for the open of the selected node
    :param close_modifier: modifier to use for the close of the selected node
    :param indent: indent of the tree
    :return: string representation of the tree

    - Nodes not in the ancestry are included on one line (even if they have
      children).
    - The selected node (last in the ancestry) is included highlighted.
    """
    prefix = "  " * indent + "- "
    result = []
    for node in tree:
        _LOG.debug(hprint.to_str("node"))
        # Check if this node is the next expected one in the ancestry branch.
        if ancestry and node is ancestry[0]:
            # If this is the last in the ancestry, it is the selected node.
            val = prefix
            if len(ancestry) == 1:
                val += open_modifier + node.description + close_modifier
            else:
                val += node.description
            _LOG.debug("-> %s", hprint.to_str("val"))
            if val:
                result.append(val)
            # Expand this node’s children using the rest of the ancestry.
            val = header_tree_to_str(
                node.children,
                ancestry[1:],
                indent=indent + 1,
                open_modifier=open_modifier,
                close_modifier=close_modifier,
            )
        else:
            # For nodes not on the selected branch, include them without
            # expanding.
            val = prefix + node.description
        _LOG.debug("-> %s", hprint.to_str("val"))
        if val:
            result.append(val)
    return "\n".join(result)


def selected_navigation_to_str(
    tree: _HeaderTree,
    level: int,
    description: str,
    *,
    open_modifier: str = "**",
    close_modifier: str = "**",
) -> str:
    """
    Given a level and description for the selected node, print the navigation.

    :param tree: header tree
    :param level: level of the selected node
    :param description: description of the selected node
    :param open_modifier: modifier for opening the selected node
    :param close_modifier: modifier for closing the selected node
    :return: navigation string with selected node highlighted
    """
    ancestry = _find_header_tree_ancestry(tree, level, description)
    hdbg.dassert_ne(
        ancestry,
        None,
        "Node (%s, '%s') not found",
        level,
        description,
    )
    _LOG.debug(hprint.to_str("ancestry"))
    txt = header_tree_to_str(
        tree,
        ancestry,
        open_modifier=open_modifier,
        close_modifier=close_modifier,
    )
    return txt
