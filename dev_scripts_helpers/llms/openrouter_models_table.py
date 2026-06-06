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

The script fetches data from multiple sources and displays a comparison table.

Available data sources:
- `openrouter_pricing`: Pricing and context from the OpenRouter API
- `aa_benchmarks`: Benchmark data from the Artificial Analysis API
- `openrouter_throughput`: Throughput metrics from OpenRouter model pages
- `openrouter_per_model_usage`: Per-model usage statistics from OpenRouter
  rankings API

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


# There are several representation of model names
# - Short model name: "claude-opus-4.7"
# - Short OpenRouter ID: "google/gemini-3.1-pro-preview" (provider/model-name)
# - Full versioned OpenRouter ID: "anthropic/claude-4.7-opus-20260416"
# - Artificial Analysis: "claude-opus-4-7"

# #############################################################################
# API Fetching Layer: OpenRouter
# #############################################################################


# @functools.lru_cache
@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_models_from_api() -> Dict[str, Dict[str, Any]]:
    """
    Fetch all models from the OpenRouter API.

    :return: Dict mapping model ID (e.g. "google/gemini-3.1-pro-preview")
        to a dict with structure:
        ```
        {
            'name': 'Google: Gemini 3.1 Pro Preview',
            'input_cost': 0.075,  # per 1M tokens
            'output_cost': 0.3,   # per 1M tokens
            'context_length': 128000,
            'coding_index_bench': None
        }
        ```
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
    _LOG.debug(
        "Result (first items):\n%s",
        pprint.pformat(lookup[list(lookup.keys())[0]]),
    )
    return lookup


# #############################################################################
# Model Name Mapping
# #############################################################################


def _build_short_to_full_model_map() -> Dict[str, str]:
    """
    Build a mapping from short model names to full OpenRouter API model names.

    :return: Dict mapping short names (case-insensitive) to full model IDs
        ```
        {
            'claude-opus-4.7': 'anthropic/claude-4.7-opus-20260416',
            'google/gemini-3.1-pro-preview': 'google/gemini-3.1-pro-preview'
        }
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    models = _fetch_models_from_api()
    # Build the map.
    short_to_full: Dict[str, str] = {}
    for model_id in models.keys():
        if "/" not in model_id:
            continue
        provider, model_name = model_id.split("/", 1)
        short_to_full[model_name.lower()] = model_id
        short_to_full[model_id.lower()] = model_id
    return short_to_full


def _normalize_model_name_for_matching(name: str) -> str:
    """
    Normalize a model name by removing version suffixes and dates for fuzzy matching.

    Removes version numbers, dates, and provider prefixes to enable fuzzy matching.

    :param name: Model name to normalize
    :return: Normalized lowercase name for fuzzy comparison
        "claude-opus-4.7" -> "claude-opus"
        "claude-4.7-opus-20260416" -> "claude-opus"
        "gemini-2.5-pro" -> "gemini-pro"
        "google/gemini-3.1-pro-preview" -> "gemini-pro-preview"
        "anthropic/claude-opus-4.7" -> "claude-opus"
    """
    name = name.lower()
    if "/" in name:
        name = name.split("/", 1)[1]
    name = re.sub(r"-\d+\.\d+(-\w+)?(-\d{8})?", "", name)
    name = re.sub(r"v\d+(\.\d+)?", "", name)
    name = re.sub(r"-\d{8}", "", name)
    return name.strip()


def _resolve_model_name(short_name: str, short_to_full: Dict[str, str]) -> str:
    """
    Resolve a short model name to its full OpenRouter API version.

    Tries exact match first, then fuzzy matching by removing version suffixes
    and dates to find the closest match.

    :param short_name: Model name (short, full OpenRouter ID, or unrecognized)
    :param short_to_full: Mapping of short names to full model IDs
    :return: Full model ID or original name if no match found
        "claude-opus-4.7" -> 'anthropic/claude-4.7-opus-20260416'
    """
    _LOG.debug(hprint.func_signature_to_str())
    short_lower = short_name.lower()
    if short_lower in short_to_full:
        return short_to_full[short_lower]
    if short_name in short_to_full:
        return short_to_full[short_name]
    normalized = _normalize_model_name_for_matching(short_name)
    for short, full in short_to_full.items():
        full_normalized = _normalize_model_name_for_matching(full)
        if normalized in full_normalized or full_normalized in normalized:
            _LOG.info("Matched '%s' to '%s' via fuzzy match", short_name, full)
            return full
    _LOG.debug("No match found for '%s', returning original", short_name)
    return short_name


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_openrouter_throughput(model_id: str) -> Optional[float]:
    """
    Fetch throughput (tokens/sec) from OpenRouter page for a model.

    Scrapes the OpenRouter model detail page and extracts throughput information
    from embedded JSON data (p50_throughput metric).

    :param model_id: Full OpenRouter model ID (must contain "/" separator)
        - Full OpenRouter ID: "google/gemini-3.1-pro-preview" or
          "anthropic/claude-4.7-opus-20260416" (provider/model-name)
    :return: Throughput in tokens/sec (float) or None if not found
        E.g., 25.5  # tokens per second (50th percentile)
    """
    _LOG.debug(hprint.func_signature_to_str())
    url = f"https://openrouter.ai/{model_id}"
    _LOG.debug("Fetching throughput from %s", url)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request, timeout=30)
    html_content = response.read().decode("utf-8")
    # Extract p50_throughput from embedded JSON data in HTML.
    # The OpenRouter page embeds JSON with escaped quotes like:
    # \"p50_throughput\":43
    match = re.search(r'\\"p50_throughput\\":(\d+(?:\.\d+)?)', html_content)
    if match:
        throughput = float(match.group(1))
        _LOG.info("Found throughput for %s: %f", model_id, throughput)
        _LOG.debug("%s -> return=%s", model_id, throughput)
        return throughput
    _LOG.debug("No throughput found for %s", model_id)
    _LOG.debug("%s -> return=None", model_id)
    return None


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_openrouter_per_model_usage() -> Dict[str, Dict[str, Any]]:
    """
    Fetch per-model usage statistics from OpenRouter rankings API.

    The API returns daily rankings data over the past 30 days. This function
    aggregates total_tokens by model and date range to compute weekly and
    monthly usage statistics. Uses model_permaslug as the key.

    :return: Dict mapping model permaslug to usage stats with
        'week_tokens' (past 7 days) and 'month_tokens' (past 30 days)
        ```
        {
            "gpt-4-omni": {
                "week_tokens": 1234567890,
                "month_tokens": 5678901234
            },
            "claude-3-opus": {
                "week_tokens": 987654321,
                "month_tokens": 4567890123
            }
        }
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    # TODO(ai_gp): Move it up
    from datetime import datetime, timedelta

    api_key = os.environ.get("OPENROUTER_API_KEY")
    hdbg.dassert(api_key, "OPENROUTER_API_KEY environment variable must be set")
    # Get the data.
    url = "https://openrouter.ai/api/v1/datasets/rankings-daily"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ),
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
    per_model_usage: Dict[str, Dict[str, Any]] = {}
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    for ranking in rankings:
        if not isinstance(ranking, dict):
            continue
        model_permaslug = ranking.get("model_permaslug", "")
        if not model_permaslug:
            continue
        total_tokens_str = ranking.get("total_tokens", "0")
        try:
            total_tokens = int(total_tokens_str)
        except (ValueError, TypeError):
            total_tokens = 0
        date_str = ranking.get("date", "")
        if not date_str:
            continue
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if model_permaslug not in per_model_usage:
            per_model_usage[model_permaslug] = {
                "week_tokens": 0,
                "month_tokens": 0,
            }
        if date >= week_ago:
            per_model_usage[model_permaslug]["week_tokens"] += total_tokens
        if date >= month_ago:
            per_model_usage[model_permaslug]["month_tokens"] += total_tokens
    _LOG.info("Fetched per-model usage for %d models", len(per_model_usage))
    _LOG.debug(
        "Return (first one):\n%s",
        pprint.pformat(dict(list(per_model_usage.items())[:1])),
    )
    return per_model_usage


