#!/usr/bin/env python3
"""
Extract function context and enrich a Markdown table.

This script reads a Markdown table containing function metadata and appends
the source line range and docstring of each function by parsing the original script files.

Usage:
> generate_EDA_context.py --i ABC.md --o XYZ.md

Example input (Markdown table):

| Function Type   | Script Path     | Function Name             |
|-----------------|-----------------|---------------------------|
| data conversion | helpers/hcsv.py | convert_csv_to_pq         |
| data conversion | helpers/hcsv.py | convert_csv_dir_to_pq_dir |

Example output (Markdown table):

| Function Type | Script Path | Function Name | Line Range | Docstring |
| ------------- | ----------- | ------------- | ---------- | --------- |
| data conversion | helpers/hcsv.py | convert_csv_to_pq | 191-216 | Convert CSV file to Parquet file. :param ...|
| data conversion | helpers/hcsv.py | convert_csv_dir_to_pq_dir | 219-273 | Apply `convert_csv_to_pq()` to all files in `csv_dir`. :param ...|
"""

import argparse
import ast
import logging
import os
from typing import Tuple

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _read_function_table(filepath: str) -> pd.DataFrame:
    """
    Convert a table from a Markdown file into a DataFrame.

    :param filepath: path to the Markdown file
    :return: table with function metadata (e.g., function type, script
        path, and function name)
    """
    df = pd.read_csv(filepath, sep="|", engine="python")
    df = df.dropna(axis=1, how="all")
    # Drop auto-generated 'Unnamed' index column.
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df.columns = df.columns.str.strip()
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    # Remove separator line.
    is_separator_row = df["Script Path"].str.fullmatch(r"-+")
    df = df[~is_separator_row]
    return df


def _get_function_line_range_and_docstring(
    file_path: str, function_name: str
) -> Tuple[str, str]:
    """
    Get a function's line range and docstring.

    :param file_path: path to the Python script containing the function
    :param function_name: name of the function
    :return: line range of function and docstring text
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            # Extract the function's start and end lines.
            start_line = node.lineno
            end_line = (
                node.end_lineno if hasattr(node, "end_lineno") else start_line
            )
            docstring = ast.get_docstring(node) or ""
            return f"{start_line}-{end_line}", docstring
    raise ValueError(f"Function '{function_name}' not found in {file_path}")


def _enrich_function_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'Line Range' and 'Docstring' to a table of function metadata.

    :param df: table with function metadata (e.g., function type, script
        path, function name, line range, and docstring)
    :return: table including 'Line Range' and 'Docstring' columns

    Example output:
    ```
    | Function Type | Script Path | Function Name | Line Range | Docstring |
    | ------------- | ----------- | ------------- | ---------- | --------- |
    | data conversion | helpers/hcsv.py | convert_csv_to_pq | 191-216 | Convert CSV file to Parquet file. :param ...|
    | data conversion | helpers/hcsv.py | convert_csv_dir_to_pq_dir | 219-273 | Apply `convert_csv_to_pq()` to all files in `csv_dir`. :param ...|
    ```
    """
    df["Line Range"] = None
    df["Docstring"] = None
    for idx, row in df.iterrows():
        script_path = row["Script Path"]
        function_name = row["Function Name"]
        if not os.path.isfile(script_path):
            # Skip file if it does not exist.
            _LOG.warning("File not found: %s", script_path)
            continue
        # Extract line range and docstring for the function.
        line_range, doc = _get_function_line_range_and_docstring(
            script_path, function_name
        )
        df.at[idx, "Line Range"] = line_range
        df.at[idx, "Docstring"] = doc
    return df


def _write_markdown_table(df: pd.DataFrame, filepath: str) -> None:
    """
    Write a table of function metadata to a markdown-formatted file.

    :param df: table with function metadata (e.g., function type, script
        path, function name, line range, and docstring)
    :param filepath: path where the output markdown file will be saved
    """
    with open(filepath, "w", encoding="utf-8") as f:
        # Create table header and seperator.
        header_cells = []
        separator_cells = []
        for col in list(df.columns):
            width = max(len(col), 3)
            header_cells.append(f"{col:<{width}}")
            separator_cells.append("-" * width)
        header = "| " + " | ".join(header_cells) + " |\n"
        separator = "| " + " | ".join(separator_cells) + " |\n"
        f.write(header)
        f.write(separator)
        # Write function metadata rows.
        for _, row in df.iterrows():
            line = (
                "| "
                + " | ".join(
                    str(row[col]).replace("\n", " ") if pd.notna(row[col]) else ""
                    for col in df.columns
                )
                + " |\n"
            )
            f.write(line)
    _LOG.info("Output written to: %s", filepath)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-i",
        "--in_file",
        required=True,
        help="Path to input markdown table",
    )
    parser.add_argument(
        "-o",
        "--out_file",
        required=True,
        help="Path to output enriched markdown table",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Read given Markdown file.
    df = _read_function_table(args.in_file)
    required_col = {"Function Type", "Script Path", "Function Name"}
    hdbg.dassert_is_subset(required_col, df.columns)
    # Enrich Markdown file.
    df = _enrich_function_table(df)
    _write_markdown_table(df, args.out_file)


if __name__ == "__main__":
    _main(_parse())
