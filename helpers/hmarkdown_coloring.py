"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging
import re
from typing import List, Optional

import helpers.hdbg as hdbg
from helpers.hmarkdown_fenced_blocks import (
    replace_fenced_blocks_with_tags,
    replace_tags_with_fenced_blocks,
)

_LOG = logging.getLogger(__name__)


# #############################################################################
# Colorize
# #############################################################################

# Define colors and their LaTeX equivalents.
_MD_COLORS_LATEX_MAPPING = {
    "red": "red",
    "orange": "orange",
    "yellow": "yellow",
    "lime": "lime",
    "green": "darkgreen",
    "teal": "teal",
    "cyan": "cyan",
    "blue": "blue",
    "purple": "purple",
    "violet": "violet",
    "magenta": "magenta",
    "pink": "pink",
    "brown": "brown",
    "olive": "olive",
    "gray": "gray",
    "darkgray": "darkgray",
    "lightgray": "lightgray",
    "black": "black",
    "white": "white",
}


_MD_COLORS = {
    "red",
    "orange",
    # "yellow",
    # "lime",
    "green",
    "teal",
    "cyan",
    "blue",
    # "purple",
    "violet",
    "magenta",
    # "pink",
    "brown",
    "olive",
    "gray",
    "darkgray",
    # "lightgray",
    # "black",
    # "white",
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
    for md_color, latex_color in _MD_COLORS_LATEX_MAPPING.items():
        # This regex matches color commands like \red{content}, \blue{content},
        # etc.
        pattern = re.compile(
            rf"""
            \\{md_color}    # Match the color command (e.g., \red, \blue, etc.).
            \{{          # Match the opening curly brace.
            ([^}}]*)     # Capture everything inside the curly braces.
            \}}          # Match the closing curly brace.
            """,
            re.VERBOSE,
        )

        def _replacement(match: re.Match, latex_color: str) -> str:
            content = match.group(1)
            # Check if content appears to be a math expression, otherwise wrap
            # it in `\text{}`.
            is_math_expr = any(c in content for c in "+-*/=<>{}[]()^_")
            if is_math_expr:
                ret = rf"\textcolor{{{latex_color}}}{{{content}}}"
            else:
                ret = rf"\textcolor{{{latex_color}}}{{\text{{{content}}}}}"
            return ret

        # Replace the color command with the LaTeX color command.
        in_line = re.sub(pattern, lambda m: _replacement(m, latex_color),
            in_line)
    return in_line


def has_color_command(line: str) -> bool:
    """
    Check if line contains any color commands.

    :param line: line to check
    :return: whether the line contains color commands
    """
    hdbg.dassert_isinstance(line, str)
    # hdbg.dassert_not_in("\n", line)
    for color in _MD_COLORS_LATEX_MAPPING.keys():
        # This regex matches LaTeX color commands like \red{content},
        # \blue{content}, etc.
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
    txt: str, *, use_abbreviations: bool = True,
    interpolate_colors: bool = False,
    all_md_colors: Optional[List[str]] = None,
) -> str:
    r"""
    Colorize bold text in a given string.

    :param txt: text to colorize
    :param use_abbreviations: use abbreviations for the colors like
        `\red{foo}` instead of `\textcolor{red}{foo}`
    :param interpolate_colors: interpolate the colors to use for the bold items
        instead of using a fixed set of colors
    :param all_colors: list of colors to use for the bold items
    :return: colored text
    """
    hdbg.dassert_isinstance(txt, str)
    if all_md_colors is None:
        all_md_colors = list(_MD_COLORS)
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
    def _interpolate_colors(num_bolds: int) -> List[str]:
        """
        Sample `num_bolds` colors evenly spaced from the available colors.
        """
        step = len(all_md_colors) // num_bolds
        colors = list(all_md_colors)[::step][:num_bolds]
        return colors

    if interpolate_colors:
        colors = _interpolate_colors(num_bolds)
    else:
        if num_bolds == 1:
            colors = ["red"]
        elif num_bolds == 2:
            colors = ["red", "blue"]
        elif num_bolds == 3:
            colors = ["red", "green", "blue"]
        elif num_bolds == 4:
            colors = ["red", "green", "blue", "violet"]
        else:
            colors = _interpolate_colors(num_bolds)
    _LOG.debug("colors=%s", colors)
    hdbg.dassert_lte(num_bolds, len(colors))
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
            hdbg.dassert_in(color_to_use, _MD_COLORS_LATEX_MAPPING)
            latex_color = _MD_COLORS_LATEX_MAPPING[color_to_use]
            color_idx += 1
            if use_abbreviations:
                ret = f"**\\{color_to_use}{{{text}}}**"
            else:
                ret = f"**\\textcolor{{{latex_color}}}{{{text}}}**"
            return ret

        line = re.sub(r"\*\*([^*]+)\*\*", color_replacer, line)
        txt_out.append(line)
    # Replace the tags with the fenced code blocks.
    txt_out = replace_tags_with_fenced_blocks(txt_out, fence_map)
    txt_out = "\n".join(txt_out)
    return txt_out
