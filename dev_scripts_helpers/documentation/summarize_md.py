#!/usr/bin/env -S uv run

# /// script
# dependencies = ["llm", "tokencost", "markdown-it-py", "tqdm"]
# ///

r"""
Summarize markdown headers using an LLM.

The script reads a markdown file and, for each header at a specified level
(--md_level), extracts the full section (including all nested content) and
either sends it to an LLM for summarization.

Results are appended to the output file incrementally.

The output preserves the markdown header structure with summaries or digests.

Examples:
# Summarize all level-1 chapters with LLM
> summarize_md.py -i book.md -o book.summary.md --md_level 1

# Compute SHA1 digests instead of LLM summaries (for testing)
> summarize_md.py -i book.md -o book.digest.md --md_level 1 --test

# Summarize level-2 sections in a range
> summarize_md.py -i book.md -o out.md --md_level 2 --md_start "Chapter 1" --md_end "Chapter 2"

# Dry run: test with the first section only
> summarize_md.py -i book.md -o out.md --md_level 1 --dry_run

# Use a different LLM model
> summarize_md.py -i book.md -o out.md --md_level 1 --model "claude-3-opus"
"""

import argparse
import hashlib
import logging
import os
from typing import Dict, List, Optional, Tuple

from markdown_it import MarkdownIt
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hlint as hlint
import helpers.hllm_cli as hllmcli
import helpers.hmarkdown_headers as hmarhead
import helpers.hmarkdown_select as hmarsele
import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser
import helpers.hselect_action as hselacti
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

_VALID_ACTIONS = ["summarize", "lint"]
_DEFAULT_ACTIONS = ["summarize", "lint"]


