#!/usr/bin/env python3

"""
Create a summary of a markdown file that preserves the header structure.

The script processes markdown files and generates summaries using LLM while maintaining
the original header hierarchy.

Examples:
# Summarize content under level 2 headers
> create_markdown_summary.py --in_file input.md --action summarize --out_file output.md --max_level 2

# Summarize using llm library instead of command line llm tool
> create_markdown_summary.py --in_file input.md --action summarize --out_file output.md --max_level 2 --use_library

# Preview which chunks will be summarized (save to file)
> create_markdown_summary.py --in_file input.md --action preview_chunks --out_file preview.md --max_level 2

# Check that output file has same structure as input
> create_markdown_summary.py --in_file input.md --action check_output --out_file output.md --max_level 2

Import as:

import create_markdown_summary as crmasu
"""

# TODO(gp): Use mistletoe to parse the markdown file and process it.
# See https://github.com/miyuchina/mistletoe/blob/master/dev-guide.md


import argparse
import logging
import os
from typing import List, Tuple

import llm
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

_VALID_ACTIONS = ["summarize", "preview_chunks", "check_output"]
_DEFAULT_ACTIONS = ["summarize"]

# #############################################################################


def _validate_llm_availability() -> None:
    """
    Check if the llm command is available.
    """
    hsystem.system("which llm", suppress_output=True)


def _extract_sections_at_level(
    lines: List[str], header_list: hmarkdo.HeaderList, max_level: int
) -> List[Tuple[int, int, str, int]]:
    """
    Extract content sections based on header level.

    :param lines: input markdown lines
    :param header_list: parsed header information
    :param max_level: maximum header level to process
    :return: list of (start_line, end_line, section_content,
        chunk_number) tuples
    """
    sections = []
    chunk_num = 1
    # Find sections that match the specified max_level.
    target_headers = [h for h in header_list if h.level == max_level]
    #
    for i, header in enumerate(target_headers):
        start_line = header.line_number
        # Find the end of this section.
        if i + 1 < len(target_headers):
            # Next header at same level.
            end_line = target_headers[i + 1].line_number - 1
        else:
            # Look for next header at same or higher level.
            next_header_idx = None
            for j, h in enumerate(header_list):
                if h.line_number > header.line_number and h.level <= max_level:
                    next_header_idx = j
                    break
            if next_header_idx is not None:
                end_line = header_list[next_header_idx].line_number - 1
            else:
                end_line = len(lines)
        # Extract section content.
        section_lines = lines[start_line - 1 : end_line]
        section_content = "\n".join(section_lines)
        sections.append((start_line, end_line, section_content, chunk_num))
        chunk_num += 1
    return sections


def _summarize_section_with_llm(
    content: str, max_num_bullets: int, use_library: bool = False
) -> str:
    """
    Summarize content using LLM.

    :param content: markdown content to summarize
    :param max_num_bullets: maximum number of bullet points
    :param use_library: if True, use llm library; if False, use command
        line llm tool
    :return: summarized content as bullet points
    """
    # Create base prompt.
    base_prompt = f"Given the following markdown text summarize it into up to {max_num_bullets} bullets to capture the most important points"
    # Add guidelines if available.
    guidelines_file = "/Users/saggese/src/tutorials1/guidelines_for_notes.txt"
    hdbg.dassert_file_exists(guidelines_file)
    guidelines_content = hio.from_file(guidelines_file)
    prompt = f"""
    {base_prompt}


    You must follow the instructions below:
    {guidelines_content}

    Markdown content to summarize:
    {content}"""
    prompt = hprint.dedent(prompt)
    if use_library:
        # Use llm library
        model = llm.get_model("gpt-4o-mini")
        response = model.prompt(prompt)
        summary = response.text()
    else:
        # Use command line llm tool - write both prompt and content to file
        tmp_prompt_file = "tmp.create_markdown_summary.prompt.txt"
        full_content = f"{prompt}\n\n{content}"
        hio.to_file(tmp_prompt_file, full_content)
        cmd = f"llm -m gpt-4o-mini < {tmp_prompt_file}"
        _, summary = hsystem.system_to_string(cmd)
    return summary.strip()


