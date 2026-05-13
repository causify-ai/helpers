"""
Import as:

import dev_scripts_helpers.documentation.documentation_utils as dshddout
"""

import logging
import re
from typing import List

_LOG = logging.getLogger(__name__)


# #############################################################################
# Remove functions for cleaning markdown
# #############################################################################


def remove_span_with_multiple_attributes(content: str) -> str:
    """
    Remove span tags that have multiple attributes (completely remove the tag).

    Matches span tags with 2 or more attribute assignments (indicated by `=`).
    This pattern identifies spans like:
    `<span id="foo" class="bar">content</span>`

    :param content: the markdown content
    :return: content with multi-attribute span tags removed
    """
    # Pattern matches span tags with at least 2 attributes.
    pattern = r"<span\s+[^>]*=[^>]*\s+[^>]*=[^>]*>.*?</span>"
    content = re.sub(pattern, "", content, flags=re.DOTALL)
    return content


def remove_label_span_tags(content: str) -> str:
    """
    Remove only class="label" span tags but keep their content.

    Matches span tags with only `class="label"` attribute and replaces them
    with their content (e.g., `<span class="label">Part I. </span>` becomes
    `Part I. `).

    :param content: the markdown content
    :return: content with class="label" span tags removed but content kept
    """
    # Pattern matches span tags with only class="label" attribute.
    # Handles both single and double quotes.
    pattern = r'<span\s+class=["\']label["\']>([^<]*)</span>'
    content = re.sub(pattern, r"\1", content)
    return content


def remove_keep_together_span_tags(content: str) -> str:
    """
    Remove only class="keep-together" span tags but keep their content.

    Matches span tags with only `class="keep-together"` attribute and
    replaces them with their content (e.g.,
    `<span class="keep-together">causation</span>` becomes `causation`).

    :param content: the markdown content
    :return: content with class="keep-together" span tags removed but content
        kept
    """
    # Pattern matches span tags with only class="keep-together" attribute.
    # Handles both single and double quotes.
    pattern = r'<span\s+class=["\']keep-together["\']>([^<]*)</span>'
    content = re.sub(pattern, r"\1", content)
    return content


def remove_html_link_span_tags(content: str) -> str:
    """
    Remove span tags with id attributes containing .html pattern (chapter links).

    These are anchor/link spans like `<span id="ch12.html"></span>` that are
    used for cross-references and should be completely removed.

    :param content: the markdown content
    :return: content with HTML link span tags removed
    """
    # Pattern matches span tags with id attribute containing .html pattern.
    # Handles both single and double quotes. The id value can contain any
    # characters except the closing quote (e.g., ch12.html or
    # part03.html_part-3).
    # Matches: <span id="...html..."></span> or <span id='...html...'></span>
    pattern = r'<span\s+id=(?:"[^"]*\.html[^"]*"|\'[^\']*\.html[^\']*\')[^>]*>\s*</span>'
    content = re.sub(pattern, "", content, flags=re.DOTALL)
    return content


def remove_pre_span_tags(content: str) -> str:
    """
    Remove only class="pre" span tags but keep their content.

    Matches span tags with only `class="pre"` attribute and replaces them
    with their content (e.g., `<span class="pre">`is_on_sale`</span>` becomes
    `` `is_on_sale` ``).

    :param content: the markdown content
    :return: content with class="pre" span tags removed but content kept
    """
    # Pattern matches span tags with only class="pre" attribute.
    # Handles both single and double quotes.
    pattern = r'<span\s+class=["\']pre["\']>([^<]*)</span>'
    content = re.sub(pattern, r"\1", content)
    return content


def remove_bold_span_tags(content: str) -> str:
    """
    Convert class="b" span tags to markdown bold formatting.

    Matches span tags with only `class="b"` attribute and replaces them
    with markdown bold syntax (e.g., `<span class="b">text</span>` becomes
    `**text**`).

    :param content: the markdown content
    :return: content with class="b" span tags converted to markdown bold
    """
    # Pattern matches span tags with only class="b" attribute.
    # Handles both single and double quotes.
    pattern = r'<span\s+class=["\']b["\']>([^<]*)</span>'
    content = re.sub(pattern, r"**\1**", content)
    return content


