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
import datetime
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


# There are several representations of model names:
# - Short model name: "claude-opus-4.7"
# - Short OpenRouter ID: "google/gemini-3.1-pro-preview" (provider/model-name)
# - Full versioned OpenRouter ID: "anthropic/claude-4.7-opus-20260416"
# - Artificial Analysis slug: "claude-opus-4-7"

OpenRouterId = str
AaSlug = str
OpenRouterPermaslug = str

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
        _, model_name = model_id.split("/", 1)
        short_to_full[model_name.lower()] = model_id
        short_to_full[model_id.lower()] = model_id
    return short_to_full


def _normalize_for_fuzzy_matching(name: str) -> str:
    """
    Normalize a model name by removing version suffixes and dates for fuzzy matching.

    Removes version numbers, dates, and provider prefixes to enable fuzzy matching.

    Internal helper only—called at the input boundary in
    _normalize_input_to_openrouter_ids.

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


def _normalize_for_aa_lookup(name: str) -> AaSlug:
    """
    Normalize model name to Artificial Analysis slug format.

    Converts any model name representation to the AA slug format (lowercase,
    dashes, no dots). Called once during mapping table construction.

    :param name: Model name in any format
    :return: Normalized slug format
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


# #############################################################################
# Fetch data
# #############################################################################


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
    today = datetime.datetime.now().date()
    week_ago = today - datetime.timedelta(days=7)
    month_ago = today - datetime.timedelta(days=30)
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
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
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


def _build_openrouter_id_to_permaslug(
    api_lookup: Dict[str, Dict[str, Any]],
    available_permaslugs: Optional[List[str]] = None,
) -> Dict[OpenRouterId, OpenRouterPermaslug]:
    """
    Build mapping from full OpenRouter ID to permaslug (for rankings API).

    Since canonical_slug is not available in the API, uses fuzzy matching against
    available permaslugs from the rankings API. Matches by normalized model name.

    :param api_lookup: Dict from _fetch_models_from_api()
    :param available_permaslugs: List of permaslugs from rankings API (optional)
    :return: Dict mapping OpenRouterId to OpenRouterPermaslug
    """
    _LOG.debug(hprint.func_signature_to_str())
    result: Dict[OpenRouterId, OpenRouterPermaslug] = {}
    hdbg.dassert(available_permaslugs,
        "No available permaslugs provided")
    for model_id in api_lookup.keys():
        # Skip entries without provider prefix (e.g., canonical_slug aliases).
        if "/" not in model_id:
            continue
        model_id_lower = model_id.lower()
        best_match = None
        best_match_score = 0
        # Try multiple matching strategies in order of confidence:
        # 1. Full model ID substring match (highest confidence)
        # 2. Model name exact match after splitting by "/"
        # 3. Model name substring match
        # 4. Normalized fuzzy match
        # 5. Normalized substring match (lowest confidence)
        for permaslug in available_permaslugs:
            permaslug_lower = permaslug.lower()
            # Strategy 1: Check if full model_id appears in permaslug (e.g.,
            # "openai/gpt-4-omni" contains "openai/gpt-4-omni" exactly).
            if model_id_lower in permaslug_lower:
                best_match = permaslug
                best_match_score = 3
                break
            # Strategy 2: Extract and compare just the model names after "/" to handle
            # different provider prefixes (e.g., "gpt-4-omni" == "gpt-4-omni").
            _, model_name = model_id.split("/", 1)
            if "/" in permaslug:
                _, permaslug_name = permaslug.split("/", 1)
            else:
                permaslug_name = permaslug
            if model_name.lower() == permaslug_name.lower():
                best_match = permaslug
                best_match_score = 3
                break
            # Strategy 3: Substring match on model names (handles partial names).
            if model_name.lower() in permaslug_name.lower():
                if best_match_score < 2:
                    best_match = permaslug
                    best_match_score = 2
            # Strategy 4 & 5: Normalize both strings (remove versions, dates) for
            # fuzzy matching. Handles "claude-3.5" == "claude-3-5" after normalization.
            normalized_model = _normalize_for_fuzzy_matching(model_id)
            normalized_perma = _normalize_for_fuzzy_matching(permaslug)
            if normalized_model == normalized_perma:
                if best_match_score < 2:
                    best_match = permaslug
                    best_match_score = 2
            elif (normalized_model in normalized_perma and
                  len(normalized_model) > 5):
                # Only accept short normalized names as substrings if they're long
                # enough (>5 chars) to avoid false positives (e.g., "gpt" matching
                # "gpt-4-omni", "gpt-4-vision", etc.).
                if best_match_score < 1:
                    best_match = permaslug
                    best_match_score = 1
        if best_match:
            result[model_id] = best_match
            _LOG.debug("Mapped %s -> %s (score=%f)", model_id, best_match, best_match_score)
        else:
            _LOG.debug("No permaslug match found for %s", model_id)
    _LOG.info("Built permaslug mapping with %d entries", len(result))
    return result


