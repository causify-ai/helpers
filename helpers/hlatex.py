import logging
import re
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hdockerized_executables as hdocexec
import helpers.hio as hio
import helpers.hmarkdown_headers as hmarkdo
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# TODO(gp): Consider using `pypandoc` instead of calling `pandoc` directly.
# https://boisgera.github.io/pandoc


# TODO(gp): Add a switch to keep the tmp files or delete them.
def convert_pandoc_md_to_latex(txt: str) -> str:
    """
    Run pandoc to convert a markdown file to a latex file.
    """
    hdbg.dassert_isinstance(txt, str)
    # Save to tmp file.
    in_file_name = "./tmp.run_pandoc_in.md"
    hio.to_file(in_file_name, txt)
    # Run Pandoc.
    out_file_name = "./tmp.run_pandoc_out.tex"
    cmd = (
        f"pandoc {in_file_name} -o {out_file_name} --read=markdown --write=latex"
    )
    container_type = "pandoc_only"
    hdocexec.run_dockerized_pandoc(cmd, container_type)
    # Read tmp file.
    res = hio.from_file(out_file_name)
    # Remove lines that contain \tightlist.
    res = "\n".join(
        [line for line in res.splitlines() if "\\tightlist" not in line]
    )
    return res


def markdown_list_to_latex(markdown: str) -> str:
    """
    Convert a Markdown list to LaTeX format.

    :param markdown: The Markdown text to convert
    :return: The converted LaTeX text
    """
    hdbg.dassert_isinstance(markdown, str)
    markdown = hprint.dedent(markdown)
    # Remove the first line if it's a title.
    markdown = markdown.split("\n")
    m = re.match(r"^(\*+ )(.*)", markdown[0])
    if m:
        title = m.group(2)
        markdown = markdown[1:]
    else:
        title = ""
    markdown = "\n".join(markdown)
    # Convert.
    txt = convert_pandoc_md_to_latex(markdown)
    # Remove `\tightlist` and empty lines.
    lines = txt.splitlines()
    lines = [line for line in lines if "\\tightlist" not in line]
    lines = [line for line in lines if line.strip() != ""]
    txt = "\n".join(lines)
    # Add the title frame.
    if title:
        txt = f"\\begin{{frame}}{{{title}}}" + "\n" + txt + "\n" + "\\end{frame}"
    return txt


def remove_latex_formatting(latex_string: str) -> str:
    r"""
    Remove LaTeX formatting such as \textcolor{color}{content} and retains only
    the content.
    """
    cleaned_string = re.sub(
        r"\\textcolor\{[^}]*\}\{([^}]*)\}", r"\1", latex_string
    )
    return cleaned_string


def format_latex(txt: str) -> str:
    """
    Format LaTeX text using `prettier`.

    :param txt: input LaTeX text to format
    :return: formatted LaTeX text
    """
    file_type = "tex"
    txt = hdocexec.prettier_on_str(txt, file_type)
    return txt


# #############################################################################
# Frame Latex sections
# #############################################################################


def _is_latex_line_separator(line: str, *, min_repeats: int = 5) -> bool:
    """
    Check if the given line is a LaTeX comment separator.

    This function determines if a line consists of a comment character `%`
    followed by repeated characters (`#`, `=`, `-`) that would indicate
    a section separator.

    :param line: current line of text being processed
    :param min_repeats: minimum number of times the characters have to
        be repeated to be considered a separator
    :return: whether the line is a separator
    """
    separator_pattern = rf"""
    ^\s*%\s*                          # %
    ([#=\-])\1{{{min_repeats - 1},}}  # Capture a character, then repeat it
                                      #   (`min_repeats` - 1) times.
    \s*$                              # Match only whitespace characters
                                      #   until the end of the line.
    """
    res = bool(re.match(separator_pattern, line, re.VERBOSE))
    return res


def frame_sections(lines: List[str]) -> List[str]:
    """
    Add line separators before LaTeX section commands.

    This function adds comment separators before \section, \subsection, and
    \subsubsection commands in LaTeX files. The separators are:
    ```
    % #####...
    \section

    % =====...
    \subsection:

    % -----...
    \subsubsection
    ```

    If a separator comment already exists immediately before the section command,
    no separator is added.

    :param lines: list of strings representing the LaTeX file content
    :return: list of strings with separators added before section commands
    """
    hdbg.dassert_isinstance(lines, list)
    # Loop 1: Remove existing latex separators.
    txt_tmp: List[str] = []
    for line in lines:
        if not _is_latex_line_separator(line):
            txt_tmp.append(line)
    # Loop 2: Remove consecutive empty lines, leaving only one.
    txt_tmp2: List[str] = []
    prev_was_empty = False
    for line in txt_tmp:
        is_empty = line.strip() == ""
        if is_empty:
            if not prev_was_empty:
                txt_tmp2.append(line)
            prev_was_empty = True
        else:
            txt_tmp2.append(line)
            prev_was_empty = False
    # Loop 3: Add correct LaTeX separator based on section commands.
    txt_new: List[str] = []
    # Define the section patterns and their corresponding separators.
    # Total line length is 78 characters, "% " is 2 characters, so 76 separator chars.
    prefix = "  % "
    section_patterns = [
        (r"^\\section\{", prefix + "#" * 76),
        (r"^\\subsection\{", prefix + "=" * 76),
        (r"^\\subsubsection\{", prefix + "-" * 76),
    ]
    for i, line in enumerate(txt_tmp2):
        _LOG.debug("line=%d:%s", i, line)
        txt_processed = False
        # Check if the line matches any section command.
        for pattern, separator in section_patterns:
            m = re.match(pattern, line.strip())
            if m:
                _LOG.debug("  -> Found section command")
                txt_new.append(separator)
                _LOG.debug("  -> Added separator: %s", separator)
                txt_new.append(line)
                txt_processed = True
                break
        if not txt_processed:
            txt_new.append(line)
    hdbg.dassert_isinstance(txt_new, list)
    return txt_new


