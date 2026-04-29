"""
Utilities for colorizing markdown and LaTeX text with color commands.

Import as:

import helpers.hmarkdown_coloring as hmarcolo
"""

import logging
import re
from typing import Dict, List, Optional

import helpers.hdbg as hdbg
from helpers.hmarkdown_fenced_blocks import (
    replace_fenced_blocks_with_tags,
    replace_tags_with_fenced_blocks,
)
from helpers.hmarkdown_tables import (
    replace_tables_with_tags,
    replace_tags_with_tables,
)

_LOG = logging.getLogger(__name__)


# #############################################################################
# Colorize
# #############################################################################

# Mapping of markdown color names to their LaTeX color equivalents for use in
# \textcolor{} commands.
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


def get_md_colors_latex_mapping() -> Dict[str, str]:
    """
    Get a copy of the markdown-to-LaTeX color mapping.

    :return: Dict mapping color names (e.g., 'red', 'blue') to LaTeX color names
    """
    return dict(_MD_COLORS_LATEX_MAPPING)


# Curated list of colors that are visually distinguishable and work well in
# both markdown and LaTeX contexts (excludes ones which are too light or have
# poor contrast).
_MD_COLORS = [
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
    "black",
    # "white",
]


def get_md_colors() -> List[str]:
    """
    Get a copy of the curated list of markdown colors.

    :return: List of color names suitable for colorizing markdown/LaTeX
    """
    return list(_MD_COLORS)


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
    for md_color, latex_color in get_md_colors_latex_mapping().items():
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
            """
            Replace a color command with LaTeX \textcolor directive.
            """
            content = match.group(1)
            # Math expressions (containing operators, brackets, etc.) render
            # directly; plain text needs \text{} wrapper for proper LaTeX rendering.
            is_math_expr = any(c in content for c in "+-*/=<>{}[]()^_")
            if is_math_expr:
                ret = rf"\textcolor{{{latex_color}}}{{{content}}}"
            else:
                ret = rf"\textcolor{{{latex_color}}}{{\text{{{content}}}}}"
            return ret

        # Replace the color command with the LaTeX color command.
        in_line = re.sub(
            pattern, lambda m: _replacement(m, latex_color), in_line
        )
    return in_line


def has_color_command(text: str) -> bool:
    """
    Check if text contains any color commands like `\\red{...}` or `\\blue{...}`.

    :param text: text to check
    :return: True if text contains at least one color command
    """
    hdbg.dassert_isinstance(text, str)
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
        if re.search(pattern, text):
            return True
    return False


# TODO(gp): -> List[str]
# TODO(gp): Use hmarkdown.process_lines() and test it.
def colorize_bullet_points_in_slide(
    txt: str,
    *,
    use_abbreviations: bool = True,
    interpolate_colors: bool = False,
    all_md_colors: Optional[List[str]] = None,
) -> str:
    r"""
    Colorize bold markdown items `**text**` with color commands.

    Scans the text line-by-line for bold markdown items and wraps each in a
    color command (e.g., `**\red{text}**`). Skips code blocks and tables to
    preserve their formatting. Bold items are colored sequentially using the
    provided color list.

    :param txt: Markdown text containing bold items to colorize
    :param use_abbreviations:
        - If True, use abbreviated color syntax (e.g., `\red{foo}`)
        - If False, use full LaTeX syntax (e.g., `\textcolor{red}{foo}`)
    :param interpolate_colors:
        - If True, evenly space selected colors across all bold items
        - If False, use a predefined sequence for common counts (1-4 items get
          fixed color sets, more items cycle through all_md_colors)
    :param all_md_colors: List of available colors to cycle through
        - Default: curated list from `get_md_colors()`
    :return: Markdown text with bold items wrapped in color commands
    """
    hdbg.dassert_isinstance(txt, str)
    if all_md_colors is None:
        all_md_colors = list(get_md_colors())
    # Strip code blocks and tables to avoid colorizing content inside them.
    lines = txt.split("\n")
    lines, fence_map = replace_fenced_blocks_with_tags(lines)
    _LOG.debug("Found %s fenced blocks", len(fence_map))
    lines, table_map = replace_tables_with_tags(lines)
    _LOG.debug("Found %s tables", len(table_map))
    # Count bold markers (**) to determine how many bold items exist.
    tot_bold = 0
    # Scan the text line by line and count how many bold items there are.
    for line in lines:
        # Count the number of bold items.
        num_bold = len(re.findall(r"\*\*", line))
        tot_bold += num_bold
    _LOG.debug("tot_bold=%s", tot_bold)
    if tot_bold == 0:
        return txt
    # Divide by 2 since each bold item is wrapped with ** on both sides.
    # hdbg.dassert_eq(tot_bold % 2, 0, "tot_bold=%s needs to be even", tot_bold)
    num_bolds = tot_bold // 2

    def _interpolate_colors(num_bolds: int) -> List[str]:
        """
        Sample colors evenly spaced to cover all bold items distinctly.
        """
        step = len(all_md_colors) // num_bolds
        colors = list(all_md_colors)[::step][:num_bolds]
        return colors

    if interpolate_colors:
        colors = _interpolate_colors(num_bolds)
    else:
        # Use fixed color sequences for small numbers of bold items; for larger
        # counts, cycle through the available colors.
        if num_bolds == 1:
            colors = ["red"]
        elif num_bolds == 2:
            colors = ["red", "blue"]
        elif num_bolds == 3:
            colors = ["red", "green", "blue"]
        elif num_bolds == 4:
            colors = ["red", "green", "blue", "violet"]
        else:
            colors = all_md_colors[:num_bolds]
    _LOG.debug("colors=%s", colors)
    hdbg.dassert_lte(
        num_bolds, len(colors), "Number of bold items exceeds available colors"
    )
    color_idx = 0
    txt_out = []
    for line in lines:

        def color_replacer(match: re.Match[str]) -> str:
            """
            Replace strings like "**foo**" with strings like "**\red{foo}**".
            """
            nonlocal color_idx
            text = match.group(1)
            hdbg.dassert_lte(
                color_idx,
                len(colors),
                "Color index out of bounds; not enough colors assigned",
            )
            color_to_use = colors[color_idx]
            hdbg.dassert_in(
                color_to_use,
                get_md_colors_latex_mapping(),
                "Selected color is not in the color mapping",
            )
            latex_color = get_md_colors_latex_mapping()[color_to_use]
            color_idx += 1
            if use_abbreviations:
                ret = f"**\\{color_to_use}{{{text}}}**"
            else:
                ret = f"**\\textcolor{{{latex_color}}}{{{text}}}**"
            return ret

        line = re.sub(r"\*\*([^*]+)\*\*", color_replacer, line)
        txt_out.append(line)
    # Restore code blocks and tables that were temporarily replaced with tags.
    txt_out = replace_tags_with_fenced_blocks(txt_out, fence_map)
    txt_out = replace_tags_with_tables(txt_out, table_map)
    txt_out = "\n".join(txt_out)
    return txt_out
