"""
Utilities for colorizing markdown and LaTeX text with color commands.

Import as:

import helpers.hmarkdown_coloring as hmarcolo
"""

import logging
import re
from typing import Dict, List, Match, Optional

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

# Mapping of markdown color names to their Typst color equivalents.
# Uses Typst built-in colors where available; rgb() for others.
_MD_COLORS_TYPST_MAPPING = {
    "red": "red",
    "orange": "orange",
    "yellow": "yellow",
    "lime": 'rgb("#00FF00")',  # Typst lime not standard; use bright green
    "green": "green",
    "teal": "teal",
    "cyan": 'rgb("#00FFFF")',  # Typst cyan uses different name
    "blue": "blue",
    "purple": "purple",
    "violet": 'rgb("#8B00FF")',  # Typst violet via rgb
    "magenta": 'rgb("#FF00FF")',  # Typst magenta via rgb
    "pink": 'rgb("#FFC0CB")',  # Typst pink via rgb
    "brown": 'rgb("#8B4513")',  # Typst brown via rgb
    "olive": "olive",
    "gray": "gray",
    "darkgray": 'rgb("#A9A9A9")',  # Typst darkgray via rgb
    "lightgray": 'rgb("#D3D3D3")',  # Typst lightgray via rgb
    "black": "black",
    "white": "white",
}


def get_md_colors_mapping(output_format: str) -> Dict[str, str]:
    """
    Get a copy of the markdown color mapping for the specified output format.

    :param output_format: "latex" (default) or "typst"
    :return: Dict mapping color names (e.g., 'red', 'blue') to output format color names
    """
    hdbg.dassert_in(output_format, ("latex", "typst"))
    if output_format == "latex":
        ret = dict(_MD_COLORS_LATEX_MAPPING)
    else:
        ret = dict(_MD_COLORS_TYPST_MAPPING)
    return ret


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