def remove_italic_span_tags(content: str) -> str:
    """
    Convert class="i" span tags to markdown italic formatting.

    Matches span tags with only `class="i"` attribute and replaces them
    with markdown italic syntax (e.g., `<span class="i">text</span>` becomes
    `_text_`).

    :param content: the markdown content
    :return: content with class="i" span tags converted to markdown italic
    """
    # Pattern matches span tags with only class="i" attribute.
    # Handles both single and double quotes.
    pattern = r'<span\s+class=["\']i["\']>([^<]*)</span>'
    content = re.sub(pattern, r"_\1_", content)
    return content


def convert_section_div_headers(content: str) -> str:
    """
    Convert level-1 headers inside `<div class="sectionN">` to level N.

    Detects an opening `<div class="sectionN">` tag (with any extra
    attributes) followed by a level-1 markdown header (`# Title`) and rewrites
    the header to have N `#` characters (e.g., `<div class="section2">` plus
    `# Title` becomes `<div class="section2">` plus `## Title`). The div tag
    is left untouched so a later pass (e.g., `remove_div_tags()`) can strip
    it.

    :param content: the markdown content
    :return: content with section headers promoted to the right level
    """
    # Pattern parts:
    # - `<div\b[^>]*\bclass=["\']section(\d+)["\'][^>]*>`: section div opening
    #   tag, capturing the section level digits.
    # - `(\s*\n)`: any whitespace and at least one newline, so the `#` lands at
    #   the start of a following line (typically after a blank line).
    # - `#(\s+)`: a level-1 header marker `#` followed by at least one space.
    pattern = r'(<div\b[^>]*\bclass=["\']section(\d+)["\'][^>]*>)(\s*\n)#(\s+)'

    def _replace(match) -> str:
        # Reconstruct the match with `#` repeated `section_level` times to
        # promote the header to the right level.
        div_tag = match.group(1)
        section_level = int(match.group(2))
        whitespace = match.group(3)
        space_after = match.group(4)
        header_prefix = "#" * section_level
        return f"{div_tag}{whitespace}{header_prefix}{space_after}"

    content = re.sub(pattern, _replace, content)
    return content


def remove_div_tags(content: str) -> str:
    """
    Remove all div tags but keep their content.

    Strips opening div tags with any attributes (e.g., `<div class="foo">`,
    `<div id="bar">`, `<div class="x" style="y:z;">`) and closing `</div>`
    tags, preserving the content between them. Each tag is removed
    independently, which correctly handles nested divs without needing a
    balanced matcher.

    :param content: the markdown content
    :return: content with all div tags stripped but content kept
    """
    # Match any opening `<div ...>` tag with optional attributes.
    pattern_open = r"<div\b[^>]*>"
    content = re.sub(pattern_open, "", content)
    # Match closing `</div>` tags.
    pattern_close = r"</div>"
    content = re.sub(pattern_close, "", content)
    return content


def remove_anchor_tags(content: str) -> str:
    """
    Remove anchor tags but keep their content.

    Matches anchor tags like `<a href="#part03.html_part-3" data-type="xref">
    Part III</a>` and replaces them with just the content (`Part III`).
    Handles nested HTML tags like `<a href="#notes.html_ch2en1"><sup>1</sup></a>`.

    :param content: the markdown content
    :return: content with anchor tags removed but content kept
    """
    # Pattern matches anchor tags with any attributes and captures the content.
    # Uses [\s\S]*? to match any character including nested HTML tags.
    pattern = r"<a\s+[^>]*>([\s\S]*?)</a>"
    content = re.sub(pattern, r"\1", content)
    return content


def remove_backticks_in_math(content: str) -> str:
    """
    Remove backticks from LaTeX math expressions.

    Matches LaTeX math delimited by `$` with backticks inside
    (e.g., `$`Y(1)`$`) and removes the backticks (e.g., `$Y(1)$`).

    :param content: the markdown content
    :return: content with backticks removed from LaTeX math
    """
    # Pattern matches $`...`$ and removes the backticks.
    pattern = r"\$`([^`]*)`\$"
    content = re.sub(pattern, r"$\1$", content)
    return content


