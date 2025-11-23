import logging
import re
from typing import List

import helpers.hdbg as hdbg
import helpers.hdockerized_executables as hdocexec
import helpers.hio as hio
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


def is_latex_line_separator(line: str, *, min_repeats: int = 5) -> bool:
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
        if not is_latex_line_separator(line):
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
    section_patterns = [
        (r"^\\section\{", "% " + "#" * (80 - 2)),
        (r"^\\subsection\{", "% " + "=" * (80 - 2)),
        (r"^\\subsubsection\{", "% " + "-" * (80 - 2)),
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
