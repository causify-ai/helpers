#!/usr/bin/env -S uv run

# /// script
# dependencies = ["pandas"]
# ///

"""
Fetch OpenRouter model pricing and metadata, then display a comparison table.

The input is a text file with one OpenRouter model ID per line, e.g.:
```
google/gemini-3.1-pro-preview
deepseek/deepseek-v4-pro
```

Usage:
> openrouter_models_table.py --models_from_file models.txt
> openrouter_models_table.py --models_from_file models.txt -v DEBUG
> openrouter_models_table.py --models_from_file models.txt -a fetch_aa_benchmarks -a fetch_openrouter_throughput
> openrouter_models_table.py --models_list "google/gemini-3.1-pro-preview deepseek/deepseek-v4-pro"

The script fetches
- Pricing and context from the OpenRouter API (https://openrouter.ai/api/v1/models)
- Benchmark data from the Artificial Analysis API, including the Artificial
  Analysis Coding Index
- Throughput metrics from OpenRouter model pages
- Per-model usage statistics from OpenRouter rankings API

Use action selection flags to control which data sources are queried:
- `-a/--action`: Select specific actions to run
- `-sa/--skip_action`: Skip specific actions from the default set
- `-e/--enable`: Enable additional actions beyond defaults
- `--all`: Run all available actions (default behavior)
"""

import argparse
import json
import logging
import os
import pprint
import re
import urllib.request
from typing import Any, Dict, List, Optional

import pandas as pd

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hselect_action as hselacti

_LOG = logging.getLogger(__name__)

# #############################################################################
# API Fetching Layer: OpenRouter
# #############################################################################


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_models_from_api() -> Dict[str, Dict[str, Any]]:
    """
    Fetch all models from the OpenRouter API.

    :return: Dict mapping model ID (e.g. "google/gemini-3.1-pro-preview")
        ```
        {'coding_index_bench': None,
         'context_length': 128000,
         'input_cost': 0.0,
         'name': 'NVIDIA: Nemotron 3.5 Content Safety (free)',
         'output_cost': 0.0}
        ```
        to a dict with keys "name", "input_cost", "output_cost",
        "context_length"
    """
    _LOG.debug(hprint.func_signature_to_str())
    url = "https://openrouter.ai/api/v1/models"
    _LOG.debug("Fetching models from %s", url)
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    hdbg.dassert_in("data", data, "API response must contain 'data' key")
    models_list: List[Dict[str, Any]] = data["data"]
    _LOG.info("Fetched %d models from OpenRouter API", len(models_list))
    # Build lookup dict indexed by model ID and canonical slug.
    lookup: Dict[str, Dict[str, Any]] = {}
    for m in models_list:
        model_id: str = m["id"]
        # Extract and convert pricing from per-token to per-1M-tokens.
        pricing: Dict[str, str] = m.get("pricing", {})
        prompt_cost = float(pricing.get("prompt", 0))
        completion_cost = float(pricing.get("completion", 0))
        # Convert from per-token to per-million-tokens pricing for easier comparison.
        input_cost = prompt_cost * 1_000_000
        output_cost = completion_cost * 1_000_000
        # Extract model metadata.
        context_length: int = m.get("context_length", 0)
        name: str = m.get("name", model_id)
        lookup[model_id] = {
            "name": name,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "context_length": context_length,
            "coding_index_bench": None,
        }
        # Create alias by canonical slug to support flexible model lookups.
        canonical_slug: Optional[str] = m.get("canonical_slug")
        if canonical_slug:
            lookup[canonical_slug] = lookup[model_id]
    hdbg.dassert_lte(1, len(lookup.keys()))
    _LOG.debug("Result (first items):\n%s",
               pprint.pformat(lookup[list(lookup.keys())[0]]))
    return lookup


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_openrouter_throughput(model_id: str) -> Optional[float]:
    """
    Fetch throughput (tokens/sec) from OpenRouter page for a model.

    Scrapes the model detail page and extracts throughput information.

    :param model_id: OpenRouter model ID (e.g., "google/gemini-3.1-pro-preview")
    :return: Throughput in tokens/sec or None if not found
    """
    _LOG.debug(hprint.func_signature_to_str())
    url = f"https://openrouter.ai/{model_id}"
    _LOG.debug("Fetching throughput from %s", url)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36"
        )
    }
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request, timeout=30)
    html_content = response.read().decode("utf-8")
    # Try multiple regex patterns to extract throughput from HTML page.
    patterns = [
        r'(\d+(?:\.\d+)?)\s*tokens?/\s*s(?:ec)?',
        r'(\d+(?:\.\d+)?)\s*tok/s',
        r'throughput["\s:]+(\d+(?:\.\d+)?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            throughput = float(match.group(1))
            _LOG.info("Found throughput for %s: %f", model_id,
                     throughput)
            _LOG.debug("%s -> return=%s",
                       model_id, throughput)
            return throughput
    _LOG.debug("No throughput found for %s", model_id)
    _LOG.debug("%s -> return=None", model_id)
    return None


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_openrouter_per_model_usage() -> Dict[str, Dict[str, Any]]:
    """
    Fetch per-model usage statistics from OpenRouter rankings API.

    Requires OPENROUTER_API_KEY environment variable.

    :return: Dict mapping model ID to usage stats with 'week_tokens' and 'month_tokens'
    """
    _LOG.debug(hprint.func_signature_to_str())
    api_key = os.environ.get("OPENROUTER_API_KEY")
    hdbg.dassert(api_key, "OPENROUTER_API_KEY environment variable must be set")
    # Get the data.
    url = "https://openrouter.ai/api/v1/datasets/rankings-daily"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36"
        )
    }
    _LOG.debug("url=%s", url)
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request, timeout=30)
    data = json.loads(response.read().decode("utf-8"))
    # Handle flexible API response format (dict or list).
    if isinstance(data, dict):
        rankings = data.get("data", [])
    elif isinstance(data, list):
        rankings = data
    else:
        rankings = []
    # Extract weekly and monthly token usage by model ID.
    per_model_usage: Dict[str, Dict[str, Any]] = {}
    for ranking in rankings:
        if isinstance(ranking, dict):
            model_id = ranking.get("model_id", "")
            week_tokens = ranking.get("tokens_week", 0)
            month_tokens = ranking.get("tokens_month", 0)
            if model_id:
                per_model_usage[model_id] = {
                    "week_tokens": week_tokens,
                    "month_tokens": month_tokens,
                }
    _LOG.info("Fetched per-model usage for %d models",
              len(per_model_usage))
    _LOG.debug("Return (first one):\n%s",
               pprint.pformat(dict(list(per_model_usage.items())[:1])))
    return per_model_usage