# #############################################################################
# API Fetching Layer: Artificial Analysis
# #############################################################################


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_all_aa_models() -> Dict[str, Dict[str, Any]]:
    """
    Fetch all models from Artificial Analysis API with API key.

    Uses the direct endpoint: https://artificialanalysis.ai/api/v2/data/llms/models

    :return: Dict mapping model slug/name (lowercase) to full model data with benchmarks
        ```
        {
            "name": "Claude 3.5 Opus",
            "slug": "claude-opus-3-5",
            "evaluations": {
                "artificial_analysis_coding_index": 72.3,
                "artificial_analysis_intelligence_index": 85.2,
                "mmlu_pro": 0.92,
                ...
            },
            "pricing": {
                "price_1m_input_tokens": 3.0,
                "price_1m_output_tokens": 15.0,
                ...
            }
        }
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    url = "https://artificialanalysis.ai/api/v2/data/llms/models"
    api_key = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")
    # Prepare request with User-Agent header and optional API key.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
    _LOG.info("Fetched %d models from Artificial Analysis API", len(lookup))
    _LOG.debug(
        "Return (first one):\n%s", pprint.pformat(dict(list(lookup.items())[:1]))
    )
    return lookup


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _normalize_model_name(name: str) -> str:
    """
    Normalize model name for consistent matching across all naming conventions.

    :param name: Model name in any of the three formats
    :return: Normalized slug format (lowercase, dashes, no dots)
        "anthropic/claude-opus-4.7" -> "claude-opus-4-7"
        "Anthropic: Claude Opus 4.7" -> "claude-opus-4-7"
        "claude-opus-4.7" -> "claude-opus-4-7"
        "claude-opus-4-7" -> "claude-opus-4-7"
    """
    normalized = name
    if "/" in normalized:
        normalized = normalized.split("/", 1)[1]
    if ":" in normalized:
        normalized = normalized.split(":", 1)[1].strip()
    normalized = normalized.replace(" ", "-").replace(".", "-").lower()
    return normalized


def _fetch_aa_benchmarks(model_name: str) -> Dict[str, Optional[float]]:
    """
    Fetch benchmark data from Artificial Analysis API using cached models.

    :param model_name: Model name in OpenRouter or AA format
    :return: Dict with "coding_score" and "intelligence_score" (None if not found)
        ```
        {'coding_score': None, 'intelligence_score': None}
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    aa_models = _fetch_all_aa_models()
    # Try exact match first (case-insensitive), then substring match.
    model_name_lower = model_name.lower()
    model_name_normalized = _normalize_model_name(model_name)
    model = None
    # Try direct lookups first.
    if model_name_lower in aa_models:
        model = aa_models[model_name_lower]
    elif model_name in aa_models:
        model = aa_models[model_name]
    elif model_name_normalized in aa_models:
        model = aa_models[model_name_normalized]
    else:
        for aa_name, aa_model in aa_models.items():
            if not isinstance(aa_name, str):
                continue
            aa_name_normalized = _normalize_model_name(aa_name)
            # Try normalized comparison first, then substring match
            if (
                model_name_normalized == aa_name_normalized
                or model_name_normalized in aa_name
                or aa_name_normalized in model_name_normalized
                or model_name.lower() in aa_name
                or aa_name in model_name.lower()
            ):
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
            coding_score = evaluations.get("artificial_analysis_coding_index")
    result = {
        "coding_score": coding_score,
        "intelligence_score": intelligence_score,
    }
    _LOG.debug("%s -> return:\n%s", model_name, pprint.pformat(result))
    return result


# #############################################################################
# Formatting Layer
# #############################################################################


def _format_cost(cost: float) -> str:
    """
    Format cost per 1M tokens with appropriate precision.

    Adjusts decimal places based on the magnitude of the cost value to keep
    numbers readable while preserving precision.

    :param cost: Cost value per 1M tokens (float)
    :return: Formatted cost string with 0-4 decimal places based on magnitude
        0.0 -> "0"
        0.000075 -> "0.0001"
        0.003 -> "0.003"
        0.5 -> "0.50"
        2.5 -> "2.50"
        15.0 -> "15.0"
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

    Converts context length to human-readable format with appropriate units.

    :param ctx: Context length in tokens (integer)
    :return: Human-readable string with K (thousands) or M (millions) suffix
        0 -> "0"
        500 -> "500"
        4000 -> "4K"
        128000 -> "128K"
        1000000 -> "1M"
        2000000 -> "2M"

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

    :param score: Benchmark score value or None
    :return: Formatted string with 1 decimal place, or empty string if None
        None -> ""
        0.0 -> "0.0"
        0.782 -> "0.8"
        72.345 -> "72.3"
        92.999 -> "93.0"
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
    Compute Efficiency metric = (Coding_Score × Throughput) / (Input_Cost + Output_Cost).

    Efficiency measures performance-per-dollar: higher scores are better.
    Formula helps identify models with good quality and speed at low cost.

    :param coding_score: Artificial Analysis coding index score (0-100 scale)
    :param throughput: Throughput in tokens/sec
    :param input_cost: Input cost per 1M tokens
    :param output_cost: Output cost per 1M tokens
    :return: Formatted integer string, "N/A" if data is missing or cost is zero
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

    Applies formatting to numerical columns for display:
    - Input_Cost, Output_Cost: formatted via _format_cost()
    - Context: formatted via _format_context()
    - Speed_(tok/s): formatted via _format_benchmark()
    - Coding_IQ, General_IQ: formatted via _format_benchmark()

    :param table: DataFrame with raw numerical data
        ```
        Model_ID | Input_Cost | Output_Cost | Context | Speed_(tok/s) | Coding_IQ
        ---
        openai/... | 0.003 | 0.015 | 128000 | 25.5 | 72.3
        ```

    :return: DataFrame with formatted string columns for display
        ```
        Model_ID | Input_Cost | Output_Cost | Context | Speed_(tok/s) | Coding_IQ
        ---
        openai/... | "0.003" | "0.015" | "128K" | "25.5" | "72.3"
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    table = table.copy()
    if "Input_Cost" in table.columns:
        table["Input_Cost"] = table["Input_Cost"].apply(_format_cost)
    if "Output_Cost" in table.columns:
        table["Output_Cost"] = table["Output_Cost"].apply(_format_cost)
    if "Context" in table.columns:
        table["Context"] = table["Context"].apply(_format_context)
    if "Speed_(tok/s)" in table.columns:
        table["Speed_(tok/s)"] = table["Speed_(tok/s)"].apply(
            lambda x: _format_benchmark(x) if x is not None else ""
        )
    if "Coding_IQ" in table.columns:
        table["Coding_IQ"] = table["Coding_IQ"].apply(_format_benchmark)
    if "General_IQ" in table.columns:
        table["General_IQ"] = table["General_IQ"].apply(_format_benchmark)
    return table


