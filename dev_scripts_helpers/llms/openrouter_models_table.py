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
(https://openrouter.ai/api/v1/models). It also fetches benchmark data from
the Artificial Analysis API, including the Artificial Analysis Coding Index.
"""

import argparse
import json
import logging
import os
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# Module-level cache for AA models
_aa_models_cache: Optional[Dict[str, Dict[str, Any]]] = None

# #############################################################################


def _fetch_all_aa_models() -> Dict[str, Dict[str, Any]]:
    """
    Fetch all models from Artificial Analysis API with optional API key.

    Uses the direct endpoint: https://artificialanalysis.ai/api/v2/data/llms/models
    Caches the result to avoid repeated API calls within a session.

    :return: Dict mapping model name/slug to full model data including benchmarks
    """
    global _aa_models_cache
    if _aa_models_cache is not None:
        return _aa_models_cache

    try:
        url = "https://artificialanalysis.ai/api/v2/data/llms/models"
        api_key = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        }
        if api_key:
            headers["x-api-key"] = api_key

        request = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(request, timeout=30)
        data = json.loads(response.read().decode("utf-8"))

        # Build lookup dict by model name
        lookup: Dict[str, Dict[str, Any]] = {}
        if isinstance(data, dict) and "models" in data:
            models_list = data["models"]
        elif isinstance(data, list):
            models_list = data
        else:
            models_list = []

        for model in models_list:
            if isinstance(model, dict):
                # Index by multiple keys for flexible matching
                model_name = model.get("name", "")
                if model_name:
                    lookup[model_name.lower()] = model
                    lookup[model_name] = model

        _LOG.info("Fetched %d models from Artificial Analysis API",
                  len(lookup))
        _aa_models_cache = lookup
        return lookup
    except Exception as e:
        _LOG.warning("Failed to fetch AA models: %s", e)
        _aa_models_cache = {}
        return {}


def _fetch_aa_benchmarks(model_name: str) -> Dict[str, Optional[float]]:
    """
    Fetch benchmark data from Artificial Analysis API using cached models.

    :param model_name: Model name to search for
    :return: Dict with "coding", "intelligence", "agentic", "coding_index"
        benchmark scores
    """
    try:
        # Get the cached AA models
        aa_models = _fetch_all_aa_models()

        coding_score = None
        intelligence_score = None
        agentic_score = None
        coding_index = None

        # Try exact match first (case-insensitive)
        model_name_lower = model_name.lower()
        if model_name_lower in aa_models:
            model = aa_models[model_name_lower]
        elif model_name in aa_models:
            model = aa_models[model_name]
        else:
            # Try partial match
            model = None
            for aa_name, aa_model in aa_models.items():
                if (isinstance(aa_name, str) and
                    (model_name.lower() in aa_name or
                     aa_name in model_name.lower())):
                    model = aa_model
                    break

        if model and isinstance(model, dict):
            benchmarks = model.get("benchmarks", {})
            coding_score = benchmarks.get("coding")
            intelligence_score = benchmarks.get("intelligence")
            agentic_score = benchmarks.get("agentic")
            coding_index = model.get("artificial_analysis_coding_index")
            if coding_index is not None:
                coding_index = float(coding_index)

        return {
            "coding": coding_score,
            "intelligence": intelligence_score,
            "agentic": agentic_score,
            "coding_index": coding_index,
        }
    except Exception as e:
        _LOG.warning("Failed to fetch AA benchmarks for %s: %s",
                     model_name, e)
        return {
            "coding": None,
            "intelligence": None,
            "agentic": None,
            "coding_index": None,
        }


def _fetch_openrouter_usage() -> Dict[str, Any]:
    """
    Fetch usage statistics from OpenRouter API.

    Requires OPENROUTER_API_KEY environment variable.

    :return: Dict with usage statistics including 'daily', 'weekly', and
        'monthly' keys if available, or empty dict on error
    """
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            _LOG.warning("OPENROUTER_API_KEY not set; cannot fetch usage stats")
            return {}

        url = "https://openrouter.ai/api/v1/auth/key"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        }

        request = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(request, timeout=30)
        data = json.loads(response.read().decode("utf-8"))

        if "data" not in data:
            _LOG.warning("Unexpected API response format for usage")
            return {}

        api_data = data["data"]
        usage = api_data.get("usage", {})

        result = {
            "daily": usage.get("daily", 0),
            "weekly": usage.get("weekly", 0),
            "monthly": usage.get("monthly", 0),
        }

        _LOG.info(
            "Fetched OpenRouter usage: daily=%s, weekly=%s, monthly=%s",
            result["daily"],
            result["weekly"],
            result["monthly"]
        )
        return result
    except Exception as e:
        _LOG.warning("Failed to fetch OpenRouter usage: %s", e)
        return {}


def _format_usage(usage_dict: Dict[str, Any]) -> str:
    """
    Format usage statistics as a readable string.

    :param usage_dict: Dict with 'daily', 'weekly', 'monthly' keys
    :return: Formatted usage string
    """
    if not usage_dict:
        return "Usage stats unavailable"

    daily = usage_dict.get("daily", 0)
    weekly = usage_dict.get("weekly", 0)
    monthly = usage_dict.get("monthly", 0)

    return (f"Daily: ${daily:.4f} | Weekly: ${weekly:.4f} | "
            f"Monthly: ${monthly:.4f}")

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
    ("Coding Index", 12, ">"),
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
            "coding_index_bench": None,
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
        # Fetch AA benchmarks
        coding_index_bench = None
        if api_data is not None:
            coding_index_bench = api_data.get("coding_index_bench")
        if coding_index_bench is None:
            benchmarks = _fetch_aa_benchmarks(name)
            coding_index_bench = benchmarks.get("coding_index")
            if api_data is not None:
                api_data["coding_index_bench"] = coding_index_bench
        coding_index_str = (f"{coding_index_bench:.1f}"
                            if coding_index_bench else "")
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
            coding_index_str,
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
    parser.add_argument(
        "--show-usage",
        action="store_true",
        help="Fetch and display OpenRouter API usage statistics "
             "(requires OPENROUTER_API_KEY)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)

    if args.show_usage:
        usage = _fetch_openrouter_usage()
        print("OpenRouter API Usage Statistics:")
        print(_format_usage(usage))
        print()

    model_ids = _read_model_ids(args.models)
    api_lookup = _fetch_models_from_api()
    rows = _build_rows(model_ids, api_lookup)
    table = _format_table(rows)
    print(table)


if __name__ == "__main__":
    _main(_parse())