# #############################################################################
# API Fetching Layer: Artificial Analysis
# #############################################################################


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_all_aa_models() -> Dict[str, Dict[str, Any]]:
    """
    Fetch all models from Artificial Analysis API with API key.

    Uses the direct endpoint: https://artificialanalysis.ai/api/v2/data/llms/models

    :return: Dict mapping model name/slug to full model data including benchmarks
    """
    _LOG.debug(hprint.func_signature_to_str())
    url = "https://artificialanalysis.ai/api/v2/data/llms/models"
    api_key = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")
    # Prepare request with User-Agent header and optional API key.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36"
        )
    }
    if api_key:
        headers["x-api-key"] = api_key
    # Fetch and parse API response.
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request, timeout=30)
    response_data = json.loads(response.read().decode("utf-8"))
    # Handle flexible API response format and normalize to list.
    if isinstance(response_data, dict):
        models_list = response_data.get("data", [])
    elif isinstance(response_data, list):
        models_list = response_data
    else:
        models_list = []
    if not isinstance(models_list, list):
        models_list = []
    # Index by both exact and lowercase name/slug for flexible model matching.
    lookup: Dict[str, Dict[str, Any]] = {}
    for model in models_list:
        if isinstance(model, dict):
            model_name = model.get("name", "")
            model_slug = model.get("slug", "")
            if model_name:
                lookup[model_name.lower()] = model
                lookup[model_name] = model
            if model_slug:
                lookup[model_slug.lower()] = model
                lookup[model_slug] = model
    _LOG.info("Fetched %d models from Artificial Analysis API",
              len(lookup))
    _LOG.debug("Return (first one):\n%s",
               pprint.pformat(dict(list(lookup.items())[:1])))
    return lookup


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_aa_benchmarks(model_name: str) -> Dict[str, Optional[float]]:
    """
    Fetch benchmark data from Artificial Analysis API using cached models.

    :param model_name: Model name to search for
    :return: Dict with "coding_score", "intelligence_score"
        benchmark scores

    """
    _LOG.debug(hprint.func_signature_to_str())
    aa_models = _fetch_all_aa_models()
    # Try exact match first (case-insensitive), then substring match.
    model_name_lower = model_name.lower()
    model = None
    if model_name_lower in aa_models:
        model = aa_models[model_name_lower]
    elif model_name in aa_models:
        model = aa_models[model_name]
    else:
        for aa_name, aa_model in aa_models.items():
            if (isinstance(aa_name, str) and
                (model_name.lower() in aa_name or
                 aa_name in model_name.lower())):
                model = aa_model
                break
    # Extract benchmark scores from model's evaluations dict.
    coding_score = None
    intelligence_score = None
    # {'gpt-oss-120b': {'evaluations': {'aime': None,
    #                                   'aime_25': 0.934416666666667,
    #                                   'artificial_analysis_coding_index': 28.6,
    #                                   'artificial_analysis_intelligence_index': 33.3,
    #                                   'artificial_analysis_math_index': 93.4,
    #                                   'gpqa': 0.782,
    #                                   'hle': 0.185,
    #                                   'ifbench': 0.689795918367347,
    #                                   'lcr': 0.506666666,
    #                                   'livecodebench': 0.878,
    #                                   'math_500': None,
    #                                   'mmlu_pro': 0.808,
    #                                   'scicode': 0.389,
    #                                   'tau2': 0.657894736842105,
    #                                   'terminalbench_hard': 0.234848484848485},
    #                   'id': 'f0083258-8646-45b8-8082-7aaf6c2ea82a',
    #                   'median_output_tokens_per_second': 362.317,
    #                   'median_time_to_first_answer_token': 6.037,
    #                   'median_time_to_first_token_seconds': 0.517,
    #                   'model_creator': {'id': 'e67e56e3-15cd-43db-b679-da4660a69f41',
    #                                     'name': 'OpenAI',
    #                                     'slug': 'openai'},
    #                   'name': 'gpt-oss-120b (high)',
    #                   'pricing': {'price_1m_blended_3_to_1': 0.262,
    #                               'price_1m_input_tokens': 0.15,
    #                               'price_1m_output_tokens': 0.6},
    #                   'release_date': '2025-08-05',
    #                   'slug': 'gpt-oss-120b'},
    if model and isinstance(model, dict):
        evaluations = model.get("evaluations", {})
        if isinstance(evaluations, dict):
            intelligence_score = evaluations.get(
                "artificial_analysis_intelligence_index"
            )
            coding_score = evaluations.get(
                "artificial_analysis_coding_index"
            )
    result = {
        "coding_score": coding_score,
        "intelligence_score": intelligence_score,
    }
    _LOG.debug("%s -> return:\n%s",
               model_name, pprint.pformat(result))
    return result


