import dataclasses
import logging
import re
from typing import Generator, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

_TRACE = False

# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.


# # TODO(gp): -> _skip_comments
# def skip_comments(line: str, skip_block: bool) -> Tuple[bool, bool]:
#     """
#     Skip comments in the given line and handle comment blocks.

#     Comments are like:
#     - Single line: %% This is a comment
#     - Block: <!-- This is a comment -->

#     :param line: The line of text to check for comments
#     :param skip_block: A flag indicating if currently inside a comment block
#     :return: A tuple containing a flag indicating if the line should be skipped
#         and the updated skip_block flag
#     """
#     skip_this_line = False
#     # Handle comment block.
#     if line.startswith("<!--"):
#         # Start skipping comments.
#         skip_block = True
#         skip_this_line = True
#     if skip_block:
#         skip_this_line = True
#         if line.startswith("-->"):
#             # End skipping comments.
#             skip_block = False
#         else:
#             # Skip comment.
#             _LOG.debug("  -> skip")
#     else:
#         # Handle single line comment.
#         if line.startswith("%%"):
#             _LOG.debug("  -> skip")
#             skip_this_line = True
#     return skip_this_line, skip_block


def is_markdown_line_separator(line: str) -> bool:
    res = (
        re.match(r"#*\s*#########+", line)
        or re.match(r"#*\s*/////////+", line)
        or re.match(r"#*\s*---------+", line)
        or re.match(r"#*\s*=========+", line)
    )
    res = bool(res)
    return res


def process_comment_block(line: str, in_skip_block: bool) -> Tuple[bool, bool]:
    """
    Process lines of text to identify blocks that start with '<!--' or '/*' and
    end with '-->' or '*/'.

    :param line: The current line of text being processed.
    :param in_skip_block: A flag indicating if the function is currently
        inside a comment block.
    :return: A tuple
        - do_continue: whether to continue processing the current line or skip
          it
        - in_skip_block: a boolean indicating whether the function is currently
          inside a comment block
    """
    do_continue = False
    if line.startswith(r"<!--") or re.search(r"^\s*\/\*", line):
        hdbg.dassert(not in_skip_block)
        # Start skipping comments.
        in_skip_block = True
    if in_skip_block:
        if line.endswith(r"-->") or re.search(r"^\s*\*\/", line):
            # End skipping comments.
            in_skip_block = False
        # Skip comment.
        _LOG.debug("  -> skip")
        do_continue = True
    return do_continue, in_skip_block


def process_code_block(
    line: str, in_code_block: bool, i: int, lines: List[str]
) -> Tuple[bool, bool, List[str]]:
    """
    Process lines of text to handle code blocks that start and end with '```'.

    The transformation is to:
    - add an empty line before the start/end of the code
    - indent the code block with four spaces
    - replace '//' with '# ' to comment out lines in Python code

    :param line: The current line of text being processed.
    :param in_code_block: A flag indicating if the function is currently
        inside a code block.
    :param i: The index of the current line in the list of lines.
    :param lines: the lines of text to process
    :return: A tuple
        - do_continue: whether to continue processing the current line or skip
          it
        - in_code_block: a boolean indicating whether the function is currently
          inside a code block
        - a list of processed lines of text
    """
    out: List[str] = []
    do_continue = False
    # Look for a code block.
    if re.match(r"^(\s*)```", line):
        _LOG.debug("  -> code block")
        in_code_block = not in_code_block
        # Add empty line before the start of the code block.
        if (
            in_code_block
            and (i + 1 < len(lines))
            and re.match(r"\s*", lines[i + 1])
        ):
            out.append("\n")
        out.append("    " + line)
        if (
            not in_code_block
            and (i + 1 < len(lines))
            and re.match(r"\s*", lines[i + 1])
        ):
            out.append("\n")
        do_continue = True
        return do_continue, in_code_block, out
    if in_code_block:
        line = line.replace("// ", "# ")
        out.append("    " + line)
        # We don't do any of the other post-processing.
        do_continue = True
        return do_continue, in_code_block, out
    return do_continue, in_code_block, out


def process_single_line_comment(line: str) -> bool:
    """
    Handle single line comment.

    We need to do it after the // in code blocks have been handled.
    """
    do_continue = False
    if line.startswith(r"%%") or line.startswith(r"//"):
        do_continue = True
        _LOG.debug("  -> do_continue=True")
        return do_continue
    # Skip frame.
    # TODO(gp): Use is_markdown_line_separator
    if (
        re.match(r"\#+ -----", line)
        or re.match(r"\#+ \#\#\#\#\#", line)
        or re.match(r"\#+ =====", line)
        or re.match(r"\#+ \/\/\/\/\/", line)
    ):
        do_continue = True
        _LOG.debug("  -> do_continue=True")
        return do_continue
    # Nothing to do.
    return do_continue


