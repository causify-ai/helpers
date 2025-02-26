import logging
import re
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.


# TODO(gp): -> _skip_comments
def skip_comments(line: str, skip_block: bool) -> Tuple[bool, bool]:
    """
    Skip comments in the given line and handle comment blocks.

    Comments are like:
    - Single line: %% This is a comment
    - Block: <!-- This is a comment -->

    :param line: The line of text to check for comments
    :param skip_block: A flag indicating if currently inside a comment block
    :return: A tuple containing a flag indicating if the line should be skipped
        and the updated skip_block flag
    """
    skip_this_line = False
    # Handle comment block.
    if line.startswith("<!--"):
        # Start skipping comments.
        skip_block = True
        skip_this_line = True
    if skip_block:
        skip_this_line = True
        if line.startswith("-->"):
            # End skipping comments.
            skip_block = False
        else:
            # Skip comment.
            _LOG.debug("  -> skip")
    else:
        # Handle single line comment.
        if line.startswith("%%"):
            _LOG.debug("  -> skip")
            skip_this_line = True
    return skip_this_line, skip_block


# #############################################################################


def extract_section_from_markdown(content: str, header_name: str) -> str:
    """
    Extract a section of text from a Markdown document based on the header
    name.

    The function identifies a section by locating the specified header and
    captures all lines until encountering another header of the same or higher
    level. Headers are identified by the '#' prefix, and their level is
    determined by the number of '#' characters.

    :param content: The markdown content as a single string.
    :param header_name: The exact header name to extract (excluding '#'
        symbols).
    :return: The extracted section as a string, including the header
        line itself and all lines until the next header of the same or
        higher level.
    """
    lines = content.splitlines()
    _LOG.debug(hprint.to_str("lines"))
    extracted_lines = []
    # Level of the current header being processed.
    current_level: Optional[int] = None
    # Flag to indicate if we're inside the desired section.
    inside_section: bool = False
    found = False
    # Process each line in the markdown content.
    for line in lines:
        _LOG.debug(hprint.to_str("line"))
        # Check if the line is a markdown header.
        if line.strip().startswith("#"):
            # Determine the level of the header by counting leading '#'
            # characters.
            header_level = len(line) - len(line.lstrip("#"))
            # Extract the actual header text by stripping '#' and surrounding
            # whitespace.
            header_text = line.strip("#").strip()
            _LOG.debug(hprint.to_str("header_level, header_text"))
            # Handle the end of the desired section when encountering another
            # header.
            if inside_section:
                if header_level <= current_level:
                    break
            # Check if the current line is the desired header.
            if header_text == header_name:
                found = True
                # Set the level of the matched header.
                current_level = header_level
                # Mark that we are now inside the desired section.
                inside_section = True
        # Add the line to the output if inside the desired section.
        if inside_section:
            extracted_lines.append(line)
            _LOG.debug(hprint.to_str("extracted_lines"))
    if not found:
        raise ValueError(f"Header '{header_name}' not found")
    return "\n".join(extracted_lines)


# #############################################################################


# TODO(gp): -> extract_headers_from_markdown
def extract_headers(
    markdown_file: str, input_content: str, *, max_level: int = 6
) -> str:
    """
    Extract headers from Markdown file and generate Vim cfile to navigate them.

    Use the generated file in Vim as:
        `:cfile <output_file>`
        Use `:cnext` and `:cprev` to navigate between headers.

    :param markdown_file: Path to the input Markdown file.
    :param input_content: Path to the input Markdown file.
    :param max_level: Maximum header levels to parse (1 for `#`, 2 for `##`,
        etc.).
    :return: the generated output file content, e.g.,
        The generated cfile format:
            <file path>:<line number>:<header title>
    """
    summary = []
    # Find an header like `# Header1` or `## Header2`.
    header_pattern = re.compile(r"^(#+)\s+(.*)")
    headers = []
    # Process the input file to extract headers.
    for line_number, line in enumerate(input_content.splitlines(), start=1):
        # Skip the visual separators.
        if "########################################" in line:
            continue
        match = header_pattern.match(line)
        if match:
            # Number of '#' determines level.
            level = len(match.group(1))
            if level <= max_level:
                title = match.group(2).strip()
                headers.append((line_number, level, title))
                #
                summary.append("  " * (level - 1) + title + f" {line_number}")
    # Generate the output file content.
    output_lines = [
        f"{markdown_file}:{line_number}:{title}"
        for line_number, level, title in headers
    ]
    output_content = "\n".join(output_lines)
    print("\n".join(summary))
    return output_content


