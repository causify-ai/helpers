"""
Import as:

import helpers.hmarkdown_formatting as hmarkdo
"""

import logging
import re
from typing import List

import helpers.hdbg as hdbg
import helpers.hdockerized_executables as hdocexec
import helpers.hmarkdown_slides as hmarkdo
import helpers.hmarkdown_headers as hmarkdohe

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
    txt = hdocexec.prettier_on_str(txt, file_type)
    return txt


def format_markdown(txt: str) -> str:
    """
    Format markdown text.

    :param txt: input text to format
    :return: formatted text
    """
    file_type = "md"
    txt = hdocexec.prettier_on_str(txt, file_type)
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
    Convert markdown slides with figures to use fenced div syntax with column layout.

    If the input already uses column format or contains no figures, returns unchanged.

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


def format_links(lines: List[str]) -> List[str]:
    r"""
    Convert markdown links to formatted links with LaTeX styling.

    Converts plain URLs and existing formatted links to the format:
    [\textcolor{blue}{\underline{URL}}](URL)

    Also validates that links are reachable and fixes mismatched link text.

    :param lines: list of input markdown lines
    :return: formatted markdown lines with styled links
    """
    hdbg.dassert_isinstance(lines, list)
    result = []
    # URL regex pattern - matches http:// and https:// URLs.
    url_pattern = r"https?://[^\s)}\]`]+"
    # Pattern for URLs in backticks.
    backtick_url_pattern = r"`(https?://[^\s`]+)`"
    # Pattern for existing formatted links.
    formatted_link_pattern = r"\[\\textcolor\{blue\}\{\\underline\{([^}]+)\}\}\]\(([^)]+)\)"
    for line in lines:
        # Process the line for all URL patterns.
        processed_line = line
        # 1. Handle existing formatted links - fix mismatched ones.
        def fix_formatted_link(match):
            link_text = match.group(1)
            link_url = match.group(2)
            # If they don't match, use the URL as the text.
            if link_text != link_url:
                return fr"[\textcolor{{blue}}{{\underline{{{link_url}}}}}]({link_url})"
            else:
                # Already correct, keep as is.
                return match.group(0)
        processed_line = re.sub(formatted_link_pattern, fix_formatted_link, processed_line)
        # 2. Convert URLs in backticks.
        def convert_backtick_url(match):
            url = match.group(1)
            return fr"[\textcolor{{blue}}{{\underline{{{url}}}}}]({url})"
        processed_line = re.sub(backtick_url_pattern, convert_backtick_url, processed_line)
        # 3. Convert plain URLs (but avoid converting URLs that are already part of formatted links).
        # First, temporarily replace formatted links to avoid interfering with them.
        temp_placeholders = []
        def store_formatted_link(match):
            placeholder = f"__FORMATTED_LINK_{len(temp_placeholders)}__"
            temp_placeholders.append(match.group(0))
            return placeholder
        # Store existing formatted links temporarily.
        temp_line = re.sub(formatted_link_pattern, store_formatted_link, processed_line)
        # Convert remaining plain URLs.
        def convert_plain_url(match):
            url = match.group(0)
            return fr"[\textcolor{{blue}}{{\underline{{{url}}}}}]({url})"
        temp_line = re.sub(url_pattern, convert_plain_url, temp_line)
        # Restore formatted links.
        for i, placeholder in enumerate(temp_placeholders):
            temp_line = temp_line.replace(f"__FORMATTED_LINK_{i}__", placeholder)
        result.append(temp_line)
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


def format_markdown_slide(lines: List[str]) -> List[str]:
    """
    Format markdown text for a slide.

    :param lines: input lines to format
    :return: formatted slide text
    """
    hdbg.dassert_isinstance(lines, list)
    if False:
        lines = bold_first_level_bullets(lines)
        txt = "\n".join(lines)
    # Format the markdown slides.
    # TODO(gp): Maybe the conversion should be done inside `prettier_on_str`
    # passing a marker to indicate that the text is a slide.
    lines = hmarkdo.convert_slide_to_markdown(lines)
    # lines = format_column_blocks()
    #
    file_type = "md"
    txt = "\n".join(lines)
    txt = hdocexec.prettier_on_str(txt, file_type)
    #
    lines = txt.split("\n")
    lines = hmarkdo.markdown_to_slide(lines)
    # Format the first level bullets.
    lines = format_first_level_bullets(lines)
    #
    lines = hmarkdohe.capitalize_header(lines)
    return lines


def format_latex(txt: str) -> str:
    """
    Format LaTeX text using `prettier`.

    :param txt: input LaTeX text to format
    :return: formatted LaTeX text
    """
    file_type = "tex"
    txt = hdocexec.prettier_on_str(txt, file_type)
    return txt