def _build_openrouter_id_to_aa_slug(
    api_lookup: Dict[str, Dict[str, Any]],
    aa_models: Dict[str, Dict[str, Any]],
) -> Dict[OpenRouterId, AaSlug]:
    """
    Build mapping from OpenRouter ID to Artificial Analysis slug.

    Iterates OR models, normalizes each OR display name to AA slug format,
    and looks up in the AA dict. All matching happens here once.

    :param api_lookup: Dict from _fetch_models_from_api()
    :param aa_models: Dict from _fetch_all_aa_models()
    :return: Dict mapping OpenRouterId to AaSlug (or None if not found)
    """
    _LOG.debug(hprint.func_signature_to_str())
    result: Dict[OpenRouterId, AaSlug] = {}
    for model_id, data in api_lookup.items():
        if "/" not in model_id:
            continue
        or_display_name = str(data.get("name", ""))
        aa_slug = _normalize_for_aa_lookup(or_display_name)
        if aa_slug in aa_models:
            result[model_id] = aa_slug
            _LOG.debug("Matched OR id %s to AA slug %s", model_id, aa_slug)
        else:
            _LOG.debug("No AA match for OR id %s (tried slug %s)", model_id, aa_slug)
    return result


def _fetch_aa_benchmarks(aa_slug: AaSlug) -> Dict[str, Optional[float]]:
    """
    Fetch benchmark data from Artificial Analysis API by slug.

    Direct slug lookup, no fuzzy matching. Slug must already be in AA format.

    :param aa_slug: AA slug (e.g., "claude-opus-4-7")
    :return: Dict with "coding_score" and "intelligence_score" (None if not found)
        ```
        {'coding_score': None, 'intelligence_score': None}
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    aa_models = _fetch_all_aa_models()
    model = aa_models.get(aa_slug)
    coding_score = None
    intelligence_score = None
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
    _LOG.debug("%s -> return:\n%s", aa_slug, pprint.pformat(result))
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


def _format_tokens(tokens: int) -> str:
    """
    Format token count as human-readable string.

    Converts token counts to human-readable format with appropriate units.

    :param tokens: Token count (integer)
    :return: Human-readable string with B (billions), M (millions), or K (thousands) suffix
        0 -> "0"
        500 -> "500"
        1500000 -> "1.5M"
        1500000000 -> "1.5B"
        1234567890123 -> "1234.6B"
    """
    if tokens >= 1_000_000_000:
        result = f"{tokens / 1_000_000_000:.1f}B"
    elif tokens >= 1_000_000:
        result = f"{tokens / 1_000_000:.1f}M"
    elif tokens >= 1_000:
        result = f"{tokens // 1_000}K"
    else:
        result = str(tokens)
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
    - Week_Tokens, Month_Tokens: formatted via _format_tokens()
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
    if "Week_Tokens" in table.columns:
        table["Week_Tokens"] = table["Week_Tokens"].apply(
            lambda x: _format_tokens(int(x)) if x and x > 0 else "0"
        )
    if "Month_Tokens" in table.columns:
        table["Month_Tokens"] = table["Month_Tokens"].apply(
            lambda x: _format_tokens(int(x)) if x and x > 0 else "0"
        )
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


def _normalize_input_to_openrouter_ids(model_ids: List[str]) -> List[OpenRouterId]:
    """
    Resolve short model names to their full OpenRouter API versions.

    This is the sole boundary where user-supplied strings (in any format) are
    converted to canonical OpenRouterId (full versioned OR ID). All functions
    downstream work with OpenRouterId exclusively.

    Input formats:
    - Short name: "claude-opus-4.7"
    - Short OpenRouter ID: "google/gemini-3.1-pro-preview"
    - Full OpenRouter ID: "anthropic/claude-4.7-opus-20260416"

    Output format:
    - Full OpenRouter ID: "anthropic/claude-4.7-opus-20260416"

    :param model_ids: List of model IDs (any mix of short/full names)
    :return: List of resolved full OpenRouter IDs
    """
    _LOG.debug(hprint.func_signature_to_str())
    _LOG.info("Building model name resolution map...")
    short_to_full = _build_short_to_full_model_map()
    resolved_ids: List[OpenRouterId] = []
    for model_id in model_ids:
        short_lower = model_id.lower()
        if short_lower in short_to_full:
            resolved = short_to_full[short_lower]
        elif model_id in short_to_full:
            resolved = short_to_full[model_id]
        else:
            normalized = _normalize_for_fuzzy_matching(model_id)
            resolved = None
            for full_value in short_to_full.values():
                full_normalized = _normalize_for_fuzzy_matching(full_value)
                if normalized in full_normalized or full_normalized in normalized:
                    _LOG.info("Matched '%s' to '%s' via fuzzy match", model_id, full_value)
                    resolved = full_value
                    break
            if resolved is None:
                resolved = model_id
                _LOG.debug("No match found for '%s', returning original", model_id)
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
    model_ids: List[OpenRouterId],
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
    model_ids: List[OpenRouterId],
    id_to_aa_slug: Dict[OpenRouterId, AaSlug],
) -> pd.DataFrame:
    """
    Build dataframe with Artificial Analysis benchmark scores.

    Uses prebuilt mapping from OpenRouterId to AA slug for direct lookups.

    :param model_ids: List of full OpenRouter IDs
    :param id_to_aa_slug: Prebuilt mapping from _build_openrouter_id_to_aa_slug()
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
        aa_slug = id_to_aa_slug.get(model_id)
        if not aa_slug:
            _LOG.debug("No AA slug mapping for %s, skipping", model_id)
            continue
        benchmarks = _fetch_aa_benchmarks(aa_slug)
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
    model_ids: List[OpenRouterId],
) -> pd.DataFrame:
    """
    Build dataframe with OpenRouter throughput data.

    Fetches p50_throughput metric (50th percentile) from OpenRouter model pages.

    :param model_ids: List of full OpenRouter model IDs
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
    model_ids: List[OpenRouterId],
    id_to_permaslug: Dict[OpenRouterId, OpenRouterPermaslug],
    per_model_usage: Optional[Dict[str, Dict[str, Any]]] = None,
) -> pd.DataFrame:
    """
    Build dataframe with OpenRouter per-model usage statistics.

    Uses prebuilt permaslug mapping to translate full OR IDs to rankings API keys.

    :param model_ids: List of full OpenRouter model IDs
    :param id_to_permaslug: Prebuilt mapping from _build_openrouter_id_to_permaslug()
    :param per_model_usage: Pre-fetched usage data from _fetch_openrouter_per_model_usage()
    :return: DataFrame with columns: Model_ID, Week_Tokens, Month_Tokens
        ```
        Model_ID | Week_Tokens | Month_Tokens
        ---
        gpt-4-omni | 1234567890 | 5678901234
        claude-opus | 987654321 | 4567890123
        ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    _LOG.debug("id_to_permaslug has %d entries", len(id_to_permaslug))
    if per_model_usage is None:
        per_model_usage = _fetch_openrouter_per_model_usage()
    if per_model_usage is None:
        per_model_usage = {}
    _LOG.debug("per_model_usage has %d entries", len(per_model_usage))
    _LOG.debug("Available permaslugs: %s", list(per_model_usage.keys())[:10])
    rows: List[List[Any]] = []
    for model_id in model_ids:
        _LOG.debug("Fetching usage for %s", model_id)
        permaslug = id_to_permaslug.get(model_id)
        _LOG.debug("  permaslug=%s", permaslug)
        if permaslug:
            usage_data = per_model_usage.get(permaslug, {})
            _LOG.debug("  usage_data=%s", usage_data)
        else:
            _LOG.debug("  No permaslug mapping found for %s", model_id)
            usage_data = {}
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
    # Normalize to canonical OpenRouter IDs (boundary: only place with fuzzy logic).
    model_ids = _normalize_input_to_openrouter_ids(model_ids)
    _LOG.debug("model_ids=%s", str(model_ids))
    # Start with minimal dataframe containing just model IDs.
    table = _build_model_ids_dataframe(model_ids)
    _LOG.info("Model IDs DataFrame:\n%s", table.to_string())
    # Build mapping tables once (needed by multiple dataframe builders).
    api_lookup: Dict[str, Dict[str, Any]] = {}
    aa_models: Dict[str, Dict[str, Any]] = {}
    id_to_aa_slug: Dict[OpenRouterId, AaSlug] = {}
    id_to_permaslug: Dict[OpenRouterId, OpenRouterPermaslug] = {}
    per_model_usage_raw: Dict[str, Dict[str, Any]] = {}
    needs_api_data = (
        "openrouter_pricing" in actions
        or "aa_benchmarks" in actions
        or "openrouter_per_model_usage" in actions
    )
    if needs_api_data:
        api_lookup = _fetch_models_from_api()
        _LOG.debug("api_lookup has %d entries", len(api_lookup))
    if "aa_benchmarks" in actions:
        aa_models = _fetch_all_aa_models()
        id_to_aa_slug = _build_openrouter_id_to_aa_slug(api_lookup, aa_models)
        _LOG.debug("id_to_aa_slug has %d entries", len(id_to_aa_slug))
    if "openrouter_per_model_usage" in actions:
        per_model_usage_raw = _fetch_openrouter_per_model_usage()
        available_permaslugs = list(per_model_usage_raw.keys())
        id_to_permaslug = _build_openrouter_id_to_permaslug(
            api_lookup, available_permaslugs
        )
        _LOG.debug("id_to_permaslug has %d entries", len(id_to_permaslug))
    # Build and merge action-specific dataframes.
    dataframes_to_merge: List[pd.DataFrame] = []
    actions_copy = list(actions)
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
        benchmarks_df = _build_aa_benchmarks_dataframe(model_ids, id_to_aa_slug)
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
        usage_df = _build_openrouter_per_model_usage_dataframe(
            model_ids, id_to_permaslug, per_model_usage_raw if per_model_usage_raw else None
        )
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