# #############################################################################
# Data Processing Layer
# #############################################################################


def _read_model_ids_from_file(models_file: str) -> List[str]:
    """
    Read model IDs from a text file, one per line.

    Supports both short and full model name formats:
    - Short name: "claude-opus-4.7"
    - Full OpenRouter ID: "anthropic/claude-4.7-opus-20260416"
    - Short OpenRouter ID: "google/gemini-3.1-pro-preview"

    File format:
    - One model ID per line
    - Lines starting with '#' are comments and ignored
    - Empty lines are ignored

    :param models_file: Path to the text file
    :return: List of model ID strings (comments and empty lines filtered out)
        - E.g.,
        ```
        ['claude-opus-4.7', 'google/gemini-3.1-pro-preview', 'openai/gpt-4-omni']
        ```
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
    hdbg.dassert_lt(
        0, len(model_ids), "Models file must contain at least one model ID"
    )
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


def _resolve_model_ids(model_ids: List[str]) -> List[str]:
    """
    Resolve short model names to their full OpenRouter API versions.

    For each model ID, tries to match it to the full versioned name used by
    the OpenRouter API using exact and fuzzy matching. If no match is found,
    returns the original name.

    Input formats:
    - Short name: "claude-opus-4.7"
    - Short OpenRouter ID: "google/gemini-3.1-pro-preview"
    - Full OpenRouter ID: "anthropic/claude-4.7-opus-20260416"

    Output format:
    - Full OpenRouter ID: "anthropic/claude-4.7-opus-20260416"

    :param model_ids: List of model IDs (any mix of short/full names)
        E.g., `["claude-opus-4.7", "gpt-4o"]`
    :return: List of resolved full OpenRouter IDs
        E.g., `['anthropic/claude-4.7-opus-20260416', 'openai/gpt-4-omni']`
    """
    _LOG.debug(hprint.func_signature_to_str())
    _LOG.info("Building model name resolution map...")
    short_to_full = _build_short_to_full_model_map()
    resolved_ids: List[str] = []
    for model_id in model_ids:
        resolved = _resolve_model_name(model_id, short_to_full)
        if resolved != model_id:
            _LOG.info("Resolved '%s' -> '%s'", model_id, resolved)
        resolved_ids.append(resolved)
    return resolved_ids


def _build_model_ids_dataframe(
    model_ids: List[str],
) -> pd.DataFrame:
    """
    Build minimal dataframe with just model IDs for merging purposes.

    Creates a base dataframe to which other dataframes (pricing, benchmarks,
    throughput, usage) are merged using the Model_ID column.

    Input format:
    - Full OpenRouter ID: "google/gemini-3.1-pro-preview" or
      "anthropic/claude-4.7-opus-20260416"

    :param model_ids: List of resolved model IDs (full OpenRouter format)
    :return: DataFrame with single Model_ID column
    """
    _LOG.debug(hprint.func_signature_to_str())
    data = [[model_id] for model_id in model_ids]
    columns = ["Model_ID"]
    df = pd.DataFrame(data=data, columns=columns)  # type: ignore
    _LOG.info("Built model IDs dataframe with %d rows", len(df))
    return df


def _build_openrouter_pricing_dataframe(
    model_ids: List[str],
    api_lookup: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    """
    Build dataframe with OpenRouter pricing and context data.

    Fetches pricing information from the OpenRouter API lookup dict.
    Costs are stored per 1M tokens (not per-token).

    :param model_ids: List of full OpenRouter IDs (e.g., "openai/gpt-4-omni")
    :param api_lookup: Dict from _fetch_models_from_api() with pricing/context
    :return: DataFrame with columns: Model_ID, Name, Input_Cost, Output_Cost, Context
        ```
        Model_ID | Name | Input_Cost | Output_Cost | Context
        ---
        openai/gpt-4-omni | "OpenAI: GPT-4 Omni" | 2.5 | 10.0 | 128000
        anthropic/claude-opus | "Anthropic: Claude Opus" | 3.0 | 15.0 | 200000
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    rows: List[List[Any]] = []
    for model_id in model_ids:
        _LOG.debug("Fetching pricing for %s", model_id)
        if model_id not in api_lookup:
            _LOG.warning(
                "Can't find '%s' in the OpenRouter API data: skipping", model_id
            )
            continue
        api_data = api_lookup[model_id]
        name = str(api_data["name"])
        input_cost = float(api_data["input_cost"])
        output_cost = float(api_data["output_cost"])
        context = int(api_data["context_length"])
        row = [
            model_id,
            name,
            input_cost,
            output_cost,
            context,
        ]
        _LOG.debug("row=%s", row)
        rows.append(row)
    columns = [
        "Model_ID",
        "Name",
        "Input_Cost",
        "Output_Cost",
        "Context",
    ]
    df = pd.DataFrame(data=rows, columns=columns)  # type: ignore
    _LOG.info("Built OpenRouter pricing dataframe with %d rows", len(df))
    return df


def _build_aa_benchmarks_dataframe(
    model_ids: List[str],
    api_lookup: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    """
    Build dataframe with Artificial Analysis benchmark scores.

    Fetches benchmark scores from the Artificial Analysis API by model name.
    Scores come from the OpenRouter API name field (e.g., "Anthropic: Claude Opus").

    :param model_ids: List of resolved full OpenRouter model IDs
    :param api_lookup: Dict from _fetch_models_from_api() with display names
    :return: DataFrame with columns: Model_ID, Coding_IQ, General_IQ
        ```
        Model_ID | Coding_IQ | General_IQ
        ---
        openai/gpt-4-omni | 75.2 | 88.5
        anthropic/claude-opus | 72.3 | 85.2
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    rows: List[List[Any]] = []
    for model_id in model_ids:
        _LOG.debug("Fetching AA benchmarks for %s", model_id)
        if model_id not in api_lookup:
            _LOG.debug("Skipping %s (not in API lookup)", model_id)
            continue
        api_data = api_lookup[model_id]
        name = str(api_data["name"])
        benchmarks = _fetch_aa_benchmarks(name)
        coding_score = benchmarks.get("coding_score")
        intelligence_score = benchmarks.get("intelligence_score")
        row = [
            model_id,
            coding_score,
            intelligence_score,
        ]
        _LOG.debug("row=%s", row)
        rows.append(row)
    columns = ["Model_ID", "Coding_IQ", "General_IQ"]
    df = pd.DataFrame(data=rows, columns=columns)  # type: ignore
    _LOG.info("Built AA benchmarks dataframe with %d rows", len(df))
    return df


