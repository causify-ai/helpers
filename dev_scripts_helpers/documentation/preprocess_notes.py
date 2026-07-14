#!/usr/bin/env python

"""
Convert a "notes" text file into markdown suitable for `notes_to_pdf.py`.

The full list of transformations is:
- Handle banners around chapters
- Handle comments
- Prepend some directive for pandoc
- Remove comments
- Expand abbreviations
- Process questions "* ..."
- Remove empty lines in the questions and answers
- Remove all the lines with only spaces
- Add TOC

Import as:

import dev_scripts_helpers.documentation.preprocess_notes as dsdoprno
"""

import argparse
import logging
import os
import re
from typing import Dict, List, Match, Optional, Tuple, cast

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hmarkdown_toc as hmartoc
import helpers.hparser as hparser
import helpers.hselect_action as hselacti
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################


_NUM_SPACES = 2

_TRACE = False


_DEFAULT_ACTIONS: List[str] = []
_VALID_ACTIONS = [
    "process_links",
    "colorize_bullets",
    "validate_slide_names",
    "add_duplicate_counters",
    "validate_unique_slide_names",
]

# #############################################################################
# Helper functions
# #############################################################################


def _colorize_backticks(
    in_line: str, output_format: str, *, color: str = "blue"
) -> str:
    r"""
    Convert backtick-wrapped strings to colored format.

    For LaTeX output, converts backticks to `\textcolor{color}{\texttt{content}}`
    E.g., `store` into `\textcolor{blue}{\texttt{store}}`
    E.g., `weeks_to_xmas` into `\textcolor{blue}{\texttt{weeks\_to\_xmas}}`

    For Typst output, converts backticks to `#text(fill: color)[`content`]`
    E.g., `store` into `#text(fill: blue)[`store`]`
    E.g., `weeks_to_xmas` into `#text(fill: blue)[`weeks_to_xmas`]`

    :param in_line: input line to process
    :param color: color name
    :param output_format: "latex" or "typst"
    :return: transformed line with backticks replaced
    """
    hdbg.dassert_in(output_format, ("latex", "typst"))
    line = in_line
    # Pattern to match single backticks (not triple backticks).
    # This matches backtick-wrapped text that doesn't contain triple backticks.
    pattern = r"(?<!`)`(?!`)([^`]+?)(?<!`)`(?!`)"

    def replace_func(m: Match) -> str:
        """
        Replace function that converts backticks to format-specific syntax.
        """
        matched_text = m.group(1)
        if output_format == "latex":
            # Escape underscores for LaTeX.
            escaped_text = matched_text.replace("_", r"\_")
            txt = rf"\textcolor{{{color}}}{{\texttt{{{escaped_text}}}}}"
        else:  # typst
            # Typst doesn't need underscore escaping in backticks.
            # Use #text with backticks for monospace colored text.
            txt = f"#text(fill: {color})[`{matched_text}`]"
            txt = "``" + txt + "``{=typst}"
        return txt

    line = re.sub(pattern, replace_func, line)
    if line != in_line:
        _LOG.debug("    -> line=%s", line)
    return line


def _process_abbreviations(in_line: str) -> str:
    r"""
    Transform some abbreviations into LaTeX.

    E.g., - `->` into `$\rightarrow$`

    :param in_line: input line to process
    :return: transformed line with abbreviations replaced
    """
    line = in_line
    for x, y in [
        (r"=>", r"\implies"),
        # TODO(gp): This collides with the arrow in graphviz commands. We
        # should skip this transformation if we are in a graphviz block.
        # (r"->", r"\rightarrow"),
        # (r"-^", r"\uparrow"),
        # (r"-v", r"\downarrow"),
    ]:
        line = re.sub(rf"(\s){re.escape(x)}(\s)", rf"\1${re.escape(y)}$\2", line)
    if line != in_line:
        _LOG.debug("    -> line=%s", line)
    return line


def _process_enumerated_list(in_line: str) -> str:
    """
    Transform enumerated list with parenthesis to `.`.

    E.g., "1) foo bar" is transformed into "1. foo bar".

    :param in_line: input line to process
    :return: transformed line with enumerated lists updated
    """
    line = re.sub(r"^(\s*)(\d+)\)\s", r"\1\2. ", in_line)
    return line


