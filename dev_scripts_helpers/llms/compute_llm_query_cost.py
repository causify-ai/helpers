#!/usr/bin/env python

"""
Compute the cost of an LLM query using the llm library and tokencost.

This script makes LLM API calls and calculates the associated costs using
the tokencost library. Supports batch processing with shared system prompts
to optimize costs.

Example usage:
# Single query
> dev_scripts_helpers/compute_llm_query_cost.py

# Multiple queries with shared system prompt
> dev_scripts_helpers/compute_llm_query_cost.py --prompts_file prompts.txt --system_prompt "You are a helpful assistant"

Import as:

import dev_scripts_helpers.compute_llm_query_cost as dscclqco
"""

import argparse
import logging
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################


def _check_dependencies() -> None:
    """
    Check that required dependencies are installed.
    """
    # Check if llm command is available.
    _LOG.debug("Checking for llm command")
    hsystem.system("which llm", suppress_output=True)
    # Check if tokencost is available.
    _LOG.debug("Checking for tokencost package")
    hsystem.system(
        "python -c 'import tokencost'",
        suppress_output=True,
    )


def _call_llm_and_compute_cost(
    model: str,
    prompt: str,
    *,
    system_prompt: str = "",
) -> Tuple[str, float, float, float]:
    """
    Call the LLM API and compute the cost of the query.

    :param model: model name to use for the API call
    :param prompt: user prompt to send to the model
    :param system_prompt: system prompt to use (optional)
    :return: tuple of (completion, prompt_cost, completion_cost, total_cost)
    """
    from tokencost import calculate_completion_cost, calculate_prompt_cost
    # Format the messages.
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    _LOG.debug("Prompt: %s", prompt)
    # Call the llm CLI to get a response.
    # The llm command returns the completion text.
    if system_prompt:
        # Escape single quotes in system prompt.
        escaped_system = system_prompt.replace("'", "'\\''")
        cmd = f"llm -m {model} -s '{escaped_system}' '{prompt}'"
    else:
        cmd = f"llm -m {model} '{prompt}'"
    _, completion = hsystem.system_to_string(cmd)
    completion = completion.strip()
    _LOG.debug("Completion received: %s", completion)
    # Calculate prompt cost.
    prompt_cost = calculate_prompt_cost(messages, model)
    _LOG.debug("Prompt cost: $%.6f", prompt_cost)
    # Calculate completion cost.
    completion_cost = calculate_completion_cost(completion, model)
    _LOG.debug("Completion cost: $%.6f", completion_cost)
    # Total cost.
    total_cost = prompt_cost + completion_cost
    return completion, float(prompt_cost), float(completion_cost), float(total_cost)


def _read_prompts_from_file(file_path: str) -> List[str]:
    """
    Read prompts from a file, one prompt per line.

    :param file_path: path to file containing prompts
    :return: list of prompts
    """
    import os
    hdbg.dassert(
        os.path.exists(file_path),
        "Prompts file does not exist:",
        file_path,
    )
    content = hio.from_file(file_path)
    prompts = [line.strip() for line in content.split("\n") if line.strip()]
    hdbg.dassert_lt(0, len(prompts), "No prompts found in file:", file_path)
    _LOG.info("Read %d prompts from file: %s", len(prompts), file_path)
    return prompts


