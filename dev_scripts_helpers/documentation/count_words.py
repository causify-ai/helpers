#!/usr/bin/env python

"""
Count words in a file and estimate reading time.

Examples:
    python count_words.py -i input.txt
    python count_words.py -i document.md
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# Words per minute for reading time calculation.
WORDS_PER_MINUTE = 150


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input_file",
        type=str,
        required=True,
        help="Path to input file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _count_words(file_path: str) -> int:
    """
    Count the total number of words in a file.

    :param file_path: path to the file to count words from
    :return: number of words in the file
    """
    hdbg.dassert_file_exists(file_path)
    content = hio.from_file(file_path)
    words = content.split()
    word_count = len(words)
    return word_count


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Count words and calculate reading time.
    word_count = _count_words(args.input_file)
    reading_minutes = word_count / WORDS_PER_MINUTE
    reading_hours = reading_minutes / 60
    # Print results.
    _LOG.info("Word count: %d", word_count)
    _LOG.info(
        "Estimated reading time: %.1f minutes (%.2f hours)",
        reading_minutes,
        reading_hours,
    )


if __name__ == "__main__":
    _main(_parse())