def _process_question_to_markdown(line: str) -> Tuple[bool, str]:
    """
    Transform `* foo bar` into `- **foo bar**`.

    :param line: input line to process
    :return: tuple of (should_continue, transformed_line)
    """
    # Bold.
    meta = "**"
    # Bold + italic: meta = "_**"
    # Underline (not working): meta = "__"
    # Italic: meta = "_"
    do_continue = False
    regex = r"^(\*|\*\*|\*:)(\s+)(\S.*)\s*$"
    m = re.search(regex, line)
    if m:
        # TODO(gp): Not sure why we need to use the same number of spaces and
        # not just one.
        spaces = m.group(2)
        tag = m.group(3)
        line = f"-{spaces}{meta}{tag}{meta}"
        do_continue = True
    return do_continue, line


def _process_question_to_slides(
    line: str, *, level: int = 4
) -> Tuple[bool, str]:
    """
    Transform `* foo bar` into `#### foo bar`.

    :param line: input line to process
    :param level: header level to use (default: 4)
    :return: tuple of (should_continue, transformed_line)
    """
    hdbg.dassert_lte(1, level)
    prefix = "#" * level
    do_continue = False
    regex = r"^(\*|\*\*|\*:)\s+(\S.*)\s*$"
    m = re.search(regex, line)
    if m:
        tag = m.group(2)
        line = f"{prefix} {tag}"
        do_continue = True
    return do_continue, line