def process_color_commands(in_line: str, output_format: str) -> str:
    r"""
    Transform color commands like `\red{xyz}` into valid syntax.

    For LaTeX output, if content is text (not math), wraps it in `\text{}`.
    E.g. (LaTeX):
    - `\red{abc}` -> `\textcolor{red}{\text{abc}}`
    - `\blue{x + y}` -> `\textcolor{blue}{x + y}`

    For Typst output, uses `#text(fill: color)[content]` syntax.
    E.g. (Typst):
    - `\red{abc}` -> `#text(fill: red)[abc]`
    - `\blue{x + y}` -> `#text(fill: blue)[x + y]`

    Note: For typst output, color commands inside math delimiters ($...$) are
    not processed, as typst syntax is incompatible with LaTeX math mode.

    :param in_line: input line to process
    :param output_format: "latex" (default) or "typst"
    :return: line with color commands transformed
    """
    hdbg.dassert_in(output_format, ("latex", "typst"))
    # For typst output, skip processing \red{} commands if line contains math
    # delimiters to avoid inserting typst syntax inside LaTeX math mode (which
    # pandoc can't parse).
    if output_format == "typst" and ("$" in in_line or "$$" in in_line):
        return in_line
    color_mapping = get_md_colors_mapping(output_format)
    for md_color, output_color in color_mapping.items():
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

        def _replacement(match: Match, output_color: str) -> str:
            """
            Replace a color command with output-format-specific color directive.
            """
            content = match.group(1)
            if output_format == "latex":
                # Math expressions (containing operators, brackets, etc.) render
                # directly; plain text needs \text{} wrapper for proper LaTeX rendering.
                is_math_expr = any(c in content for c in "+-*/=<>{}[]()^_")
                if is_math_expr:
                    ret = rf"\textcolor{{{output_color}}}{{{content}}}"
                else:
                    ret = rf"\textcolor{{{output_color}}}{{\text{{{content}}}}}"
            elif output_format == "typst":
                ret = f'#text(fill: {output_color}, weight: "bold")[{content}]'
            else:
                raise ValueError("Invalid output_format='%s'" % output_format)
            return ret

        # Replace the color command with the output-format-specific color command.
        in_line = re.sub(
            pattern, lambda m: _replacement(m, output_color), in_line
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
    latex_mapping = get_md_colors_mapping("latex")
    for color in latex_mapping.keys():
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


# Regex matching `@text@` markers requesting colorized bold text. The opening
# `@` must not be preceded by a word character so that email addresses like
# `foo@bar.com` are not mistaken for markers (real markers are always preceded
# by whitespace or punctuation, e.g., `- @Definition@:`).
# TODO(ai_gp): Use re.VERBOSE and comments
_COLOR_MARKER_REGEX = r"(?<!\w)@([^@\n]+)@"


# TODO(gp): -> List[str]
# TODO(gp): Use hmarkdown.process_lines() and test it.
# TODO(gp): Consider use_abbreviations which seems to make things more complex
# than needed
def colorize_bullet_points_in_slide(
    txt: str,
    output_format: str,
    *,
    use_abbreviations: bool = True,
    interpolate_colors: bool = False,
    all_md_colors: Optional[List[str]] = None,
) -> str:
    r"""
    Colorize `@text@` markers with color commands; leave `**text**` as-is.

    Scans the text line-by-line for `@text@` markers and replaces each with
    colored bold text, e.g., `@text@` -> `**\red{text}**`. Regular bold
    markdown `**text**` is left untouched, so it renders as plain (black)
    bold. Skips code blocks and tables to preserve their formatting. `@text@`
    markers are colored sequentially using the provided color list.

    E.g.:
    ```
    - @Definition@: **Knowledge Representation (KR)** is ...
    ```
    becomes (LaTeX, abbreviated):
    ```
    - **\red{Definition}**: **Knowledge Representation (KR)** is ...
    ```

    For LaTeX output (default), emits `**\red{text}**` or
    `**\textcolor{red}{text}**` depending on use_abbreviations.

    For Typst output, emits `#red[text]` (abbreviated, if supported by
    template) or `#text(fill: red)[text]` (full).

    :param txt: Markdown text containing `@text@` markers to colorize
    :param use_abbreviations:
        - If True, use abbreviated color syntax (e.g., `\red{foo}` for LaTeX,
          `#red[foo]` for Typst)
        - If False, use full syntax (e.g., `\textcolor{red}{foo}` for LaTeX,
          `#text(fill: red)[foo]` for Typst)
    :param interpolate_colors:
        - If True, evenly space selected colors across all `@text@` markers
        - If False, use a predefined sequence for common counts (1-4 items get
          fixed color sets, more items cycle through all_md_colors)
    :param all_md_colors: List of available colors to cycle through
        - Default: curated list from `get_md_colors()`
    :param output_format: "latex" (default) or "typst"
    :return: Markdown text with `@text@` markers replaced by colored bold text
    """
    hdbg.dassert_isinstance(txt, str)
    hdbg.dassert_in(output_format, ("latex", "typst"))
    if all_md_colors is None:
        all_md_colors = list(get_md_colors())
    # Strip code blocks and tables to avoid colorizing content inside them.
    lines = txt.split("\n")
    lines, fence_map = replace_fenced_blocks_with_tags(lines)
    _LOG.debug("Found %s fenced blocks", len(fence_map))
    lines, table_map = replace_tables_with_tags(lines)
    _LOG.debug("Found %s tables", len(table_map))
    # Count `@text@` markers to determine how many colorized items exist.
    tot_markers = 0
    # Scan the text line by line and count how many markers there are.
    for line in lines:
        # Count the number of `@text@` markers.
        num_markers = len(re.findall(_COLOR_MARKER_REGEX, line))
        tot_markers += num_markers
    _LOG.debug("tot_markers=%s", tot_markers)
    if tot_markers == 0:
        return txt
    num_bolds = tot_markers

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

        def color_replacer(match: Match[str]) -> str:
            r"""
            Replace a `@foo@` marker with colored bold text.
            """
            nonlocal color_idx
            text = match.group(1)
            hdbg.dassert_lte(
                color_idx,
                len(colors),
                "Color index out of bounds; not enough colors assigned",
            )
            color_to_use = colors[color_idx]
            color_idx += 1
            if output_format == "latex":
                latex_mapping = get_md_colors_mapping("latex")
                hdbg.dassert_in(
                    color_to_use,
                    latex_mapping,
                    "Selected color is not in the LaTeX color mapping",
                )
                latex_color = latex_mapping[color_to_use]
                # LaTeX requires escaping underscores and ampersands.
                escaped_text = text.replace("_", "\\_").replace("&", "\\&")
                if use_abbreviations:
                    ret = f"**\\{color_to_use}{{{escaped_text}}}**"
                else:
                    ret = f"**\\textcolor{{{latex_color}}}{{{escaped_text}}}**"
            else:  # typst
                typst_mapping = get_md_colors_mapping("typst")
                hdbg.dassert_in(
                    color_to_use,
                    typst_mapping,
                    "Selected color is not in the Typst color mapping",
                )
                typst_color = typst_mapping[color_to_use]
                # Typst: no escaping needed for underscores/ampersands in text mode.
                # TODO(gp): They seem exactly the same?
                if use_abbreviations:
                    # Abbreviated: wrap in backticks for proper typst syntax
                    ret = f'`#text(fill: {typst_color}, weight: "bold")[{text}]`{{=typst}}'
                else:
                    # Full: #text(fill: color)[text]
                    ret = f'#text(fill: {typst_color}, weight: "bold")[{text}]'
                    ret = "`" + ret + "`{=typst}"
            return ret

        line = re.sub(_COLOR_MARKER_REGEX, color_replacer, line)
        txt_out.append(line)
    # Restore code blocks and tables that were temporarily replaced with tags.
    txt_out = replace_tags_with_fenced_blocks(txt_out, fence_map)
    txt_out = replace_tags_with_tables(txt_out, table_map)
    txt_out = "\n".join(txt_out)
    return txt_out
