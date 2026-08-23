"""
Import as:

import helpers.hmarkdown_formatting as hmarform
"""

import logging
import re
from typing import List, Match

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown_headers as hmarhead
import helpers.hmarkdown_slides as hmarslid
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.htimer as htimer
import dev_scripts_helpers.dockerize.lib_prettier as dshdlipr

_LOG = logging.getLogger(__name__)


def remove_end_of_line_periods(lines: List[str]) -> List[str]:
    """
    Remove periods at the end of each line in the given text.

    :param lines: list of input lines to process
    :return: lines with end-of-line periods removed
    """
    hdbg.dassert_isinstance(lines, list)
    txt_out = [line.rstrip(".") for line in lines]
    hdbg.dassert_isinstance(txt_out, list)
    return txt_out


def remove_empty_lines(lines: List[str]) -> List[str]:
    """
    Remove empty lines from the given text.

    :param lines: list of input lines to process
    :return: lines with empty lines removed
    """
    hdbg.dassert_isinstance(lines, list)
    txt_out = [line for line in lines if line != ""]
    hdbg.dassert_isinstance(txt_out, list)
    return txt_out


# def remove_gdoc_artifacts(lines: List[str]) -> List[str]:
#     """
#     Remove empty lines from the given text.

#     :param lines: list of input lines to process
#     :return: lines with empty lines removed
#     """
#     hdbg.dassert_isinstance(lines, list)
#     # Remove “” and ….
#     lines = re.sub(r"“", '"', lines)
#     lines = re.sub(r"”", '"', lines)
#     lines = re.sub(r"’", "'", lines)
#     lines = re.sub(r"…", "", lines)
#     hdbg.dassert_isinstance(lines, list)
#     return lines


# TODO(gp): Add tests.
def remove_code_delimiters(lines: List[str]) -> List[str]:
    """
    Remove ```python and ``` delimiters from a given text.

    :param lines: list of input lines containing code delimiters
    :return: lines with the code delimiters removed
    """
    hdbg.dassert_isinstance(lines, list)
    # Join lines back to text, apply regex logic, then split again.
    txt = "\n".join(lines)
    # Replace the ```python and ``` delimiters with empty strings.
    txt_out = txt.replace("```python", "").replace("```", "")
    txt_out = txt_out.strip()
    # Remove the numbers at the beginning of the line, if needed
    # E.g., `3: """` -> `"""`.
    txt_out = re.sub(r"(^\d+: )", "", txt_out, flags=re.MULTILINE)
    # Split back into lines.
    result = txt_out.split("\n") if txt_out else []
    hdbg.dassert_isinstance(result, list)
    return result


def add_line_numbers(lines: List[str]) -> List[str]:
    """
    Add line numbers to each line of text.

    :param lines: list of input lines to process
    :return: lines with line numbers added
    """
    hdbg.dassert_isinstance(lines, list)
    numbered_lines = []
    for i, line in enumerate(lines, 1):
        numbered_lines.append(f"{i}: {line}")
    hdbg.dassert_isinstance(numbered_lines, list)
    return numbered_lines


def remove_formatting(txt: str) -> str:
    """
    Remove markdown and LaTeX formatting from text.

    :param txt: input text to process
    :return: text with formatting removed
    """
    # Replace bold markdown syntax with plain text.
    txt = re.sub(r"\*\*(.*?)\*\*", r"\1", txt)
    # Replace italic markdown syntax with plain text.
    txt = re.sub(r"\*(.*?)\*", r"\1", txt)
    # Remove \textcolor{red}{ ... }.
    txt = re.sub(r"\\textcolor\{(.*?)\}\{(.*?)\}", r"\2", txt)
    # Remove \red{ ... }.
    txt = re.sub(r"\\\S+\{(.*?)\}", r"\1", txt)
    return txt


