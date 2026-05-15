#!/usr/bin/env -S uv run

# /// script
# dependencies = ["tabulate"]
# ///

r"""
Count words in a file and estimate reading time.

Examples:
> count_words.py -i input.txt
> count_words.py -i document.md
> count_words.py --input_files file1.md file2.md file3.md
> count_words.py --input_files "file1.md,file2.md,file3.md"
"""

import argparse
from typing import cast, Dict, List, Tuple

from tabulate import tabulate

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

WORDS_PER_MINUTE = 150


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input_file",
        type=str,
        required=False,
        help="Path to input file",
    )
    parser.add_argument(
        "--input_files",
        nargs="+",
        default=None,
        help="One or more files (space-separated) or comma-separated list",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _count_words_in_file(*, file_path: str) -> int:
    """
    Count the total number of words in a single file.

    :param file_path: Path to the file to count words from
    :return: Number of words in the file
    """
    hdbg.dassert_file_exists(file_path)
    content = hio.from_file(file_path)
    words = content.split()
    word_count = len(words)
    return word_count


def _count_words(*, file_paths: List[str]) -> Tuple[int, Dict[str, int]]:
    """
    Count the total number of words in one or more files.

    :param file_paths: List of paths to files to count words from
    :return: Tuple of (total word count, dict mapping file path to word count)
    """
    total_words = 0
    file_counts: Dict[str, int] = {}
    for file_path in file_paths:
        count = _count_words_in_file(file_path=file_path)
        file_counts[file_path] = count
        total_words += count
    return total_words, file_counts


def _format_reading_time(*, words: int) -> str:
    """
    Format word count as readable time (minutes or hours).

    :param words: Number of words
    :return: Formatted time string (e.g., "32.8m" or "7.17h")
    """
    minutes = words / WORDS_PER_MINUTE
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    return f"{hours:.2f}h"


def _build_table_data(*, file_counts: Dict[str, int], total_words: int
                     ) -> Tuple[List[List[str]], List[str]]:
    """
    Build table data with file counts and reading times.

    :param file_counts: Mapping of file path to word count
    :param total_words: Total number of words across all files
    :return: Tuple of (table rows, headers)
    """
    rows: List[List[str]] = []
    headers = ["File", "Words", "Reading Time"]
    for file_path, count in sorted(file_counts.items()):
        reading_time = _format_reading_time(words=count)
        rows.append([file_path, str(count), reading_time])
    reading_time_total = _format_reading_time(words=total_words)
    rows.append(["TOTAL", str(total_words), reading_time_total])
    return rows, headers


def _print_table(*, file_counts: Dict[str, int], total_words: int) -> None:
    """
    Print word counts and reading times as a formatted table.

    :param file_counts: Mapping of file path to word count
    :param total_words: Total number of words across all files
    """
    hdbg.dassert(file_counts, "No files to display")
    rows, headers = _build_table_data(file_counts=file_counts,
                                       total_words=total_words)
    table_str = tabulate(rows, headers=headers, tablefmt="simple")
    print(table_str)


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    files_to_process: List[str]
    if args.input_files:
        result = hparser.parse_input_output_files(args)
        hdbg.dassert(result is not None,
                     "parse_input_output_files returned None")
        files_to_process = cast(List[str], result)
    elif args.input_file:
        files_to_process = [args.input_file]
    else:
        parser.error("Either --input_file or --input_files must be specified")
    hdbg.dassert(files_to_process, "No files to process")
    total_words, file_counts = _count_words(file_paths=files_to_process)
    _print_table(file_counts=file_counts, total_words=total_words)


if __name__ == "__main__":
    _main(_parse())