def _create_output_structure(
    sections: List[Tuple[int, int, str, int]],
    header_list: hmarkdo.HeaderList,
    max_level: int,
    input_file: str,
    lines: List[str],
) -> str:
    """
    Create output markdown structure with summaries.

    :param sections: extracted sections with summaries
    :param header_list: original header list
    :param max_level: maximum level processed
    :param input_file: input file name for source tracking
    :param lines: original lines for non-summarized content
    :return: formatted output markdown
    """
    output_lines = []
    # Track which lines we've already processed
    processed_lines = set()
    # Process headers in order.
    for header in header_list:
        header_line_num = header.line_number - 1  # Convert to 0-based indexing
        #
        if header.level < max_level:
            # Include higher-level headers and content until next header
            if header_line_num not in processed_lines:
                output_lines.append(lines[header_line_num])
                processed_lines.add(header_line_num)
                # Add content after this header until next header at same/higher level
                content_start = header_line_num + 1
                content_end = len(lines)
                # Find next header at same or higher level
                for next_header in header_list:
                    if (
                        next_header.line_number > header.line_number
                        and next_header.level <= header.level
                    ):
                        content_end = next_header.line_number - 1
                        break
                # Add non-summarized content
                for line_num in range(content_start, content_end):
                    if line_num < len(lines) and line_num not in processed_lines:
                        # Check if this line is part of a max_level section
                        is_in_section = False
                        for start_line, end_line, _, _ in sections:
                            if start_line - 1 <= line_num < end_line:
                                is_in_section = True
                                break
                        if not is_in_section:
                            output_lines.append(lines[line_num])
                            processed_lines.add(line_num)
        elif header.level == max_level:
            # Replace this section with summary
            section_found = False
            for start_line, end_line, summary_content, chunk_num in sections:
                if start_line == header.line_number:
                    section_found = True
                    # Add header
                    output_lines.append(lines[header_line_num])
                    processed_lines.add(header_line_num)
                    # Add source tracking comment
                    source_comment = (
                        f"// From {input_file}: [{start_line}, {end_line}]"
                    )
                    output_lines.append(source_comment)
                    # Add summary
                    output_lines.append(summary_content)
                    output_lines.append("")  # Add blank line
                    # Mark all lines in this section as processed
                    for line_num in range(start_line - 1, end_line):
                        if line_num < len(lines):
                            processed_lines.add(line_num)
                    break
            if not section_found:
                # Fallback: include header as-is
                if header_line_num not in processed_lines:
                    output_lines.append(lines[header_line_num])
                    processed_lines.add(header_line_num)
    #
    # Add any remaining unprocessed lines
    for line_num in range(len(lines)):
        if line_num not in processed_lines:
            output_lines.append(lines[line_num])
    #
    return "\n".join(output_lines)


