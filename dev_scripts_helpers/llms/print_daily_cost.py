#!/usr/bin/env python

"""
Print daily costs for OpenAI and Anthropic API usage.

This script queries the OpenAI and Anthropic billing APIs to retrieve cost
data for today (or a specified date range) and displays it in a formatted
table.

Requirements:
- OPENAI_API_KEY environment variable for OpenAI costs
- ANTHROPIC_KEY environment variable for Anthropic costs

Example usage:
# Print today's costs
> print_daily_cost.py

# Print costs with debug logging
> print_daily_cost.py -v DEBUG

# Print costs for a specific date
> print_daily_cost.py --date 2025-12-30

Import as:

import dev_scripts_helpers.llms.print_daily_cost as dslprdc
"""

# For OpenAI:
#
# You need one of:
# 1. Organization admin key - Create one in your OpenAI organization settings
# 2. Service account key with billing read permissions
# 3. Or use the OpenAI web dashboard at https://platform.openai.com/usage for cost data
#
# For Anthropic:
#
# You need:
# 1. Admin API key - Available in the Anthropic Console under organization settings
# 2. Must have admin role in your organization
# 3. The admin key has a different format/permissions than regular API keys

import argparse
import datetime
import logging
import os
from typing import Dict, Optional

import requests

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# #############################################################################


def _get_openai_daily_cost(
    date: datetime.date,
    *,
    api_key: Optional[str] = None,
) -> Optional[float]:
    """
    Fetch daily cost from OpenAI Costs API.

    :param date: date for which to fetch costs
    :param api_key: OpenAI API key (uses OPENAI_API_KEY env var if None)
    :return: total cost in USD, or None if request fails
    """
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        _LOG.warning("OPENAI_API_KEY not found in environment")
        return None
    # Convert date to Unix timestamps (start and end of day in UTC).
    start_datetime = datetime.datetime.combine(
        date, datetime.time.min, tzinfo=datetime.timezone.utc
    )
    end_datetime = datetime.datetime.combine(
        date, datetime.time.max, tzinfo=datetime.timezone.utc
    )
    start_time = int(start_datetime.timestamp())
    end_time = int(end_datetime.timestamp())
    # Make API request.
    endpoint = "https://api.openai.com/v1/organization/costs"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    params = {
        "start_time": start_time,
        "end_time": end_time,
        "bucket_width": "1d",
    }
    _LOG.debug(
        "Fetching OpenAI costs for %s (start_time=%s, end_time=%s)",
        date,
        start_time,
        end_time,
    )
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        _LOG.debug("OpenAI API response: %s", hprint.to_str("data"))
        # Extract total cost from response.
        # Response format: {"data": [{"start_time": ..., "end_time": ..., "results": [{"object": "organization.costs.result", "amount": {"value": 123, "currency": "usd"}, ...}]}]}
        if "data" in data and len(data["data"]) > 0:
            results = data["data"][0].get("results", [])
            total_cost = 0.0
            for result in results:
                amount = result.get("amount", {})
                # Amount is in cents, convert to dollars.
                value = amount.get("value", 0) / 100.0
                total_cost += value
            _LOG.info("OpenAI daily cost for %s: $%.4f", date, total_cost)
            return total_cost
        _LOG.warning("No cost data found in OpenAI response")
        return 0.0
    except requests.exceptions.RequestException as e:
        _LOG.error("Failed to fetch OpenAI costs: %s", e)
        return None


def _get_anthropic_daily_cost(
    date: datetime.date,
    *,
    api_key: Optional[str] = None,
) -> Optional[float]:
    """
    Fetch daily cost from Anthropic Admin API.

    :param date: date for which to fetch costs
    :param api_key: Anthropic API key (uses ANTHROPIC_KEY env var if None)
    :return: total cost in USD, or None if request fails
    """
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_KEY")
    if not api_key:
        _LOG.warning("ANTHROPIC_KEY not found in environment")
        return None
    # Convert date to ISO format.
    date_str = date.isoformat()
    # Make API request.
    endpoint = "https://api.anthropic.com/v1/organizations/cost_report"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    params = {
        "start_date": date_str,
        "end_date": date_str,
    }
    _LOG.debug("Fetching Anthropic costs for %s", date)
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        _LOG.debug("Anthropic API response: %s", hprint.to_str("data"))
        # Extract total cost from response.
        # Response format varies - extract total cost from the data.
        total_cost = 0.0
        if isinstance(data, dict):
            # Try to extract cost from different possible response structures.
            if "data" in data:
                for item in data["data"]:
                    if "cost_usd" in item:
                        total_cost += float(item["cost_usd"])
                    elif "amount" in item:
                        total_cost += float(item["amount"])
            elif "total_cost" in data:
                total_cost = float(data["total_cost"])
            elif "cost" in data:
                total_cost = float(data["cost"])
        _LOG.info("Anthropic daily cost for %s: $%.4f", date, total_cost)
        return total_cost
    except requests.exceptions.RequestException as e:
        _LOG.error("Failed to fetch Anthropic costs: %s", e)
        return None


def _format_cost_table(costs: Dict[str, Optional[float]]) -> str:
    """
    Format costs as a text table.

    :param costs: dictionary mapping provider name to cost
    :return: formatted table string
    """
    lines = []
    lines.append("=" * 50)
    lines.append("Daily API Costs")
    lines.append("=" * 50)
    total_cost = 0.0
    for provider, cost in costs.items():
        if cost is not None:
            lines.append(f"{provider:<20} ${cost:>10.4f}")
            total_cost += cost
        else:
            lines.append(f"{provider:<20} {'N/A':>10}")
    lines.append("-" * 50)
    lines.append(f"{'Total':<20} ${total_cost:>10.4f}")
    lines.append("=" * 50)
    return "\n".join(lines)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--date",
        action="store",
        type=str,
        default=None,
        help="Date for which to fetch costs (YYYY-MM-DD format, default: today)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Parse target date.
    if args.date:
        try:
            target_date = datetime.datetime.strptime(
                args.date, "%Y-%m-%d"
            ).date()
        except ValueError:
            hdbg.dfatal("Invalid date format. Use YYYY-MM-DD format.")
    else:
        target_date = datetime.date.today()
    _LOG.info("Fetching costs for date: %s", target_date)
    # Fetch costs from both providers.
    costs = {}
    costs["OpenAI"] = _get_openai_daily_cost(target_date)
    costs["Anthropic"] = _get_anthropic_daily_cost(target_date)
    # Format and print results.
    table = _format_cost_table(costs)
    print(table)
    # Log summary.
    total_cost = sum(c for c in costs.values() if c is not None)
    _LOG.info("Total daily cost: $%.4f", total_cost)


if __name__ == "__main__":
    _main(_parse())
