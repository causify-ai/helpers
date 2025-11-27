#!/usr/bin/env python

"""
Detect and remove AI slop using the Undetectable.ai REST API.

This script provides two actions:
- detect: Analyze text to determine if it was AI-generated (score 1-100)
- fix: Humanize AI-generated text to make it undetectable

Examples:
# Detect AI content in a file.
> dev_scripts_helpers/documentation/check_ai_slop.py -i input.txt --action detect

# Humanize AI content and save to output file.
> dev_scripts_helpers/documentation/check_ai_slop.py -i input.txt -o output.txt --action fix

# Process with specific humanization settings.
> dev_scripts_helpers/documentation/check_ai_slop.py -i input.txt -o output.txt --action fix --readability "University" --purpose "Essay"

Import as:

import dev_scripts_helpers.documentation.check_ai_slop as dsdochais
"""

import argparse
import json
import logging
import os
import time
from typing import Any, Dict

import requests

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# Valid actions for the script.
_VALID_ACTIONS = ["detect", "fix"]
_DEFAULT_ACTIONS = ["detect"]

# TODO(ai_gp): Move close to the only use.
# API endpoints.
_DETECT_ENDPOINT = "https://ai-detect.undetectable.ai/detect"
_QUERY_ENDPOINT = "https://ai-detect.undetectable.ai/query"
_HUMANIZE_SUBMIT_ENDPOINT = "https://humanize.undetectable.ai/submit"
_HUMANIZE_DOCUMENT_ENDPOINT = "https://humanize.undetectable.ai/document"

# #############################################################################


def _get_api_key() -> str:
    """
    Get the Undetectable.ai API key from environment variable.

    :return: API key string
    """
    key = "API_UNDETECTABLE"
    hdbg.dassert_in(
            key,
            os.keys(),
        "Environment variable API_UNDETECTABLE is not set",
    )
    api_key = os.getenv(key)
    return api_key


def _detect_ai_content(text: str, api_key: str) -> Dict[str, Any]:
    """
    Detect if text is AI-generated.

    :param text: text content to analyze
    :param api_key: Undetectable.ai API key
    :return: detection results including score and status
    """
    hdbg.dassert_isinstance(text, str)
    hdbg.dassert_lt(
        0,
        len(text),
        "Text must not be empty",
    )
    _LOG.info("Submitting text for AI detection")
    _LOG.debug("Text length: %s characters", len(text))
    # Prepare the request.
    payload = {"text": text, "key": api_key, "model": "xlm_ud_detector"}
    headers = {"Content-Type": "application/json"}
    # Submit for detection.
    response = requests.post(
        _DETECT_ENDPOINT, json=payload, headers=headers, timeout=30
    )
    response.raise_for_status()
    result = response.json()
    _LOG.debug("Detection API response: %s", result)
    # Check if we need to poll for results.
    if "id" in result and result.get("status") == "pending":
        doc_id = result["id"]
        _LOG.info("Detection in progress, polling for results...")
        result = _poll_detection_result(doc_id, api_key)
    return result


def _poll_detection_result(
    doc_id: str, api_key: str, *, max_attempts: int = 30, delay_secs: int = 2
) -> Dict[str, Any]:
    """
    Poll the detection API for results using document ID.

    :param doc_id: document ID from initial detection submission
    :param api_key: Undetectable.ai API key
    :param max_attempts: maximum number of polling attempts
    :param delay_secs: seconds to wait between polling attempts
    :return: detection results once complete
    """
    payload = {"id": doc_id, "key": api_key}
    headers = {"Content-Type": "application/json"}
    for attempt in range(max_attempts):
        _LOG.debug("Polling attempt %s/%s", attempt + 1, max_attempts)
        response = requests.post(
            _QUERY_ENDPOINT, json=payload, headers=headers, timeout=30
        )
        response.raise_for_status()
        result = response.json()
        if result.get("status") == "done":
            _LOG.info("Detection complete")
            return result
        _LOG.debug("Status: %s, waiting %s seconds...", result.get("status"), delay_secs)
        time.sleep(delay_secs)
    hdbg.dfatal(
        "Detection timed out after %s attempts",
        max_attempts,
    )


def _format_detection_result(result: Dict[str, Any]) -> str:
    """
    Format detection results for display.

    :param result: detection result dictionary
    :return: formatted string
    """
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("AI Detection Results")
    output_lines.append("=" * 80)
    # Main score.
    if "result" in result:
        score = result["result"]
        output_lines.append(f"Overall Score: {score}/100")
        # Interpretation.
        if score < 50:
            interpretation = "HUMAN (definitely human)"
        elif score < 60:
            interpretation = "UNCERTAIN (possible AI)"
        else:
            interpretation = "AI (definitely AI-generated)"
        output_lines.append(f"Interpretation: {interpretation}")
        output_lines.append("")
    # Detailed results.
    if "result_details" in result:
        output_lines.append("Detailed Detector Scores:")
        output_lines.append("-" * 80)
        details = result["result_details"]
        for detector, score in details.items():
            output_lines.append(f"  {detector}: {score}")
        output_lines.append("")
    output_lines.append("=" * 80)
    return "\n".join(output_lines)


