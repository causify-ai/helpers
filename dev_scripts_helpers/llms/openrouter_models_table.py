#!/usr/bin/env python3

"""
Fetch OpenRouter model pricing and metadata, then display a comparison table.

The input is a text file with one OpenRouter model ID per line, e.g.:

    google/gemini-3.1-pro-preview
    deepseek/deepseek-v4-pro

Usage:

    > openrouter_models_table.py --models models.txt
    > openrouter_models_table.py --models models.txt -v DEBUG

The script fetches pricing and context from the OpenRouter API
(https://openrouter.ai/api/v1/models) and prints a formatted comparison
table. Subjective fields (Speed tok/s, Speed rating, Agentic Coding, Notes)
are left blank for manual fill-in.
"""

import argparse
import json
import logging
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################

# Column definitions for the comparison table.
# Each entry is (header_name, width, alignment).
_COLUMNS: List[Tuple[str, int, str]] = [
    ("Model", 30, "<"),
    ("OpenRouter Model ID", 40, "<"),
    ("Input $/1M", 12, ">"),
    ("Output $/1M", 12, ">"),
    ("Context", 10, ">"),
    ("Speed tok/s", 12, ">"),
    ("Speed", 8, ">"),
    ("Agentic Coding (1-5)", 20, ">"),
    ("Notes", 40, "<"),
    ("Efficiency", 12, ">"),
]


def _fetch_models_from_api() -> Dict[str, Dict[str, Any]]:
    """
    Fetch all models from the OpenRouter API.

    :return: Dict mapping model ID (e.g. "google/gemini-3.1-pro-preview")
        to a dict with keys "name", "input_cost", "output_cost",
        "context_length"
    """
    url = "https://openrouter.ai/api/v1/models"
    _LOG.debug("Fetching models from %s", url)
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    hdbg.dassert_in("data", data, "API response must contain 'data' key")
    models_list: List[Dict[str, Any]] = data["data"]
    _LOG.info("Fetched %d models from OpenRouter API", len(models_list))
    # Build lookup dict.
    lookup: Dict[str, Dict[str, Any]] = {}
    for m in models_list:
        model_id: str = m["id"]
        # Extract pricing per 1M tokens.
        pricing: Dict[str, str] = m.get("pricing", {})
        prompt_cost = float(pricing.get("prompt", 0))
        completion_cost = float(pricing.get("completion", 0))
        # Convert per-token cost to per-1M-tokens cost.
        input_cost = prompt_cost * 1_000_000
        output_cost = completion_cost * 1_000_000
        context_length: int = m.get("context_length", 0)
        name: str = m.get("name", model_id)
        lookup[model_id] = {
            "name": name,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "context_length": context_length,
        }
        # Also index by canonical_slug if present.
        canonical_slug: Optional[str] = m.get("canonical_slug")
        if canonical_slug:
            lookup[canonical_slug] = lookup[model_id]
    return lookup


