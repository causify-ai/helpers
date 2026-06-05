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
> openrouter_models_table.py --models models.txt
> openrouter_models_table.py --models models.txt -v DEBUG
> openrouter_models_table.py --models models.txt -a fetch_aa_benchmarks -a fetch_openrouter_throughput

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
    # Read the data from OpenRouter about those models.
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
        # Also index by canonical slug for flexible lookups.
        canonical_slug: Optional[str] = m.get("canonical_slug")
        if canonical_slug:
            lookup[canonical_slug] = lookup[model_id]
    hdbg.dassert_lte(1, len(lookup.keys()))
    _LOG.debug("_fetch_models_from_api result (first items):\n%s",
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
    # Fetch HTML content with User-Agent header.
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
    # Try to match throughput patterns in HTML content.
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
            _LOG.debug("_fetch_openrouter_throughput(%s) result: %s",
                       model_id, throughput)
            return throughput
    _LOG.debug("No throughput found for %s", model_id)
    _LOG.debug("_fetch_openrouter_throughput(%s) result: None",
               model_id)
    return None


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_openrouter_per_model_usage() -> Dict[str, Dict[str, Any]]:
    """
    Fetch per-model usage statistics from OpenRouter rankings API.

    Uses the endpoint: https://openrouter.ai/api/v1/datasets/rankings/daily
    Requires OPENROUTER_API_KEY environment variable.

    :return: Dict mapping model ID to usage stats with 'week_tokens' and 'month_tokens'
    """
    _LOG.debug("# _fetch_openrouter_per_model_usage")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    hdbg.dassert(api_key, "OPENROUTER_API_KEY environment variable must be set")
    # Get the data.
    url = "https://openrouter.ai/api/v1/datasets/rankings/daily"
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
    # Extract per-model usage from API response.
    per_model_usage: Dict[str, Dict[str, Any]] = {}
    if isinstance(data, dict):
        rankings = data.get("data", [])
    elif isinstance(data, list):
        rankings = data
    else:
        rankings = []
    # Build lookup indexed by model ID with weekly and monthly token counts.
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
    _LOG.debug("_fetch_openrouter_per_model_usage result (first 3 items):\n%s",
               pprint.pformat(dict(list(per_model_usage.items())[:3])))
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
    _LOG.debug("# _fetch_all_aa_models")
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
    # Extract models list from response, handling various response formats.
    if isinstance(response_data, dict):
        models_list = response_data.get("data", [])
    elif isinstance(response_data, list):
        models_list = response_data
    else:
        models_list = []
    if not isinstance(models_list, list):
        models_list = []
    # Build lookup dict indexed by model name and slug for flexible matching.
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
    _LOG.debug("_fetch_all_aa_models result (first 3 items):\n%s",
               pprint.pformat(dict(list(lookup.items())[:3])))
    return lookup


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_aa_benchmarks(model_name: str) -> Dict[str, Optional[float]]:
    """
    Fetch benchmark data from Artificial Analysis API using cached models.

    :param model_name: Model name to search for
    :return: Dict with "coding", "intelligence", "agentic", "coding_index"
        benchmark scores

    """
    _LOG.debug("# _fetch_aa_benchmarks")
    aa_models = _fetch_all_aa_models()
    # Try exact match first (case-insensitive), then partial match.
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
    # Extract benchmark scores from model's evaluations.
    coding_score = None
    intelligence_score = None
    agentic_score = None
    coding_index = None
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
            #agentic_score = evaluations.get(
            #    "artificial_analysis_agentic_coding_index"
            #)
            coding_score = evaluations.get(
                "artificial_analysis_coding_index"
            )
    result = {
        "coding_score": coding_score,
        "intelligence_score": intelligence_score,
    }
    _LOG.debug("_fetch_aa_benchmarks(%s) result:\n%s",
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
    _LOG.debug("_format_cost(%s) result: %s", cost, result)
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
    _LOG.debug("_format_context(%s) result: %s", ctx, result)
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
    _LOG.debug("_format_benchmark(%s) result: %s", score, result)
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
    _LOG.debug(
        "_format_efficiency(coding=%s, throughput=%s, input=%s, output=%s) result: %s",
        coding_score,
        throughput,
        input_cost,
        output_cost,
        result
    )
    return result


# #############################################################################
# Data Processing Layer
# #############################################################################


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
    _LOG.debug("_read_model_ids result:\n%s", pprint.pformat(model_ids))
    return model_ids


def _build_rows(
    model_ids: List[str],
    api_lookup: Dict[str, Dict[str, Any]],
    actions: Optional[List[str]] = None,
) -> List[List[str]]:
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
    :return: List of rows, where each row is a list of formatted cell strings
    """
    _LOG.debug
    rows: List[List[str]] = []
    for model_id in model_ids:
        _LOG.debug("Processing %s", model_id)
        actions_copy = list(actions) if actions else None
        # Extract pricing and context from OpenRouter API.
        hdbg.dassert_in(model_id, api_lookup)
        api_data = api_lookup.get(model_id)
        #
        name = str(api_data["name"])
        input_cost = float(api_data["input_cost"])
        output_cost = float(api_data["output_cost"])
        context = int(api_data["context_length"])
        # Format.
        input_cost_str = _format_cost(input_cost)
        output_cost_str = _format_cost(output_cost)
        context_str = _format_context(context)
        # Fetch and format benchmark scores from Artificial Analysis.
        to_exec_benchmarks, actions_copy = hselacti.mark_action(
            "fetch_aa_benchmarks", actions_copy
        )
        if to_exec_benchmarks:
            benchmarks = _fetch_aa_benchmarks(name)
        else:
            benchmarks = {}
        coding_index_bench = benchmarks.get("coding_index")
        intelligence_bench = benchmarks.get("intelligence")
        agentic_bench = benchmarks.get("agentic")
        coding_bench = benchmarks.get("coding")
        # Format.
        coding_index_str = _format_benchmark(coding_index_bench)
        intelligence_str = _format_benchmark(intelligence_bench)
        agentic_str = _format_benchmark(agentic_bench)
        coding_str = _format_benchmark(coding_bench)
        # Fetch throughput and compute efficiency metric.
        to_exec_throughput, actions_copy = hselacti.mark_action(
            "fetch_openrouter_throughput", actions_copy
        )
        if to_exec_throughput:
            throughput = _fetch_openrouter_throughput(model_id)
        else:
            throughput = None
        speed_tok_s_str = f"{throughput:.0f}" if throughput and throughput > 0 else ""
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
        week_tokens_str = f"{week_tokens:,}" if week_tokens > 0 else ""
        month_tokens_str = f"{month_tokens:,}" if month_tokens > 0 else ""
        # Assemble row with all fields in column order.
        row = [
            name,
            model_id,
            input_cost_str,
            output_cost_str,
            context_str,
            speed_tok_s_str,
            week_tokens_str,
            month_tokens_str,
            coding_index_str,
            intelligence_str,
            agentic_str,
            coding_str,
            efficiency_str,
        ]
        _LOG.debug("row=%s", row)
        rows.append(row)
        assert 0
    _LOG.debug("_build_rows result (first 3 rows):\n%s",
               pprint.pformat(rows[:3]))
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
    # TODO(ai_gp): Add an options like "--models" to specify a list of models
    # as a space separated list.
    # TODO(ai_gp): Rename --models_from_file
    parser.add_argument(
        "--models",
        type=str,
        required=True,
        help="Path to a text file with one OpenRouter model ID per line",
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
    # Parse command line options.
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hcacsimp.parse_cache_control_args(args)
    # Process the actions.
    valid_actions = [
        "fetch_aa_benchmarks",
        "fetch_openrouter_throughput",
        "fetch_openrouter_per_model_usage",
    ]
    default_actions = valid_actions
    actions = hselacti.select_actions(args, valid_actions, default_actions)
    print(hselacti.actions_to_string(actions, valid_actions, add_frame=True))
    # Read the models from the file.
    model_ids = _read_model_ids(args.models)
    _LOG.debug("model_ids=%s", str(model_ids))
    # Fetch all models from the OpenRouter API.
    api_lookup = _fetch_models_from_api()
    _LOG.debug("api_lookup=%s", api_lookup.keys())
    # Process the data.
    rows = _build_rows(model_ids, api_lookup, actions)
    columns = [
        "Name", "Model ID", "Input Cost", "Output Cost", "Context",
        "Speed (tok/s)", "Week Tokens", "Month Tokens",
        "Coding Index", "General Intelligence", "Agentic Intelligence",
        "Coding", "Efficiency"
    ]
    # Assemble the data.
    table = pd.DataFrame(rows, columns=columns)
    print(table.to_string())


if __name__ == "__main__":
    _main(_parse())
