#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pandas", "tabulate"]
# ///
"""
Convert markdown tables, CSV, and TSV formats.

Supports file I/O and stdin/stdout with mode specification.

Example:
# CSV to markdown
> convert_table.py -i table.csv -o table.md

# TSV to CSV
> convert_table.py -i table.tsv -o table.csv

# stdin to stdout with mode flags
> convert_table.py -i - -o - --input_mode md --output_mode csv

# Copy to clipboard
> convert_table.py -i table.csv --output_mode md --pbcopy

Import as:

import dev_scripts_helpers.documentation.convert_table as dsdccotbl
"""

# NOTE: `tabulate` dependency
# The _format_as_md() function uses pandas.DataFrame.to_markdown(), which requires
# the `tabulate` package. If tabulate is not available in the environment (e.g.,
# the dev container), tests that use markdown formatting will be skipped.
#
# To resolve this, choose one of:
# 1. Test the executable directly (preferred): The script uses the uv runner with
#    tabulate in dependencies, so the executable works even if the unit tests skip
# 2. Add tabulate to the container: Install tabulate in the Docker container/CI
#    environment used for running unit tests
# 3. Refactor to not rely on tabulate: Implement markdown formatting without
#    `pandas.to_markdown()` to reduce external dependencies

import argparse
import csv
import io
from typing import List, Tuple

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser
import helpers.hsystem as hsystem


def _detect_mode(file_name: str) -> str:
    """
    Detect table format from file extension.
    """
    hdbg.dassert_ne(file_name, "-")
    if file_name.endswith(".md"):
        res = "md"
    elif file_name.endswith(".csv"):
        res = "csv"
    elif file_name.endswith(".tsv"):
        res = "tsv"
    else:
        raise ValueError(f"Invalid mode for file_name='{file_name}'")
    return res


def _parse_md_table(
    lines: List[str],
) -> Tuple[List[str], List[List[str]]]:
    """
    Parse markdown table from lines using pandas.

    Expected format:
      | header1 | header2 |
      |---------|---------|
      | val1    | val2    |

    :return: tuple of (header_row, data_rows)
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_lt(0, len(lines), "Input table is empty")
    # Convert the markdown table into a CSV.
    start_idx = 0
    sep_idx = None
    for i, line in enumerate(lines):
        if "|" in line and line.strip():
            start_idx = i
            break
    hdbg.dassert_lte(0, start_idx, "No markdown table found in input")
    hdbg.dassert_lt(
        start_idx + 1, len(lines), "Markdown table has no separator row"
    )
    sep_line = lines[start_idx + 1].strip()
    hdbg.dassert_in("|", sep_line, "Expected separator row")
    hdbg.dassert_in("-", sep_line, "Expected separator row")
    sep_idx = start_idx + 1
    filtered_lines = [lines[start_idx]] + lines[sep_idx + 1 :]
    txt = "\n".join(filtered_lines)
    # Parse.
    df = pd.read_csv(
        io.StringIO(txt), sep="|", engine="python", skipinitialspace=True
    )
    df = df.dropna(axis=1, how="all")
    df.columns = df.columns.str.strip()
    header = list(df.columns)
    df = df.fillna("").astype(str).applymap(str.strip)
    rows = df.values.tolist()
    return header, rows


def _parse_delimited(
    lines: List[str], delimiter: str
) -> Tuple[List[str], List[List[str]]]:
    """
    Parse CSV or TSV from lines.

    :param lines: input lines
    :param delimiter: field delimiter (comma for CSV, tab for TSV)
    :return: tuple of (header_row, data_rows)
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_lt(0, len(lines), "Input table is empty")
    # Join lines and parse as CSV.
    txt = "\n".join(lines)
    reader = csv.reader(txt.split("\n"), delimiter=delimiter)
    rows_list = list(reader)
    # First row is header.
    hdbg.dassert_lt(0, len(rows_list), "CSV/TSV has no rows")
    header = rows_list[0]
    data_rows = rows_list[1:]
    # Remove trailing empty rows.
    while data_rows and not any(data_rows[-1]):
        data_rows.pop()
    return header, data_rows


# #############################################################################


def _format_as_md(header: List[str], rows: List[List[str]]) -> str:
    """
    Format table as markdown using pandas.

    :return: markdown table as string
    """
    hdbg.dassert_isinstance(header, list)
    hdbg.dassert_isinstance(rows, list)
    hdbg.dassert_lt(0, len(header), "Header is empty")
    df = pd.DataFrame(rows, columns=header)
    result = df.to_markdown(index=False)
    if result is None:
        raise ValueError("Failed to format as markdown")
    return result


def _format_as_delimited(
    header: List[str], rows: List[List[str]], delimiter: str
) -> str:
    """
    Format table as CSV or TSV.

    :param header: header row
    :param rows: data rows
    :param delimiter: field delimiter
    :return: CSV/TSV as string
    """
    hdbg.dassert_isinstance(header, list)
    hdbg.dassert_isinstance(rows, list)
    hdbg.dassert_lt(0, len(header), "Header is empty")
    # Write to StringIO using csv.writer.
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    result = output.getvalue().replace("\r\n", "\n").rstrip("\n")
    return result


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hseinout.add_input_output_args(parser)
    parser.add_argument(
        "--input_mode",
        type=str,
        choices=["md", "csv", "tsv"],
        default="",
        help="Input format when using stdin (required if -i is -)",
    )
    parser.add_argument(
        "--output_mode",
        type=str,
        choices=["md", "csv", "tsv"],
        default="",
        help="Output format when using stdout (required if -o is -)",
    )
    parser.add_argument(
        "--pbcopy",
        action="store_true",
        help="Copy output to system clipboard (macOS only)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hseinout.init_logger_for_input_output_transform(args)
    in_file_name, out_file_name = hseinout.parse_input_output_args(args)
    # Detect input mode.
    if in_file_name == "-":
        hdbg.dassert(
            args.input_mode,
            "--input_mode is required when input is stdin (-)",
        )
        input_mode = args.input_mode
    else:
        input_mode = args.input_mode or _detect_mode(in_file_name)
    # Detect output mode.
    if out_file_name == "-" or args.pbcopy:
        hdbg.dassert(
            args.output_mode,
            "--output_mode is required when output is stdout (-) or --pbcopy is set",
        )
        output_mode = args.output_mode
    else:
        output_mode = args.output_mode or _detect_mode(out_file_name)
    # Read input.
    txt = hseinout.from_file(in_file_name)
    # Parse table.
    if input_mode == "md":
        header, rows = _parse_md_table(txt)
    else:
        delimiter = "\t" if input_mode == "tsv" else ","
        header, rows = _parse_delimited(txt, delimiter)
    # Format output.
    if output_mode == "md":
        result = _format_as_md(header, rows)
    else:
        delimiter = "\t" if output_mode == "tsv" else ","
        result = _format_as_delimited(header, rows, delimiter)
    # Write output.
    if args.pbcopy:
        hsystem.to_pbcopy(result, pbcopy=True)
    else:
        if out_file_name == "-":
            hseinout.to_file(result, "-")
        else:
            hseinout.to_file(result.split("\n"), out_file_name)


if __name__ == "__main__":
    _main(_parse())
