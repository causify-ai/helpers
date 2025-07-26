"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging
import re
from typing import List

import helpers.hdbg as hdbg
import helpers.hdockerized_executables as hdocexec

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
    # Join lines back to text, apply original regex logic, then split again
    txt = "\n".join(lines)
    # Replace the ```python and ``` delimiters with empty strings.
    txt_out = txt.replace("```python", "").replace("```", "")
    txt_out = txt_out.strip()
    # Remove the numbers at the beginning of the line, if needed
    # E.g., `3: """` -> `"""`.
    txt_out = re.sub(r"(^\d+: )", "", txt_out, flags=re.MULTILINE)
    # Split back into lines
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


def bold_first_level_bullets(lines: List[str], *, max_length: int = 30) -> List[str]:
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


def format_first_level_bullets(lines: List[str]) -> List[str]:
    """
    Add empty lines only before first level bullets and remove all empty lines
    from markdown text.

    :param lines: list of input markdown lines
    :return: formatted markdown lines
    """
    hdbg.dassert_isinstance(lines, list)
    # Remove empty lines.
    lines_clean = [line for line in lines if line.strip()]
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


def format_markdown_slide(txt: str) -> str:
    """
    Format markdown text for a slide.

    :param txt: input text to format
    :return: formatted slide text
    """
    # Split the text into title and body.
    lines = txt.split("\n")
    lines = bold_first_level_bullets(lines)
    txt = "\n".join(lines)
    file_type = "md"
    txt = hdocexec.prettier_on_str(txt, file_type)
    lines = txt.split("\n")
    lines = format_first_level_bullets(lines)
    txt = "\n".join(lines)
    # txt = capitalize_slide_titles(txt)
    return txt


def format_latex(txt: str) -> str:
    """
    Format LaTeX text using `prettier`.

    :param txt: input LaTeX text to format
    :return: formatted LaTeX text
    """
    file_type = "tex"
    txt = hdocexec.prettier_on_str(txt, file_type)
    return txt