def _get_system_prompt() -> str:
    """
    Build system prompt for LLM-based markdown summarization.

    Loads bullet point style rules and constructs a prompt that instructs the
    LLM to preserve markdown structure and chapter numbering.

    :return: System prompt string with formatting instructions and examples
    """
    rules_file = hgit.find_file_in_git_tree("text.rules.md")
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
    # TODO(ai_gp): use str = ""
    md_start: Optional[str],
    # TODO(ai_gp): use str = ""
    md_end: Optional[str],
) -> List[Tuple[int, str, int]]:
    """
    Filter headers by level and optional start/end boundaries.

    Selects headers at the specified level, optionally restricting the range
    to start from and end at specific headers (matched by prefix).

    :param all_headers: List of (level, title, line_number) tuples
    :param md_level: Header level to select (1=H1, 2=H2, etc.)
    :param md_start: Optional header prefix to start from; None means start from beginning
    :param md_end: Optional header prefix to end at; None means continue to end
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
    if md_start is not None:
        header_list = [
            hmarhead.HeaderInfo(h[0], h[1], h[2] + 1) for h in target_headers
        ]
        match = hmarsele.find_header_by_partial_title(header_list, md_start)
        hdbg.dassert_is_not(
            match, None, "No header matches --md_start: '%s'", md_start
        )
        start_idx = next(
            i for i, h in enumerate(target_headers) if h[1] == match.description
        )
        target_headers = target_headers[start_idx:]
    # Apply end boundary if specified: find matching header and slice up to there.
    if md_end is not None:
        header_list = [
            hmarhead.HeaderInfo(h[0], h[1], h[2] + 1) for h in target_headers
        ]
        match = hmarsele.find_header_by_partial_title(header_list, md_end)
        hdbg.dassert_is_not(
            match, None, "No header matches --md_end: '%s'", md_end
        )
        end_idx = next(
            i for i, h in enumerate(target_headers) if h[1] == match.description
        )
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


def _extract_intro_text(
    parent_header: Tuple[int, str, int],
    header: Tuple[int, str, int],
    lines: List[str],
) -> str:
    """
    Extract introductory text between a parent header and the first child header.

    Extracts content that appears after the parent header and before the given child header.

    :param parent_header: The (level, title, line_number) tuple for the parent header
    :param header: The (level, title, line_number) tuple for the child header
    :param lines: All markdown lines (0-indexed)
    :return: Introductory text (empty string if no intro text found)
    """
    # Start from the line after the parent header
    start_idx = parent_header[2] + 1
    # End at the child header
    end_idx = header[2]
    if start_idx >= end_idx:
        return ""
    intro_lines = lines[start_idx:end_idx]
    # Remove leading and trailing empty lines
    while intro_lines and intro_lines[0].strip() == "":
        intro_lines.pop(0)
    while intro_lines and intro_lines[-1].strip() == "":
        intro_lines.pop()
    intro_text = "\n".join(intro_lines)
    return intro_text.strip()


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


def _summarize_text(
    text: str,
    system_prompt: str,
    model: str,
    *,
    test_mode: bool,
) -> Tuple[str, float]:
    """
    Compute summary via LLM or SHA1 digest.

    :param text: Text to summarize
    :param system_prompt: System prompt for LLM
    :param model: LLM model name
    :param test_mode: If True, compute SHA1 digest; otherwise use LLM
    :return: Tuple of (summary_text, cost) where cost is 0 in test mode
    """
    if test_mode:
        digest = _compute_sha1_digest(text)
        summary, cost = f"SHA1: {digest}\n", 0.0
    else:
        summary, cost = hllmcli.apply_llm(
            input_str=text,
            system_prompt=system_prompt,
            model=model,
            backend="library",
        )
        _LOG.debug("LLM cost: $%.6f", cost)
    return summary, cost


def _prepare_output_file(
    in_file_name: str,
    # TODO(ai_gp): use str and use "" instead of None
    out_file_name: Optional[str],
    overwrite: bool,
) -> str:
    """
    Prepare output file path and handle existing file.

    Generates output filename if not provided, and manages existing files
    based on the overwrite flag.

    :param in_file_name: Input markdown file path
    :param out_file_name: Output file path (None = auto-generate)
    :param overwrite: Whether to overwrite existing output file
    :return: Path to output file
    """
    if out_file_name == in_file_name or out_file_name is None:
        if in_file_name.endswith(".md"):
            out_file_name = in_file_name[:-3] + ".summary.md"
        else:
            out_file_name = in_file_name + ".summary"
    if os.path.exists(out_file_name):
        if overwrite:
            os.remove(out_file_name)
            _LOG.info("Deleted existing output file: %s", out_file_name)
        else:
            raise ValueError(
                f"Output file already exists: {out_file_name} (use --overwrite to replace)"
            )
    return out_file_name


def _read_and_parse_markdown(
    in_file_name: str,
) -> Tuple[List[str], List[Tuple[int, str, int]]]:
    """
    Read markdown file and extract headers using AST parser.

    :param in_file_name: Path to markdown file
    :return: Tuple of (lines, headers) where headers are (level, title, line_number)
    """
    content = hio.from_file(in_file_name)
    lines = content.splitlines()
    _LOG.debug("Read %d lines from %s", len(lines), in_file_name)
    md_parser = MarkdownIt()
    tokens = md_parser.parse(content)
    all_headers = _extract_headers_from_ast(tokens)
    _LOG.debug("Extracted %d headers from input file", len(all_headers))
    return lines, all_headers


def _process_headers_for_summarization(
    target_headers: List[Tuple[int, str, int]],
    all_headers: List[Tuple[int, str, int]],
    lines: List[str],
    out_file_name: str,
    system_prompt: str,
    model: str,
    *,
    md_level: int,
    test_mode: bool,
    dry_run: bool,
) -> float:
    """
    Process and summarize target headers, writing results to output file.

    Iterates through target headers, extracts sections, generates summaries,
    and writes parent headers and summaries to the output file.

    :param target_headers: List of headers to summarize
    :param all_headers: All headers in the document
    :param lines: All markdown lines
    :param out_file_name: Output file path
    :param system_prompt: System prompt for LLM
    :param model: LLM model name
    :param md_level: Target header level
    :param test_mode: If True, compute SHA1 digest; otherwise use LLM
    :param dry_run: If True, summarize only first section
    :return: Total cost of LLM calls
    """
    with open(out_file_name, "w") as f:
        pass
    total_cost = 0.0
    written_headers: Dict[Tuple[int, str], bool] = {}
    pbar = tqdm(target_headers, desc="Summarizing sections")
    for header in pbar:
        parent_headers = _get_parent_headers(
            header, all_headers, md_level=md_level
        )
        with open(out_file_name, "a") as f:
            for parent in parent_headers:
                parent_key = (parent[0], parent[1])
                if parent_key not in written_headers:
                    f.write("#" * parent[0] + " " + parent[1])
                    f.write("\n\n")
                    written_headers[parent_key] = True
                    intro_text = _extract_intro_text(parent, header, lines)
                    if intro_text:
                        intro_summary, intro_cost = _summarize_text(
                            intro_text,
                            system_prompt,
                            model,
                            test_mode=test_mode,
                        )
                        total_cost += intro_cost
                        pbar.set_postfix_str(f"Cost: ${total_cost:.4f}")
                        f.write(intro_summary)
                        f.write("\n\n")
            header_key = (header[0], header[1])
            f.write("#" * header[0] + " " + header[1])
            f.write("\n\n")
            written_headers[header_key] = True
        section_text = _extract_section(
            header, all_headers, lines, md_level=md_level
        )
        _LOG.debug(
            "Extracted section for header: %s",
            header[1],
        )
        summary, cost = _summarize_text(
            section_text,
            system_prompt,
            model,
            test_mode=test_mode,
        )
        total_cost += cost
        pbar.set_postfix_str(f"Cost: ${total_cost:.4f}")
        with open(out_file_name, "a") as f:
            f.write(summary)
            f.write("\n\n")
        if dry_run:
            _LOG.info("Dry run: summarized first section only")
            print(summary)
            break
    return total_cost


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hseinout.add_input_output_args(parser, out_required=False)
    parser.add_argument(
        "--md_level",
        type=int,
        default=1,
        help="Header level to summarize (1=H1, 2=H2, etc.; default: 1)",
    )
    hmarsele.add_select_arg(parser, required=False)
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="LLM model to use (default: gpt-4o-mini)",
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
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete target file if it already exists",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to summarize markdown sections or lint with prettier.

    Summarizes sections using LLM by default, or computes SHA1 digests if
    `--test` flag is enabled. With --action lint, formats the file using prettier.
    """
    args = parser.parse_args()
    hparser.parse_verbosity_args(args)
    in_file_name, out_file_name = hseinout.parse_input_output_args(args)
    hdbg.dassert_file_exists(in_file_name, "Input markdown file must exist")
    #
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info(
        "Actions selected:\n%s",
        hselacti.actions_to_string(actions, _VALID_ACTIONS, add_frame=True),
    )
    # Handle summarize action.
    to_summarize, actions = hselacti.mark_action("summarize", actions)
    if to_summarize:
        hdbg.dassert(args.md_level >= 1, "--md_level must be >= 1")
        out_file_name = _prepare_output_file(
            in_file_name, out_file_name, args.overwrite
        )
        lines, all_headers = _read_and_parse_markdown(in_file_name)
        md_start = None
        md_end = None
        if args.select:
            md_start, md_end = hmarsele.parse_select_arg(args.select)
        target_headers = _get_target_headers(
            all_headers,
            md_level=args.md_level,
            md_start=md_start,
            md_end=md_end,
        )
        _LOG.info(
            "Processing %d headers at level %d",
            len(target_headers),
            args.md_level,
        )
        print("\nHeaders to summarize:")
        for i, header in enumerate(target_headers, 1):
            level, title, _ = header
            indent = "  " * (level - 1)
            print(f"{indent}{i}. {title}")
        system_prompt = _get_system_prompt()
        total_cost = _process_headers_for_summarization(
            target_headers,
            all_headers,
            lines,
            out_file_name,
            system_prompt,
            args.model,
            md_level=args.md_level,
            test_mode=args.test,
            dry_run=args.dry_run,
        )
        if not args.test:
            _LOG.info("Total LLM cost: $%.6f", total_cost)
        _LOG.info("Summaries written to: %s", out_file_name)
    # Handle lint action after summarization and process the output file.
    to_lint, actions = hselacti.mark_action("lint", actions)
    if to_lint and not args.test:
        hlint.lint_file(out_file_name)
        _LOG.info("Linting complete: %s", out_file_name)


if __name__ == "__main__":
    _main(_parse())