def _process_batch_prompts(
    model: str,
    prompts: List[str],
    *,
    system_prompt: str = "",
) -> None:
    """
    Process multiple prompts with a shared system prompt.

    Shows cost comparison between using shared system prompt vs individual calls.

    :param model: model name to use for the API calls
    :param prompts: list of user prompts
    :param system_prompt: shared system prompt (optional)
    """
    import json
    from tokencost import calculate_prompt_cost
    _LOG.info("Processing %d prompts with model=%s", len(prompts), model)
    if system_prompt:
        _LOG.info("Using shared system prompt: %s", system_prompt)
    # Process each prompt.
    results = []
    total_prompt_cost = 0.0
    total_completion_cost = 0.0
    for i, prompt in enumerate(prompts, 1):
        _LOG.info("Processing prompt %d/%d", i, len(prompts))
        completion, prompt_cost, completion_cost, query_cost = (
            _call_llm_and_compute_cost(
                model, prompt, system_prompt=system_prompt
            )
        )
        total_prompt_cost += prompt_cost
        total_completion_cost += completion_cost
        results.append(
            {
                "prompt_num": i,
                "prompt": prompt,
                "completion": completion,
                "prompt_cost": prompt_cost,
                "completion_cost": completion_cost,
                "total_cost": query_cost,
            }
        )
    # Calculate total costs.
    total_cost = total_prompt_cost + total_completion_cost
    _LOG.info("=" * 80)
    _LOG.info("BATCH PROCESSING SUMMARY")
    _LOG.info("=" * 80)
    _LOG.info("Number of queries: %d", len(prompts))
    _LOG.info("Total prompt cost: $%.6f", total_prompt_cost)
    _LOG.info("Total completion cost: $%.6f", total_completion_cost)
    _LOG.info("Total cost: $%.6f", total_cost)
    # Calculate cost comparison if system prompt is used.
    if system_prompt:
        # Calculate what the cost would be without shared system prompt.
        # With shared system prompt, we pay for it once in the first query.
        # Without sharing, we'd pay for it in every query.
        system_message = [{"role": "system", "content": system_prompt}]
        system_prompt_cost = float(calculate_prompt_cost(system_message, model))
        # Cost without sharing = current cost + (system_prompt_cost * (num_queries - 1)).
        cost_without_sharing = total_cost + (
            system_prompt_cost * (len(prompts) - 1)
        )
        savings = cost_without_sharing - total_cost
        savings_pct = (savings / cost_without_sharing) * 100
        _LOG.info("-" * 80)
        _LOG.info("COST COMPARISON (with shared system prompt)")
        _LOG.info("-" * 80)
        _LOG.info("System prompt cost per query: $%.6f", system_prompt_cost)
        _LOG.info("Cost without sharing: $%.6f", cost_without_sharing)
        _LOG.info("Cost with sharing (actual): $%.6f", total_cost)
        _LOG.info("Savings: $%.6f (%.2f%%)", savings, savings_pct)
    _LOG.info("=" * 80)
    # Output detailed results.
    _LOG.info("Detailed results:\n%s", json.dumps(results, indent=2))


