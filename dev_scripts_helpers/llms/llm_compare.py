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
import requests

import helpers.hcache_simple as hcaches
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


@hcaches.simple_cache()
def _download_gutenberg_book(url: str, book_name: str) -> str:
    """
    Download a book from Project Gutenberg.

    :param url: Full URL to the book text file
    :param book_name: Human-readable name of the book (for logging)
    :return: Text content of the book
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    _LOG.info("Downloading '%s' from '%s'", book_name, url)
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text


def _create_summarization_benchmark(
    url: str, book_name: str,
) -> Tuple[str, str]:
    """
    Create a summarization benchmark from downloaded text.

    :param url: Full URL to the book text file
    :param book_name: Human-readable name of the book (for logging)
    :return: (input_text_file, prompt_file)
    """
    # Download with caching.
    full_text = _download_gutenberg_book(url, book_name)
    # Extract first 1000 words from the text.
    words = full_text.split()
    text = " ".join(words[:1000])
    _LOG.info("Extracted %d words", len(words[:1000]))
    # Save the full input text for reference.
    input_text_file = "tmp.llm_compare.input_text.txt"
    hio.to_file(input_text_file, text)
    _LOG.info("Input text saved to %s", input_text_file)
    # Create summarization prompt.
    prompt = (
        f"Please summarize the following text concisely in 3  markdown bullet points:\n\n"
    )
    # Save prompt to file.
    benchmark_file = "tmp.llm_compare.prompt.txt"
    hio.to_file(benchmark_file, prompt)
    _LOG.info("Benchmark prompt saved to %s", benchmark_file)
    return input_text_file, benchmark_file


def _get_benchmark(benchmark_name: str) -> Tuple[str, str]:
    """
    Get benchmark by name and return llm_cli commands.

    :param benchmark_name: Name of the benchmark (e.g., 'summarization1')
    :return: Tuple of (prompt_file, llm_cli_cmds)
    """
    benchmarks = {
        "summarization1": (
            "https://www.gutenberg.org/files/1342/1342-0.txt",
            "Pride and Prejudice",
        ),
        "summarization2": (
            "https://www.gutenberg.org/files/36/36-0.txt",
            "War of the Worlds",
        ),
    }
    hdbg.dassert_in(
        benchmark_name,
        benchmarks,
        "Unknown benchmark must be one of: %s",
        ", ".join(benchmarks.keys()),
    )
    _LOG.info("Loading benchmark: %s", benchmark_name)
    url, text_source_name = benchmarks[benchmark_name]
    # Download the book and create the benchmark.
    _, prompt_file = _create_summarization_benchmark(
        url, text_source_name,
    )
    # Generate llm_cli commands from the prompt file.
    llm_cli_cmds = f'--input {shlex.quote(prompt_file)}'
    return prompt_file, llm_cli_cmds


def _get_model_files(output_dir: str, model: str) -> Tuple[str, str]:
    """
    Get output and stat file paths for a model.

    :param output_dir: Output directory
    :param model: Model code
    :return: Tuple of (output_file_path, stat_file_path)
    """
    output_file = os.path.join(output_dir, f"{model}.output.txt")
    stat_file = os.path.join(output_dir, f"{model}.stat.txt")
    return output_file, stat_file


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
    # Find llm_cli in the git tree.
    llm_cli_path = hgit.find_file_in_git_tree("llm_cli.py")
    cmd = (
        f"{shlex.quote(llm_cli_path)} {llm_cli_cmds} "
        f"--model {shlex.quote(model)} "
        f"--output {shlex.quote(output_file)} "
        f"--stat_file {shlex.quote(stat_file)} "
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
            stat_data = hllmcli.TokenStats()
            rows.append(
                {
                    "model": model,
                    "cost_from_tokencost": stat_data.cost_from_tokencost,
                    "cost_from_llm_library": stat_data.cost_from_llm_library,
                    "time_elapsed": stat_data.elapsed_time_in_seconds,
                    "output_length": None,
                    "file": None,
                    "status": "FAILED",
                }
            )
            continue
        # Build file paths for successful models.
        output_file, stat_file = _get_model_files(output_dir, model)
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
    # Determine llm_cli_cmds from benchmark or direct argument.
    if args.benchmark:
        _, llm_cli_cmds = _get_benchmark(args.benchmark)
    elif args.llm_cli_cmds:
        llm_cli_cmds = args.llm_cli_cmds
    else:
        raise ValueError(
            "Either --benchmark or --llm_cli_cmds must be provided"
        )
    models = _load_models(args.models, args.models_from_file)
    output_dir = args.output_dir
    hio.create_dir(output_dir, True)
    _LOG.info("Output directory: %s", output_dir)
    _LOG.info(
        "Running %d models with commands: %s", len(models), llm_cli_cmds
    )
    results = {}
    for model in models:
        output_file, stat_file = _get_model_files(output_dir, model)
        success, exc = _run_llm_cli(
            model=model,
            llm_cli_cmds=llm_cli_cmds,
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
            exc or "Model failed: %s",
            model,
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
        "--benchmark",
        type=str,
        default="",
        help="Benchmark to run (e.g., 'summarization1')",
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
    parser.add_argument(
        "--llm_cli_cmds",
        type=str,
        default="",
        help="Arguments to pass to llm_cli.py (e.g., '--input input.txt --input_text \"...')",
    )
    hparser.add_verbosity_arg(parser)
    return parser


if __name__ == "__main__":
    _main(_parse())