def md_clean_up(txt: str) -> str:
    """
    Clean up a Markdown file copy-pasted from Google Docs, ChatGPT.

    :param txt: input text to process
    :return: text with the cleaning up applied
    """
    # 0) General formatting.
    # Remove dot at the end of each line.
    txt = re.sub(r"\.\s*$", "", txt, flags=re.MULTILINE)
    # 1) ChatGPT formatting.
    # E.g.,``  • Description Logics (DLs) are a family``
    # Replace `•` with `-`
    txt = re.sub(r"•\s+", r"- ", txt)
    # Replace `\t` with 2 spaces
    txt = re.sub(r"\t", r"  ", txt)
    # Remove `⋅`.
    txt = re.sub(r"⸻", r"", txt)
    # “
    txt = re.sub(r"“", r'"', txt)
    # ”
    txt = re.sub(r"”", r'"', txt)
    # ’
    txt = re.sub(r"’", r"'", txt)
    # …
    txt = re.sub(r"…", r"...", txt)
    # 2) Latex formatting.
    # Replace \( ... \) math syntax with $ ... $.
    txt = re.sub(r"\\\(\s*(.*?)\s*\\\)", r"$\1$", txt)
    # Replace \[ ... \] math syntax with $$ ... $$, handling multiline equations.
    txt = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", txt, flags=re.DOTALL)
    # Replace `P(.)`` with `\Pr(.)`.
    txt = re.sub(r"P\((.*?)\)", r"\\Pr(\1)", txt)
    #
    txt = re.sub(r"\\left\[", r"[", txt)
    txt = re.sub(r"\\right\]", r"]", txt)
    #
    txt = re.sub(r"\\mid", r"|", txt)
    #
    txt = re.sub(r"→", r"$\\rightarrow$", txt)
    # Remove empty spaces at beginning / end of Latex equations $...$.
    # E.g., $ \text{Student} $ becomes $\text{Student}$
    # txt = re.sub(r"\$\s+(.*?)\s\$", r"$\1$", txt)
    # Transform `Example: Training a deep` into `E.g., training a deep`,
    # converting the word after `Example:` to lower case.
    txt = re.sub(r"\bExample:", "E.g.,", txt)
    txt = re.sub(r"\bE.g.,\s+(\w)", lambda m: "E.g., " + m.group(1).lower(), txt)
    return txt


def remove_empty_lines_from_markdown(lines: List[str]) -> List[str]:
    """
    Remove all empty lines from markdown text.

    :param lines: list of input markdown lines
    :return: formatted markdown lines
    """
    hdbg.dassert_isinstance(lines, list)
    # Remove empty lines.
    result = [line for line in lines if line.strip()]
    hdbg.dassert_isinstance(result, list)
    return result


def prettier_markdown(txt: str) -> str:
    """
    Format markdown text using `prettier`.

    :param txt: input text to format
    :return: formatted text
    """
    file_type = "md"
    txt = dshdlipr.prettier_on_str(txt, file_type)
    return txt


def format_markdown(txt: str) -> str:
    """
    Format markdown text.

    :param txt: input text to format
    :return: formatted text
    """
    file_type = "md"
    txt = dshdlipr.prettier_on_str(txt, file_type)
    lines = txt.split("\n")
    clean_lines = remove_empty_lines_from_markdown(lines)
    txt = "\n".join(clean_lines)
    return txt


def bold_first_level_bullets(
    lines: List[str], *, max_length: int = 30
) -> List[str]:
    """
    Make first-level bullets bold in markdown text.

    :param lines: list of input markdown lines
    :param max_length: max length of the bullet text to be bolded. The
        value '-1' means no limit
    :return: formatted markdown lines with first-level bullets in bold
    """
    hdbg.dassert_isinstance(lines, list)
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
    hdbg.dassert_isinstance(result, list)
    return result