# TODO(ai_gp): Rename detect_ai_content_from_file()
def _run_detect_action(input_file: str, api_key: str) -> None:
    """
    Run the detect action to analyze text for AI content.

    :param input_file: path to input file
    :param api_key: Undetectable.ai API key
    """
    _LOG.info("Running detect action on file: %s", input_file)
    # Read input file.
    text = hio.from_file(input_file)
    # Detect AI content.
    result = _detect_ai_content(text, api_key)
    # Format and display results.
    formatted_result = _format_detection_result(result)
    _LOG.info("\n%s", formatted_result)
    # Save raw JSON result to temporary file for debugging.
    tmp_file = "tmp.check_ai_slop.detect_result.json"
    hio.to_file(tmp_file, json.dumps(result, indent=2))
    _LOG.debug("Raw detection result saved to: %s", tmp_file)


# #############################################################################


def _humanize_text(
    text: str,
    api_key: str,
    *,
    readability: str = "University",
    purpose: str = "General Writing",
    strength: str = "Balanced",
) -> str:
    """
    Humanize AI-generated text using the Undetectable.ai Humanization API.

    :param text: text content to humanize
    :param api_key: Undetectable.ai API key
    :param readability: target readability level
    :param purpose: writing purpose
    :param strength: humanization strength
    :return: humanized text
    """
    hdbg.dassert_isinstance(text, str)
    hdbg.dassert_lte(
            0,
        len(text),
    )
    _LOG.info("Submitting text for humanization")
    _LOG.debug("Text length: %s characters", len(text))
    _LOG.debug("Settings: readability: %s, purpose: %s, strength: %s", readability, purpose, strength)
    # Prepare the request.
    payload = {
        "content": text,
        "readability": readability,
        "purpose": purpose,
        "strength": strength,
    }
    headers = {"Content-Type": "application/json", "apikey": api_key}
    # Submit for humanization.
    response = requests.post(
        _HUMANIZE_SUBMIT_ENDPOINT, json=payload, headers=headers, timeout=30
    )
    response.raise_for_status()
    result = response.json()
    _LOG.debug("Humanization submit response: %s", result)
    # Get document ID and poll for results.
    hdbg.dassert_in("id", result, "Response missing document ID")
    doc_id = result["id"]
    _LOG.info("Humanization in progress, polling for results...")
    humanized_result = _poll_humanization_result(doc_id, api_key)
    # Extract humanized text.
    hdbg.dassert_in("output", humanized_result, "Response missing humanized output")
    humanized_text = humanized_result["output"]
    _LOG.info("Humanization complete")
    return humanized_text


def _poll_humanization_result(
    doc_id: str, api_key: str, *, max_attempts: int = 60, delay_secs: int = 3
) -> Dict[str, Any]:
    """
    Poll the humanization API for results using document ID.

    :param doc_id: document ID from humanization submission
    :param api_key: Undetectable.ai API key
    :param max_attempts: maximum number of polling attempts
    :param delay_secs: seconds to wait between polling attempts
    :return: humanization results once complete
    """
    payload = {"id": doc_id}
    headers = {"Content-Type": "application/json", "apikey": api_key}
    for attempt in range(max_attempts):
        _LOG.debug("Polling attempt %s/%s", attempt + 1, max_attempts)
        response = requests.post(
            _HUMANIZE_DOCUMENT_ENDPOINT, json=payload, headers=headers, timeout=30
        )
        response.raise_for_status()
        result = response.json()
        # Check if output is available.
        if "output" in result and result["output"]:
            _LOG.info("Humanization complete")
            return result
        _LOG.debug("Waiting %s seconds...", delay_secs)
        time.sleep(delay_secs)
    hdbg.dfatal(
        "Humanization timed out after %s attempts",
        max_attempts,
    )


# TODO(ai_gp): Rename humanize_from_file()
def _run_fix_action(
    input_file: str,
    output_file: str,
    api_key: str,
    *,
    readability: str,
    purpose: str,
    strength: str,
) -> None:
    """
    Run the fix action to humanize AI-generated text.

    :param input_file: path to input file
    :param output_file: path to output file
    :param api_key: Undetectable.ai API key
    :param readability: target readability level
    :param purpose: writing purpose
    :param strength: humanization strength
    """
    _LOG.info("Running fix action on file: %s", input_file)
    # Read input file.
    text = hio.from_file(input_file)
    # Humanize text.
    humanized_text = _humanize_text(
        text,
        api_key,
        readability=readability,
        purpose=purpose,
        strength=strength,
    )
    # Write output file.
    hio.to_file(output_file, humanized_text)
    _LOG.info("Humanized text written to: %s", output_file)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(
        parser, in_required=True, out_required=False
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    # Humanization options.
    parser.add_argument(
        "--readability",
        choices=[
            "High School",
            "University",
            "Doctorate",
            "Journalist",
            "Marketing",
        ],
        default="University",
        help="Target readability level for humanization",
    )
    parser.add_argument(
        "--purpose",
        choices=[
            "General Writing",
            "Essay",
            "Article",
            "Marketing Material",
            "Story",
            "Cover Letter",
            "Report",
            "Business Material",
            "Legal Material",
        ],
        default="General Writing",
        help="Writing purpose for humanization",
    )
    parser.add_argument(
        "--strength",
        choices=["Quality", "Balanced", "More Human"],
        default="Balanced",
        help="Humanization strength",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Parse input/output files.
    input_file, output_file = hparser.parse_input_output_args(args)
    # Get API key.
    api_key = _get_api_key()
    # Select actions to run.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info("Selected actions: %s", actions)
    # Run actions.
    for action in actions:
        if action == "detect":
            _run_detect_action(input_file, api_key)
        elif action == "fix":
            _run_fix_action(
                input_file,
                output_file,
                api_key,
                readability=args.readability,
                purpose=args.purpose,
                strength=args.strength,
            )
        else:
            hdbg.dfatal("Invalid action: %s", action)


if __name__ == "__main__":
    _main(_parse())
