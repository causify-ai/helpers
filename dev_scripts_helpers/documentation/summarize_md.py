#!/usr/bin/env -S uv run

# /// script
# dependencies = ["llm", "tokencost", "markdown-it-py", "tqdm"]
# ///

r"""
Summarize markdown text using an LLM.

The script:
- reads a markdown file
- prints file statistics (word count, read time, header levels)
- for each header at a specified level (--md_level) extracts the full section
  (including all nested content)
- uses an LLM for summarization
- by default compresses each section to 10% of original size (--pct_words 0.1)

Results are appended to the output file incrementally.

The output preserves the markdown header structure with summaries or digests.

# Usage Example

- Summarize all level-1 chapters (default: 10% compression):
> summarize_md.py -i book.md -o book.summary.md --md_level 1

- Summarize entire file in one shot (default: 10% compression):
> summarize_md.py -i book.md -o out.md --md_level 0

- Summarize with max words per chunk (disable default compression):
> summarize_md.py -i book.md -o out.md --md_level 1 --max_words 500

- Summarize to 5% of original size (custom compression):
> summarize_md.py -i book.md -o out.md --md_level 1 --pct_words 0.05

- Summarize level-2 sections in a range (default: 10% compression):
> summarize_md.py -i book.md -o out.md --md_level 2 --md_start "Chapter 1" --md_end "Chapter 2"

- Dry run: test with the first section only (default: 10% compression):
> summarize_md.py -i book.md -o out.md --md_level 1 --dry_run

- Use a different LLM model (default: 10% compression):
> summarize_md.py -i book.md -o out.md --md_level 1 --model "claude-3-opus"

- Compute SHA1 digests instead of LLM summaries (for testing):
> summarize_md.py -i book.md -o book.digest.md --md_level 1 --test
"""

import argparse
import hashlib
import logging
import os
from typing import Dict, List, Tuple

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
_AVG_WORDS_PER_MINUTE = 250


# #############################################################################
# Statistics
# #############################################################################


def _count_words(text: str) -> int:
    """
    Count words in text.

    :param text: Input text to count
    :return: Number of words
    """
    words = text.split()
    return len(words)


def _estimate_read_time(num_words: int) -> float:
    """
    Estimate read time in minutes.

    Assumes ~250 words per minute for average reader.

    :param num_words: Number of words in text
    :return: Estimated read time in minutes
    """
    read_time = num_words / _AVG_WORDS_PER_MINUTE
    return read_time


def _calculate_compression_rate(
    original_words: int, summarized_words: int
) -> float:
    """
    Calculate compression rate as percentage reduction.

    :param original_words: Number of words in original text
    :param summarized_words: Number of words in summarized text
    :return: Compression rate as percentage (e.g., 0.5 = 50% reduction)
    """
    if original_words == 0:
        return 0.0
    compression = (original_words - summarized_words) / original_words
    return compression


# #############################################################################
# System Prompt and Hashing
# #############################################################################


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


# #############################################################################
# Markdown Parsing and Header Extraction
# #############################################################################