def format_figures(lines: List[str]) -> List[str]:
    """
    Convert markdown slides with figures to use fenced div syntax with column
    layout.

    If the input already uses column format or contains no figures,
    returns unchanged.

    :param lines: list of input markdown lines
    :return: formatted markdown lines with figures in column layout
    """
    hdbg.dassert_isinstance(lines, list)
    # Check if already in column format.
    text = "\n".join(lines)
    if "::: columns" in text and ":::: {.column" in text:
        return lines
    # Find first figure line to split content.
    first_figure_idx = -1
    for i, line in enumerate(lines):
        if re.match(r"^\s*!\[.*\]\(.*\)\s*$", line.strip()):
            first_figure_idx = i
            break
    # If no figures found, return original lines unchanged.
    if first_figure_idx == -1:
        return lines
    # Split content: slide titles (lines starting with *) stay outside columns,
    # other content before first figure goes to left column,
    # everything from first figure onwards goes to right column.
    pre_figure_lines = lines[:first_figure_idx]
    figure_content = lines[first_figure_idx:]
    # Separate slide titles from other content
    slide_titles = []
    text_lines = []
    for line in pre_figure_lines:
        if line.strip().startswith("*"):
            slide_titles.append(line)
        else:
            text_lines.append(line)
    # Remove empty lines at the beginning and end of text_lines.
    while text_lines and not text_lines[0].strip():
        text_lines.pop(0)
    while text_lines and not text_lines[-1].strip():
        text_lines.pop()
    # Build the column format.
    result = []
    # Add slide titles first (outside columns)
    result.extend(slide_titles)
    result.append("::: columns")
    result.append(":::: {.column width=65%}")
    result.extend(text_lines)
    result.append("::::")
    result.append(":::: {.column width=40%}")
    result.append("")
    result.extend(figure_content)
    result.append("::::")
    result.append(":::")
    hdbg.dassert_isinstance(result, list)
    return result


def _escape_typst_markup(text: str) -> str:
    r"""
    Escape a plain-text string for safe embedding inside Typst markup
    content (e.g., the `content` in `#text(...)[content]`).

    Uses the same escaping rules as `_colorize_backticks()` in
    `preprocess_notes.py`, since the characters below all have special meaning
    to the Typst markup parser.

    :param text: plain text to embed in Typst markup
    :return: text with Typst-special characters escaped
    """
    # Escape `_` since Typst treats it as underscore emphasis markup.
    text = text.replace("_", r"\_")
    # Escape `*` since Typst parses it as strong-emphasis markup.
    text = text.replace("*", r"\*")
    # Escape `//` since Typst treats it as a line comment, which swallows
    # the rest of the line (e.g., the `//` in `https://...`).
    text = text.replace("//", r"\//")
    # Escape `#` since Typst parses it as the start of code mode.
    text = text.replace("#", r"\#")
    # Escape `$` since Typst parses it as math-mode delimiters.
    text = text.replace("$", r"\$")
    # Escape `@` since Typst parses `@name` as a citation/reference.
    text = text.replace("@", r"\@")
    # Escape `<` since Typst parses `<name>` as a label reference.
    text = text.replace("<", r"\<")
    return text


# Link color: matches Google's product hyperlink color (Gmail, Docs,
# Drive), rather than a generic named "blue".
_LINK_COLOR_HEX = "1A73E8"


def _style_link_latex(text: str) -> str:
    r"""
    Build the LaTeX-styled (colored, underlined) inline text for a link.

    :param text: link label text
    :return: `\textcolor[HTML]{...}{\underline{text}}` snippet
    """
    return rf"\textcolor[HTML]{{{_LINK_COLOR_HEX}}}{{\underline{{{text}}}}}"


# Regex matching the snippet built by `_style_link_latex()`, used to detect
# links that were already converted (to normalize them and to protect them
# from being re-processed by later passes below).
_STYLED_LINK_TEXT_RE = (
    r"\\textcolor\[HTML\]\{"
    + _LINK_COLOR_HEX
    + r"\}\{\\underline\{([^}]+)\}\}"
)


