#!/usr/bin/env python3

r"""
CLI script to compare LLM model performance by running the same workload
with different models and generating comparison statistics.

For detailed documentation, usage examples, and feature descriptions, see:
`dev_scripts_helpers/llms/README.md`

Import as:

import dev_scripts_helpers.llms.llm_compare as dshllcmp
"""

import argparse
import logging
import os
import shlex
from typing import Dict, List, Tuple

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _load_models(
    models_arg: str,
    models_from_file_arg: str,
) -> List[str]:
    """
    Load model list from command-line arg or file.

    :param models_arg: Comma-separated model list
    :param models_from_file_arg: Path to file with one model per line
    :return: List of model codes
    """
    if models_arg:
        models = [m.strip() for m in models_arg.split(",")]
    elif models_from_file_arg:
        content = hio.from_file(models_from_file_arg)
        models = [m.strip() for m in content.strip().split("\n") if m.strip()]
    else:
        raise RuntimeError(
            "Either --models or --models_from_file must be provided"
        )
    hdbg.dassert_lt(0, len(models), "At least one model must be provided")
    _LOG.info("Loaded %d models: %s", len(models), models)
    return models


def _run_llm_cli(
    model: str,
    llm_cli_cmds: str,
    output_file: str,
    stat_file: str,
    abort_on_error: bool,
) -> Tuple[bool, str]:
    """
    Run llm_cli.py for a single model.

    :param model: Model code to use
    :param llm_cli_cmds: Base command arguments to pass to llm_cli.py
    :param output_file: Where to save the output
    :param stat_file: Where to save the stats (JSON)
    :param abort_on_error: Whether to raise on error
    :return: (success, exception) tuple
    """
    cmd = (
        f"python3 -m dev_scripts_helpers.llms.llm_cli "
        f"{llm_cli_cmds} "
        f"--model {shlex.quote(model)} "
        f"--output {shlex.quote(output_file)} "
        f"--stat_file {shlex.quote(stat_file)}"
    )
    _LOG.info("Running model '%s'...", model)
    _LOG.debug("Command: %s", cmd)
    rc = hsystem.system(cmd, print_command=False, abort_on_error=False)
    if rc != 0:
        error_msg = (
            f"llm_cli.py failed with return code {rc} for model '{model}'"
        )
        _LOG.error(error_msg)
        if abort_on_error:
            raise RuntimeError(error_msg)
        return False, error_msg
    _LOG.info("Model '%s' completed successfully", model)
    return True, ""


def _build_comparison_table(
    models: List[str],
    output_dir: str,
    results: Dict[str, Tuple[bool, str]],
) -> pd.DataFrame:
    """
    Build a comparison table from model results.

    :param models: List of model codes that were run
    :param output_dir: Output directory containing results
    :param results: Dict mapping model to (success, error) tuple
    :return: DataFrame with comparison data
    """
    rows = []
    for model in models:
        hdbg.dassert_in(model, results, "Model must be in results")
        success, _ = results[model]
        if not success:
            # TODO(ai_gp): Start from an empty TokenStats.
            # Use default values for failed models.
            rows.append(
                {
                    "model": model,
                    "costs": None,
                    "time_elapsed": None,
                    "output_length": None,
                    "file": None,
                    "status": "FAILED",
                }
            )
            continue
        # Build file paths for successful models.
        output_file = os.path.join(output_dir, f"{model}.output.txt")
        stat_file = os.path.join(output_dir, f"{model}.stat.txt")
        # Load statistics from JSON file.
        stat_data = hllmcli.TokenStats.from_file(stat_file)
        # Extract metrics from output file and statistics.
        hdbg.dassert_file_exists(output_file, "Output file must exist")
        output_length = os.path.getsize(output_file)
        rows.append(
            {
                "model": model,
                "cost_from_tokencost": stat_data.cost_from_tokencost,
                "cost_from_llm_library": stat_data.cost_from_llm_library,
                "time_elapsed": stat_data.elapsed_time_in_seconds,
                "output_length": output_length,
                "file": output_file,
                "status": "SUCCESS",
            }
        )
    df = pd.DataFrame(rows)
    return df


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("Starting LLM model comparison")
    models = _load_models(args.models, args.models_from_file)
    output_dir = args.output_dir
    hio.create_dir(output_dir, True)
    _LOG.info("Output directory: %s", output_dir)
    _LOG.info(
        "Running %d models with commands: %s", len(models), args.llm_cli_cmds
    )
    results = {}
    for model in models:
        output_file = os.path.join(output_dir, f"{model}.output.txt")
        stat_file = os.path.join(output_dir, f"{model}.stat.txt")
        success, exc = _run_llm_cli(
            model=model,
            llm_cli_cmds=args.llm_cli_cmds,
            output_file=output_file,
            stat_file=stat_file,
            abort_on_error=args.abort_on_error,
        )
        results[model] = (success, exc)
        if not success and args.abort_on_error:
            _LOG.error("Aborting due to error in model '%s'", model)
        hdbg.dassert_imply(
            args.abort_on_error,
            success,
            exc or f"Model '{model}' failed",
        )
    df = _build_comparison_table(models, output_dir, results)
    csv_file = os.path.join(output_dir, "comparison.csv")
    df.to_csv(csv_file, index=False)
    _LOG.info("Comparison Results:\n%s", df.to_string(index=False))
    _LOG.info("Results saved to CSV: %s", csv_file)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    models_group = parser.add_mutually_exclusive_group(required=True)
    models_group.add_argument(
        "--models",
        type=str,
        default="",
        help="Comma-separated list of model codes (e.g., 'gpt-4o-mini,claude-opus-4.8')",
    )
    models_group.add_argument(
        "--models_from_file",
        type=str,
        default="",
        help="Path to file with one model code per line",
    )
    parser.add_argument(
        "--llm_cli_cmds",
        type=str,
        required=True,
        help="Arguments to pass to llm_cli.py (e.g., '--input input.txt --input_text \"...')",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory to save results and stats",
    )
    parser.add_argument(
        "--abort_on_error",
        action="store_true",
        default=False,
        help="Abort on first model error (default: skip failed models)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


if __name__ == "__main__":
    _main(_parse())