# #############################################################################
# Formatting Layer
# #############################################################################


def _format_cost(cost: float) -> str:
    """
    Format cost per 1M tokens with appropriate precision.

    Adjusts decimal places based on the magnitude of the cost value.

    :param cost: Cost per 1M tokens
    :return: Formatted cost string with appropriate precision
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Choose precision based on cost magnitude to keep values readable.
    if cost == 0:
        result = "0"
    elif cost < 0.01:
        result = f"{cost:.4f}"
    elif cost < 1:
        result = f"{cost:.3f}"
    elif cost < 10:
        result = f"{cost:.2f}"
    else:
        result = f"{cost:.1f}"
    return result


def _format_context(ctx: int) -> str:
    """
    Format context length as human-readable string.

    Converts context length to human-readable format (e.g., "128K", "1M").

    :param ctx: Context length in tokens
    :return: Human-readable string representation
    """
    if ctx >= 1_000_000:
        result = f"{ctx / 1_000_000:.0f}M"
    elif ctx >= 1_000:
        result = f"{ctx // 1_000}K"
    else:
        result = str(ctx)
    return result


def _format_benchmark(score: Optional[float]) -> str:
    """
    Format a benchmark score for display.

    :param score: Benchmark score or None
    :return: Formatted string or empty string if None
    """
    if score is None:
        result = ""
    else:
        result = f"{score:.1f}"
    return result


def _format_efficiency(
    coding_score: Optional[float],
    throughput: Optional[float],
    input_cost: float,
    output_cost: float,
) -> str:
    """
    Compute Efficiency = Coding_Score × Throughput / (Input + Output Cost).

    :return: Formatted string or "N/A" if fields are missing
    """
    if coding_score is None or throughput is None:
        result = "N/A"
    else:
        total_cost = input_cost + output_cost
        if total_cost == 0:
            result = "N/A"
        else:
            efficiency = coding_score * throughput / total_cost
            result = f"{efficiency:.0f}"
    return result


def _format_table(table: pd.DataFrame) -> pd.DataFrame:
    """
    Format table columns using appropriate formatting functions.

    :param table: DataFrame with raw unformatted data
    :return: DataFrame with formatted string columns
    """
    _LOG.debug(hprint.func_signature_to_str())
    table = table.copy()
    table["Input_Cost"] = table["Input_Cost"].apply(_format_cost)
    table["Output_Cost"] = table["Output_Cost"].apply(_format_cost)
    table["Context"] = table["Context"].apply(_format_context)
    table["Speed_(tok/s)"] = table["Speed_(tok/s)"].apply(
        lambda x: _format_benchmark(x) if x is not None else ""
    )
    table["Coding_IQ"] = table["Coding_IQ"].apply(_format_benchmark)
    table["General_IQ"] = table["General_IQ"].apply(_format_benchmark)
    return table


# #############################################################################
# Data Processing Layer
# #############################################################################


def _read_model_ids_from_file(models_file: str) -> List[str]:
    """
    Read model IDs from a text file, one per line.

    :param models_file: Path to the file
    :return: List of model ID strings
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_file_exists(models_file, "Models file must exist")
    model_ids: List[str] = []
    # Read file and filter out comments and empty lines.
    with open(models_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            model_ids.append(line)
    hdbg.dassert_lt(0, len(model_ids), "Models file must contain at least one model ID")
    _LOG.info("Read %d model IDs from %s", len(model_ids), models_file)
    _LOG.debug("Return (first one):\n%s", pprint.pformat(model_ids[:1]))
    return model_ids


def _read_model_ids_from_list(models_list_str: str) -> List[str]:
    """
    Parse model IDs from a space-separated string.

    :param models_list_str: Space-separated model IDs
    :return: List of model ID strings
    """
    _LOG.debug(hprint.func_signature_to_str())
    model_ids = models_list_str.split()
    hdbg.dassert_lt(0, len(model_ids), "Must provide at least one model ID")
    _LOG.info("Parsed %d model IDs from list", len(model_ids))
    _LOG.debug("Return (first one):\n%s", pprint.pformat(model_ids[:1]))
    return model_ids


def _build_rows(
    model_ids: List[str],
    api_lookup: Dict[str, Dict[str, Any]],
    actions: Optional[List[str]],
    *,
    abort_on_na: bool = True
) -> List[List[Any]]:
    """
    Build table rows from model IDs and API data.

    Optionally fetches benchmark data, throughput, and usage statistics based
    on the selected actions. Available actions are:
    - "fetch_aa_benchmarks": Fetch benchmark scores from Artificial Analysis
    - "fetch_openrouter_throughput": Fetch throughput (tokens/sec) from OpenRouter
    - "fetch_openrouter_per_model_usage": Fetch usage statistics (tokens/week/month)

    :param model_ids: List of model IDs from the input file
    :param api_lookup: Dict from _fetch_models_from_api() with pricing and context
    :param actions: List of selected actions to execute. If None, executes all actions.
        Skipped actions result in empty values for their corresponding columns.
    :return: List of rows with raw unformatted data
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_is_not(actions, None)
    if actions is None:
        actions = []
    rows: List[List[str]] = []
    for model_id in model_ids:
        _LOG.debug("Processing %s", model_id)
        actions_copy = list(actions)
        # Extract pricing and context from OpenRouter API.
        if model_id not in api_lookup:
            _LOG.warning("Can't find '%s' in the OpenRouter API data: skipping")
            continue
        hdbg.dassert_in(model_id, api_lookup)
        api_data = api_lookup[model_id]
        #
        name = str(api_data["name"])
        input_cost = float(api_data["input_cost"])
        output_cost = float(api_data["output_cost"])
        context = int(api_data["context_length"])
        # Fetch and format benchmark scores from Artificial Analysis.
        to_exec_benchmarks, actions_copy = hselacti.mark_action(
            "fetch_aa_benchmarks", actions_copy
        )
        if to_exec_benchmarks:
            benchmarks = _fetch_aa_benchmarks(name)
        else:
            benchmarks = {}
        # Extract correct keys from benchmarks dict.
        coding_bench = benchmarks.get("coding_score")
        intelligence_bench = benchmarks.get("intelligence_score")
        to_exec_throughput, actions_copy = hselacti.mark_action(
            "fetch_openrouter_throughput", actions_copy
        )
        if to_exec_throughput:
            throughput = _fetch_openrouter_throughput(model_id)
        else:
            throughput = None
        efficiency_str = _format_efficiency(
            coding_bench, throughput, input_cost, output_cost
        )
        # Fetch per-model usage statistics.
        to_exec_usage, actions_copy = hselacti.mark_action(
            "fetch_openrouter_per_model_usage", actions_copy
        )
        if to_exec_usage:
            per_model_usage = _fetch_openrouter_per_model_usage()
        else:
            per_model_usage = {}
        usage_data = per_model_usage.get(model_id, {})
        week_tokens = usage_data.get("week_tokens", 0)
        month_tokens = usage_data.get("month_tokens", 0)
        # Assemble row with all fields in column order.
        row = [
            name,
            model_id,
            input_cost,
            output_cost,
            context,
            throughput,
            week_tokens,
            month_tokens,
            coding_bench,
            intelligence_bench,
            efficiency_str,
        ]
        _LOG.debug("row=%s", row)
        rows.append(row)
    _LOG.debug("Return (first 1):\n%s", pprint.pformat(rows[:1]))
    return rows


# #############################################################################
# CLI / Entry Point
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Create and return argument parser for the script.

    Defines command-line arguments for model file path and optional usage display.

    :return: Configured `argparse.ArgumentParser` instance
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Create mutually exclusive group for model input sources.
    models_group = parser.add_mutually_exclusive_group(required=True)
    models_group.add_argument(
        "--models_from_file",
        type=str,
        help="Path to a text file with one OpenRouter model ID per line",
    )
    models_group.add_argument(
        "--models_list",
        type=str,
        help="Space-separated list of OpenRouter model IDs",
    )
    valid_actions = [
        "fetch_aa_benchmarks",
        "fetch_openrouter_throughput",
        "fetch_openrouter_per_model_usage",
    ]
    default_actions = valid_actions
    hselacti.add_action_arg(parser, valid_actions, default_actions)
    hcacsimp.add_cache_control_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main script entry point.

    Fetches model data from OpenRouter and Artificial Analysis APIs, then
    displays a formatted comparison table.

    :param parser: Configured argument parser
    """
    _LOG.debug(hprint.func_signature_to_str())
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hcacsimp.parse_cache_control_args(args)
    # Select which data sources to query based on command-line actions.
    valid_actions = [
        "fetch_aa_benchmarks",
        "fetch_openrouter_throughput",
        "fetch_openrouter_per_model_usage",
    ]
    default_actions = valid_actions
    actions = hselacti.select_actions(args, valid_actions, default_actions)
    print(hselacti.actions_to_string(actions, valid_actions, add_frame=True))
    # Read the models from file or list.
    if args.models_from_file:
        model_ids = _read_model_ids_from_file(args.models_from_file)
    else:
        model_ids = _read_model_ids_from_list(args.models_list)
    _LOG.debug("model_ids=%s", str(model_ids))
    # Fetch all models from the OpenRouter API.
    api_lookup = _fetch_models_from_api()
    _LOG.debug("api_lookup=%s", api_lookup.keys())
    # Process the data.
    rows = _build_rows(model_ids, api_lookup, actions)
    columns = [
        "Name", "Model_ID", "Input_Cost", "Output_Cost", "Context",
        "Speed_(tok/s)", "Week_Tokens", "Month_Tokens",
        "Coding_IQ", "General_IQ", "Efficiency"
    ]
    # Assemble and display the table.
    table = pd.DataFrame(data=rows, columns=columns)  # type: ignore
    table = _format_table(table)
    print(table.to_string())


if __name__ == "__main__":
    _main(_parse())