def _convert_textcolor_underline_to_typst(line: str) -> str:
    r"""
    Convert the `_style_link_latex()` snippet on a line to the Typst
    raw-code equivalent.

    :param line: line possibly containing the `_style_link_latex()` snippet
    :return: line with those occurrences converted to Typst raw code
    """

    # Pandoc parses a bare `\textcolor[HTML]{...}{...}` appearing in plain
    # markdown text as a `RawInline` node tagged with format `tex`, which the
    # Typst writer silently drops (it only emits raw-inline content tagged
    # `typst`). That is why a line like
    #     [\textcolor[HTML]{1A73E8}{\underline{ELMS}}](URL)
    # renders as an empty link (`#link("URL")[]`) when compiling to Typst
    # instead of latex/beamer. The fix is to emit a backtick-quoted Typst
    # raw-code span (`` `...`{=typst} ``, pandoc's "raw attribute" syntax)
    # instead, so the content survives as a `RawInline` tagged `typst`.

    def _replace(match: Match) -> str:
        content = _escape_typst_markup(match.group(1))
        color = f'rgb("#{_LINK_COLOR_HEX}")'
        return f"`#text(fill: {color})[#underline[{content}]]`{{=typst}}"

    return re.sub(_STYLED_LINK_TEXT_RE, _replace, line)


