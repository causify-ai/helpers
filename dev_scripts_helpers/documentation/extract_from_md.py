#!/usr/bin/env python3

r"""
Extract text from a file between two markdown headers or slides.

The script:
- Processes the input Markdown `.md` or txt slide `.txt` file
- Extracts text between specified start and end headers/slides
- If `--md_end` is not provided, extracts until the next header at the same or
  higher level (fewer # symbols)
- If `--md_start` header is not found, raises an error
- Outputs the extracted text to a file or stdout

For `.txt` slide files, headers can be specified as:
- Slides: "* Slide Title" (shorthand for `##### Slide Title`)
- Full header format: "##### Section 1" (includes the # symbols)
- Partial match: "Section 1" (just the title, matches if unique)

For `.md` files, headers can be specified as:
- Full format: "## Section 1" (includes the # symbols)
- Partial match: "Section 1" (just the title, matches if unique)

Examples:
# Extract text between two headers (full format)
> extract_from_md.py -i input.md --md_start "## Section 1" --md_end "## Section 2" -o output.txt

# Extract text using partial header match
> extract_from_md.py -i input.md --md_start "Section 1" --md_end "Section 2" -o output.txt

# Extract text from "## Section 1" until the next level-2 header
> extract_from_md.py -i input.md --md_start "## Section 1" -o output.txt

# Extract text and print to stdout
> extract_from_md.py -i input.md --md_start "Chapter 1" --md_end "Chapter 2" -o -

# Extract text between slides in a .txt file (using slide notation)
> extract_from_md.py -i input.txt --md_start "* Slide 1" --md_end "* Slide 2" -o output.txt

# Extract text from a slide until next same-level slide (no explicit end)
> extract_from_md.py -i input.txt --md_start "* Introduction" -o output.txt
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown_select as hmarsele
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def extract_rule_from_file(rule_spec: str) -> str:
    """
    Extract a rule section from a rules file based on a rule specification.

    :param rule_spec: rule specification in one of these formats:
        - `path/to/file.md`: return all content
        - `path/to/file.md:N`: extract section starting at line N (must be
          a markdown header)
        - `path/to/file.md:N:# Section Name`: same with header name
          validation
    :return: extracted rule text as a string
    """
    # Parse the rule specification.
    parts = rule_spec.split(":", 2)
    file_path = parts[0]
    # Check file exists.
    hdbg.dassert_file_exists(file_path, "Rule file does not exist")
    # Read file content.
    content = hio.from_file(file_path)
    lines = content.splitlines()
    # If only path provided, return full content.
    if len(parts) == 1:
        return content
    # Parse line number.
    try:
        line_num = int(parts[1])
    except ValueError:
        raise ValueError(
            "Invalid line number '%s' in rule spec: %s" % (parts[1], rule_spec)
        )
    # Convert to 0-based index.
    line_idx = line_num - 1
    hdbg.dassert_lt(
        line_idx,
        len(lines),
        "Line number %d exceeds file length %d",
        line_num,
        len(lines),
    )
    # Check that the target line is a header.
    header_line = lines[line_idx]
    if not header_line.startswith("#"):
        raise ValueError(
            "Line %d is not a markdown header: '%s'" % (line_num, header_line)
        )
    # Validate section name if provided.
    if len(parts) == 3:
        expected_name = parts[2]
        if header_line.strip() != expected_name.strip():
            raise ValueError(
                "Section name mismatch at line %d: expected '%s', got '%s'"
                % (line_num, expected_name, header_line)
            )
    # Determine header level (number of leading '#' characters).
    header_level = len(header_line) - len(header_line.lstrip("#"))
    # Find the end of section (next header at same or higher level).
    end_idx = len(lines)
    for i in range(line_idx + 1, len(lines)):
        line = lines[i]
        if line.startswith("#"):
            this_level = len(line) - len(line.lstrip("#"))
            if this_level <= header_level:
                end_idx = i
                break
    # Extract and return the section.
    section_lines = lines[line_idx:end_idx]
    return "\n".join(section_lines)


def _parse() -> argparse.ArgumentParser:
    """
    Create and return the argument parser for the script.

    :return: ArgumentParser configured with input, output, start, and end arguments
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    out_default = "-"
    hparser.add_input_output_args(parser, out_default=out_default)
    hparser.add_md_start_end_args(parser, start_required=True)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Parse arguments and extract text from the input file between specified headers.

    :param parser: ArgumentParser with configured arguments
    """
    args = parser.parse_args()
    verbose = False
    hparser.init_logger_for_input_output_transform(args, verbose=verbose)
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    input_content = hparser.from_file(in_file_name)
    hdbg.dassert_isinstance(
        input_content, list, "input_content must be a list of lines"
    )
    hdbg.dassert_ne(len(input_content), 0, "Input file is empty")
    _, ext = os.path.splitext(in_file_name)
    is_slide_format = ext == ".txt"
    extracted_lines = hmarsele.extract_text_from_markdown_lines(
        input_content,
        args.md_start,
        args.md_end,
        is_slide_format=is_slide_format,
    )
    output_content = "\n".join(extracted_lines)
    start_line_idx = next(
        (
            i + 1
            for i, line in enumerate(input_content)
            if line.lstrip() == args.md_start.lstrip()
        ),
        1,
    )
    end_line_idx = start_line_idx + len(extracted_lines) - 1
    _LOG.info(f"Extracted lines {start_line_idx}-{end_line_idx}")
    hparser.to_file(output_content, out_file_name)


if __name__ == "__main__":
    _main(_parse())