# #############################################################################
# LaTeX Header Extraction
# #############################################################################


def _is_latex_comment(line: str) -> bool:
    """
    Check if a line is a LaTeX comment.

    A LaTeX comment line starts with the `%` character. This function
    handles the edge case where `%` is escaped (e.g., `\%`), which should
    not be treated as a comment.

    :param line: line of text to check
    :return: True if the line is a comment, False otherwise
    """
    hdbg.dassert_isinstance(line, str)
    # Strip leading whitespace to check the first non-whitespace character.
    stripped_line = line.lstrip()
    # Check if line starts with %.
    if not stripped_line.startswith("%"):
        return False
    # Check if the % is escaped by looking at the character before it in the
    # original line.
    # Find the position of % in the original line.
    percent_pos = line.find("%")
    # If there's a character before %, check if it's a backslash.
    if percent_pos > 0 and line[percent_pos - 1] == "\\":
        # Check if the backslash itself is escaped.
        if percent_pos > 1 and line[percent_pos - 2] == "\\":
            # Double backslash before %, so % is not escaped.
            return True
        # Single backslash before %, so % is escaped.
        return False
    # % is at the beginning or has no backslash before it.
    return True


def _extract_latex_section(
    line: str, line_number: int
) -> Optional[hmarkdo.HeaderInfo]:
    r"""
    Parse a LaTeX section command and extract section information.

    This function identifies LaTeX section commands (\section{}, \subsection{},
    \subsubsection{}) and extracts the section title. It handles several edge
    cases including:
    - Regex parsing of `\section[Short]{Long Title}` (extracts "Long Title")
    - Handles nested braces within titles (e.g., `\section{Intro to \textbf{ML}}`)
    - Does not handle multi-line section titles

    :param line: line of text to parse
    :param line_number: line number in the original file
    :return: HeaderInfo object if section found, None otherwise
    """
    hdbg.dassert_isinstance(line, str)
    hdbg.dassert_isinstance(line_number, int)
    # Define section patterns with their corresponding levels.
    # Pattern supports optional [short title] before {long title}.
    regex = r'(?:\[.*?\])?\{(.*)\}'
    section_patterns = [
        (r"\\section" + regex, 1),
        (r"\\subsection" + regex, 2),
        (r"\\subsubsection" + regex, 3),
    ]
    line_stripped = line.strip()
    # Try to match each section pattern.
    for pattern, level in section_patterns:
        # Check if line starts with the section command.
        match = re.match(pattern, line_stripped)
        if match:
            # Extract the title from the first capture group.
            title = match.group(1)
            # Skip sections with empty titles.
            if not title:
                return None
            # Return HeaderInfo with level, title, and line number.
            return hmarkdo.HeaderInfo(level, title, line_number)
    # No section command found.
    return None


def extract_headers_from_latex(
    lines: List[str], max_level: int, *, sanity_check: bool = True
) -> hmarkdo.HeaderList:
    """
    Extract headers from a LaTeX file and return a HeaderList.

    This function processes a LaTeX file line by line, identifies section
    commands (\section, \subsection, \subsubsection), and creates a list
    of HeaderInfo objects. It skips commented-out lines (lines starting
    with %) and only includes headers up to the specified maximum level.

    :param lines: content of the input LaTeX file as list of strings
    :param max_level: maximum header levels to parse (e.g., '3' parses
        \section, \subsection, and \subsubsection, but not deeper levels)
    :param sanity_check: whether to check that the header list is valid
        using the same validation as Markdown headers
    :return: list of HeaderInfo objects, each containing (level, title,
        line_number), e.g.:
        ```
        [
            HeaderInfo(1, "Introduction", 5),
            HeaderInfo(2, "Background", 10),
            ...
        ]
        ```
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_lte(1, max_level)
    header_list: hmarkdo.HeaderList = []
    # Process the input file to extract headers.
    for line_number, line in enumerate(lines, start=1):
        # Skip LaTeX comment lines.
        if _is_latex_comment(line):
            continue
        # Check if this line contains a section command.
        header_info = _extract_latex_section(line, line_number)
        if header_info and header_info.level <= max_level:
            # Add HeaderInfo to list.
            header_list.append(header_info)
    # Check the header list.
    if sanity_check:
        hmarkdo.sanity_check_header_list(header_list)
    else:
        _LOG.debug("Skipping sanity check")
    hdbg.dassert_isinstance(header_list, list)
    return header_list