def format_md_links_to_latex_format(
    lines: List[str], *, output_format: str = "latex"
) -> List[str]:
    r"""
    Convert markdown links to formatted (colored, underlined) links.

    Convert markdown links:
    - Plain URLs:
        http://... or https://...
      to the format (LaTeX):
        [\textcolor[HTML]{1A73E8}{\underline{URL}}](URL)

    - Existing formatted links:
        [Text](URL)
      to the format (LaTeX):
        [\textcolor[HTML]{1A73E8}{\underline{Text}}](URL)

    - Email links:
        [](email@domain.com) or [](http://...) or [](https://...)
      to the format (LaTeX):
        [\textcolor[HTML]{1A73E8}{\underline{URL}}](URL)

    - Markdown links with an email target (display text != email):
        [Email](email@domain.com)
      to the format (LaTeX):
        [\textcolor[HTML]{1A73E8}{\underline{Email}}](email@domain.com)

    - Picture links
        ![](lectures_source/.../lec_4_1_slide_5_image_1.png)
      are left untouched

    The color used (`_LINK_COLOR_HEX`) matches Google's product hyperlink
    color (Gmail, Docs, Drive).

    For `output_format="typst"`, the same conversions are done, but the
    styling is emitted as Typst raw code (e.g.,
    `` [`#text(fill: rgb("#1A73E8"))[#underline[URL]]`{=typst}](URL) ``)
    instead of the LaTeX `\textcolor{}{\underline{}}` snippet, since the
    latter is dropped by pandoc's Typst writer (see
    `_convert_textcolor_underline_to_typst()`).

    :param lines: list of input markdown lines
    :param output_format: "latex" or "typst"
    :return: formatted markdown lines with styled links
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_in(output_format, ("latex", "typst"))
    result = []
    # URL regex pattern.
    url_pattern = r"https?://[^\s)}\]`]+"
    # Pattern for URLs in backticks.
    backtick_url_pattern = r"`(https?://[^\s`]+)`"
    # Pattern for existing formatted links that need normalization.
    # This matches [\textcolor[HTML]{1A73E8}{\underline{Text}}](URL) where
    # Text != URL.
    formatted_link_pattern = (
        r"\[" + _STYLED_LINK_TEXT_RE + r"\]\((https?://[^)]+)\)"
    )
    # Pattern for markdown links: [Text](URL).
    # Matches text that can include escaped underscores (\_ ).
    markdown_link_pattern = r"\[((?:[^\]\\]|\\[_])+)\]\((https?://[^\)]+)\)"
    # Pattern for email links: [email@domain.com](email@domain.com).
    email_link_pattern = r"\[([^\]\\]+@[^\]\\]+)\]\(([^)]+@[^)]+)\)"
    # Pattern for markdown links with an email target: [Text](email@domain.com).
    # Unlike `email_link_pattern`, the display text does not need to be an
    # email address itself (e.g., [Email](gsaggese@umd.edu)).
    email_target_link_pattern = (
        r"\[((?:[^\]\\]|\\[_])+)\]\(([^\s\)@]+@[^\s\)@]+\.[^\s\)]+)\)"
    )
    # Pattern for empty bracket links: [](URL) or [](email).
    empty_bracket_pattern = r"\[\]\(([^\)]+)\)"
    # Pattern for image links: ![...](...).
    image_link_pattern = r"!\[.*?\]\([^\)]+\)"
    for line in lines:
        # Process the line for all URL patterns.
        processed_line = line
        # Store image links temporarily to avoid processing them.
        image_placeholders = []

        def store_image_link(match):
            placeholder = f"__IMAGE_LINK_{len(image_placeholders)}__"
            image_placeholders.append(match.group(0))
            return placeholder

        processed_line = re.sub(
            image_link_pattern, store_image_link, processed_line
        )

        # Convert empty bracket links [](URL) or [](email).
        def convert_empty_bracket_link(match):
            target = match.group(1)
            return f"[{_style_link_latex(target)}]({target})"

        processed_line = re.sub(
            empty_bracket_pattern, convert_empty_bracket_link, processed_line
        )

        # Convert URLs in backticks.
        def convert_backtick_url(match):
            url = match.group(1)
            return f"[{_style_link_latex(url)}]({url})"

        processed_line = re.sub(
            backtick_url_pattern, convert_backtick_url, processed_line
        )

        # Normalize existing formatted links to keep existing display text.
        def normalize_formatted_link(match):
            text = match.group(1)
            url = match.group(2)
            return f"[{_style_link_latex(text)}]({url})"

        processed_line = re.sub(
            formatted_link_pattern, normalize_formatted_link, processed_line
        )

        # Convert markdown links [Text](URL) to formatted links.
        def convert_markdown_link(match):
            text = match.group(1)
            url = match.group(2)
            return f"[{_style_link_latex(text)}]({url})"

        processed_line = re.sub(
            markdown_link_pattern, convert_markdown_link, processed_line
        )

        # Convert email links [email@domain.com](email@domain.com) to formatted links.
        def convert_email_link(match):
            email = match.group(2)
            return f"[{_style_link_latex(email)}]({email})"

        processed_line = re.sub(
            email_link_pattern, convert_email_link, processed_line
        )

        # Convert markdown links with an email target [Text](email@domain)
        # to formatted links, preserving the display text.
        def convert_email_target_link(match):
            text = match.group(1)
            email = match.group(2)
            return f"[{_style_link_latex(text)}]({email})"

        processed_line = re.sub(
            email_target_link_pattern,
            convert_email_target_link,
            processed_line,
        )
        # Convert plain URLs (but avoid converting URLs that are already part
        # of formatted links).
        # First, temporarily replace formatted links to avoid interfering with
        # them.
        temp_placeholders = []
        # Store existing correctly formatted links temporarily.
        correct_formatted_link_pattern = (
            r"\[" + _STYLED_LINK_TEXT_RE + r"\]\(([^)]+)\)"
        )

        def store_formatted_link(match):
            placeholder = f"__FORMATTED_LINK_{len(temp_placeholders)}__"
            temp_placeholders.append(match.group(0))
            return placeholder

        temp_line = re.sub(
            correct_formatted_link_pattern, store_formatted_link, processed_line
        )
        # Also mask any OTHER already-existing `[text](URL)`-shaped
        # construct that slipped through every conversion pass above
        # untouched, e.g. a link already styled with a color scheme that
        # predates `_STYLED_LINK_TEXT_RE` (like a legacy `\textcolor{blue}
        # {\underline{...}}`), whose display text contains characters
        # `markdown_link_pattern` doesn't allow (arbitrary backslash
        # sequences). Without this, the URL inside `(...)` would be
        # independently matched and re-linkified by the plain-URL pass
        # below, corrupting the link into malformed nested markdown (e.g.
        # `]([\textcolor[HTML]{...}](URL))`).
        any_existing_link_pattern = r"\[.*?\]\(https?://[^)]+\)"
        temp_line = re.sub(
            any_existing_link_pattern, store_formatted_link, temp_line
        )

        # Convert remaining plain URLs.
        def convert_plain_url(match):
            url = match.group(0)
            return f"[{_style_link_latex(url)}]({url})"

        temp_line = re.sub(url_pattern, convert_plain_url, temp_line)
        # Restore formatted links.
        for i, placeholder in enumerate(temp_placeholders):
            temp_line = temp_line.replace(f"__FORMATTED_LINK_{i}__", placeholder)
        # Restore image links.
        for i, image_link in enumerate(image_placeholders):
            temp_line = temp_line.replace(f"__IMAGE_LINK_{i}__", image_link)
        result.append(temp_line)
    if output_format == "typst":
        # The transformations above always build the LaTeX-style
        # `_style_link_latex()` snippet (it also doubles as the "already
        # formatted" marker used to protect links from being re-processed
        # above). Convert it to Typst raw code as a final pass.
        result = [_convert_textcolor_underline_to_typst(line) for line in result]
    hdbg.dassert_isinstance(result, list)
    return result


# TODO(gp): -> format_first_level_bullets_in_slide
def format_first_level_bullets(lines: List[str]) -> List[str]:
    """
    Add empty lines to separate first level bullets and remove all remaining
    empty lines.

    This is the formatting we use in the slides.

    :param lines: list of input markdown lines
    :return: formatted markdown lines
    """
    hdbg.dassert_isinstance(lines, list)
    # Remove empty lines.
    lines_clean = [line for line in lines if line.strip()]
    # Handle special case: if input was only empty lines, preserve structure.
    if not lines_clean and lines:
        return lines
    # Add empty lines only before first level bullets.
    result = []
    for i, line in enumerate(lines_clean):
        # Check if current line is a first level bullet (no indentation).
        if re.match(r"^- ", line):
            # Add empty line before first level bullet if not at start.
            if i > 0:
                result.append("")
        result.append(line)
    hdbg.dassert_isinstance(result, list)
    return result


# TODO(gp): Implement and add tests.
def format_column_blocks(lines: List[str]) -> List[str]:
    """
    # Make sure that there is a single empty line before and after the following
    # block:
    # <!-- prettier-ignore-start -->
    # 1)
    # ```
    # ::: columns
    # :::: {.column width=55%}
    # ```
    # 2)
    # ```
    # ::::
    # :::: {.column width=40%}
    # ```
    # 3)
    # ```
    # ::::
    # :::
    # ```

    #
    """
    return lines


def format_markdown_slide(lines: List[str], *, tmp_dir: str = ".") -> List[str]:
    """
    Format markdown text for a slide.

    :param lines: input lines to format
    :param tmp_dir: directory (e.g., a test's scratch space) to save the
        tmp file used internally by `prettier_on_str()`
    :return: formatted slide text
    """
    hdbg.dassert_isinstance(lines, list)
    if False:
        lines = bold_first_level_bullets(lines)
        txt = "\n".join(lines)
    # Format the markdown slides.
    # TODO(gp): Maybe the conversion should be done inside `prettier_on_str`
    # passing a marker to indicate that the text is a slide.
    lines = hmarslid.convert_slide_to_markdown(lines)
    # lines = format_column_blocks()
    #
    file_type = "md"
    txt = "\n".join(lines)
    txt = dshdlipr.prettier_on_str(txt, file_type, tmp_dir=tmp_dir)
    #
    lines = txt.split("\n")
    lines = hmarslid.convert_markdown_to_slide(lines)
    # Format the first level bullets.
    lines = format_first_level_bullets(lines)
    #
    lines = hmarhead.capitalize_header(lines)
    return lines


# #############################################################################
# Formatting with prettier, mdformat, flowmark
# #############################################################################


def is_prettier_available(backend: str) -> bool:
    """
    Check if prettier executable is available for the given backend.

    :param backend: prettier backend ("dockerized" or "global")
    :return: True if prettier is available, False otherwise
    """
    if backend == "dockerized":
        return True
    elif backend == "global":
        result = hsystem.system("which prettier", suppress_output=True, abort_on_error=False)
        return result == 0
    else:
        raise ValueError("Invalid backend='%s'" % backend)


def is_mdformat_available(backend: str) -> bool:
    """
    Check if mdformat executable is available for the given backend.

    :param backend: mdformat backend ("library", "uvx", or "global")
    :return: True if mdformat is available, False otherwise
    """
    if backend == "library":
        try:
            import mdformat  # noqa: F401

            return True
        except ImportError:
            return False
    elif backend == "uvx":
        result = hsystem.system("which uvx", suppress_output=True, abort_on_error=False)
        return result == 0
    elif backend == "global":
        result = hsystem.system("which mdformat", suppress_output=True, abort_on_error=False)
        return result == 0
    else:
        raise ValueError("Invalid backend='%s'" % backend)


def is_flowmark_available(backend: str) -> bool:
    """
    Check if flowmark executable is available for the given backend.

    :param backend: flowmark backend ("library", "uvx-rs", "uvx", "global", or "global-rs")
    :return: True if flowmark is available, False otherwise
    """
    if backend == "library":
        try:
            import flowmark  # noqa: F401

            return True
        except ImportError:
            return False
    elif backend in ("uvx-rs", "uvx"):
        result = hsystem.system("which uvx", suppress_output=True, abort_on_error=False)
        return result == 0
    elif backend in ("global", "global-rs"):
        result = hsystem.system("which flowmark", suppress_output=True, abort_on_error=False)
        return result == 0
    else:
        raise ValueError("Invalid backend='%s'" % backend)


# #############################################################################


def _format_with_prettier(
    txt: str,
    backend: str,
    width: int,
) -> str:
    """
    Format markdown text using Prettier.

    :param txt: input text to format
    :param backend: execution backend ("dockerized" or "global")
    :param width: line width for formatting
    :return: formatted text
    """
    hdbg.dassert_in(backend, ["dockerized", "global"])
    if backend == "dockerized":
        _LOG.debug("Using dockerized prettier for formatting")
        formatted_txt = dshdlipr.prettier_on_str(txt, "md", width=width)
    elif backend == "global":
        # backend == "global": use global prettier executable.
        hdbg.dassert(
            is_prettier_available("global"),
            "prettier executable not found in PATH.",
        )
        _LOG.debug("Using global prettier executable for formatting")
        tmp_file = "tmp.format_md.prettier.md"
        hio.to_file(tmp_file, txt)
        cmd_parts = [
            "prettier",
            f"--print-width={width}",
            "--parser=markdown",
            "--prose-wrap=always",
            "--write",
            tmp_file,
        ]
        cmd = " ".join(cmd_parts)
        hsystem.system(cmd)
        formatted_txt = hio.from_file(tmp_file)
    else:
        raise ValueError("Invalid backend='%s'" % backend)
    return formatted_txt


def _format_with_mdformat(
    txt: str,
    backend: str,
    width: int,
) -> str:
    """
    Format markdown text using mdformat.

    :param txt: input text to format
    :param backend: execution backend ("library", "uvx", or "global")
    :param width: line width for formatting
    :return: formatted text
    """
    hdbg.dassert_in(backend, ["library", "uvx", "global"])
    if backend == "library":
        # Import and use mdformat library directly.
        _LOG.debug("Using mdformat library for formatting")
        import mdformat

        formatted_txt = mdformat.text(txt, options={"wrap": width})
    else:
        # Save to file and call via executable.
        tmp_file = "tmp.format_md.mdformat.md"
        hio.to_file(tmp_file, txt)
        cmd_parts = [
            "mdformat",
            f"--wrap={width}",
            tmp_file,
        ]
        if backend == "uvx":
            _LOG.debug("Using mdformat via uvx for formatting")
            cmd_parts.insert(0, "uvx")
        elif backend == "global":
            hdbg.dassert(
                is_mdformat_available(backend),
                "mdformat executable not found in PATH.",
            )
            _LOG.debug("Using global mdformat executable for formatting")
        else:
            raise ValueError("Invalid backend='%s'" % backend)
        cmd = " ".join(cmd_parts)
        hsystem.system(cmd)
        formatted_txt = hio.from_file(tmp_file)
    return formatted_txt


def _format_with_flowmark(
    txt: str,
    backend: str,
    width: int,
) -> str:
    """
    Format markdown text using flowmark.

    :param txt: input text to format
    :param backend: execution backend ("library", "uvx-rs", "uvx", "global", "global-rs")
    :param width: line width for formatting
    :return: formatted text
    """
    hdbg.dassert_in(backend, ["library", "uvx-rs", "uvx", "global", "global-rs"])
    if backend == "library":
        # Import and use flowmark library directly
        _LOG.debug("Using flowmark library for formatting")
        import flowmark

        formatted_txt = flowmark.reformat_text(txt, width=width)
    else:
        # Save to file and call via executable
        tmp_file = "tmp.format_md.flowmark.md"
        hio.to_file(tmp_file, txt)
        opts = ["--auto", f"-w {width}", tmp_file]
        if backend == "uvx-rs":
            _LOG.debug("Using flowmark via uvx-rs for formatting")
            cmd_parts = ["uvx", "--from flowmark", "flowmark"]
        elif backend == "uvx":
            _LOG.debug("Using flowmark via uvx for formatting")
            cmd_parts = [
                "uvx",
                "flowmark",
            ]
        elif backend == "global-rs":
            # Rust-based flowmark from global path.
            hdbg.dassert(
                is_flowmark_available(backend),
                "flowmark executable not found in PATH.",
            )
            _LOG.debug("Using global flowmark (Rust) executable for formatting")
            cmd_parts = [
                "flowmark",
            ]
        elif backend == "global":
            hdbg.dassert(
                is_flowmark_available(backend),
                "flowmark executable not found in PATH.",
            )
            _LOG.debug("Using global flowmark executable for formatting")
            cmd_parts = [
                "flowmark",
            ]
        else:
            raise ValueError("Invalid backend='%s'" % backend)
        cmd_parts.extend(opts)
        cmd = " ".join(cmd_parts)
        hsystem.system(cmd)
        formatted_txt = hio.from_file(tmp_file)
    return formatted_txt


def format_md(
    txt: str,
    tool: str,
    backend: str,
    *,
    width: int = 80,
) -> str:
    """
    Format markdown text using specified tool and backend.

    Supports multiple markdown formatters with different execution backends:
    - prettier: "dockerized" (Docker container), "global" (system executable)
    - mdformat: "library" (Python package), "uvx" (uv executable), "global" (system)
    - flowmark: "library" (Python), "uvx-rs" (Rust via uv), "uvx" (uv), "global" (system)

    :param txt: markdown text to format
    :param tool: formatter tool ("prettier", "mdformat", or "flowmark")
    :param backend: execution backend (depends on tool)
    :param width: line width for text wrapping (default: 80)
    :return: formatted markdown text
    """
    _LOG.debug(hprint.to_str("tool backend width"))
    hdbg.dassert_isinstance(txt, str)
    hdbg.dassert_in(
        tool,
        ["prettier", "mdformat", "flowmark"],
        "Invalid tool specified",
    )
    hdbg.dassert_lte(1, width, "Width must be at least 1")
    timer_ = htimer.Timer()
    _LOG.debug(
        "Formatting with tool='%s' backend='%s' width=%s", tool, backend, width
    )
    if tool == "prettier":
        formatted_txt = _format_with_prettier(txt, backend, width)
    elif tool == "mdformat":
        formatted_txt = _format_with_mdformat(txt, backend, width)
    elif tool == "flowmark":
        formatted_txt = _format_with_flowmark(txt, backend, width)
    else:
        raise ValueError(f"Unknown tool: {tool}")
    timer_.stop()
    _LOG.info(
        "format_md completed: tool=%s, backend=%s, time=%s",
        tool,
        backend,
        str(timer_),
    )
    return formatted_txt
