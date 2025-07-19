"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging
import re
from typing import Generator, List, Tuple

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

_TRACE = False


## TODO(gp): Copied from hamrkdown_headers.py to avoid problems importing.
# def is_markdown_line_separator(line: str, min_repeats: int = 5) -> bool:
#    """
#    Check if the given line is a Markdown separator.
#
#    This function determines if a line consists of repeated characters (`#`,
#    `/`, `-`, `=`) that would indicate a markdown separator.
#
#    :param line: the current line of text being processed
#    :param min_repeats: the minimum number of times the characters have to be
#        repeated to be considered a separator, e.g., if `min_repeats` = 2, then
#        `##`, `###`, `//` are considered to be line separators, but `#`, `/` are
#        not
#    :return: true if the line is a separator
#    """
#    separator_pattern = rf"""
#    \#*\s*                                  # Allow optional leading `#` and whitespace.
#    ([#/=\-])\1{{{min_repeats - 1},}}       # Capture a character, then repeat it (`min_repeats` - 1) times.
#    \s*$                                    # Match only whitespace characters until the end of the line.
#    """
#    res = bool(re.match(separator_pattern, line, re.VERBOSE))
#    return res


from helpers.hmarkdown_headers import is_markdown_line_separator


# #############################################################################
# Formatting markdown
# #############################################################################


def capitalize_first_level_bullets(markdown_text: str) -> str:
    """
    Make first-level bullets bold in markdown text.

    :param markdown_text: Input markdown text
    :return: Formatted markdown text with first-level bullets in bold
    """
    # **Subject-Matter Experts (SMEs)** -> **Subject-Matter Experts (SMEs)**
    # Business Strategists -> Business strategists
    # Establish a Phased, Collaborative Approach -> Establish a phased, collaborative approach
    lines = markdown_text.split("\n")
    result = []
    for line in lines:
        # Check if this is a first-level bullet point.
        if re.match(r"^\s*- ", line):
            # Check if the line has bold text it in it.
            if not re.search(r"\*\*", line):
                # Bold first-level bullets.
                indentation = len(line) - len(line.lstrip())
                if indentation == 0:
                    # First-level bullet, add bold markers.
                    line = re.sub(r"^(\s*-\s+)(.*)", r"\1**\2**", line)
            result.append(line)
        else:
            result.append(line)
    return "\n".join(result)


# These are the colors that are supported by Latex / markdown, are readable on
# white, and form an equidistant color palette.
_ALL_COLORS = [
    "red",
    "orange",
    "brown",
    "olive",
    "green",
    "teal",
    "cyan",
    "blue",
    "violet",
    "darkgray",
    "gray",
]


def bold_first_level_bullets(markdown_text: str, *, max_length: int = 30) -> str:
    """
    Make first-level bullets bold in markdown text.

    :param markdown_text: Input markdown text
    :param max_length: Max length of the bullet text to be bolded. -1
        means no limit.
    :return: Formatted markdown text with first-level bullets in bold
    """
    lines = markdown_text.split("\n")
    result = []
    for line in lines:
        # Check if this is a first-level bullet point.
        if re.match(r"^\s*- ", line):
            # Check if the line has already bold text it in it.
            if not re.search(r"\*\*", line):
                # Bold first-level bullets.
                indentation = len(line) - len(line.lstrip())
                if indentation == 0:
                    # First-level bullet, add bold markers.
                    m = re.match(r"^(\s*-\s+)(.*)", line)
                    hdbg.dassert(m, "Can't parse line='%s'", line)
                    bullet_text = m.group(2)  # type: ignore[union-attr]
                    if max_length > -1 and len(bullet_text) <= max_length:
                        spaces = m.group(1)  # type: ignore[union-attr]
                        line = spaces + "**" + bullet_text + "**"
        result.append(line)
    return "\n".join(result)


# TODO(gp): -> hmarkdown_color.py


# TODO(gp): This seems the same as `_colorize_bullet_points()`.
def colorize_bold_text(
    markdown_text: str, *, use_abbreviations: bool = True
) -> str:
    r"""
    Add colors to bold text in markdown using equidistant colors from an array.

    The function finds all bold text (enclosed in ** or __) and adds
    LaTeX color commands while preserving the rest of the markdown
    unchanged.

    :param markdown_text: Input markdown text
    :param use_abbreviations: Use LaTeX abbreviations for colors,
        `\red{text}` instead of `\textcolor{red}{text}`
    :return: Markdown text with colored bold sections
    """
    # Remove any existing color formatting.
    # Remove \color{text} format.
    markdown_text = re.sub(r"\\[a-z]+\{([^}]+)\}", r"\1", markdown_text)
    # Remove \textcolor{color}{text} format.
    markdown_text = re.sub(
        r"\\textcolor\{[^}]+\}\{([^}]+)\}", r"\1", markdown_text
    )
    # Find all bold text (both ** and __ formats).
    bold_pattern = r"\*\*(.*?)\*\*|__(.*?)__"
    # matches will look like:
    # For **text**: group(1)='text', group(2)=None.
    # For __text__: group(1)=None, group(2)='text'.
    matches = list(re.finditer(bold_pattern, markdown_text))
    if not matches:
        return markdown_text
    result = markdown_text
    # Calculate color spacing to use equidistant colors.
    color_step = len(_ALL_COLORS) / len(matches)
    # Process matches in reverse to not mess up string indices.
    for i, match in enumerate(reversed(matches)):
        # Get the matched bold text (either ** or __ format).
        bold_text = match.group(1) or match.group(2)
        # Calculate `color_idx` using equidistant spacing.
        color_idx = int((len(matches) - 1 - i) * color_step) % len(_ALL_COLORS)
        color = _ALL_COLORS[color_idx]
        # Create the colored version.
        if use_abbreviations:
            # E.g., \red{text}
            colored_text = f"\\{color}{{{bold_text}}}"
        else:
            # E.g., \textcolor{red}{text}
            colored_text = f"\\textcolor{{{color}}}{{{bold_text}}}"
        # Apply bold.
        colored_text = f"**{colored_text}**"
        # Replace in the original text.
        result = result[: match.start()] + colored_text + result[match.end() :]
    return result


def format_first_level_bullets(markdown_text: str) -> str:
    """
    Add empty lines only before first level bullets and remove all empty lines
    from markdown text.

    :param markdown_text: Input markdown text
    :return: Formatted markdown text
    """
    # Split into lines and remove empty ones.
    lines = [line for line in markdown_text.split("\n") if line.strip()]
    # Add empty lines only before first level bullets.
    result = []
    for i, line in enumerate(lines):
        # Check if current line is a first level bullet (no indentation).
        if re.match(r"^- ", line):
            # Add empty line before first level bullet if not at start.
            if i > 0:
                result.append("")
        result.append(line)
    return "\n".join(result)


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


# TODO(gp): -> iterator
# TODO(gp): where is this used?
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
