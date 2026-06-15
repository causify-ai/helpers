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


# ---------------------------------------------------------------------------
# Pricing table
# ---------------------------------------------------------------------------
# Each entry: (cc_model_substring, input_price_per_1k, output_price_per_1k).
# First match wins, so order specific entries first.
# Values are USD per 1 000 tokens.
# Keep in sync with helpers_root/dev_scripts_helpers/ai/cc.
PRICING_ENTRIES: list[tuple[str, float, float]] = [
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


def lookup_prices(key: str) -> tuple[float, float] | None:
    """
    Find the (input_price, output_price) pair whose substring matches *key*.

    Returns None if no entry matches.
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
) -> float | None:
    """
    Compute cost from token counts using pricing for *cc_model*.

    Strategy:
      1. Try to match *cc_model* (the full model string from the cc script)
         against the pricing table.
      2. If no match and *cc_model* is empty (--anth path), try matching on
         the combined model display name + api model string.
      3. Returns cost in USD, or *None* if no pricing entry matches.
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
    cc_model = os.environ.get("CC_MODEL", "")

    if len(sys.argv) < 5:
        print("", end="")
        return

    model_display = sys.argv[1]
    model_api = sys.argv[2]
    try:
        in_tok = int(sys.argv[3])
        out_tok = int(sys.argv[4])
    except ValueError:
        print("", end="")
        return

    reported_cost_str = sys.argv[5] if len(sys.argv) > 5 else "0"

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
