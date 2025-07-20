"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging
import re

import helpers.hdbg as hdbg
from helpers.hmarkdown_fenced_blocks import (
    replace_fenced_blocks_with_tags,
    replace_tags_with_fenced_blocks,
)

_LOG = logging.getLogger(__name__)

# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.

# #############################################################################
# Colorize
# #############################################################################

# Define colors and their LaTeX equivalents.
_COLORS = {
    "red": "red",
    "orange": "orange",
    # "yellow": "yellow",
    # "lime": "lime",
    #
    "green": "darkgreen",
    "teal": "teal",
    "cyan": "cyan",
    "blue": "blue",
    # "purple": "purple",
    "violet": "violet",
    "magenta": "magenta",
    # "pink": "pink",
    "brown": "brown",
    "olive": "olive",
    "gray": "gray",
    "darkgray": "darkgray",
    # "lightgray": "lightgray",
    # "black": "black",
    # "white": "white",
}


def process_color_commands(in_line: str) -> str:
    r"""
    Transform color commands like `\red{xyz}` into valid LaTeX syntax.

    If the content is text (not math), wraps it in `\text{}`.

    E.g.:
    - `\red{abc}` -> `\textcolor{red}{\text{abc}}`
    - `\blue{x + y}` -> `\textcolor{blue}{x + y}`

    :param in_line: input line to process
    :return: line with color commands transformed
    """
    for color, value in _COLORS.items():
        # This regex matches LaTeX color commands like \red{content}, \blue{content}, etc.
        pattern = re.compile(
            rf"""
            \\{color}    # Match the color command (e.g., \red, \blue, etc.).
            \{{          # Match the opening curly brace.
            ([^}}]*)     # Capture everything inside the curly braces.
            \}}          # Match the closing curly brace.
            """,
            re.VERBOSE,
        )

        def _replacement(match: re.Match, value: str) -> str:
            content = match.group(1)
            # Check if content appears to be math expression.
            is_math = any(c in content for c in "+-*/=<>{}[]()^_")
            if is_math:
                ret = rf"\textcolor{{{value}}}{{{content}}}"
            else:
                ret = rf"\textcolor{{{value}}}{{\text{{{content}}}}}"
            return ret

        # Replace the color command with the LaTeX color command.
        in_line = re.sub(pattern, lambda m: _replacement(m, value), in_line)
    return in_line


def has_color_command(line: str) -> bool:
    """
    Check if line contains any color commands.

    :param line: line to check
    :return: whether the line contains color commands
    """
    hdbg.dassert_isinstance(line, str)
    # hdbg.dassert_not_in("\n", line)
    for color in _COLORS.keys():
        # This regex matches LaTeX color commands like \red{content}, \blue{content}, etc.
        pattern = re.compile(
            rf"""
            \\{color}    # Match the color command (e.g., \red, \blue, etc.).
            \{{          # Match the opening curly brace.
            ([^}}]*)     # Capture everything inside the curly braces.
            \}}          # Match the closing curly brace.
            """,
            re.VERBOSE,
        )
        if re.search(pattern, line):
            return True
    return False


# TODO(gp): -> List[str]
# TODO(gp): Use hmarkdown.process_lines() and test it.
def colorize_bullet_points_in_slide(
    txt: str, *, use_abbreviations: bool = True
) -> str:
    """
    Colorize bold text in a given string.

    :param txt: text to colorize
    :param use_abbreviations: use abbreviations for the colors like
        `\red{foo}` instead of `\textcolor{red}{foo}`
    :return: colored text
    """
    hdbg.dassert_isinstance(txt, str)
    # Replace fenced code blocks with tags.
    lines = txt.split("\n")
    lines, fence_map = replace_fenced_blocks_with_tags(lines)
    _LOG.debug("Found %s fenced blocks", len(fence_map))
    # Count the number of bold items.
    tot_bold = 0
    # Scan the text line by line and count how many bold items there are.
    for line in lines:
        # Count the number of bold items.
        num_bold = len(re.findall(r"\*\*", line))
        tot_bold += num_bold
    _LOG.debug("tot_bold=%s", tot_bold)
    if tot_bold == 0:
        return txt
    # Divide by 2 since we count the number of occurrences of `**`, while we
    # want to count `**bold**` as 1.
    hdbg.dassert_eq(tot_bold % 2, 0, "tot_bold=%s needs to be even", tot_bold)
    num_bolds = tot_bold // 2
    # Use the colors in the order of the list of colors.
    hdbg.dassert_lte(num_bolds, len(_COLORS))
    # Sample num_bolds colors evenly spaced from the available colors
    step = len(_COLORS) // num_bolds
    colors = list(_COLORS.keys())[::step][:num_bolds]
    _LOG.debug("colors=%s", colors)
    # Colorize the bold items.
    color_idx = 0
    txt_out = []
    for line in lines:
        def color_replacer(match: re.Match[str]) -> str:
            r"""
            Replace strings like "**foo**" with strings like "**\red{foo}**".
            """
            nonlocal color_idx
            text = match.group(1)
            hdbg.dassert_lte(color_idx, len(colors))
            color_to_use = colors[color_idx]
            color_idx += 1
            if use_abbreviations:
                ret = f"**\\{color_to_use}{{{text}}}**"
            else:
                ret = f"**\\textcolor{{{color_to_use}}}{{{text}}}**"
            return ret

        line = re.sub(r"\*\*([^*]+)\*\*", color_replacer, line)
        txt_out.append(line)
    # Replace the tags with the fenced code blocks.
    txt_out = replace_tags_with_fenced_blocks(txt_out, fence_map)
    txt_out = "\n".join(txt_out)
    return txt_out
