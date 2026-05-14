#!/usr/bin/env python3

r"""
Summarize markdown headers using an LLM.

The script reads a markdown file and, for each header at a specified level
(--md_level), extracts the full section (including all nested content) and
sends it to an LLM for summarization. Results are appended to the output
file incrementally.

The output preserves the markdown header structure with bullet-point summaries.

Examples:
# Summarize all level-1 chapters
> ./summarize_md.py -i book.md -o book.summary.md --md_level 1

# Summarize level-2 sections in a range
> ./summarize_md.py -i book.md -o out.md --md_level 2 --start "Chapter 1" --end "Chapter 2"

# Dry run: test with the first section only
> ./summarize_md.py -i book.md -o out.md --md_level 1 --dry_run

# Use a different LLM model
> ./summarize_md.py -i book.md -o out.md --md_level 1 --model "claude-3-opus"
"""

import argparse
import logging
from typing import List, Optional, Tuple

from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hmarkdown_headers as hmarhead
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _get_system_prompt() -> str:
    rules_file = hgit.find_file_in_git_tree("text.rules.bullet_points.md")
    rules_content = hio.from_file(rules_file)
    system_prompt = f"""
    # Keep the same structure

    - Use the same structure of the chapter and subchapter in markdown headers
      - Use numbers of chapter (e.g., 1.) and subchapters (e.g., 1.1)
      - Use the chapter numbers that come from the document

    # Bullet point rules

    Write a summary in bullet points using the following rules from the style guide:
    {rules_content}

    # Example

    An example of the output is:

    ```
    # 1. Hello

    ## 1.1. Hello world

    - Point
      - Subpoint
      - Subpoint
    - Point

    ## 1.2. Good bye world

    # 2. Hello again
    ```
    """
    system_prompt = hprint.dedent(system_prompt)
    return system_prompt


def _get_target_headers(
    all_headers: hmarhead.HeaderList,
    *,
    md_level: int,
    start: Optional[str],
    end: Optional[str],
) -> hmarhead.HeaderList:
    target_headers = [h for h in all_headers if h.level == md_level]
    if not target_headers:
        raise ValueError(
            f"No headers found at level {md_level}. "
            f"Available levels: {sorted(set(h.level for h in all_headers))}"
        )
    if start is not None:
        start_idx = -1
        for i, h in enumerate(target_headers):
            if h.description.startswith(start):
                start_idx = i
                break
        hdbg.dassert_ne(start_idx, -1, "No header matches --start: '%s'", start)
        target_headers = target_headers[start_idx:]
    if end is not None:
        end_idx = -1
        for i, h in enumerate(target_headers):
            if h.description.startswith(end):
                end_idx = i
                break
        hdbg.dassert_ne(end_idx, -1, "No header matches --end: '%s'", end)
        target_headers = target_headers[: end_idx + 1]
    return target_headers


def _extract_section(
    header: hmarhead.HeaderInfo,
    all_headers: hmarhead.HeaderList,
    lines: List[str],
    *,
    md_level: int,
) -> List[str]:
    start_idx = header.line_number - 1
    header_pos = -1
    for i, h in enumerate(all_headers):
        if h.line_number == header.line_number:
            header_pos = i
            break
    hdbg.dassert_ne(header_pos, -1, "Header position not found")
    next_header_line = None
    for i in range(header_pos + 1, len(all_headers)):
        if all_headers[i].level <= md_level:
            next_header_line = all_headers[i].line_number - 1
            break
    if next_header_line is None:
        end_idx = len(lines)
    else:
        end_idx = next_header_line
    section_lines = lines[start_idx:end_idx]
    while section_lines and section_lines[-1].strip() == "":
        section_lines.pop()
    return section_lines


def _summarize_section(
    section_lines: List[str],
    system_prompt: str,
    *,
    model: str,
    use_llm_executable: bool,
) -> Tuple[str, float]:
    input_str = "\n".join(section_lines)
    result, cost = hllmcli.apply_llm(
        input_str=input_str,
        system_prompt=system_prompt,
        model=model,
        use_llm_executable=use_llm_executable,
    )
    return result, cost


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(parser)
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
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hparser.parse_verbosity_args(args)
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    hdbg.dassert_file_exists(in_file_name)
    hdbg.dassert(args.md_level >= 1, "--md_level must be >= 1")
    lines = hparser.from_file(in_file_name)
    _LOG.debug("Read %d lines from %s", len(lines), in_file_name)
    all_headers = hmarhead.extract_headers_from_markdown(
        lines, max_level=10, sanity_check=False
    )
    _LOG.debug("Extracted %d headers from input file", len(all_headers))
    target_headers = _get_target_headers(
        all_headers, md_level=args.md_level, start=args.start, end=args.end
    )
    _LOG.info("Processing %d headers at level %d", len(target_headers), args.md_level)
    system_prompt = _get_system_prompt()
    with open(out_file_name, "w") as f:
        pass
    total_cost = 0.0
    for header in tqdm(target_headers, desc="Summarizing sections"):
        section_lines = _extract_section(
            header, all_headers, lines, md_level=args.md_level
        )
        _LOG.debug(
            "Extracted %d lines for header: %s", len(section_lines), header.description
        )
        summary, cost = _summarize_section(
            section_lines,
            system_prompt,
            model=args.model,
            use_llm_executable=args.use_llm_executable,
        )
        total_cost += cost
        _LOG.debug("LLM cost: $%.6f", cost)
        with open(out_file_name, "a") as f:
            f.write(summary)
            f.write("\n\n")
        if args.dry_run:
            _LOG.info("Dry run: summarized first section only")
            print(summary)
            break
    _LOG.info("Total LLM cost: $%.6f", total_cost)
    _LOG.info("Summaries written to: %s", out_file_name)


if __name__ == "__main__":
    _main(_parse())