def _extract_headers_from_ast(
    tokens: List,
) -> List[Tuple[int, str, int]]:
    """
    Extract headers from markdown-it-py AST tokens.

    Scans tokens for heading_open blocks and extracts level, title, and line
    number.

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


# #############################################################################
# Header Selection and Section Extraction
# #############################################################################


def _get_target_headers(
    all_headers: List[Tuple[int, str, int]],
    *,
    md_level: int,
    md_start: str = "",
    md_end: str = "",
) -> List[Tuple[int, str, int]]:
    """
    Filter headers by level and optional start/end boundaries.

    Selects headers at the specified level, optionally restricting the range
    to start from and end at specific headers (matched by prefix).

    When md_level is 0 or -1, treats entire file as one section (synthetic header).

    :param all_headers: List of (level, title, line_number) tuples
    :param md_level: Header level to select (1=H1, 2=H2, etc.; 0/-1=entire file)
    :param md_start: Optional header prefix to start from; ignored for entire file
    :param md_end: Optional header prefix to end at; ignored for entire file
    :return: Filtered list of headers at the specified level within the range
    """
    if md_level <= 0:
        return [(0, "Entire Document", 0)]
    target_headers = [h for h in all_headers if h[0] == md_level]
    hdbg.dassert(
        target_headers,
        "No headers found at level %d. Available levels: %s",
        md_level,
        sorted(set(h[0] for h in all_headers)),
    )
    # Apply start boundary if specified: find matching header and slice from there.
    if md_start != "":
        header_list = [
            hmarhead.HeaderInfo(h[0], h[1], h[2] + 1) for h in target_headers
        ]
        match = hmarsele.find_header_by_partial_title(header_list, md_start)
        hdbg.dassert_is_not(
            match, None, "No header matches --md_start: '%s'", md_start
        )
        if match is not None:
            start_idx = next(
                i
                for i, h in enumerate(target_headers)
                if h[1] == match.description
            )
            target_headers = target_headers[start_idx:]
    # Apply end boundary if specified: find matching header and slice up to there.
    if md_end != "":
        header_list = [
            hmarhead.HeaderInfo(h[0], h[1], h[2] + 1) for h in target_headers
        ]
        match = hmarsele.find_header_by_partial_title(header_list, md_end)
        hdbg.dassert_is_not(
            match, None, "No header matches --md_end: '%s'", md_end
        )
        if match is not None:
            end_idx = next(
                i
                for i, h in enumerate(target_headers)
                if h[1] == match.description
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

    For md_level=0/-1 (entire document), returns all lines.

    :param header: The (level, title, line_number) tuple for the header
    :param all_headers: List of all (level, title, line_number) tuples
    :param lines: All markdown lines (0-indexed)
    :param md_level: The target header level (used to find end boundary; 0/-1 = all)
    :return: Section content as a string (trailing empty lines removed)
    """
    if md_level <= 0:
        section_lines = lines[:]
    else:
        start_idx = header[2]
        header_pos = -1
        for i, h in enumerate(all_headers):
            if h[2] == header[2]:
                header_pos = i
                break
        hdbg.dassert_ne(header_pos, -1, "Header position not found")
        next_header_line = None
        for i in range(header_pos + 1, len(all_headers)):
            if all_headers[i][0] <= md_level:
                next_header_line = all_headers[i][2]
                break
        if next_header_line is None:
            end_idx = len(lines)
        else:
            end_idx = next_header_line
        section_lines = lines[start_idx:end_idx]
    while section_lines and section_lines[-1].strip() == "":
        section_lines.pop()
    section_text = "\n".join(section_lines)
    return section_text


# #############################################################################
# Text Truncation
# #############################################################################


def _truncate_text_by_words(text: str, max_words: int) -> str:
    """
    Truncate text to maximum word count.

    :param text: Text to truncate
    :param max_words: Maximum number of words to keep
    :return: Truncated text (or original if smaller than max_words)
    """
    if max_words <= 0:
        return text
    words = text.split()
    if len(words) <= max_words:
        return text
    truncated_words = words[:max_words]
    return " ".join(truncated_words)


def _truncate_text_by_factor(text: str, pct_words: float) -> str:
    """
    Truncate text to a percentage of original size.

    :param text: Text to truncate
    :param pct_words: Target size as fraction (e.g., 0.1 = 10% of original)
    :return: Truncated text
    """
    if pct_words <= 0:
        return text
    words = text.split()
    max_words = max(1, int(len(words) * pct_words))
    return _truncate_text_by_words(text, max_words)


# #############################################################################
# Summarization and Output Preparation
# #############################################################################


def _summarize_text(
    text: str,
    system_prompt: str,
    model: str,
    *,
    test_mode: bool,
    max_words: int = 0,
    pct_words: float = 0.0,
) -> Tuple[str, float]:
    """
    Compute summary via LLM or SHA1 digest.

    Optionally truncates text to max_words or pct_words before summarization.

    :param text: Text to summarize
    :param system_prompt: System prompt for LLM
    :param model: LLM model name
    :param test_mode: If True, compute SHA1 digest; otherwise use LLM
    :param max_words: Maximum words to include in summary (0 = no limit)
    :param pct_words: Compression factor (e.g., 0.1 = 10% of original; 0.0 = no limit)
    :return: Tuple of (summary_text, cost) where cost is 0 in test mode
    """
    truncated_text = text
    if max_words > 0:
        truncated_text = _truncate_text_by_words(text, max_words)
    elif pct_words > 0.0:
        truncated_text = _truncate_text_by_factor(text, pct_words)
    if test_mode:
        digest = _compute_sha1_digest(truncated_text)
        summary, cost = f"SHA1: {digest}\n", 0.0
    else:
        summary, cost_stats = hllmcli.apply_llm(
            input_str=truncated_text,
            system_prompt=system_prompt,
            model=model,
            backend="library",
        )
        cost = cost_stats.to_float()
        _LOG.debug("LLM cost: $%.6f", cost)
    return summary, cost


