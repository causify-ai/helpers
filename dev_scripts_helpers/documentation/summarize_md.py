#!/usr/bin/env -S uv run

# /// script
# dependencies = ["markdown-it-py", "tqdm"]
# ///

r"""
Summarize markdown headers using an LLM or compute SHA1 digests.

The script reads a markdown file and, for each header at a specified level
(--md_level), extracts the full section (including all nested content) and
either sends it to an LLM for summarization or computes a SHA1 digest.
Results are appended to the output file incrementally.

The output preserves the markdown header structure with summaries or digests.

Uses markdown-it-py to parse the markdown into an AST and process it for
header extraction and section boundaries.

Examples:
# Summarize all level-1 chapters with LLM
> ./summarize_md.py -i book.md -o book.summary.md --md_level 1

# Compute SHA1 digests instead of LLM summaries (for testing)
> ./summarize_md.py -i book.md -o book.digest.md --md_level 1 --test

# Summarize level-2 sections in a range
> ./summarize_md.py -i book.md -o out.md --md_level 2 --start "Chapter 1" --end "Chapter 2"

# Dry run: test with the first section only
> ./summarize_md.py -i book.md -o out.md --md_level 1 --dry_run

# Use a different LLM model
> ./summarize_md.py -i book.md -o out.md --md_level 1 --model "claude-3-opus"
"""

import argparse
import hashlib
import logging
from typing import Dict, List, Optional, Tuple

from markdown_it import MarkdownIt
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


def _get_system_prompt() -> str:
    """
    Build system prompt for LLM-based markdown summarization.

    Loads bullet point style rules and constructs a prompt that instructs the
    LLM to preserve markdown structure and chapter numbering.

    :return: System prompt string with formatting instructions and examples
    """
    rules_file = hgit.find_file_in_git_tree("text.rules.bullet_points.md")
    rules_content = hio.from_file(rules_file)
    system_prompt = f"""
    Write a summary in bullet points using the following rules from the style guide:
    {rules_content}
    """
    system_prompt = hprint.dedent(system_prompt)
    return system_prompt


def _compute_sha1_digest(text: str) -> str:
    """
    Compute SHA1 digest of text.

    :param text: Input text to digest
    :return: Hex-encoded SHA1 digest
    """
    sha1 = hashlib.sha1(text.encode("utf-8"))
    return sha1.hexdigest()


def _extract_headers_from_ast(
    tokens: List,
) -> List[Tuple[int, str, int]]:
    """
    Extract headers from markdown-it-py AST tokens.

    Scans tokens for heading_open blocks and extracts level, title, and line number.

    :param tokens: List of tokens from MarkdownIt parser
    :return: List of (level, title, line_number) tuples
    """
    headers = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == "heading_open":
            # Extract level from tag (h1, h2, etc.)
            level = int(token.tag[1])
            # Get the next token which contains the content.
            if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                inline_token = tokens[i + 1]
                # Extract text from inline children.
                title = ""
                if inline_token.children:
                    for child in inline_token.children:
                        if child.type == "text":
                            title += child.content
                # Store header with line number (convert from 0-indexed).
                line_number = token.map[0] if token.map else 0
                headers.append((level, title, line_number))
        i += 1
    return headers


def _get_target_headers(
    all_headers: List[Tuple[int, str, int]],
    *,
    md_level: int,
    start: Optional[str],
    end: Optional[str],
) -> List[Tuple[int, str, int]]:
    """
    Filter headers by level and optional start/end boundaries.

    Selects headers at the specified level, optionally restricting the range
    to start from and end at specific headers (matched by prefix).

    :param all_headers: List of (level, title, line_number) tuples
    :param md_level: Header level to select (1=H1, 2=H2, etc.)
    :param start: Optional header prefix to start from; None means start from beginning
    :param end: Optional header prefix to end at; None means continue to end
    :return: Filtered list of headers at the specified level within the range
    """
    target_headers = [h for h in all_headers if h[0] == md_level]
    hdbg.dassert(
        target_headers,
        "No headers found at level %d. Available levels: %s",
        md_level,
        sorted(set(h[0] for h in all_headers)),
    )
    # Apply start boundary if specified: find matching header and slice from there.
    if start is not None:
        start_idx = -1
        for i, h in enumerate(target_headers):
            if h[1].startswith(start):
                start_idx = i
                break
        hdbg.dassert_ne(start_idx, -1, "No header matches --start: '%s'", start)
        target_headers = target_headers[start_idx:]
    # Apply end boundary if specified: find matching header and slice up to there.
    if end is not None:
        end_idx = -1
        for i, h in enumerate(target_headers):
            if h[1].startswith(end):
                end_idx = i
                break
        hdbg.dassert_ne(end_idx, -1, "No header matches --end: '%s'", end)
        target_headers = target_headers[: end_idx + 1]
    return target_headers


def _get_parent_headers(
    header: Tuple[int, str, int],
    all_headers: List[Tuple[int, str, int]],
    *,
    md_level: int,
) -> List[Tuple[int, str, int]]:
    """
    Get all parent headers (level < md_level) before the given header.

    :param header: The (level, title, line_number) tuple for the target header
    :param all_headers: List of all (level, title, line_number) tuples
    :param md_level: The target level
    :return: List of parent header tuples in order
    """
    parents = []
    target_pos = -1
    for i, h in enumerate(all_headers):
        if h[2] == header[2]:
            target_pos = i
            break
    if target_pos == -1:
        return parents
    # Collect all headers before this one that have level < md_level.
    for i in range(target_pos - 1, -1, -1):
        h = all_headers[i]
        if h[0] < md_level:
            parents.insert(0, h)
    return parents