def merge_consecutive_same_level_headers(content: str) -> str:
    """
    Merge runs of same-level markdown headers into a single header line.

    Consecutive markdown headers at the same level (e.g., three lines each
    starting with `# `), separated only by blank lines or directly
    adjacent, are combined into one header line whose text is the
    space-joined concatenation of the individual header texts. For
    example:

        # 1

        # Introduction

        # _Machine Intelligence_

    becomes

        # 1 Introduction _Machine Intelligence_

    Headers at different levels, or sequences interrupted by any
    non-blank, non-header content, are left untouched. A solitary header
    (no neighbor at the same level) is emitted exactly as written.

    :param content: the markdown content
    :return: content with runs of same-level headers merged
    """
    # A markdown header is 1+ `#` characters, then whitespace, then
    # non-empty text. The capture groups extract the leading `#`s and the
    # stripped header text (no leading/trailing whitespace).
    header_re = re.compile(r"^(#+)\s+(.*\S)\s*$")
    lines = content.split("\n")
    result: List[str] = []
    i = 0
    n = len(lines)
    while i < n:
        match = header_re.match(lines[i])
        # Non-header line: emit as-is and advance.
        if not match:
            result.append(lines[i])
            i += 1
            continue
        # Found a header. Scan forward for same-level neighbors, skipping
        # blank lines. Stop at any non-blank, non-matching content.
        hashes = match.group(1)
        texts = [match.group(2)]
        last_header_pos = i
        j = i + 1
        while j < n:
            if lines[j].strip() == "":
                j += 1
                continue
            next_match = header_re.match(lines[j])
            if next_match and next_match.group(1) == hashes:
                texts.append(next_match.group(2))
                last_header_pos = j
                j += 1
                continue
            break
        # Single header: preserve the original line untouched so we don't
        # accidentally normalize whitespace on lines that aren't merged.
        if len(texts) == 1:
            result.append(lines[i])
            i += 1
        # Run of same-level headers: emit one merged header. Subsequent
        # blank lines after the last merged header (at indices >
        # `last_header_pos`) will be processed normally on the next pass.
        else:
            merged_line = f"{hashes} {' '.join(texts)}"
            result.append(merged_line)
            i = last_header_pos + 1
    return "\n".join(result)


def collapse_blank_lines(content: str) -> str:
    """
    Collapse two or more consecutive blank lines into a single blank line.

    A blank line is one that is empty or contains only whitespace. Runs of
    such lines are reduced to a single empty line. Leading/trailing
    whitespace on non-blank lines is preserved.

    :param content: the markdown content
    :return: content with runs of blank lines collapsed to one
    """
    # Match 2+ consecutive blank lines (each possibly containing only
    # whitespace) and replace with a single newline-separated blank line.
    pattern = r"(?:[ \t]*\n){2,}"
    content = re.sub(pattern, "\n\n", content)
    return content


# #############################################################################
# Combined cleanup function
# #############################################################################


def remove_junk(content: str) -> str:
    """
    Remove all HTML markup junk from markdown content.

    Applies all removal functions in sequence to clean up HTML-generated
    markdown, removing various span tags, anchor tags, and fixing math
    expressions.

    :param content: the markdown content
    :return: cleaned markdown content
    """
    # Remove span tags with multiple attributes (completely remove them).
    _LOG.info("Removing span tags with multiple attributes")
    content = remove_span_with_multiple_attributes(content)
    # Remove only class="label" span tags but keep their content.
    _LOG.info("Removing class='label' span tags (keeping content)")
    content = remove_label_span_tags(content)
    # Remove only class="keep-together" span tags but keep their content.
    _LOG.info("Removing class='keep-together' span tags (keeping content)")
    content = remove_keep_together_span_tags(content)
    # Remove HTML link span tags (e.g., <span id="ch12.html"></span>).
    _LOG.info("Removing HTML link span tags")
    content = remove_html_link_span_tags(content)
    # Remove only class="pre" span tags but keep their content.
    _LOG.info("Removing class='pre' span tags (keeping content)")
    content = remove_pre_span_tags(content)
    # Convert class="b" span tags to markdown bold.
    _LOG.info("Converting class='b' span tags to markdown bold")
    content = remove_bold_span_tags(content)
    # Convert class="i" span tags to markdown italic.
    _LOG.info("Converting class='i' span tags to markdown italic")
    content = remove_italic_span_tags(content)
    # Convert headers inside section divs to the appropriate header level.
    # Must run before `remove_div_tags()` so the section level can be read
    # from the div tag.
    _LOG.info("Converting section div headers to the right level")
    content = convert_section_div_headers(content)
    # Remove all div tags but keep their content.
    _LOG.info("Removing div tags (keeping content)")
    content = remove_div_tags(content)
    # Remove anchor tags but keep their content.
    _LOG.info("Removing anchor tags (keeping content)")
    content = remove_anchor_tags(content)
    # Remove backticks from LaTeX math expressions.
    _LOG.info("Removing backticks from LaTeX math expressions")
    content = remove_backticks_in_math(content)
    # Collapse runs of blank lines into a single blank line.
    _LOG.info("Collapsing consecutive blank lines")
    content = collapse_blank_lines(content)
    # Merge consecutive same-level headers (e.g., `# 1` / `# Introduction`
    # / `# _Machine Intelligence_` becomes `# 1 Introduction _Machine
    # Intelligence_`). Run after `collapse_blank_lines()` so multiple
    # blank lines between headers are normalized to single blanks before
    # merging.
    _LOG.info("Merging consecutive same-level headers")
    content = merge_consecutive_same_level_headers(content)
    return content