def _action_summarize(
    input_file: str,
    output_file: str,
    max_level: int,
    max_num_bullets: int,
    use_library: bool = False,
) -> None:
    """
    Summarize sections at specified level.

    :param input_file: path to input markdown file
    :param output_file: path to output file
    :param max_level: header level to summarize
    :param max_num_bullets: maximum number of bullets per summary
    :param use_library: if True, use llm library; if False, use command
        line llm tool
    """
    _LOG.info("Starting summarize action for file: %s", input_file)
    # Validate LLM availability.
    _validate_llm_availability()
    # Read and parse markdown.
    lines = hparser.read_file(input_file)
    header_list = hmarkdo.extract_headers_from_markdown(
        lines, max_level=max_level, sanity_check=True
    )
    # Validate header structure.
    hmarkdo.sanity_check_header_list(header_list)
    # Check that every level 1 header has content up to max_level.
    level_1_headers = [h for h in header_list if h.level == 1]
    for l1_header in level_1_headers:
        # Find headers between this L1 and next L1 (or end).
        next_l1_idx = None
        for i, h in enumerate(header_list):
            if h.line_number > l1_header.line_number and h.level == 1:
                next_l1_idx = i
                break
        #
        if next_l1_idx is not None:
            section_headers = header_list[
                header_list.index(l1_header) : next_l1_idx
            ]
        else:
            section_headers = header_list[header_list.index(l1_header) :]
        #
        has_max_level = any(h.level == max_level for h in section_headers)
        hdbg.dassert(
            has_max_level,
            "Level 1 header '%s' at line %d does not contain level %d headers",
            l1_header.description,
            l1_header.line_number,
            max_level,
        )
    # Extract sections at target level.
    sections = _extract_sections_at_level(lines, header_list, max_level)
    _LOG.info("Found %d sections to summarize", len(sections))
    # Summarize each section.
    summarized_sections = []
    for start_line, end_line, content, chunk_num in tqdm(
        sections, desc="Summarizing chunks", unit="chunk"
    ):
        _LOG.info(
            "Summarizing chunk %d: lines %d-%d", chunk_num, start_line, end_line
        )
        summary = _summarize_section_with_llm(
            content, max_num_bullets, use_library
        )
        summarized_sections.append((start_line, end_line, summary, chunk_num))
    # Create output structure.
    output_content = _create_output_structure(
        summarized_sections, header_list, max_level, input_file, lines
    )
    # Save output.
    output_dir = os.path.dirname(output_file)
    if output_dir:
        hio.create_dir(output_dir, incremental=True)
    hparser.write_file(output_content, output_file)
    _LOG.info("Summary saved to: %s", output_file)


def _action_preview_chunks(
    input_file: str, output_file: str, max_level: int
) -> None:
    """
    Preview which chunks will be summarized.
    """
    _LOG.info("Starting preview_chunks action for file: %s", input_file)
    # Read and parse markdown.
    lines = hparser.read_file(input_file)
    header_list = hmarkdo.extract_headers_from_markdown(
        lines, max_level=max_level, sanity_check=True
    )
    # Extract sections.
    sections = _extract_sections_at_level(lines, header_list, max_level)
    # Create annotated output.
    output_lines = []
    line_idx = 0
    #
    for start_line, end_line, content, chunk_num in sections:
        # Add lines before this section.
        while line_idx < start_line - 1:
            output_lines.append(lines[line_idx])
            line_idx += 1
        # Add end marker for previous chunk (if not first chunk)
        if chunk_num > 1:
            end_marker = f"// ---------------------> end chunk {chunk_num - 1} <---------------------"
            output_lines.append(end_marker)
            output_lines.append("")  # Add blank line
        # Get section content
        section_lines = lines[start_line - 1 : end_line]
        # Look for header frame pattern: decorative line, header, decorative line
        # Check if this section starts with a decorated header
        if (
            len(section_lines) >= 3
            and "#############################################################################"
            in section_lines[0]
            and section_lines[1].startswith("##")
            and "#############################################################################"
            in section_lines[2]
        ):
            # Full 3-line header frame
            header_frame_lines = section_lines[0:3]
            content_lines = section_lines[3:]
        elif len(section_lines) >= 1 and section_lines[0].startswith("##"):
            # Simple header without decoration
            header_frame_lines = [section_lines[0]]
            content_lines = section_lines[1:]
        else:
            # No header found
            header_frame_lines = []
            content_lines = section_lines
        # Add the complete header frame
        output_lines.extend(header_frame_lines)
        output_lines.append("")  # Add blank line
        # Add start marker for current chunk
        start_marker = f"// ---------------------> start chunk {chunk_num} <---------------------"
        output_lines.append(start_marker)
        # Add remaining section content
        output_lines.extend(content_lines)
        line_idx = end_line
    # Add final end marker for last chunk
    if sections:
        final_end_marker = f"// ---------------------> end chunk {len(sections)} <---------------------"
        output_lines.append(final_end_marker)
    # Add remaining lines.
    while line_idx < len(lines):
        output_lines.append(lines[line_idx])
        line_idx += 1
    # Save output to file.
    output_content = "\n".join(output_lines)
    output_dir = os.path.dirname(output_file)
    if output_dir:
        hio.create_dir(output_dir, incremental=True)
    hparser.write_file(output_content, output_file)
    _LOG.info("Preview saved to: %s", output_file)