def process_lines(lines: List[str]) -> Generator[Tuple[int, str], None, None]:
    """
    Process lines of text to handle comment blocks, code blocks, and single
    line comments.

    :param lines: The list of all the lines of text being processed.
    :return: A list of processed lines of text.
    """
    out: List[str] = []
    in_skip_block = False
    in_code_block = False
    for i, line in enumerate(lines):
        _LOG.debug("%s:line=%s", i, line)
        # 1) Remove comment block.
        if _TRACE:
            _LOG.debug("# 1) Process comment block.")
        do_continue, in_skip_block = process_comment_block(line, in_skip_block)
        if do_continue:
            continue
        # 2) Remove code block.
        if _TRACE:
            _LOG.debug("# 2) Process code block.")
        do_continue, in_code_block, out_tmp = process_code_block(
            line, in_code_block, i, lines
        )
        out.extend(out_tmp)
        if do_continue:
            continue
        # 3) Remove single line comment.
        if _TRACE:
            _LOG.debug("# 3) Process single line comment.")
        do_continue = process_single_line_comment(line)
        if do_continue:
            continue
        yield i + 1, line


# #############################################################################
# Header processing
# #############################################################################


def extract_section_from_markdown(content: str, header_name: str) -> str:
    """
    Extract a section of text from a Markdown document based on the header
    name.

    The function identifies a section by locating the specified header
    and captures all lines until encountering another header of the same
    or higher level. Headers are identified by the '#' prefix, and their
    level is determined by the number of '#' characters.

    :param content: The markdown content as a single string.
    :param header_name: The exact header name to extract (excluding '#'
        symbols).
    :return: The extracted section as a string, including the header
        line itself and all lines until the next header of the same or
        higher level.
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
    original file, e.g., `(1, "Chapter 1", 5)`` `(2, "Section 1.1", 10)`
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
        self.description = description
        #
        hdbg.dassert_isinstance(line_number, int)
        hdbg.dassert_lte(1, line_number)
        self.line_number = line_number
        #
        self.children: List[_HeaderTreeNode] = []

    def __repr__(self) -> str:
        return f"Node({self.level}, {self.description}, {self.line_number})"

    def as_tuple(self) -> Tuple[int, str, int]:
        return (self.level, self.description, self.line_number)


HeaderList = List[HeaderInfo]


def _check_header_list(header_list: HeaderList) -> None:
    """
    Check that consecutive elements in the header list differ by at most one
    value of level.
    """
    for i in range(1, len(header_list)):
        hdbg.dassert_lte(
            abs(header_list[i].level - header_list[i - 1].level),
            1,
            "Consecutive headers differ by more than one level",
        )


def extract_headers_from_markdown(txt: str, *, max_level: int = 6) -> HeaderList:
    """
    Extract headers from Markdown file and return an `HeaderList`.

    :param input_content: content of the input Markdown file.
    :param max_level: Maximum header levels to parse (1 for `#`, 2 for `##`,
        etc.).
    :return: the generated `HeaderList`.
    """
    header_list: HeaderList = []
    # Parse an header like `# Header1` or `## Header2`.
    header_pattern = re.compile(r"^(#+)\s+(.*)")
    # Process the input file to extract headers.
    for line_number, line in enumerate(txt.splitlines(), start=1):
        # TODO(gp): Use the iterator.
        # Skip the visual separators.
        if is_markdown_line_separator(line):
            continue
        match = header_pattern.match(line)
        if match:
            # The number of '#' determines level.
            level = len(match.group(1))
            if level <= max_level:
                title = match.group(2).strip()
                header_list.append((level, title, line_number))
    return header_list


def header_list_to_vim_cfile(markdown_file: str, header_list: HeaderList) -> str:
    """
    Convert a list of headers into a Vim cfile format.

    Use the generated file in Vim as:
        `:cfile <output_file>`
        Use `:cnext` and `:cprev` to navigate between headers.

    :param markdown_file: Path to the input Markdown file.
    :param header_list: List of headers, where each header is a tuple containing
        the line number, level, and title.
    :return: The generated cfile content as a string in the format:
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

    :param header_list: List of headers, where each header is a tuple
        containing the level, title, and line number.
    :param mode: Specifies the format of the output.
        - "list": Indents headers to create a nested list.
        - "headers": Uses Markdown header syntax (e.g., #, ##, ###).
    :return: The generated Markdown content as a string.
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


# # TODO(gp): -> header_list_to_markdown
# def table_of_content(file_name: str, max_lev: int) -> None:
#     """
#     Generate a table of contents from the given file, considering the specified
#     maximum level of headings.
#     :param file_name: The name of the file to read and generate the table of
#         contents from
#     :param max_lev: The maximum level of headings to include in the table of
#         contents
#     """
#     skip_block = False
#     txt = hparser.read_file(file_name)
#     for line in txt:
#         # Skip comments.
#         skip_this_line, skip_block = skip_comments(line, skip_block)
#         if False and skip_this_line:
#             continue
#         #
#         for i in range(1, max_lev + 1):
#             if line.startswith("#" * i + " "):
#                 if (
#                     ("#########" not in line)
#                     and ("///////" not in line)
#                     and ("-------" not in line)
#                     and ("======" not in line)
#                 ):
#                     if i == 1:
#                         print()
#                     print(f"{'    ' * (i - 1)}{line}")
#                 break


# #############################################################################


# TODO(gp): Add tests.
def format_headers(in_file_name: str, out_file_name: str, max_lev: int) -> None:
    """
    Format the headers in the input file and write the formatted text to the
    output file.

    :param in_file_name: The name of the input file to read
    :param out_file_name: The name of the output file to write the
        formatted text to
    :param max_lev: The maximum level of headings to include in the
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
        # TODO(gp): Use is_markdown_line_separator()
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


# TODO(gp): Add tests.
# TODO(gp): Generalize this to also decrease the header level
# TODO(gp): -> modify_header_level
def increase_chapter(in_file_name: str, out_file_name: str) -> None:
    """
    Increase the level of chapters by one for text in stdin.

    :param in_file_name: The name of the input file to read
    :param out_file_name: The name of the output file to write the
        modified text to
    """
    skip_block = False
    txt = hparser.read_file(in_file_name)
    #
    txt_tmp = []
    for line in txt:
        # TODO(gp): Use the iterator.
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
# _HeaderTreeNode
# #############################################################################


# class _HeaderTreeNode:
#     """
#     A Node class to build hierarchical tree.
#     """

#     def __init__(self, level: int, description: str, line_number: int) -> None:
#         self.level = level
#         self.description = description
#         self.line_number = line_number
#         self.children: List[_HeaderTreeNode] = []

#     def __repr__(self) -> str:
#         return f"Node({self.level}, {self.description})"


_HeaderTree = List[HeaderInfo]


def build_header_tree(header_list: HeaderList) -> _HeaderTree:
    """
    Build a tree (list of Node objects) from the flat list.

    We assume that the level changes never jump by more than 1.
    """
    tree: _HeaderTree = []
    stack: _HeaderTree = []
    for level, description, line_number in header_list:
        node = HeaderInfo(level, description, line_number)
        if level == 1:
            tree.append(node)
            stack = [node]
        else:
            # Pop until we find the proper parent: one with level < current
            # level.
            while stack and stack[-1].level >= level:
                stack.pop()
            if stack:
                stack[-1].children.append(node)
            else:
                tree.append(node)
            stack.append(node)
    return tree


def _find_header_tree_ancestry(
    tree: _HeaderTree, target_level: int, target_description: str
) -> Optional[_HeaderTree]:
    """
    Recursively search for the node matching (target_level,
    target_description).

    If found, return the ancestry as a list from the root down to that
    node. Otherwise return None.
    """
    for node in tree:
        if node.level == target_level and node.description == target_description:
            return [node]
        result = _find_header_tree_ancestry(
            node.children, target_level, target_description
        )
        if result:
            return [node] + result
    return None


def header_tree_to_str(
    tree: _HeaderTree, ancestry: Optional[_HeaderTree], *, indent: int = 0
) -> str:
    """
    Return the tree as a string.

    Only expand (i.e. recursively include children) for a node if it is part of
    the ancestry of the selected node.

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
            if len(ancestry) == 1:
                val = prefix + "*" + node.description + "*"
            else:
                val = prefix + node.description
            _LOG.debug("-> " + hprint.to_str("val"))
            if val:
                result.append(val)
            # Expand this node’s children using the rest of the ancestry.
            val = header_tree_to_str(
                node.children, ancestry[1:], indent=indent + 1
            )
        else:
            # For nodes not on the selected branch, include them without
            # expanding.
            val = prefix + node.description
        _LOG.debug("-> " + hprint.to_str("val"))
        if val:
            result.append(val)
    return "\n".join(result)


def selected_navigation_to_str(
    tree: _HeaderTree, selected_level: int, selected_description: str
) -> None:
    """
    Given a level and description for the selected node, print the navigation.
    """
    ancestry = _find_header_tree_ancestry(
        tree, selected_level, selected_description
    )
    hdbg.dassert_ne(
        ancestry,
        None,
        "Node (%s, %s) not found",
        selected_level,
        selected_description,
    )
    return header_tree_to_str(tree, ancestry)


# #############################################################################
# Utils
# #############################################################################


def remove_end_of_line_periods(txt: str) -> str:
    """
    Remove periods at the end of each line in the given text.

    :param txt: The input text to process
    :return: The text with end-of-line periods removed
    """
    hdbg.dassert_isinstance(txt, str)
    txt_out = [line.rstrip(".") for line in txt.split("\n")]
    txt_out = "\n".join(txt_out)
    return txt_out


def remove_empty_lines(txt: str) -> str:
    """
    Remove empty lines from the given text.

    :param txt: The input text to process
    :return: The text with empty lines removed
    """
    hdbg.dassert_isinstance(txt, str)
    txt_out = [line for line in txt.split("\n") if line != ""]
    txt_out = "\n".join(txt_out)
    return txt_out


# TODO(gp): Add tests.
def remove_code_delimiters(text: str) -> str:
    """
    Remove ```python and ``` delimiters from a given text.

    :param text: The input text containing code delimiters.
    :return: The text with the code delimiters removed.
    """
    # Replace the ```python and ``` delimiters with empty strings.
    text = text.replace("```python", "").replace("```", "")
    return text.strip()