# #############################################################################
# Filename standardization
# #############################################################################


def standardize_filename(filename: str) -> str:
    """
    Convert a file name (book or paper) into a standard format.

    Transforms filenames like:
    `Ajay Agrawal, Joshua Gans, Avi Goldfarb - Prediction Machines_ The
    Simple Economics of Artificial Intelligence (2018, Harvard Business
    Review Press) - libgen.li.epub`

    Into standardized format:
    `2018.Agrawal_et_al.Prediction_Machines_The_Simple_Economics_of_Artificial_Intelligence.epub`

    Format: `<Year>.<LastName_of_FirstAuthor>[_et_al].<Title>.<ext>`

    Rules:
    - Year is extracted from pattern `(YYYY,` or from the end if available
    - Authors are extracted as `Author1, Author2, ... - Title` pattern
    - If multiple authors, append `_et_al`
    - Title is cleaned by replacing spaces, dots, slashes, backslashes with
      underscores and removing other special characters
    - The file extension is preserved

    :param filename: The filename to standardize
    :return: Standardized filename
    """
    # Extract file extension.
    if "." in filename:
        base_name = ".".join(filename.split(".")[:-1])
        ext = "." + filename.split(".")[-1]
    else:
        base_name = filename
        ext = ""
    _LOG.debug("Extracted extension: %s", ext)
    # Extract year from pattern (YYYY, or similar).
    year_match = re.search(r"\(\s*(\d{4})\s*,", base_name)
    if year_match:
        year = year_match.group(1)
        _LOG.debug("Extracted year: %s", year)
    else:
        year = ""
    # Extract authors and title.
    # Pattern: Authors - Title (Year, Publisher) - Source
    author_title_match = re.match(
        r"^(.+?)\s*-\s*(.+?)(?:\s*\(\d{4}|$)", base_name
    )
    if author_title_match:
        authors_str = author_title_match.group(1).strip()
        title_str = author_title_match.group(2).strip()
        _LOG.debug("Extracted authors: %s", authors_str)
        _LOG.debug("Extracted title: %s", title_str)
    else:
        authors_str = ""
        title_str = base_name
    # Process authors.
    if authors_str:
        author_list = [a.strip() for a in authors_str.split(",")]
        first_author = author_list[0]
        # Extract last name (last word).
        first_author_parts = first_author.split()
        last_name = first_author_parts[-1] if first_author_parts else ""
        # Check if multiple authors.
        if len(author_list) > 1:
            author_part = f"{last_name}_et_al"
        else:
            author_part = last_name
        _LOG.debug("Processed author part: %s", author_part)
    else:
        author_part = ""
    # Clean title: replace unfriendly characters with underscore.
    clean_title = title_str
    # Replace spaces, dots, slashes, backslashes with underscore.
    clean_title = re.sub(r"[\s._/\\]+", "_", clean_title)
    # Remove other special characters (keep only alphanumeric and underscore).
    clean_title = re.sub(r"[^a-zA-Z0-9_]", "", clean_title)
    # Remove multiple consecutive underscores.
    clean_title = re.sub(r"_+", "_", clean_title)
    # Remove leading/trailing underscores.
    clean_title = clean_title.strip("_")
    _LOG.debug("Cleaned title: %s", clean_title)
    # Build standardized filename.
    parts: List[str] = []
    if year:
        parts.append(year)
    if author_part:
        parts.append(author_part)
    if clean_title:
        parts.append(clean_title)
    standardized = ".".join(parts) + ext
    _LOG.info("Standardized filename: %s", standardized)
    return standardized