def _extract_section(lines: List[str], title: str) -> Optional[List[str]]:
    r"""
    Extract the body content under a level-1 header with the given title.

    Finds the header `# <title>` and returns the lines immediately following it
    up to (but not including) the next level-1 header. The header line itself is
    excluded from the result.

    :param lines: list of lines to search
    :param title: the header title to find (exact match)
    :return: list of body lines, or None if header not found
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_isinstance(title, str)
    # Find the line with `# <title>` (level-1 header).
    header_line_idx = None
    header_pattern = rf"^#\s+{re.escape(title)}\s*$"
    for i, line in enumerate(lines):
        if re.match(header_pattern, line):
            header_line_idx = i
            break
    if header_line_idx is None:
        return None
    # Find the next level-1 header (or end of file).
    end_idx = len(lines)
    for i in range(header_line_idx + 1, len(lines)):
        is_header, level, _ = hmarkdo.is_header(lines[i])
        if is_header and level == 1:
            end_idx = i
            break
    # Return the body lines (excluding the header line itself).
    result = lines[header_line_idx + 1 : end_idx]
    return result


# #############################################################################
# Process title slide.
# #############################################################################


def extract_slide_metadata(
    lines: List[str],
) -> Tuple[Dict[str, str], List[str]]:
    r"""
    Extract metadata directives from the top of the file.

    Scans for consecutive lines matching `^// (\\w+)=(.+)$` at the start of the
    file. Stops at the first non-matching line. Returns a tuple of the metadata
    dict and the remaining lines (without the metadata directives).

    :param lines: list of input lines
    :return: (metadata_dict, remaining_lines)
    """
    metadata: Dict[str, str] = {}
    i = 0
    pattern = re.compile(r"^//\s*(\w+)=(.+)$")
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            metadata[m.group(1).strip()] = m.group(2).strip()
        else:
            break
    else:
        # All lines were metadata
        i += 1
    return metadata, lines[i:]


# TODO(ai_gp2): Move this to the umd_repo.
def _generate_title_slide_latex(metadata: Dict[str, str]) -> List[str]:
    r"""
    Generate LaTeX title slide from metadata.

    Creates a pandoc Div-based title slide using `\vspace`, `\begingroup`,
    and `\blue{}` commands matching existing hand-crafted format.

    :param metadata: dict with keys 'course_title', 'lesson_title'
    :return: list of lines forming the title slide
    """
    course_title = metadata.get("course_title", "")
    lesson_title = metadata.get("lesson_title", "")
    # Determine logo path based on course title.
    logo_path = "msml610/lectures_source/figures/UMD_Logo.png"
    if "data605" in course_title.lower() or "DATA605" in course_title:
        logo_path = "data605/lectures_source/figures/UMD_Logo.png"
    lines = [
        "::: columns",
        ":::: {.column width=15%}",
        f"![]({logo_path})",
        "::::",
        ":::: {.column width=75%}",
        "",
        r"\vspace{0.4cm}",
        r"\begingroup \large",
        course_title,
        r"\endgroup",
        "::::",
        ":::",
        "",
        r"\vspace{1cm}",
        "",
        r"\begingroup \Large",
        f"**$$\\text{{\\blue{{{lesson_title}}}}}$$**",
        r"\endgroup",
        "",
        r"\vspace{1cm}",
        "",
        "::: columns",
        ":::: {.column width=75%}",
        "**Instructor**: Dr. GP Saggese, [gsaggese@umd.edu](gsaggese@umd.edu)",
        "",
        "**References**:",
        "",
        "::::",
        ":::: {.column width=20%}",
        "",
        "::::",
        ":::",
        "",
    ]
    return lines


# TODO(ai_gp2): Move this to the umd_repo.
def _generate_title_slide_typst(metadata: Dict[str, str]) -> List[str]:
    """
    Generate Typst title slide from metadata.

    Creates a Typst grid-based title slide with text formatting and colors.

    :param metadata: dict with keys 'course_title', 'lesson_title'
    :return: list of lines forming the title slide
    """
    course_title = metadata.get("course_title", "")
    lesson_title = metadata.get("lesson_title", "")
    # Determine logo path based on course title.
    logo_path = "msml610/lectures_source/figures/UMD_Logo.png"
    if "data605" in course_title.lower() or "DATA605" in course_title:
        logo_path = "data605/lectures_source/figures/UMD_Logo.png"
    txt = r"""
        ====

        #slide[
          #grid(
            columns: (15%, 85%),
            gutter: 0.15cm,
            align(top + left)[#image("{}", width: 4.0cm)],
            align(left)[
              #v(-0.1cm)
              #text(size: 20pt)[{}]
            ]
          )

          #v(0.15cm)
          #text(size: 24pt)[*#text(fill: blue)[{}]*]

          #v(0.1cm)
          #text(size: 20pt)[Dr. GP Saggese (#link("mailto:gsaggese@umd.edu")[gsaggese\@umd.edu])]
        ]
    """.format(logo_path, course_title, lesson_title)
    txt = hprint.dedent(txt)
    lines = [
        "```{=typst}",
        txt,
        "```",
        "",
    ]
    return lines


def _generate_title_slide(
    metadata: Dict[str, str], output_format: str
) -> List[str]:
    """
    Dispatch to format-specific title slide generator.

    :param metadata: dict with keys 'course_title', 'lesson_title'
    :param output_format: 'latex' or 'typst'
    :return: list of lines forming the title slide
    """
    hdbg.dassert_in(output_format, ("latex", "typst"))
    if output_format == "latex":
        txt = _generate_title_slide_latex(metadata)
    elif output_format == "typst":
        txt = _generate_title_slide_typst(metadata)
    else:
        raise ValueError(f"Invalid output_format='{output_format}'")
    return txt


# #############################################################################


def _expand_includes(lines: List[str]) -> List[str]:
    r"""
    Expand `// include:<FILE> "<TITLE>"` directives by inlining file sections.

    - Scan lines for include directives
    - Replace them with the body content of the specified section from the
      included file
        - The included file must have a header `# <TITLE>` (level 1),
        - Only the body content under that header (until the next level-1
          header) is inlined
        - The header itself is stripped.

    Relative file paths are resolved from the current working directory.

    :param lines: list of input lines
    :return: list of lines with includes expanded
    """
    hdbg.dassert_isinstance(lines, list)
    out: List[str] = []
    # Pattern: // include:<FILE> "<TITLE>"
    include_pattern = r'^\s*//\s*include:\s*(\S+)\s+"([^"]+)"\s*$'
    for i, line in enumerate(lines):
        m = re.match(include_pattern, line)
        if m:
            file_path = m.group(1)
            title = m.group(2)
            _LOG.debug(
                "Found include directive: file=%s title=%s",
                file_path,
                title,
            )
            # Resolve file path from current working directory if relative.
            if not os.path.isabs(file_path):
                file_path = os.path.join(os.getcwd(), file_path)
            file_path = os.path.abspath(file_path)
            hdbg.dassert_file_exists(
                file_path,
                "Include file not found: %s (resolved from relative path in line %d)",
                file_path,
                i,
            )
            # Read the included file.
            included_txt = hio.from_file(file_path)
            included_lines = included_txt.split("\n")
            # Check for nested includes and reject.
            for j, inc_line in enumerate(included_lines):
                hdbg.dassert(
                    not re.match(include_pattern, inc_line),
                    "Nested include directives not allowed: "
                    "file=%s line=%d has include directive",
                    file_path,
                    j,
                )
            # Extract section under `# <TITLE>`.
            section_lines = _extract_section(included_lines, title)
            hdbg.dassert_is_not(
                section_lines,
                None,
                "Section not found: file=%s title=%s",
                file_path,
                title,
            )
            out.extend(cast(List[str], section_lines))
        else:
            out.append(line)
    hdbg.dassert_isinstance(out, list)
    return out


def _validate_slide_names(lines: List[str]) -> None:
    """
    Validate that all slides (lines starting with '*') have non-whitespace titles.

    :param lines: list of lines to validate
    """
    header_list, _ = hmarkdo.extract_slides_from_markdown(lines)
    for header_info in header_list:
        hdbg.dassert(
            header_info.description.strip(),
            "Slide at line %d has no title (only whitespace)",
            header_info.line_number,
        )


def _assert_no_existing_counters(lines: List[str]) -> None:
    """
    Assert that no slides already have counter-like format.

    Prevents conflicts with automatically-added counters.

    :param lines: list of lines to check
    """
    header_list, _ = hmarkdo.extract_slides_from_markdown(lines)
    counter_pattern = r"\(\d+/\d+\)\s*$"
    for header_info in header_list:
        hdbg.dassert(
            not re.search(counter_pattern, header_info.description),
            "Slide at line %d already has counter format (x/y): '%s'",
            header_info.line_number,
            header_info.description,
        )


def _add_duplicate_slide_counters(lines: List[str]) -> List[str]:
    """
    Add counters (x/y) to slides with duplicate names.

    For slides with identical titles, appends counter in format:
    "Original Title (1/n)", "Original Title (2/n)", etc.

    :param lines: list of lines to process
    :return: list of lines with counters added to duplicate slide names
    """
    header_list, _ = hmarkdo.extract_slides_from_markdown(lines)
    # Count occurrences of each slide name.
    name_counts: Dict[str, int] = {}
    for header_info in header_list:
        name = header_info.description
        name_counts[name] = name_counts.get(name, 0) + 1
    # Build a mapping from line number to new title.
    line_updates: Dict[int, str] = {}
    name_indices: Dict[str, int] = {}
    for header_info in header_list:
        name = header_info.description
        count = name_counts[name]
        if count > 1:
            # This name appears multiple times, add counter.
            name_indices[name] = name_indices.get(name, 0) + 1
            new_name = f"{name} ({name_indices[name]}/{count})"
            line_updates[header_info.line_number] = new_name
    # Apply updates to the lines.
    out: List[str] = []
    for i, line in enumerate(lines, start=1):
        if i in line_updates:
            # Replace the slide title with the new title (with counter).
            new_title = line_updates[i]
            line = f"* {new_title}"
        out.append(line)
    return out


def _validate_unique_slide_names(lines: List[str]) -> None:
    """
    Validate that all slides have unique titles.

    :param lines: list of lines to validate
    """
    header_list, _ = hmarkdo.extract_slides_from_markdown(lines)
    seen_names: Dict[str, int] = {}
    for header_info in header_list:
        name = header_info.description
        hdbg.dassert_not_in(
            name,
            seen_names,
            "Duplicate slide name found: '%s' at lines %d and %d",
            name,
            seen_names.get(name),
            header_info.line_number,
        )
        seen_names[name] = header_info.line_number


# TODO(gp): Use hmarkdown.process_lines().
# TODO(gp): Add a way to control the list of transformations.
def _transform_lines(
    lines: List[str],
    type_: str,
    is_qa: bool,
    output_format: str,
    *,
    actions: Optional[List[str]] = None,
) -> List[str]:
    """
    Process the notes to convert them into a format suitable for pandoc.

    :param lines: list of lines of the notes
    :param type_: type of output to generate (e.g., `pdf`, `html`, `slides`)
    :param is_qa: True if the input is a QA file
    :param actions: optional list of actions to perform
    :param output_format: output format for color commands (latex or typst)
    :return: list of processed lines
    """
    _LOG.debug("\n%s", hprint.frame("transform_lines"))
    hdbg.dassert_isinstance(lines, list)
    lines = [line.rstrip("\n") for line in lines]
    out: List[str] = []
    # a) Prepend some directive for pandoc, if they are missing.
    if output_format == "latex":
        if lines[0] != "---":
            txt = r"""
            ---
            fontsize: 10pt
            ---
            \let\emph\textit
            \let\uline\underline
            \let\ul\underline
            """
            txt = hprint.dedent(txt)
            out.append(txt)
    # b) Process text.
    # TODO(gp): We should use the approach of replacing chunks of text
    # that doesn't have to be transformed with placeholders.
    # True inside a block to skip.
    in_skip_block = False
    # True inside a code block.
    in_code_block = False
    # True inside a math block ($$...$$).
    in_math_block = False
    for i, line in enumerate(lines):
        _LOG.debug("%s:line=%s", i, line)
        # 1) Remove comment block.
        if _TRACE:
            _LOG.debug("# Process comment block.")
        do_continue, in_skip_block = hmarkdo.process_comment_block(
            line, in_skip_block
        )
        # _LOG.debug("  -> do_continue=%s in_skip_block=%s",
        #   do_continue, in_skip_block)
        if do_continue:
            continue
        # 2) Process code block.
        if _TRACE:
            _LOG.debug("# Process code block.")
        # TODO(gp): Not sure why this is needed. For sure the extra spacing
        # creates a problem with the Python code blocks rendered by pandoc beamer.
        if False:
            do_continue, in_code_block, out_tmp = hmarkdo.process_code_block(
                line, in_code_block, i, lines
            )
            out.extend(out_tmp)
            if do_continue:
                continue
        # 3) Remove single line comment.
        if _TRACE:
            _LOG.debug("# Process single line comment.")
        do_continue = hmarkdo.process_single_line_comment(line)
        if do_continue:
            continue
        # 4) Expand abbreviations.
        if _TRACE:
            _LOG.debug("# Process abbreviations.")
        line = _process_abbreviations(line)
        # 5) Process enumerated list.
        if _TRACE:
            _LOG.debug("# Process enumerated list.")
        line = _process_enumerated_list(line)
        # 6) Colorize backticks (skip if inside code block).
        if _TRACE:
            _LOG.debug("# Colorize backticks.")
        if not in_code_block:
            line = _colorize_backticks(line, output_format=output_format)
        # TODO(gp): Not sure about this.
        # Update code block status based on triple backticks.
        if line.startswith("```"):
            in_code_block = not in_code_block
        # Update math block status based on $$.
        if "$$" in line:
            in_math_block = not in_math_block
        # 7) Process color commands (skip if inside math block or inline math).
        if _TRACE:
            _LOG.debug("# Process color commands.")
        # Skip color processing inside math blocks: color syntax doesn't work
        # in math mode.
        # Use the specified output format (latex or typst) for non-math content.
        if not in_math_block:
            line = hmarkdo.process_color_commands(
                line, output_format=output_format
            )
        # 7) Process question.
        if _TRACE:
            _LOG.debug("# Process question.")
        if type_ == "slides":
            do_continue, line = _process_question_to_slides(line)
        else:
            do_continue, line = _process_question_to_markdown(line)
        if do_continue:
            out.append(line)
            continue
        # 8) Process empty lines in the questions and answers.
        if _TRACE:
            _LOG.debug("# Process empty lines in the questions and answers.")
        if not is_qa:
            out.append(line)
        else:
            is_empty = line.rstrip(" ").lstrip(" ") == ""
            if not is_empty:
                # TODO(gp): Use is_header
                if line.startswith("#"):
                    # It's a chapter.
                    out.append(line)
                else:
                    # It's a line in an answer.
                    out.append(" " * _NUM_SPACES + line)
            else:
                # Empty line.
                prev_line_is_verbatim = ((i - 1) > 0) and lines[
                    i - 1
                ].startswith("```")
                next_line_is_verbatim = ((i + 1) < len(lines)) and (
                    lines[i + 1].startswith("```")
                )
                # The next line has a chapter or the start of a new note.
                next_line_is_chapter = ((i + 1) < len(lines)) and (
                    lines[i + 1].startswith("#") or lines[i + 1].startswith("* ")
                )
                _LOG.debug(
                    "  is_empty=%s prev_line_is_verbatim=%s next_line_is_chapter=%s",
                    is_empty,
                    prev_line_is_verbatim,
                    next_line_is_chapter,
                )
                if (
                    next_line_is_chapter
                    or prev_line_is_verbatim
                    or next_line_is_verbatim
                ):
                    out.append(" " * _NUM_SPACES + line)
    #
    if type_ == "slides":
        # Colorize links.
        to_execute, actions = hselacti.mark_action("process_links", actions)
        # to_execute = False
        if to_execute:
            out = hmarkdo.format_md_links_to_latex_format(out)
        # Colorize bullets in the slides.

        def _colorize_bullets(
            slide_text: List[str],
            *,
            slide_title: str = "",
            slide_line_number: int = 0,
        ) -> List[str]:
            """
            Color bullet points in the slide.

            :param slide_text: list of lines in the slide
            :param slide_title: title of the slide (for error reporting)
            :param slide_line_number: line number where slide starts (for error
                reporting)
            :return: colorized slide text as a list of lines
            """
            slide_text_str = "\n".join(slide_text)
            if not hmarkdo.has_color_command(slide_text_str):
                try:
                    text_out = hmarkdo.colorize_bullet_points_in_slide(
                        slide_text_str, output_format, use_abbreviations=False
                    )
                except AssertionError as e:
                    context = (
                        f"\nError occurred while processing slide:\n"
                        f"  Title: {slide_title}\n"
                        f"  Line: {slide_line_number}"
                    )
                    raise AssertionError(str(e) + context) from e
            else:
                text_out = slide_text_str
            text_out = text_out.split("\n")
            return text_out

        out_str = "\n".join(out)
        to_execute, actions = hselacti.mark_action("colorize_bullets", actions)
        if to_execute:
            out_str = hmarkdo.process_slides(out_str, _colorize_bullets)
        out = out_str.split("\n")
    # out = out.split("\n")
    out_tmp = []
    for line in out:
        if type_ == "slides":
            do_continue, line = _process_question_to_slides(line)
        else:
            do_continue, line = _process_question_to_markdown(line)
        if do_continue:
            out_tmp.append(line)
            continue
        out_tmp.append(line)
    out = out_tmp
    # c) Clean up.
    _LOG.debug("Clean up")
    hdbg.dassert_isinstance(out, list)
    # Remove all the lines with only spaces.
    out_tmp = []
    for line in out:
        if re.search(r"^\s+$", line):
            line = ""
        out_tmp.append(line)
    # Return result.
    hdbg.dassert_isinstance(out_tmp, list)
    return out_tmp


def _remove_headers(lines: List[str], max_level: int) -> List[str]:
    """
    Remove all markdown headers from the lines that are smaller than level 3.

    :param lines: list of lines to process
    :param max_level: maximum level of headers to consider (default: 3)
    :return: list of lines with relevant headers removed
    """
    _LOG.debug("\n%s", hprint.frame("Remove headers smaller than level 3"))
    hdbg.dassert_isinstance(lines, list)
    out: List[str] = []
    for line in lines:
        is_header_line, level, _ = hmarkdo.is_header(line)
        # Exclude header lines with level 1 or 2 (i.e., smaller than level 3).
        if not (is_header_line and level < max_level):
            out.append(line)
    hdbg.dassert_isinstance(out, list)
    return out


def _preprocess_lines(
    lines: List[str],
    type_: str,
    toc_type: str,
    is_qa: bool,
    output_format: str,
    *,
    actions: Optional[List[str]] = None,
) -> List[str]:
    """
    Preprocess the lines of the notes.

    :param lines: list of lines of the notes
    :param type_: type of output to generate
    :param toc_type: type of table of contents to add
    :param is_qa: True if the input is a QA file
    :param output_format: "latex" (default) or "typst"
    :param actions: optional list of actions to perform
    :param output_format: output format for color commands (latex or typst)
    :return: list of preprocessed lines
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_in(output_format, ("latex", "typst"))
    # Apply transformations.
    out = _transform_lines(lines, type_, is_qa, output_format, actions=actions)
    # Add TOC, if needed.
    if toc_type == "navigation":
        hdbg.dassert_eq(type_, "slides")
        max_level = 2
        expand_all_navigation = True
        out = hmartoc.add_navigation_slides(
            out,
            max_level,
            expand_all_navigation,
            output_format,
            sanity_check=True,
        )
    elif toc_type == "partial_navigation":
        hdbg.dassert_eq(type_, "slides")
        max_level = 2
        expand_all_navigation = False
        out = hmartoc.add_navigation_slides(
            out,
            max_level,
            expand_all_navigation,
            output_format,
            sanity_check=True,
        )
    elif toc_type == "remove_headers":
        # Remove headers smaller than level 4 so that we leave only the `*`.
        out = _remove_headers(out, max_level=4)
    # Validate slide names.
    to_execute, actions = hselacti.mark_action("validate_slide_names", actions)
    if to_execute:
        _validate_slide_names(out)
    # Add duplicate slide counters.
    to_execute, actions = hselacti.mark_action("add_duplicate_counters", actions)
    if to_execute:
        _assert_no_existing_counters(out)
        out = _add_duplicate_slide_counters(out)
    # Validate unique slide names.
    to_execute, actions = hselacti.mark_action(
        "validate_unique_slide_names", actions
    )
    if to_execute:
        _validate_unique_slide_names(out)
    hdbg.dassert_isinstance(out, list)
    return out


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.

    :return: argument parser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--input", action="store", type=str, required=True)
    parser.add_argument("-o", "--output", action="store", type=str, default="")
    parser.add_argument(
        "--type",
        required=True,
        choices=["pdf", "html", "slides"],
        action="store",
        help="Type of output to generate",
    )
    parser.add_argument(
        "--toc_type",
        action="store",
        default="none",
        choices=[
            "none",
            "pandoc_native",
            "navigation",
            "partial_navigation",
            "remove_headers",
        ],
        help=(
            "Type of table of contents to generate: "
            "'none' = no TOC; "
            "'pandoc_native' = use pandoc's native --toc option (depth 2); "
            "'navigation' = add custom navigation slides for headers (levels 1-3); "
            "'partial_navigation' = add custom navigation slides for headers (levels 1-3); "
            "'remove_headers' = remove headers smaller than level 3"
        ),
    )
    # TODO(gp): Unclear what it does.
    parser.add_argument(
        "--qa", action="store_true", default=False, help="The input file is QA"
    )
    parser.add_argument(
        "--output_format",
        action="store",
        default="latex",
        choices=["latex", "typst"],
        help="Output format (latex or typst)",
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the main preprocessing logic.

    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("cmd line=%s", hdbg.get_command_line())
    # Get the selected actions.
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info("Selected actions: %s", actions)
    # Read file.
    txt = hio.from_file(args.input)
    # Process.
    lines = txt.split("\n")
    # Expand include directives before other preprocessing.
    lines = _expand_includes(lines)
    # Extract and expand metadata directives into title slide.
    metadata, lines = extract_slide_metadata(lines)
    if metadata.get("type") == "UMD_slides":
        title_lines = _generate_title_slide(metadata, args.output_format)
        lines = title_lines + lines
    out = _preprocess_lines(
        lines,
        args.type,
        args.toc_type,
        args.qa,
        args.output_format,
        actions=actions,
    )
    out = "\n".join(out)
    # Save results.
    hio.to_file(args.output, out)


if __name__ == "__main__":
    _main(_parse())