def _prepare_output_file(
    in_file_name: str,
    out_file_name: str = "",
    overwrite: bool = False,
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
    if out_file_name == in_file_name or out_file_name == "":
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


# #############################################################################
# File Processing and Summarization Execution
# #############################################################################


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
    max_words: int = 0,
    pct_words: float = 0.0,
) -> Tuple[float, int]:
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
    :param max_words: Maximum words per summarization chunk (0 = no limit)
    :param pct_words: Compression factor (e.g., 0.1; 0.0 = no limit)
    :return: Tuple of (total_cost, summarized_words)
    """
    with open(out_file_name, "w") as f:
        pass
    total_cost = 0.0
    summarized_words = 0
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
                            max_words=max_words,
                            pct_words=pct_words,
                        )
                        total_cost += intro_cost
                        summarized_words += _count_words(intro_summary)
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
            max_words=max_words,
            pct_words=pct_words,
        )
        total_cost += cost
        summarized_words += _count_words(summary)
        pbar.set_postfix_str(f"Cost: ${total_cost:.4f}")
        with open(out_file_name, "a") as f:
            f.write(summary)
            f.write("\n\n")
        if dry_run:
            _LOG.info("Dry run: summarized first section only")
            print(summary)
            break
    return total_cost, summarized_words


# #############################################################################
# CLI and Entry Points
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hseinout.add_input_output_args(parser, out_required=False)
    parser.add_argument(
        "--md_level",
        type=int,
        default=1,
        help="Header level to summarize (1=H1, 2=H2, etc.; 0=entire file)",
    )
    hmarsele.add_select_arg(parser, required=False)
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="LLM model to use",
    )
    limit_group = parser.add_mutually_exclusive_group()
    limit_group.add_argument(
        "--max_words",
        type=int,
        default=0,
        help="Maximum words per summarization chunk",
    )
    limit_group.add_argument(
        "--pct_words",
        type=float,
        default=0.1,
        help="Compression factor (e.g., 0.1 = reduce to 10 percent of original)",
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
    while actions:
        action = actions[0]
        to_execute, actions = hselacti.mark_action(action, actions)
        if not to_execute:
            continue
        if action == "summarize":
            # TODO(ai_gp): Factor out in a function.
            hdbg.dassert_lte(-1, args.md_level, "--md_level must be >= -1")
            out_file_name = _prepare_output_file(
                in_file_name, out_file_name, args.overwrite
            )
            lines, all_headers = _read_and_parse_markdown(in_file_name)
            content = hio.from_file(in_file_name)
            input_word_count = _count_words(content)
            read_time = _estimate_read_time(input_word_count)
            print("\n=== Input File Statistics ===")
            print(f"Word count: {input_word_count}")
            print(f"Estimated read time: {read_time:.1f} minutes")
            print(f"Header level: {args.md_level}")
            if args.max_words > 0:
                print(f"Max words per chunk: {args.max_words}")
            elif args.pct_words > 0.0:
                print(f"Compression factor: {args.pct_words:.1%}")
            md_start = ""
            md_end = ""
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
            for header in target_headers:
                level, title, _ = header
                header_mark = "#" * level
                print(f"{header_mark} {title}")
            system_prompt = _get_system_prompt()
            total_cost, summarized_words = _process_headers_for_summarization(
                target_headers,
                all_headers,
                lines,
                out_file_name,
                system_prompt,
                args.model,
                md_level=args.md_level,
                test_mode=args.test,
                dry_run=args.dry_run,
                max_words=args.max_words,
                pct_words=args.pct_words,
            )
            if not args.test:
                _LOG.info("Total LLM cost: $%.6f", total_cost)
            compression_rate = _calculate_compression_rate(
                input_word_count, summarized_words
            )
            output_read_time = _estimate_read_time(summarized_words)
            print("\n=== Output Summary Statistics ===")
            print(f"Summarized word count: {summarized_words}")
            print(f"Estimated read time: {output_read_time:.1f} minutes")
            print(f"Compression rate: {compression_rate * 100:.1f}%")
            _LOG.info("Summaries written to: %s", out_file_name)
        elif action == "lint":
            if not args.test:
                hlint.lint_file(out_file_name)
                _LOG.info("Linting complete: %s", out_file_name)
        else:
            raise ValueError(f"Invalid action='{action}'")
    hdbg.dassert_eq(
        len(actions), 0, "There are unprocessed actions: %s", str(actions)
    )


if __name__ == "__main__":
    _main(_parse())