# #############################################################################


def table_of_content(file_name: str, max_lev: int) -> None:
    """
    Generate a table of contents from the given file, considering the specified
    maximum level of headings.

    :param file_name: The name of the file to read and generate the table of
        contents from
    :param max_lev: The maximum level of headings to include in the table of
        contents
    """
    skip_block = False
    txt = hparser.read_file(file_name)
    for line in txt:
        # Skip comments.
        skip_this_line, skip_block = skip_comments(line, skip_block)
        if False and skip_this_line:
            continue
        #
        for i in range(1, max_lev + 1):
            if line.startswith("#" * i + " "):
                if (
                    ("#########" not in line)
                    and ("///////" not in line)
                    and ("-------" not in line)
                    and ("======" not in line)
                ):
                    if i == 1:
                        print()
                    print(f"{'    ' * (i - 1)}{line}")
                break


# #############################################################################


def format_headers(in_file_name: str, out_file_name: str, max_lev: int) -> None:
    """
    Format the headers in the input file and write the formatted text to the
    output file.

    :param in_file_name: The name of the input file to read
    :param out_file_name: The name of the output file to write the formatted
        text to
    :param max_lev: The maximum level of headings to include in the formatted
        text
    """
    txt = hparser.read_file(in_file_name)
    #
    for line in txt:
        m = re.search(r"max_level=(\d+)", line)
        if m:
            max_lev = int(m.group(1))
            _LOG.warning("Inferred max_level=%s", max_lev)
            break
    hdbg.dassert_lte(1, max_lev)
    # Remove all headings.
    txt_tmp = []
    for line in txt:
        # Keep the comments.
        if not (
            re.match("#+ ####+", line)
            or re.match("#+ /////+", line)
            or re.match("#+ ------+", line)
            or re.match("#+ ======+", line)
        ):
            txt_tmp.append(line)
    txt = txt_tmp[:]
    # Add proper heading of the correct length.
    txt_tmp = []
    for line in txt:
        # Keep comments.
        found = False
        for i in range(1, max_lev + 1):
            if line.startswith("#" * i + " "):
                row = "#" * i + " " + "#" * (79 - 1 - i)
                txt_tmp.append(row)
                txt_tmp.append(line)
                txt_tmp.append(row)
                found = True
        if not found:
            txt_tmp.append(line)
    # TODO(gp): Remove all empty lines after a heading.
    # TODO(gp): Format title (first line capital and then small).
    hparser.write_file(txt_tmp, out_file_name)


# TODO(gp): Generalize this to also decrease the header level
# TODO(gp): -> modify_header_level
def increase_chapter(in_file_name: str, out_file_name: str) -> None:
    """
    Increase the level of chapters by one for text in stdin.

    :param in_file_name: The name of the input file to read
    :param out_file_name: The name of the output file to write the
        modified text to
    """
    skip_block = False
    txt = hparser.read_file(in_file_name)
    #
    txt_tmp = []
    for line in txt:
        skip_this_line, skip_block = skip_comments(line, skip_block)
        if skip_this_line:
            continue
        #
        line = line.rstrip(r"\n")
        for i in range(1, 5):
            if line.startswith("#" * i + " "):
                line = line.replace("#" * i + " ", "#" * (i + 1) + " ")
                break
        txt_tmp.append(line)
    #
    hparser.write_file(txt_tmp, out_file_name)


# #############################################################################


