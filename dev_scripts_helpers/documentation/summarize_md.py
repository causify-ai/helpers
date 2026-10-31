#!/usr/bin/env -S uv run

# /// script
# dependencies = ["llm", "llm-openrouter", "tokencost", "markdown-it-py", "tqdm"]
# ///

r"""
Summarize the sections of a markdown file using an LLM.

- Split the file in sections at the header level `--md_level`
- Ask the LLM to shrink each section to `--pct_words` of its size (default: 10%)
- Write the summaries to the output file, keeping the header structure

- See documentation in `dev_scripts_helpers/documentation/summarize_md.py`
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
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hselect_action as hselacti
import helpers.hselect_input_output as hseinout

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


_KEEP_BULLETS_PROMPT = r"""
Structure rules, which override the rules above on how to organize the summary:
- Keep every sub-header, bullet, and sub-bullet of the text, with the same
  marker, nesting, and order
- Print each sub-header as a header line with the same `#` marks, never as a
  bullet
- Do not add, delete, merge, split, or reorder any header or bullet
- Copy tables and code blocks unchanged
- Shorten only the text of each bullet
- Drop words from every bullet, by about the ratio of the length rule, not only
  from some bullets
"""

_CAVEMAN_PROMPT = r"""
Style rules: write terse, like a caveman.
- Drop articles (a, an, the), filler, hedging, pleasantries, and restatements
- Do not write "I'd recommend", "likely", "it seems", or similar phrases
- Fragments are OK
- Keep technical terms, names, numbers, and code exact
- Write one idea per sentence
- Join a cause and its fix with `:`
- Stop when the content is complete
- Example
  - Bad: "The reason your React component is re-rendering is likely because
    you're creating a new object reference on each render cycle. I'd
    recommend using useMemo to memoize the object."
  - Good: "New object ref each render: React re-renders. Wrap prop in useMemo."
