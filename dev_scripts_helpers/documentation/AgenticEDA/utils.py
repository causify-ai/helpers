"""
Import as:

import dev_scripts_helpers.documentation.AgenticEDA.utils as dshdagut
"""

import logging
import sys

import pandas as pd

logger = logging.getLogger(__name__)


def read_input_file(file_path: str, file_type: str) -> pd.DataFrame:
    """
    Read input file (CSV or Markdown table).

    Args:
        file_path: Path to the input file.
        file_type: Type of the input file ('csv' or 'md').

    Returns pd.DataFrame: DataFrame containing the input data.
    """
    try:
        if file_type.lower() == "csv":
            df = pd.read_csv(file_path)
        elif file_type.lower() in ["md", "markdown"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Split the content into lines and extract the table
            lines = content.split("\n")
            table_lines = []
            in_table = False
            # Find the start of the table
            for line in lines:
                line = line.strip()
                if "|" in line and not line.startswith("|---"):
                    if not in_table:
                        in_table = True
                    table_lines.append(line)
                elif in_table and not line:
                    break
            # If no table found, raise an error
            if not table_lines:
                raise ValueError("No table found in markdown file")
            # Extract headers and rows
            headers = [h.strip() for h in table_lines[0].split("|")[1:-1]]
            rows = []
            # Process each row
            for line in table_lines[1:]:
                if "---" in line:
                    continue
                row = [cell.strip() for cell in line.split("|")[1:-1]]
                if len(row) == len(headers):
                    rows.append(row)
            df = pd.DataFrame(rows, columns=headers)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        return df
    except (OSError, ValueError, pd.errors.ParserError) as e:
        logger.error("Error reading input file: %s", e)
        sys.exit(1)


def write_output_file(df: pd.DataFrame, output_path: str) -> None:
    """
    Write output as markdown table.

    Args:
        df: DataFrame to write.
        output_path: Path to the output file.
    """
    try:
        output_df = df.drop(
            columns=[col for col in df.columns if col.startswith("_")],
            errors="ignore",
        )
        with open(output_path, "w", encoding="utf-8") as f:
            # Write the header
            headers = list(output_df.columns)
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---" for _ in headers]) + "|\n")
            for _, row in output_df.iterrows():
                # Prepare row data, escaping '|' characters
                row_data = []
                for col in headers:
                    cell_value = str(row[col]) if not pd.isna(row[col]) else ""
                    cell_value = cell_value.replace("|", "\\|")
                    row_data.append(cell_value)
                f.write("| " + " | ".join(row_data) + " |\n")
        logger.info("Output written to: %s", output_path)
    except (OSError, ValueError, pd.errors.ParserError) as e:
        logger.error("Error writing output file: %s", e)
        sys.exit(1)
