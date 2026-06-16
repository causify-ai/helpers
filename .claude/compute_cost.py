#!/usr/bin/env python3
"""
Compute Claude Code session cost from token counts and model key.

Reads CC_MODEL env var (set by helpers_root/dev_scripts_helpers/ai/cc) which
holds the full model string (e.g. "deepseek/deepseek-v4-flash"), looks up
the pricing table, and prints the computed cost.

Usage:
> compute_cost.py <model_display_name> <model_api_model> <in_tok> <out_tok> [reported_cost]

Positional arguments:
    model_display_name  - model.display_name from the JSON statusline input
    model_api_model     - model.api_model from the JSON input ("" if absent)
    in_tok              - total_input_tokens
    out_tok             - total_output_tokens
    reported_cost       - fallback cost when model is not in pricing table (default "0")

The script matches CC_MODEL against known model substrings.  If no match is
found, it falls back to the reported cost from the API.
"""

import os
import sys
from typing import List, Optional, Tuple


# Pricing table

# Each entry: (cc_model_substring, input_price_per_1k, output_price_per_1k).
# First match wins, so order specific entries first.
# Values are USD per 1 000 tokens.
# Keep in sync with helpers_root/dev_scripts_helpers/ai/cc.
PRICING_ENTRIES: List[Tuple[str, float, float]] = [
    ("deepseek/deepseek-v4-flash", 0.000098, 0.000196),
    ("deepseek/deepseek-v4-pro", 0.000435, 0.00087),
    ("inception/mercury-2", 0.00025, 0.00075),
    ("anthropic/claude-haiku-4.5", 0.001, 0.005),
    # Direct Anthropic fallback tiers — match on the display name / api model.
    # These are used when CC_MODEL is empty (--anth) and we fall through to
    # match on the model display name from the JSON status line.
    ("fable", 0.01, 0.05),
    ("opus", 0.005, 0.025),
    ("sonnet", 0.003, 0.015),
    ("haiku", 0.001, 0.005),
]


def lookup_prices(key: str) -> Optional[Tuple[float, float]]:
    """
    Find the pricing pair whose substring matches the given key.

    Iterates through the pricing table and returns the first matching entry.
    Matching is done via substring search: if `key` contains the pricing
    entry's substring, that entry is returned.

    :param key: String to search for in the pricing table (e.g., model name)
    :return: Tuple of (input_price_per_1k, output_price_per_1k) in USD
        - Returns None if no entry matches the key
    """
    for substring, in_price, out_price in PRICING_ENTRIES:
        if substring in key:
            return (in_price, out_price)
    return None


def compute_cost(
    cc_model: str,
    model_display: str,
    model_api: str,
    in_tok: int,
    out_tok: int,
) -> Optional[float]:
    """
    Compute cost from token counts using pricing for the given model.

    Attempts to find pricing information for the provided model by:
    1. Matching against `cc_model` (the full model string from the cc script)
       against the `PRICING_ENTRIES` table
    2. If no match and `cc_model` is empty (direct Anthropic path), tries
       matching against the combined `model_display` + `model_api` string

    :param cc_model: Full model string to match against pricing table
        (e.g., "deepseek/deepseek-v4-flash")
    :param model_display: Model display name from JSON statusline input
    :param model_api: Model API model from JSON input (empty string if absent)
    :param in_tok: Total input tokens used in the session
    :param out_tok: Total output tokens used in the session
    :return: Computed cost in USD as a float
        - Returns None if no pricing entry matches the model
    """
    prices = lookup_prices(cc_model)
    if prices is None and not cc_model:
        # For direct Anthropic (CC_MODEL is empty), fall back to matching
        # on the model display name from the JSON.
        fallback_key = f"{model_display} {model_api}"
        prices = lookup_prices(fallback_key)
    if prices is None:
        return None
    in_price, out_price = prices
    return (in_tok * in_price + out_tok * out_price) / 1000.0


def main() -> None:
    """
    Main entry point: parse arguments and compute the session cost.

    Reads command-line arguments for model names and token counts, attempts
    to compute cost using the pricing table via `compute_cost()`, and falls
    back to reported cost if no pricing entry matches.
    """
    cc_model = os.environ.get("CC_MODEL", "")
    # Validate minimum argument count.
    if len(sys.argv) < 5:
        print("", end="")
        return
    # Parse model names.
    model_display = sys.argv[1]
    model_api = sys.argv[2]
    # Parse token counts.
    try:
        in_tok = int(sys.argv[3])
        out_tok = int(sys.argv[4])
    except ValueError:
        print("", end="")
        return
    # Extract optional reported cost fallback.
    reported_cost_str = sys.argv[5] if len(sys.argv) > 5 else "0"
    # Attempt to compute cost from pricing table.
    cost = compute_cost(cc_model, model_display, model_api, in_tok, out_tok)
    if cost is not None:
        print(f"{cost:.4f}")
    else:
        # Fallback: use the reported cost from the API.
        try:
            print(f"{float(reported_cost_str):.4f}")
        except ValueError:
            print("0.0000")


if __name__ == "__main__":
    main()