def _read_model_ids(models_file: str) -> List[str]:
    """
    Read model IDs from a text file, one per line.

    :param models_file: Path to the file
    :return: List of model ID strings
    """
    hdbg.dassert_file_exists(models_file, "Models file must exist")
    model_ids: List[str] = []
    with open(models_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            model_ids.append(line)
    hdbg.dassert_lt(0, len(model_ids), "Models file must contain at least one model ID")
    _LOG.info("Read %d model IDs from %s", len(model_ids), models_file)
    return model_ids


def _format_context(ctx: int) -> str:
    """
    Format context length as human-readable string (e.g., "128K", "1M").
    """
    if ctx >= 1_000_000:
        return f"{ctx / 1_000_000:.0f}M"
    elif ctx >= 1_000:
        return f"{ctx // 1_000}K"
    else:
        return str(ctx)


def _format_cost(cost: float) -> str:
    """
    Format cost per 1M tokens, with appropriate precision.
    """
    if cost == 0:
        return "0"
    elif cost < 0.01:
        return f"{cost:.4f}"
    elif cost < 1:
        return f"{cost:.3f}"
    elif cost < 10:
        return f"{cost:.2f}"
    else:
        return f"{cost:.1f}"


def _format_efficiency(
    agentic_score: Optional[float],
    speed: Optional[float],
    input_cost: float,
    output_cost: float,
) -> str:
    """
    Compute Efficiency = Agentic_Score × Speed / (Input + Output Cost).

    :return: Formatted string or "N/A" if subjective fields are missing
    """
    if agentic_score is None or speed is None:
        return "N/A"
    total_cost = input_cost + output_cost
    if total_cost == 0:
        return "N/A"
    efficiency = agentic_score * speed / total_cost
    return f"{efficiency:.0f}"


def _build_rows(
    model_ids: List[str],
    api_lookup: Dict[str, Dict[str, Any]],
) -> List[List[str]]:
    """
    Build table rows from model IDs and API data.

    :param model_ids: List of model IDs from the input file
    :param api_lookup: Dict from _fetch_models_from_api()
    :return: List of rows, where each row is a list of formatted cell strings
    """
    rows: List[List[str]] = []
    for model_id in model_ids:
        # Look up API data.
        api_data = api_lookup.get(model_id)
        if api_data is not None:
            name = str(api_data["name"])
            input_cost = float(api_data["input_cost"])
            output_cost = float(api_data["output_cost"])
            context = int(api_data["context_length"])
            input_cost_str = _format_cost(input_cost)
            output_cost_str = _format_cost(output_cost)
            context_str = _format_context(context)
        else:
            _LOG.warning("Model ID '%s' not found in OpenRouter API", model_id)
            name = model_id
            input_cost_str = "N/A"
            output_cost_str = "N/A"
            context_str = "N/A"
            input_cost = 0.0
            output_cost = 0.0
        # Subjective fields (left blank for manual fill-in).
        speed_tok_s = ""
        speed = ""
        agentic_coding = ""
        notes = ""
        # Compute efficiency.
        efficiency_str = _format_efficiency(None, None, input_cost, output_cost)
        row = [
            name,
            model_id,
            input_cost_str,
            output_cost_str,
            context_str,
            speed_tok_s,
            speed,
            agentic_coding,
            notes,
            efficiency_str,
        ]
        rows.append(row)
    return rows


def _format_table(rows: List[List[str]]) -> str:
    """
    Format rows as a human-readable table with aligned columns.

    :param rows: List of rows from _build_rows()
    :return: Formatted table string
    """
    # Build header.
    header: List[str] = []
    separators: List[str] = []
    for col_name, width, align in _COLUMNS:
        # Truncate header if it exceeds column width.
        truncated = col_name[:width]
        if align == ">":
            header.append(truncated.rjust(width))
        else:
            header.append(truncated.ljust(width))
        separators.append("-" * width)
    header_line = " | ".join(header)
    sep_line = "-+-".join(separators)
    lines = [header_line, sep_line]
    # Build each row with proper alignment.
    for row in rows:
        cells: List[str] = []
        for i, (col_name, width, align) in enumerate(_COLUMNS):
            cell = row[i]
            if cell is None:
                cell = ""
            cell = str(cell)
            # Truncate if too long.
            if len(cell) > width:
                cell = cell[: width - 1] + "…"
            if align == ">":
                cells.append(cell.rjust(width))
            else:
                cells.append(cell.ljust(width))
        lines.append(" | ".join(cells))
    return "\n".join(lines)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--models",
        type=str,
        required=True,
        help="Path to a text file with one OpenRouter model ID per line",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Read model IDs from the input file.
    model_ids = _read_model_ids(args.models)
    # Fetch API data.
    api_lookup = _fetch_models_from_api()
    # Build and format the comparison table.
    rows = _build_rows(model_ids, api_lookup)
    table = _format_table(rows)
    print(table)


if __name__ == "__main__":
    _main(_parse())