def _extract_section(
    header: Tuple[int, str, int],
    all_headers: List[Tuple[int, str, int]],
    lines: List[str],
    *,
    md_level: int,
) -> str:
    """
    Extract a markdown section from the starting header to the next same-level header.

    Locates the line range for the given header and includes all nested content
    until the next header at the same or higher level.

    :param header: The (level, title, line_number) tuple for the header
    :param all_headers: List of all (level, title, line_number) tuples
    :param lines: All markdown lines (0-indexed)
    :param md_level: The target header level (used to find end boundary)
    :return: Section content as a string (trailing empty lines removed)
    """
    start_idx = header[2]
    # Find position of this header in the full header list for boundary detection.
    header_pos = -1
    for i, h in enumerate(all_headers):
        if h[2] == header[2]:
            header_pos = i
            break
    hdbg.dassert_ne(header_pos, -1, "Header position not found")
    # Find the next header at the same or higher level to determine section end.
    next_header_line = None
    for i in range(header_pos + 1, len(all_headers)):
        if all_headers[i][0] <= md_level:
            next_header_line = all_headers[i][2]
            break
    # Use the next header line or end of file as the section boundary.
    if next_header_line is None:
        end_idx = len(lines)
    else:
        end_idx = next_header_line
    section_lines = lines[start_idx:end_idx]
    # Remove trailing empty lines to clean up the section.
    while section_lines and section_lines[-1].strip() == "":
        section_lines.pop()
    section_text = "\n".join(section_lines)
    return section_text


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(parser, out_required=True)
    parser.add_argument(
        "--md_level",
        type=int,
        default=1,
        help="Header level to summarize (1=H1, 2=H2, etc.; default: 1)",
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start from this header (partial match on header title)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End after this header (partial match on header title)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="LLM model to use (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--use_llm_executable",
        action="store_true",
        help="Use llm CLI executable instead of Python library",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Summarize only the first section and exit",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Compute SHA1 digest of text instead of summarizing with LLM",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to summarize markdown sections.

    Summarizes sections using LLM by default, or computes SHA1 digests if
    `--test` flag is enabled.
    """
    args = parser.parse_args()
    hparser.parse_verbosity_args(args)
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    hdbg.dassert_file_exists(in_file_name, "Input markdown file must exist")
    hdbg.dassert(args.md_level >= 1, "--md_level must be >= 1")
    # Read input file and split into lines.
    content = hio.from_file(in_file_name)
    lines = content.splitlines()
    _LOG.debug("Read %d lines from %s", len(lines), in_file_name)
    # Parse markdown to extract headers using AST.
    md_parser = MarkdownIt()
    tokens = md_parser.parse(content)
    all_headers = _extract_headers_from_ast(tokens)
    _LOG.debug("Extracted %d headers from input file", len(all_headers))
    # Filter headers to the target level and optional range.
    target_headers = _get_target_headers(
        all_headers, md_level=args.md_level, start=args.start, end=args.end
    )
    _LOG.info(
        "Processing %d headers at level %d", len(target_headers), args.md_level
    )
    system_prompt = _get_system_prompt()
    # Initialize output file.
    with open(out_file_name, "w") as f:
        pass
    total_cost = 0.0
    written_headers: Dict[Tuple[int, str], bool] = {}
    # Summarize each target header section.
    for header in tqdm(target_headers, desc="Summarizing sections"):
        # Get parent headers and write them if not already written.
        parent_headers = _get_parent_headers(
            header, all_headers, md_level=args.md_level
        )
        with open(out_file_name, "a") as f:
            for parent in parent_headers:
                parent_key = (parent[0], parent[1])
                if parent_key not in written_headers:
                    f.write("#" * parent[0] + " " + parent[1])
                    f.write("\n\n")
                    written_headers[parent_key] = True
            # Write the target header itself.
            header_key = (header[0], header[1])
            f.write("#" * header[0] + " " + header[1])
            f.write("\n\n")
            written_headers[header_key] = True
        section_text = _extract_section(
            header, all_headers, lines, md_level=args.md_level
        )
        _LOG.debug(
            "Extracted section for header: %s",
            header[1],
        )
        # Compute section summary (digest in test mode, LLM in normal mode).
        if args.test:
            digest = _compute_sha1_digest(section_text)
            summary = f"SHA1: {digest}\n"
        else:
            summary, cost = hllmcli.apply_llm(
                input_str=section_text,
                system_prompt=system_prompt,
                model=args.model,
                use_llm_executable=args.use_llm_executable,
            )
            total_cost += cost
            _LOG.debug("LLM cost: $%.6f", cost)
        # Append summary to output file.
        with open(out_file_name, "a") as f:
            f.write(summary)
            f.write("\n\n")
        if args.dry_run:
            _LOG.info("Dry run: summarized first section only")
            print(summary)
            break
    if not args.test:
        _LOG.info("Total LLM cost: $%.6f", total_cost)
    _LOG.info("Summaries written to: %s", out_file_name)


if __name__ == "__main__":
    _main(_parse())