def _process_combined_prompts(
    model: str,
    prompts: List[str],
    *,
    system_prompt: str = "",
) -> None:
    """
    Process multiple prompts in a single API call with structured output.

    Combines all prompts into one query asking for JSON responses.

    :param model: model name to use for the API call
    :param prompts: list of user prompts
    :param system_prompt: system prompt (optional)
    """
    import json
    from tokencost import calculate_prompt_cost
    _LOG.info("Processing %d prompts in single combined query", len(prompts))
    if system_prompt:
        _LOG.info("Using system prompt: %s", system_prompt)
    # Build combined prompt with structured output request.
    numbered_prompts = "\n".join(
        [f"{i}. {prompt}" for i, prompt in enumerate(prompts, 1)]
    )
    combined_user_prompt = f"""Please answer each of the following {len(prompts)} questions.
Provide your response as a valid JSON object with this exact structure:
{{
  "answers": [
    {{"question_num": 1, "answer": "your answer here"}},
    {{"question_num": 2, "answer": "your answer here"}},
    ...
  ]
}}

Questions:
{numbered_prompts}

Remember to respond with ONLY the JSON object, no additional text."""
    _LOG.debug("Combined prompt:\n%s", combined_user_prompt)
    # Make the API call.
    _LOG.info("Making single combined LLM API call")
    completion, prompt_cost, completion_cost, total_cost = (
        _call_llm_and_compute_cost(
            model, combined_user_prompt, system_prompt=system_prompt
        )
    )
    _LOG.info("Received combined response")
    _LOG.debug("Response:\n%s", completion)
    # Parse JSON response.
    try:
        # Try to extract JSON from response.
        # Sometimes the LLM adds markdown code blocks.
        if "```json" in completion:
            json_start = completion.find("```json") + 7
            json_end = completion.find("```", json_start)
            json_str = completion[json_start:json_end].strip()
        elif "```" in completion:
            json_start = completion.find("```") + 3
            json_end = completion.find("```", json_start)
            json_str = completion[json_start:json_end].strip()
        else:
            json_str = completion.strip()
        parsed_response = json.loads(json_str)
        answers = parsed_response.get("answers", [])
        _LOG.info("Successfully parsed %d answers", len(answers))
    except (json.JSONDecodeError, KeyError) as e:
        _LOG.error("Failed to parse JSON response: %s", e)
        _LOG.error("Response was: %s", completion)
        answers = []
    # Display results.
    _LOG.info("=" * 80)
    _LOG.info("COMBINED PROMPT PROCESSING SUMMARY")
    _LOG.info("=" * 80)
    _LOG.info("Number of queries: %d", len(prompts))
    _LOG.info("API calls made: 1")
    _LOG.info("Total prompt cost: $%.6f", prompt_cost)
    _LOG.info("Total completion cost: $%.6f", completion_cost)
    _LOG.info("Total cost: $%.6f", total_cost)
    # Calculate comparison with individual queries.
    # Estimate cost of individual queries.
    messages_list = []
    if system_prompt:
        base_messages = [{"role": "system", "content": system_prompt}]
    else:
        base_messages = []
    for prompt in prompts:
        messages = base_messages + [{"role": "user", "content": prompt}]
        messages_list.append(messages)
    # Estimate individual prompt costs.
    individual_prompt_cost = sum(
        float(calculate_prompt_cost(msgs, model)) for msgs in messages_list
    )
    # Assume similar completion cost per query.
    avg_completion_per_query = completion_cost / len(prompts)
    individual_total = individual_prompt_cost + completion_cost
    savings = individual_total - total_cost
    savings_pct = (savings / individual_total) * 100 if individual_total > 0 else 0
    _LOG.info("-" * 80)
    _LOG.info("COST COMPARISON (combined vs individual)")
    _LOG.info("-" * 80)
    _LOG.info("Estimated individual queries cost: $%.6f", individual_total)
    _LOG.info("Combined query cost (actual): $%.6f", total_cost)
    _LOG.info("Savings: $%.6f (%.2f%%)", savings, savings_pct)
    _LOG.info("=" * 80)
    # Output detailed results.
    results = []
    for i, (prompt, answer_data) in enumerate(zip(prompts, answers), 1):
        results.append(
            {
                "question_num": i,
                "question": prompt,
                "answer": answer_data.get("answer", "N/A") if isinstance(answer_data, dict) else "N/A",
            }
        )
    _LOG.info("Detailed results:\n%s", json.dumps(results, indent=2))


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--model",
        action="store",
        default="gpt-4o-mini",
        help="Model to use for the LLM query (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--prompt",
        action="store",
        default="Write a haiku about databases",
        help="Single prompt to send to the model (default: 'Write a haiku about databases')",
    )
    parser.add_argument(
        "--prompts_file",
        action="store",
        default="",
        help="File containing multiple prompts (one per line) for batch processing",
    )
    parser.add_argument(
        "--system_prompt",
        action="store",
        default="",
        help="System prompt to use for all queries (helps reduce costs when processing multiple prompts)",
    )
    parser.add_argument(
        "--use_combined",
        action="store_true",
        default=False,
        help="Combine all prompts into single API call with structured output (most cost-efficient)",
    )
    parser.add_argument(
        "--compare_all",
        action="store_true",
        default=False,
        help="Run all three approaches and compare costs (individual, batch, combined)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    import json
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Check dependencies.
    _check_dependencies()
    # Process based on mode.
    if args.prompts_file:
        prompts = _read_prompts_from_file(args.prompts_file)
        if args.compare_all:
            # Compare all three approaches.
            _LOG.info("COMPARING ALL THREE APPROACHES")
            _LOG.info("=" * 80)
            # Approach 1: Individual queries.
            _LOG.info("\n### APPROACH 1: INDIVIDUAL QUERIES ###\n")
            _process_batch_prompts(
                args.model, prompts, system_prompt=args.system_prompt
            )
            # Approach 2: Combined prompt.
            _LOG.info("\n### APPROACH 2: COMBINED PROMPT ###\n")
            _process_combined_prompts(
                args.model, prompts, system_prompt=args.system_prompt
            )
        elif args.use_combined:
            # Combined mode: combine all prompts into single query.
            _process_combined_prompts(
                args.model, prompts, system_prompt=args.system_prompt
            )
        else:
            # Batch mode: process multiple prompts with shared system prompt.
            _process_batch_prompts(
                args.model, prompts, system_prompt=args.system_prompt
            )
    else:
        # Single query mode.
        _LOG.info("Making LLM API call with model=%s", args.model)
        if args.system_prompt:
            _LOG.info("Using system prompt: %s", args.system_prompt)
        completion, prompt_cost, completion_cost, total_cost = (
            _call_llm_and_compute_cost(
                args.model, args.prompt, system_prompt=args.system_prompt
            )
        )
        _LOG.info("Completion received: %s", completion)
        _LOG.info("Total cost: $%.6f", total_cost)
        # Format the result.
        result = {
            "model": args.model,
            "system_prompt": args.system_prompt if args.system_prompt else None,
            "prompt": args.prompt,
            "completion": completion,
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "total_cost": total_cost,
        }
        _LOG.info("Result:\n%s", json.dumps(result, indent=2))


if __name__ == "__main__":
    _main(_parse())