"""


def _get_system_prompt(
    *, keep_bullets: bool = False, caveman: bool = False
) -> str:
    """
    Build system prompt for LLM-based markdown summarization.

    Loads bullet point style rules and constructs a prompt that instructs the
    LLM to preserve markdown structure and chapter numbering.

    :param keep_bullets: if True, ask the LLM to keep every header and bullet
        and to shorten only the text of each bullet
    :param caveman: if True, ask the LLM to write terse, dropping articles
        and filler
    :return: System prompt string with formatting instructions and examples
    """
    rules_file = hgit.find_file_in_git_tree("text.rules.md")
    rules_content = hio.from_file(rules_file)
    task = "Write a summary in bullet points"
    if keep_bullets:
        task = "Shorten the text, keeping its bullet points"
    system_prompt = f"""
    {task} using the following rules from the style guide:
    {rules_content}
    """
    system_prompt = hprint.dedent(system_prompt)
    if keep_bullets:
        system_prompt += "\n" + hprint.dedent(_KEEP_BULLETS_PROMPT)
    if caveman:
        system_prompt += "\n" + hprint.dedent(_CAVEMAN_PROMPT)
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
        sorted({h[0] for h in all_headers}),
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
# Length Constraint
# #############################################################################


def _get_max_words_out(text: str, *, max_words: int, pct_words: float) -> int:
    """
    Compute the max number of words allowed in the summary of a text.

    :param text: Text to summarize
    :param max_words: Max words of the summary (0 = not set)
    :param pct_words: Max words of the summary as fraction of the words of
        `text` (e.g., 0.1 = 10%; 0.0 = not set)
    :return: Max number of words of the summary, or 0 if no limit is set
    """
    if max_words > 0:
        return max_words
    if pct_words > 0.0:
        return max(1, int(_count_words(text) * pct_words))
    return 0


def _get_length_constraint(max_words_out: int, num_words_in: int) -> str:
    """
    Build the part of the LLM prompt that limits the length of the summary.

    The text to summarize is never truncated: the LLM reads all of it and must
    fit the summary in the limit.

    :param max_words_out: Max number of words of the summary (0 = no limit)
    :param num_words_in: Number of words of the text to summarize
    :return: Prompt text, or empty string if no limit is set
    """
    if max_words_out <= 0:
        return ""
    constraint = f"""
    Length rule:
    - The text has {num_words_in} words
    - The summary must have at most {max_words_out} words, which is {max_words_out / max(1, num_words_in):.0%} of the text
    - Cover the whole text, from the first line to the last, within this limit
    - Drop details to meet the limit, not whole parts of the text
    """
    constraint = "\n" + hprint.dedent(constraint)
    return constraint


# #############################################################################
# Summarization and Output Preparation
# #############################################################################


def _remove_section_header(section_text: str) -> str:
    """
    Remove the header line from the text of a section.

    The header is written to the output file separately. The LLM must not see
    it, since it can merge it with the first sub-header and drop both.

    :param section_text: Text of a section, starting with its header line
    :return: Text of the section without the header line
    """
    lines = section_text.split("\n")[1:]
    text = "\n".join(lines).lstrip("\n")
    return text


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

    `max_words` and `pct_words` are constraints added to the prompt of the LLM.
    Neither the text nor the summary is truncated.

    :param text: Text to summarize
    :param system_prompt: System prompt for LLM
    :param model: LLM model name
    :param test_mode: If True, compute SHA1 digest; otherwise use LLM
    :param max_words: Max words of the summary (0 = no limit)
    :param pct_words: Max words of the summary as fraction of the words of
        `text` (e.g., 0.1 = 10%; 0.0 = no limit)
    :return: Tuple of (summary_text, cost) where cost is 0 in test mode
    """
    if test_mode:
        digest = _compute_sha1_digest(text)
        summary, cost = f"SHA1: {digest}\n", 0.0
    elif not text.strip():
        # Nothing to summarize: do not call the LLM.
        summary, cost = "", 0.0
    else:
        # Tell the LLM the length limit in the prompt, without cutting the text.
        max_words_out = _get_max_words_out(
            text, max_words=max_words, pct_words=pct_words
        )
        system_prompt += _get_length_constraint(
            max_words_out, _count_words(text)
        )
        summary, cost_stats = hllmcli.apply_llm(
            input_str=text,
            system_prompt=system_prompt,
            model=model,
            backend="library",
        )
        cost = cost_stats.to_float()
        _LOG.debug("LLM cost: $%.6f", cost)
        # The LLM can ignore the limit: warn but do not truncate the summary.
        num_words_out = _count_words(summary)
        if 0 < max_words_out < num_words_out:
            _LOG.warning(
                "The LLM ignored the length rule: '%d' words instead of at most '%d'",
                num_words_out,
                max_words_out,
            )
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
    :param max_words: Max words of the summary of each chunk (0 = no limit)
    :param pct_words: Max words of the summary of each chunk as fraction of
        the chunk words (e.g., 0.1; 0.0 = no limit)
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
        if md_level > 0 and not test_mode:
            # The header is already written to the file: do not send it.
            section_text = _remove_section_header(section_text)
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
        default=hllmcli.DEFAULT_MODEL,
        help="LLM model to use",
    )
    limit_group = parser.add_mutually_exclusive_group()
    limit_group.add_argument(
        "--max_words",
        type=int,
        default=0,
        help="Max words of the summary of each chunk (limit written in the LLM prompt)",
    )
    limit_group.add_argument(
        "--pct_words",
        type=float,
        default=0.1,
        help="Target size of the summary of each chunk, as fraction of the chunk words (e.g., 0.1 = 10 percent). It is written in the LLM prompt",
    )
    parser.add_argument(
        "--keep_bullets",
        action="store_true",
        help="Ask the LLM to keep every header and bullet, shortening only the text of each bullet",
    )
    parser.add_argument(
        "--caveman",
        action="store_true",
        help="Ask the LLM to write terse, dropping articles, filler, and hedging",
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


def _run_summarize_action(
    args: argparse.Namespace, in_file_name: str, out_file_name: str
) -> str:
    """
    Run the "summarize" action: extract, summarize, and write each target
    header's section.

    :param args: parsed command-line arguments
    :param in_file_name: path to the input markdown file
    :param out_file_name: requested output file path (auto-generated if
        empty)
    :return: the resolved output file path that was written to
    """
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
        print(f"Max words per summary: {args.max_words}")
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
    system_prompt = _get_system_prompt(
        keep_bullets=args.keep_bullets, caveman=args.caveman
    )
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
    return out_file_name


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to summarize markdown sections or lint with prettier.

    Summarizes sections using LLM by default, or computes SHA1 digests if
    `--test` flag is enabled. With --clear_actions --action lint, formats the
    file using prettier only.
    """
    args = parser.parse_args()
    hparser.parse_verbosity_args(args)
    in_file_name, out_file_name = hseinout.parse_input_output_args(args)
    hdbg.dassert_file_exists(in_file_name, "Input markdown file must exist")
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
            out_file_name = _run_summarize_action(
                args, in_file_name, out_file_name
            )
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
