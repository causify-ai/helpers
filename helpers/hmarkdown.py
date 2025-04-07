"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import dataclasses
import logging
import re
from typing import Generator, List, Optional, Tuple, cast

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

_TRACE = False

# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.


# #############################################################################
# Utils
# #############################################################################


def is_markdown_line_separator(line: str) -> bool:
    """
    Check if the given line is a Markdown separator.

    :param line: the current line of text being processed
    :return: true if the line is a separator
    """
    res = (
        re.match(r"#*\s*######+", line)
        or re.match(r"#*\s*/////+", line)
        or re.match(r"#*\s*-----+", line)
        or re.match(r"#*\s*=====+", line)
    )
    res = bool(res)
    return res


def is_header(line: str) -> Tuple[bool, int, str]:
    """
    Check if the given line is a Markdown header.

    :return: A tuple containing:
        - A boolean indicating if the line is a header
        - The level of the header (0 if not a header)
        - The title of the header (empty string if not a header)
    """
    hdbg.dassert(not is_markdown_line_separator(line), "line='%s'", line)
    m = re.match(r"(#+)\s+(.*)", line)
    is_header_ = bool(m)
    if m:
        level = len(m.group(1))
        title = m.group(2)
    else:
        level = 0
        title = ""
    return is_header_, level, title


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
    if is_markdown_line_separator(line):
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
        out.append(line)
    #
    yield from enumerate(out)


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
def remove_code_delimiters(txt: str) -> str:
    """
    Remove ```python and ``` delimiters from a given text.

    :param text: The input text containing code delimiters.
    :return: The text with the code delimiters removed.
    """
    # Replace the ```python and ``` delimiters with empty strings.
    txt_out = txt.replace("```python", "").replace("```", "")
    txt_out = txt_out.strip()
    return txt_out


def add_line_numbers(txt: str) -> str:
    """
    Add line numbers to each line of text.
    """
    lines = txt.split("\n")
    numbered_lines = []
    for i, line in enumerate(lines, 1):
        numbered_lines.append(f"{i}: {line}")
    txt_out = "\n".join(numbered_lines)
    return txt_out


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


def check_header_list(header_list: HeaderList) -> None:
    # The first header should be level 1.
    if header_list and header_list[0].level > 1:
        _LOG.warning(
            "First header '%s' at line %s is not level 1, but %s",
            header_list[0].description,
            header_list[0].line_number,
            header_list[0].level,
        )
    # Check that consecutive elements in the header list differ by at most one
    # value of level.
    if len(header_list) > 1:
        for i in range(1, len(header_list)):
            hdbg.dassert_isinstance(header_list[i - 1], HeaderInfo)
            hdbg.dassert_isinstance(header_list[i], HeaderInfo)
            if abs(header_list[i].level - header_list[i - 1].level) > 1:
                msg = []
                msg.append("Consecutive headers differ by more than one level:")
                msg.append(f"  {header_list[i - 1]}")
                msg.append(f"  {header_list[i]}")
                msg = "\n".join(msg)
                raise ValueError(msg)


def extract_headers_from_markdown(
    txt: str, max_level: int, *, sanity_check: bool = True
) -> HeaderList:
    """
    Extract headers from Markdown file and return an `HeaderList`.

    :param txt: content of the input Markdown file.
    :param max_level: Maximum header levels to parse (e.g., 3 parses all levels
        included `###`, but not `####`)
    :return: the generated `HeaderList`, e.g.,
        ```
        [(1, "Chapter 1", 5), (2, "Section 1.1", 10), ...]
        ```
    """
    hdbg.dassert_isinstance(txt, str)
    hdbg.dassert_lte(1, max_level)
    header_list: HeaderList = []
    # Parse an header like `# Header1` or `## Header2`.
    header_pattern = re.compile(r"^(#+)\s+(.*)")
    # Process the input file to extract headers.
    for line_number, line in enumerate(txt.splitlines(), start=1):
        # TODO(gp): Use the iterator.
        # Skip the visual separators.
        if is_markdown_line_separator(line):
            continue
        # TODO(gp): Use is_header
        match = header_pattern.match(line)
        if match:
            # The number of '#' determines level.
            level = len(match.group(1))
            if level <= max_level:
                title = match.group(2).strip()
                header_info = HeaderInfo(level, title, line_number)
                header_list.append(header_info)
    # Check the header list.
    if sanity_check:
        check_header_list(header_list)
    else:
        _LOG.debug("Skipping sanity check")
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


def modify_header_level(in_file_name: str, out_file_name: str, mode: str) -> None:
    """
    Increase or decrease the level of headings by one for text in stdin.

    :param in_file_name: the name of the input file to read
    :param out_file_name: the name of the output file to write the
        modified text to
    :param mode: indicates the increase or decrease of the header level
    """
    txt = hparser.read_file(in_file_name)
    #
    txt_tmp = []
    if mode == "increase":
        mode_level = 1
    elif mode == "decrease":
        mode_level = -1
    else:
        raise ValueError(f"Unsupported mode='{mode}'")
    for line in txt:
        # TODO(gp): Use the iterator.
        line = line.rstrip(r"\n")
        is_header_, level, title = is_header(line)
        if is_header_:
            modified_level = level + mode_level
            if (mode_level == 1 and level > 4) or (
                mode_level == -1 and level == 1
            ):
                # Handle edge cases for reducing (1 hash) and increasing (5 hashes)
                # heading levels.
                modified_level = level
            line = "#" * modified_level + " " + title
        txt_tmp.append(line)
    #
    hparser.write_file(txt_tmp, out_file_name)


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
        tree, ancestry, open_modifier=open_modifier, close_modifier=close_modifier
    )
    return txt


# #############################################################################


def colorize_first_level_bullets(markdown_text: str) -> str:
    # Define the colors to use.
    colors = ["red", "orange", "green", "teal", "cyan", "blue", "violet", "brown"]
    # Find all first-level bullet points (lines starting with "- " after any whitespace).
    lines = markdown_text.split("\n")
    color_index = 0
    result = []
    for line in lines:
        # Check if this is a first-level bullet point.
        if re.match(r"^\s*- ", line):
            # Only color first-level bullets (those with minimal indentation).
            indentation = len(line) - len(line.lstrip())
            if indentation == 0:
                # First-level bullet.
                color = colors[color_index % len(colors)]
                # Replace the bullet with a colored version.
                # - \textcolor{red}{Linear models}
                colored_line = re.sub(
                    r"^(\s*-\s+)(.*)", r"\1\\textcolor{" + color + r"}{\2}", line
                )
                result.append(colored_line)
                color_index += 1
            else:
                result.append(line)
        else:
            result.append(line)
    return "\n".join(result)