def _build_openrouter_throughput_dataframe(
    model_ids: List[str],
) -> pd.DataFrame:
    """
    Build dataframe with OpenRouter throughput data.

    Fetches p50_throughput metric (50th percentile) from OpenRouter model pages.

    :param model_ids: List of resolved full OpenRouter model IDs
    :return: DataFrame with columns: Model_ID, Speed_(tok/s) (in tokens/second)
        ```
        Model_ID | Speed_(tok/s)
        ---
        openai/gpt-4-omni | 25.5
        anthropic/claude-opus | 18.2
        deepseek/deepseek-chat | None
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    rows: List[List[Any]] = []
    for model_id in model_ids:
        _LOG.debug("Fetching throughput for %s", model_id)
        throughput = _fetch_openrouter_throughput(model_id)
        row = [
            model_id,
            throughput,
        ]
        _LOG.debug("row=%s", row)
        rows.append(row)
    columns = ["Model_ID", "Speed_(tok/s)"]
    df = pd.DataFrame(data=rows, columns=columns)  # type: ignore
    _LOG.info("Built throughput dataframe with %d rows", len(df))
    return df


def _build_openrouter_per_model_usage_dataframe(
    model_ids: List[str],
) -> pd.DataFrame:
    """
    Build dataframe with OpenRouter per-model usage statistics.

    Fetches usage data from OpenRouter rankings API and aggregates by date range.
    Note: Uses model_permaslug (from rankings API) which may differ from full
    OpenRouter model IDs.

    :param model_ids: List of resolved full OpenRouter model IDs
    :return: DataFrame with columns: Model_ID, Week_Tokens, Month_Tokens
        ```
        Model_ID | Week_Tokens | Month_Tokens
        ---
        gpt-4-omni | 1234567890 | 5678901234
        claude-opus | 987654321 | 4567890123
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    per_model_usage = _fetch_openrouter_per_model_usage()
    rows: List[List[Any]] = []
    for model_id in model_ids:
        _LOG.debug("Fetching usage for %s", model_id)
        usage_data = per_model_usage.get(model_id, {})
        week_tokens = usage_data.get("week_tokens", 0)
        month_tokens = usage_data.get("month_tokens", 0)
        row = [
            model_id,
            week_tokens,
            month_tokens,
        ]
        _LOG.debug("row=%s", row)
        rows.append(row)
    columns = ["Model_ID", "Week_Tokens", "Month_Tokens"]
    df = pd.DataFrame(data=rows, columns=columns)  # type: ignore
    _LOG.info("Built per-model usage dataframe with %d rows", len(df))
    return df


def _merge_dataframes(
    base_df: pd.DataFrame,
    dataframes: List[pd.DataFrame],
) -> pd.DataFrame:
    """
    Merge action-specific dataframes with the base dataframe.

    Performs left join on Model_ID column to combine data from multiple sources.
    Dataframes are merged in order provided.

    :param base_df: Base dataframe with Model_ID (typically from pricing action)
    :param dataframes: List of action-specific dataframes (benchmarks, throughput, usage)
    :return: Merged dataframe with all columns from all input dataframes
    """
    _LOG.debug(hprint.func_signature_to_str())
    result = base_df.copy()
    for df in dataframes:
        result = result.merge(df, on="Model_ID", how="left")
    _LOG.info(
        "Merged dataframe has %d rows and %d columns",
        len(result),
        len(result.columns),
    )
    return result


def calc_efficiency(row: pd.Series) -> str:
    """
    Calculate efficiency score for a model row (applied via DataFrame.apply).

    Efficiency = (Coding_IQ × Speed_(tok/s)) / (Input_Cost + Output_Cost)

    This function is used as a callback for DataFrame.apply(axis=1) to compute
    efficiency across all rows.

    :param row: pandas Series representing a single model row
    :return: Formatted efficiency string or "N/A" if data missing
    """
    if "Input_Cost" not in row.index or "Output_Cost" not in row.index:
        return "N/A"
    coding_iq_val = row["Coding_IQ"]
    speed_val = row["Speed_(tok/s)"]
    coding_iq: Optional[float] = (
        None
        if coding_iq_val is None
        or (isinstance(coding_iq_val, float) and pd.isna(coding_iq_val))
        else float(coding_iq_val)
    )
    speed: Optional[float] = (
        None
        if speed_val is None
        or (isinstance(speed_val, float) and pd.isna(speed_val))
        else float(speed_val)
    )
    input_cost = float(row["Input_Cost"])
    output_cost = float(row["Output_Cost"])
    return _format_efficiency(coding_iq, speed, input_cost, output_cost)


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
        "openrouter_pricing",
        "aa_benchmarks",
        "openrouter_throughput",
        "openrouter_per_model_usage",
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
        "openrouter_pricing",
        "aa_benchmarks",
        "openrouter_throughput",
        "openrouter_per_model_usage",
    ]
    default_actions = valid_actions
    actions = hselacti.select_actions(args, valid_actions, default_actions)
    print(hselacti.actions_to_string(actions, valid_actions, add_frame=True))
    # Read the models from file or list.
    if args.models_from_file:
        model_ids = _read_model_ids_from_file(args.models_from_file)
    else:
        model_ids = _read_model_ids_from_list(args.models_list)
    # Resolve short model names to full OpenRouter API versions.
    model_ids = _resolve_model_ids(model_ids)
    _LOG.debug("model_ids=%s", str(model_ids))
    # Start with minimal dataframe containing just model IDs.
    table = _build_model_ids_dataframe(model_ids)
    _LOG.info("Model IDs DataFrame:\n%s", table.to_string())
    # Build and merge action-specific dataframes.
    dataframes_to_merge: List[pd.DataFrame] = []
    actions_copy = list(actions)
    # Check which actions need API data.
    needs_api_data = (
        "openrouter_pricing" in actions or "aa_benchmarks" in actions
    )
    api_lookup: Dict[str, Dict[str, Any]] = {}
    if needs_api_data:
        api_lookup = _fetch_models_from_api()
        _LOG.debug("api_lookup=%s", api_lookup.keys())
    # Build pricing dataframe.
    to_exec_pricing, actions_copy = hselacti.mark_action(
        "openrouter_pricing", actions_copy
    )
    if to_exec_pricing:
        pricing_df = _build_openrouter_pricing_dataframe(model_ids, api_lookup)
        _LOG.debug("OpenRouter Pricing DataFrame:\n%s", pricing_df.to_string())
        dataframes_to_merge.append(pricing_df)
    # Build benchmarks dataframe.
    to_exec_benchmarks, actions_copy = hselacti.mark_action(
        "aa_benchmarks", actions_copy
    )
    if to_exec_benchmarks:
        benchmarks_df = _build_aa_benchmarks_dataframe(model_ids, api_lookup)
        _LOG.debug("AA Benchmarks DataFrame:\n%s", benchmarks_df.to_string())
        dataframes_to_merge.append(benchmarks_df)
    to_exec_throughput, actions_copy = hselacti.mark_action(
        "openrouter_throughput", actions_copy
    )
    if to_exec_throughput:
        throughput_df = _build_openrouter_throughput_dataframe(model_ids)
        _LOG.debug(
            "OpenRouter Throughput DataFrame:\n%s", throughput_df.to_string()
        )
        dataframes_to_merge.append(throughput_df)
    to_exec_usage, actions_copy = hselacti.mark_action(
        "openrouter_per_model_usage", actions_copy
    )
    if to_exec_usage:
        usage_df = _build_openrouter_per_model_usage_dataframe(model_ids)
        _LOG.debug(
            "OpenRouter Per-Model Usage DataFrame:\n%s", usage_df.to_string()
        )
        dataframes_to_merge.append(usage_df)
    # Merge all dataframes.
    if dataframes_to_merge:
        table = _merge_dataframes(table, dataframes_to_merge)
        _LOG.debug("Merged DataFrame:\n%s", table.to_string())
    # Add efficiency column if all required columns are present.
    if (
        "Coding_IQ" in table.columns
        and "Speed_(tok/s)" in table.columns
        and "Input_Cost" in table.columns
        and "Output_Cost" in table.columns
    ):
        table["Efficiency"] = table.apply(calc_efficiency, axis=1)
    # Format and display the table.
    table = _format_table(table)
    print(table.to_string())


if __name__ == "__main__":
    _main(_parse())
