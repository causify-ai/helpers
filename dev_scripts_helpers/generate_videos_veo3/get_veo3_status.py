#!/usr/bin/env python3
"""
Get Google Veo3 video generation status.

This script retrieves the status of video generation operations from the Google GenAI API
and displays them in a formatted table.

Usage:
> get_veo3_status.py
> get_veo3_status.py --operation-ids operations/12345 operations/67890

Environment:
  GOOGLE_GENAI_API_KEY  Your Google GenAI API key with Veo access.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Any, List

from google import genai

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

TIMEOUT = 30  # seconds per HTTP request



# #############################################################################
# Veo3Error
# #############################################################################

class Veo3Error(RuntimeError):
    pass


# TODO(ai): Factor out the code from get_synthesia_status.py.
def _format_timestamp(timestamp) -> str:
    """
    Format timestamp to readable format.

    Handles both ISO timestamp strings and unix timestamps.

    :param timestamp: ISO timestamp string or unix timestamp (int/float)
    :return: formatted timestamp
    """
    if not timestamp:
        return "N/A"
    try:
        # Check if it's a unix timestamp (integer or float).
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        # Check if it's a string that might be a unix timestamp.
        if isinstance(timestamp, str) and timestamp.isdigit():
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        # Try to parse as ISO timestamp.
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError, OSError):
        return str(timestamp)


def get_operations_status(
    client: genai.Client,
    *,
    limit: int = 20,
    offset: int = 0,
    operation_ids: List[str] = None,
) -> List[Any]:
    """
    Get list of operations and their status from Google GenAI API.

    Since the Google GenAI API may not support listing all operations,
    this function can check specific operation IDs if provided.

    :param client: Google GenAI client
    :param limit: maximum number of operations to retrieve
    :param offset: offset for pagination
    :param operation_ids: specific operation IDs to check
    :return: list of operation objects
    """
    try:
        operations_data = []

        if operation_ids:
            # Check specific operations
            for op_id in operation_ids:
                try:
                    operation = client.operations.get(op_id)
                    operations_data.append(operation)
                    _LOG.debug("Retrieved operation %s", op_id)
                except Exception as e:
                    _LOG.warning("Failed to get operation %s: %s", op_id, e)
        else:
            # Try to list operations - this may not be supported by the API
            _LOG.debug("Available methods on client.operations:")
            _LOG.debug(dir(client.operations))

            # Most operation-based APIs don't support listing all operations
            # They typically only support getting specific operations by ID
            _LOG.info("Google GenAI API does not support listing all operations")
            _LOG.info(
                "To check specific operations, run this script with --operation-ids"
            )
            _LOG.info(
                "Operation IDs are returned when you run generate_videos.py"
            )

        # Apply pagination if we have data
        if operations_data:
            paginated_operations = operations_data[offset : offset + limit]
            _LOG.debug("Retrieved %s operations", len(paginated_operations))
            return paginated_operations
        else:
            return []

    except Exception as e:
        raise Veo3Error(f"Failed to get operations: {e}")


def display_operations_status(operations: List[Any]) -> None:
    """
    Display operations status in a formatted table.

    :param operations: list of operation objects from API
    """
    if not operations:
        _LOG.info("No operations found.")
        return
    # Create table data structure
    table = []
    headers = ["Name", "Done", "Created", "Updated", "Model", "Status", "Error"]
    table.append(headers)
    # Process each operation and add to table
    for operation in operations:
        # Extract operation information with safe defaults
        name = getattr(operation, "name", "N/A")
        done = "Yes" if getattr(operation, "done", False) else "No"
        # Extract metadata if available
        metadata = getattr(operation, "metadata", {}) or {}
        created_time = metadata.get("createTime", "N/A")
        update_time = metadata.get("updateTime", "N/A")
        created_at = _format_timestamp(created_time)
        updated_at = _format_timestamp(update_time)
        # Extract model info if available
        model = "veo-3.0-generate-001"  # Default for Veo3
        # Extract status and error info
        status = (
            "Running" if not getattr(operation, "done", False) else "Complete"
        )
        error = "No"
        if hasattr(operation, "error") and operation.error:
            error = "Yes"
            status = "Error"
        # Add row to table
        row = [
            str(name)[:50]
            + ("..." if len(str(name)) > 50 else ""),  # Truncate long names
            str(done),
            str(created_at),
            str(updated_at),
            str(model),
            str(status),
            str(error),
        ]
        table.append(row)
    # Calculate column widths
    col_widths = []
    for i in range(len(table[0])):
        col_widths.append(max(len(str(row[i])) for row in table))
    # Print the table with aligned columns
    for i, row in enumerate(table):
        formatted_row = []
        for j, cell in enumerate(row):
            formatted_row.append(str(cell).ljust(col_widths[j]))
        print("  ".join(formatted_row))
        # Add separator line after headers
        if i == 0:
            separator = []
            for width in col_widths:
                separator.append("-" * width)
            print("  ".join(separator))


def _parse() -> argparse.Namespace:
    """
    Parse command line arguments.

    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Get Google Veo3 video generation status."
    )
    hparser.add_verbosity_arg(parser)
    # TODO(ai): Use functions in hparser.
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of operations to retrieve (default: 20)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset for pagination (default: 0)",
    )
    parser.add_argument(
        "--operation-ids",
        nargs="+",
        help="Specific operation IDs to check (space-separated)",
    )
    args = parser.parse_args()
    return args


def _main(args: argparse.Namespace) -> None:
    """
    Main function to get and display operation status.

    :param args: parsed arguments
    """
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate API key is available.
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    hdbg.dassert(api_key, "Environment variable GOOGLE_GENAI_API_KEY is not set")
    try:
        # Initialize client
        client = genai.Client(api_key=api_key)
        # Retrieve operations from Google GenAI API.
        operation_ids = getattr(args, "operation_ids", None)
        operations = get_operations_status(
            client,
            limit=args.limit,
            offset=args.offset,
            operation_ids=operation_ids,
        )
        # Display the results in table format.
        display_operations_status(operations)
        _LOG.info("Retrieved status for %s operations", len(operations))
    except Exception as e:
        _LOG.error("Google GenAI API error: %s", e)
        sys.exit(1)


def main() -> None:
    """
    Main entry point.
    """
    args = _parse()
    _main(args)


if __name__ == "__main__":
    main()
