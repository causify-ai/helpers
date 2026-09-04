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

    For Typst output, uses `#text(fill: color)[content]` syntax wrapped in a
    code fence so pandoc treats it as typst syntax even inside math blocks.
    E.g. (Typst):
    - `\red{abc}` -> `#text(fill: red)[abc]` (as backtick-wrapped typst code)
    - `\blue{x + y}` -> `#text(fill: blue)[x + y]` (as backtick-wrapped typst code)

    Color commands are processed even inside math delimiters ($...$, $$...$$)
    for both formats: LaTeX color syntax works in math mode, and typst code
    fences are recognized by pandoc even inside math blocks.

    :param in_line: input line to process
    :param output_format: "latex" (default) or "typst"
    :return: line with color commands transformed
    """
    hdbg.dassert_in(output_format, ("latex", "typst"))
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
                # Escape tildes (~) since they have special meaning in typst.
                escaped_content = content.replace("~", r"\~")
                typst_code = f'#text(fill: {output_color}, weight: "bold")[{escaped_content}]'
                ret = f"`{typst_code}`{{=typst}}"
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
_COLOR_MARKER_REGEX = re.compile(
    r"""
    (?<!\w)      # Negative lookbehind: the opening `@` must not be preceded
                 # by a word character (e.g., rejects `foo@bar.com`).
    @            # Match the opening `@` marker.
    ([^@\n]+)    # Capture everything up to the next `@` or newline.
    @            # Match the closing `@` marker.
    """,
    re.VERBOSE,
)

# Regex matching plain `**text**` bold markup that was *not* produced by the
# `@text@` marker replacement above, and that does not already wrap a color
# command's output. Marker-produced bold always starts with a backslash right
# after the opening `**` (e.g., `**\red{foo}**`), so a negative lookahead for
# `\` catches that case. A manually-typed `\color{...}` command (e.g.,
# `**\violet{violet}**`) is converted to a backtick-quoted Typst raw span by
# `process_color_commands()` *before* this function runs, turning the line
# into `` **`#text(...)[violet]`{=typst}** ``; without also excluding a
# leading backtick here, this regex would re-wrap that already-converted span
# in a second, nested backtick span, which Pandoc cannot parse as valid raw
# Typst (see `helpers/test/test_hmarkdown_coloring.py`).
_PLAIN_BOLD_REGEX = re.compile(
    r"""
    \*\*         # Match the opening `**`.
    (?!\\|`)     # Negative lookahead: skip marker-produced `**\color{...}**`
                 # and already-converted `` **`#text(...)`{=typst}** ``.
    ([^*\n]+?)   # Capture everything up to the next `*` or newline (lazy).
    \*\*         # Match the closing `**`.
    """,
    re.VERBOSE,
)

# Font weight and fill used to render plain `**text**` bold in Typst:
# "semibold" is visually lighter than the "bold" weight used for `@text@`
# markers, and a 70%-black gray tint (30% lightness) makes it read as bold
# text rather than a full-strength color, so `@text@` markers stand out as
# the stronger emphasis. LaTeX has no semibold series available in this
# repo's font setup, so plain `**text**` is left as regular LaTeX bold
# (untouched).
_PLAIN_BOLD_WEIGHT_TYPST = "semibold"
_PLAIN_BOLD_FILL_TYPST = "luma(30%)"

# Matches a single-line inline math span (`$...$`, no nested `$`).
_INLINE_MATH_REGEX = re.compile(r"\$[^$\n]+\$")


def _wrap_typst_text(text: str, fill: str, weight: str) -> str:
    r"""
    Wrap `text` in raw Typst `#text(fill=..., weight=...)[...]` span(s).

    Any inline math (`$...$`) inside `text` is left untouched, outside the
    raw span(s), so Pandoc still translates it from LaTeX to Typst math on
    its own.

    E.g., 
    ```
    text = r"$\eta$ is too small"
    ```
    becomes:
    ```
    $\eta$`#text(fill: ..., weight: ...)[ is too small]`{=typst}
    ```

    :param text: text to wrap, possibly containing inline math
    :param fill: Typst `fill` color expression, e.g. `"red"` or `"luma(30%)"`
    :param weight: Typst `weight` expression, e.g. `"bold"` or `"semibold"`
    :return: `text` with its non-math parts wrapped in raw Typst span(s)
    """

    def _wrap(chunk: str) -> str:
        # Escape tildes (~) since they have special meaning in typst.
        escaped_chunk = chunk.replace("~", r"\~")
        typst_code = f'#text(fill: {fill}, weight: "{weight}")[{escaped_chunk}]'
        return "`" + typst_code + "`{=typst}"

    parts = []
    pos = 0
    for match in _INLINE_MATH_REGEX.finditer(text):
        prefix = text[pos : match.start()]
        if prefix:
            parts.append(_wrap(prefix))
        # Leave the inline math span untouched.
        parts.append(match.group(0))
        pos = match.end()
    suffix = text[pos:]
    if suffix:
        parts.append(_wrap(suffix))
    return "".join(parts)


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
    Colorize `@text@` markers; render plain `**text**` as Typst semibold.

    Scans the text line-by-line for `@text@` markers and replaces each with
    colored bold text, e.g., `@text@` -> `**\red{text}**`, using the full
    (100%) color strength. For Typst output, regular bold markdown
    `**text**` is instead rendered at "semibold" weight with a 70%-black
    gray fill (`luma(30%)`), visually lighter than the full-strength
    "bold" weight and color used for `@text@` markers, so `@text@` markers
    stand out as the stronger emphasis. For LaTeX output, plain `**text**`
    is left untouched (no semibold series is set up in this repo's LaTeX
    fonts). Skips code blocks and tables to preserve their formatting.
    `@text@` markers are colored sequentially using the provided color
    list.

    E.g.:
    ```
    - @Definition@: **Knowledge Representation (KR)** is ...
    ```
    becomes (LaTeX, abbreviated):
    ```
    - **\red{Definition}**: **Knowledge Representation (KR)** is ...
    ```

    For LaTeX output (default), `@text@` emits `**\red{text}**` or
    `**\textcolor{red}{text}**` depending on use_abbreviations, while plain
    `**text**` is left as plain markdown bold.

    For Typst output, `@text@` emits `#red[text]` (abbreviated, if supported
    by template) or `#text(fill: red)[text]` (full), while plain `**text**`
    emits `#text(fill: luma(30%), weight: "semibold")[text]`.

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
    num_bolds = tot_markers

    def _interpolate_colors(num_bolds: int) -> List[str]:
        """
        Sample colors evenly spaced to cover all bold items distinctly.
        """
        step = len(all_md_colors) // num_bolds
        colors = list(all_md_colors)[::step][:num_bolds]
        return colors

    if num_bolds == 0:
        # No `@text@` markers: still fall through to gray-ify plain `**text**`
        # bold below, but there is no color list to compute.
        colors: List[str] = []
    elif interpolate_colors:
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
                ret = _wrap_typst_text(text, typst_color, "bold")
            return ret

        def semibold_replacer(match: Match[str]) -> str:
            """
            Replace a plain `**text**` bold with Typst semibold, gray-black.

            LaTeX has no semibold series set up, so the match is returned
            unchanged (plain markdown bold).
            """
            text = match.group(1)
            if output_format == "latex":
                ret = f"**{text}**"
            else:  # typst
                ret = _wrap_typst_text(
                    text, _PLAIN_BOLD_FILL_TYPST, _PLAIN_BOLD_WEIGHT_TYPST
                )
            return ret

        # Apply semibold weight to plain `**text**` bold first, while `**`
        # still unambiguously marks plain markdown bold (before `@text@`
        # markers are expanded into `**\color{...}**`, which would otherwise
        # be mistaken for more plain bold spans).
        line = re.sub(_PLAIN_BOLD_REGEX, semibold_replacer, line)
        line = re.sub(_COLOR_MARKER_REGEX, color_replacer, line)
        txt_out.append(line)
    # Restore code blocks and tables that were temporarily replaced with tags.
    txt_out = replace_tags_with_fenced_blocks(txt_out, fence_map)
    txt_out = replace_tags_with_tables(txt_out, table_map)
    txt_out = "\n".join(txt_out)
    return txt_out