def process_comment_block(line: str, in_skip_block: bool) -> Tuple[bool, bool]:
    """
    Process lines of text to identify blocks that start with '<!--' or '/*' and
    end with '-->' or '*/'.

    :param line: The current line of text being processed.
    :param in_skip_block: A flag indicating if the function is currently
        inside a comment block.
    :return: A tuple containing a boolean indicating whether to continue
        processing the current line and a boolean indicating whether the
        function is currently inside a comment block.
    """
    do_continue = False
    if line.startswith(r"<!--") or re.search(r"^\s*\/\*", line):
        hdbg.dassert(not in_skip_block)
        # Start skipping comments.
        in_skip_block = True
    if in_skip_block:
        if line.endswith(r"-->") or re.search(r"^\s*\*\/", line):
            # End skipping comments.
            in_skip_block = False
        # Skip comment.
        _LOG.debug("  -> skip")
        do_continue = True
    return do_continue, in_skip_block


def process_code_block(
    line: str, in_code_block: bool, i: int, lines: List[str]
) -> Tuple[bool, bool, List[str]]:
    """
    Process lines of text to handle code blocks that start and end with '```'.

    :param line: The current line of text being processed.
    :param in_code_block: A flag indicating if the function is currently
        inside a code block.
    :param i: The index of the current line in the list of lines.
    :param lines: The list of all lines of text being processed.
    :return: A tuple containing a boolean indicating whether to continue
        processing the current line, a boolean indicating whether the function
        is currently inside a code block, and a list of processed lines.
    """
    out: List[str] = []
    do_continue = False
    if re.match(r"^(\s*)```", line):
        _LOG.debug("  -> code block")
        in_code_block = not in_code_block
        # Add empty line.
        if (
            in_code_block
            and (i + 1 < len(lines))
            and re.match(r"\s*", lines[i + 1])
        ):
            out.append("\n")
        out.append("    " + line)
        if (
            not in_code_block
            and (i + 1 < len(lines))
            and re.match(r"\s*", lines[i + 1])
        ):
            out.append("\n")
        do_continue = True
        return do_continue, in_code_block, out
    if in_code_block:
        line = line.replace("// ", "# ")
        out.append("    " + line)
        # We don't do any of the other post-processing.
        do_continue = True
        return do_continue, in_code_block, out
    return do_continue, in_code_block, out


def process_single_line_comment(line: str) -> bool:
    """
    Handle single line comment.

    We need to do it after the // in code blocks have been handled.
    """
    do_continue = False
    if line.startswith(r"%%") or line.startswith(r"//"):
        do_continue = True
        _LOG.debug("  -> do_continue=True")
        return do_continue
    # Skip frame.
    if (
        re.match(r"\#+ -----", line)
        or re.match(r"\#+ \#\#\#\#\#", line)
        or re.match(r"\#+ =====", line)
        or re.match(r"\#+ \/\/\/\/\/", line)
    ):
        do_continue = True
        _LOG.debug("  -> do_continue=True")
        return do_continue
    # Nothing to do.
    return do_continue


def remove_end_of_line_periods(txt: str) -> str:
    """
    Remove periods at the end of each line in the given text.

    :param txt: The input text to process
    :return: The text with end-of-line periods removed
    """
    hdbg.dassert_isinstance(txt, str)
    txt_out = [line.rstrip(".") for line in txt.split("\n")]
    txt_out = "\n".join(txt_out)
    return txt_out


def remove_empty_lines(txt: str) -> str:
    """
    Remove empty lines from the given text.

    :param txt: The input text to process
    :return: The text with empty lines removed
    """
    hdbg.dassert_isinstance(txt, str)
    txt_out = [line for line in txt.split("\n") if line != ""]
    txt_out = "\n".join(txt_out)
    return txt_out


def remove_code_delimiters(text: str) -> str:
    """
    Remove ```python and ``` delimiters from a given text.

    :param text: The input text containing code delimiters.
    :return: The text with the code delimiters removed.
    """
    # Replace the ```python and ``` delimiters with empty strings.
    text = text.replace("```python", "").replace("```", "")
    return text.strip()