def _transform_file_to_headers(
    file_path: str, max_level: int, sanity_check: bool = True
) -> hmarkdo.HeaderList:
    """
    Transform a file into its header structure.

    :param file_path: path to markdown file
    :param max_level: maximum header level to extract
    :param sanity_check: whether to perform sanity checks on headers
    :return: extracted header list
    """
    lines = hparser.read_file(file_path)
    headers = hmarkdo.extract_headers_from_markdown(
        lines, max_level=max_level, sanity_check=sanity_check
    )
    return headers


def _action_check_output(
    input_file: str, output_file: str, max_level: int, *, tmp_dir: str = "."
) -> None:
    """
    Check that output file has same structure as input file.
    """
    _LOG.info("Starting check_output action")
    # Extract headers from both files.
    input_headers = _transform_file_to_headers(
        input_file, max_level, sanity_check=True
    )
    output_headers = _transform_file_to_headers(
        output_file, max_level, sanity_check=False
    )
    # Create temporary files for comparison.
    tmp_headers_in = os.path.join(tmp_dir, "tmp.headers_in.md")
    tmp_headers_out = os.path.join(tmp_dir, "tmp.headers_out.md")
    # Write header structures.
    input_structure_lines = hmarkdo.header_list_to_markdown(
        input_headers, "headers"
    )
    output_structure_lines = hmarkdo.header_list_to_markdown(
        output_headers, "headers"
    )
    input_structure = "\n".join(input_structure_lines)
    output_structure = "\n".join(output_structure_lines)
    hparser.write_file(input_structure, tmp_headers_in)
    hparser.write_file(output_structure, tmp_headers_out)
    # Compare using sdiff.
    _LOG.info("Comparing header structures using sdiff")
    cmd = f"sdiff {tmp_headers_in} {tmp_headers_out}"
    try:
        hsystem.system(cmd)
        _LOG.info("Header structures match")
    except RuntimeError as e:
        _LOG.warning("Header structures differ:")
        _LOG.warning(str(e))


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--in_file", required=True, help="Input markdown file")
    parser.add_argument("--out_file", help="Output file path")
    parser.add_argument(
        "--max_level",
        type=int,
        default=2,
        help="Header level to summarize (default: 2)",
    )
    parser.add_argument(
        "--max_num_bullets",
        type=int,
        default=5,
        help="Maximum number of bullets for summary (default: 5)",
    )
    parser.add_argument(
        "--use_library",
        action="store_true",
        help="Use llm library instead of command line llm tool",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate input file exists.
    hdbg.dassert(
        os.path.isfile(args.in_file), "Input file does not exist:", args.in_file
    )
    # Set default output file if not provided.
    if args.out_file is None:
        base_name = os.path.splitext(os.path.basename(args.in_file))[0]
        args.out_file = f"{base_name}.summary.txt"
    # Get selected actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    # Process each action.
    for action in actions:
        if action == "summarize":
            _action_summarize(
                args.in_file,
                args.out_file,
                args.max_level,
                args.max_num_bullets,
                args.use_library,
            )
        elif action == "preview_chunks":
            _action_preview_chunks(args.in_file, args.out_file, args.max_level)
        elif action == "check_output":
            _action_check_output(args.in_file, args.out_file, args.max_level)
        else:
            hdbg.dfatal("Invalid action: %s", action)


if __name__ == "__main__":
    _main(_parse())
