#!/usr/bin/env python
"""
Convert markdown tables, CSV, and TSV formats.

Supports file I/O and stdin/stdout with mode specification.

Example:
# CSV to markdown
> python convert_table.py -i table.csv -o table.md

# TSV to CSV
> python convert_table.py -i table.tsv -o table.csv

# stdin to stdout with mode flags
> python convert_table.py -i - -o - --input_mode md --output_mode csv

# Copy to clipboard
> python convert_table.py -i table.csv --output_mode md --pbcopy

Import as:

import dev_scripts_helpers.documentation.convert_table as dsdccotbl
"""

import argparse
import csv
import io
from typing import List, Tuple

import helpers.hdbg as hdbg
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


# TODO(ai_gp): Can we use pandas to parse a markdown file?
# df = pd.read_csv(StringIO(md), sep="|", engine="python")
# df = df.dropna(axis=1, how='all')  # remove empty columns
# df.columns = df.columns.str.strip()
def _parse_md_table(
    lines: List[str],
) -> Tuple[List[str], List[List[str]]]:
    """
    Parse markdown table from lines.

    Expected format:
      | header1 | header2 |
      |---------|---------|
      | val1    | val2    |

    :return: tuple of (header_row, data_rows)
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_lt(0, len(lines), "Input table is empty")
    start_idx = 0
    found_header = False
    for i, line in enumerate(lines):
        if "|" in line and line.strip():
            start_idx = i
            found_header = True
            break
    hdbg.dassert(found_header, "No markdown table found in input")
    # Parse header row.
    header_line = lines[start_idx].strip()
    header = [cell.strip() for cell in header_line.split("|")]
    header = [cell for cell in header if cell]
    # Skip separator row.
    sep_idx = start_idx + 1
    hdbg.dassert_lt(
        sep_idx, len(lines), "Markdown table has no separator row"
    )
    sep_line = lines[sep_idx].strip()
    hdbg.dassert_in(
        "|", sep_line,
        "Expected separator row at index %s, got '%s'",
        sep_idx,
        sep_line,
    )
    hdbg.dassert_in(
        "-", sep_line,
        "Expected separator row at index %s, got '%s'",
        sep_idx,
        sep_line,
    )
    # Parse data rows.
    rows = []
    for i in range(sep_idx + 1, len(lines)):
        line = lines[i].strip()
        if not line or "|" not in line:
            break
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if cells:
            rows.append(cells)
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


# TODO(ai_gp): Use print(df.to_markdown(index=False))
def _format_as_md(
    header: List[str], rows: List[List[str]]
) -> str:
    """
    Format table as markdown.

    :return: markdown table as string
    """
    hdbg.dassert_isinstance(header, list)
    hdbg.dassert_isinstance(rows, list)
    hdbg.dassert_lt(0, len(header), "Header is empty")
    # Compute column widths.
    widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))
    # Format header row.
    header_cells = [h.ljust(w) for h, w in zip(header, widths)]
    header_row = "| " + " | ".join(header_cells) + " |"
    # Format separator row.
    sep_cells = ["-" * w for w in widths]
    sep_row = "| " + " | ".join(sep_cells) + " |"
    # Format data rows.
    data_rows = []
    for row in rows:
        cells = [
            cell.ljust(widths[i]) if i < len(widths) else cell
            for i, cell in enumerate(row)
        ]
        data_rows.append("| " + " | ".join(cells) + " |")
    # Combine all rows.
    all_rows = [header_row, sep_row] + data_rows
    return "\n".join(all_rows)


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
    hparser.add_input_output_args(parser)
    parser.add_argument(
        "--input_mode",
        type=str,
        choices=["md", "csv", "tsv"],
        default=None,
        help="Input format when using stdin (required if -i is -)",
    )
    parser.add_argument(
        "--output_mode",
        type=str,
        choices=["md", "csv", "tsv"],
        default=None,
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
    hparser.init_logger_for_input_output_transform(args)
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    # Detect input mode.
    if in_file_name == "-":
        hdbg.dassert_is_not(
            args.input_mode,
            None,
            "--input_mode is required when input is stdin (-)",
        )
        input_mode = args.input_mode
    else:
        input_mode = args.input_mode or _detect_mode(in_file_name)
    # Detect output mode.
    if out_file_name == "-" or args.pbcopy:
        hdbg.dassert_is_not(
            args.output_mode,
            None,
            "--output_mode is required when output is stdout (-) or --pbcopy is set",
        )
        output_mode = args.output_mode
    else:
        output_mode = args.output_mode or _detect_mode(out_file_name)
    # Read input.
    txt = hparser.from_file(in_file_name)
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
            hparser.to_file(result, "-")
        else:
            hparser.to_file(result.split("\n"), out_file_name)


if __name__ == "__main__":
    _main(_parse())
