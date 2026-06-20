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

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


@hcacsimp.simple_cache()
def _download_gutenberg_book(url: str, book_name: str) -> str:
    """
    Download a book from Project Gutenberg.

    :param url: Full URL to the book text file
    :param book_name: Human-readable name of the book (for logging)
    :return: Text content of the book
    """
    _LOG.debug("\n%s", hprint.func_signature_to_str())
    # Use a common user-agent to avoid being blocked by Gutenberg.
    headers = {"User-Agent": "Mozilla/5.0"}
    _LOG.info("Downloading '%s' from '%s'", book_name, url)
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    _LOG.debug("Downloaded %d characters", len(r.text))
    return r.text


def _create_summarization_benchmark(
    url: str,
    book_name: str,
) -> Tuple[str, str]:
    """
    Create a summarization benchmark from downloaded text.

    :param url: Full URL to the book text file
    :param book_name: Human-readable name of the book (for logging)
    :return: (input_text_file, prompt_file)
    """
    _LOG.debug("\n%s", hprint.func_signature_to_str())
    # Download the full text (cached across calls via decorator).
    full_text = _download_gutenberg_book(url, book_name)
    # Slice to first 1000 words so the prompt fits within context limits.
    words = full_text.split()
    text = " ".join(words[:1000])
    _LOG.info("Extracted %d words", len(words[:1000]))
    # Build summarization instruction and embed the text into the prompt.
    prompt_instruction = "Please summarize the following text concisely in 3 markdown bullet points:\n\n"
    full_prompt = f"{prompt_instruction}{text}"
    # Persist the prompt so llm_cli.py can read it as input.
    benchmark_file = "tmp.llm_compare.prompt.txt"
    hio.to_file(benchmark_file, full_prompt)
    _LOG.info("Benchmark prompt saved to %s", benchmark_file)
    _LOG.debug(hprint.to_str("benchmark_file"))
    return benchmark_file, benchmark_file


def _get_benchmark(benchmark_name: str) -> Tuple[str, str]:
    """
    Get benchmark by name and return llm_cli commands.

    :param benchmark_name: Name of the benchmark (e.g., 'summarization1')
    :return: Tuple of (prompt_file, llm_cli_cmds)
    """
    _LOG.debug("\n%s", hprint.func_signature_to_str())
    # Pre-defined benchmarks: mapping name -> (Gutenberg URL, book display name).
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
        url,
        text_source_name,
    )
    # Generate llm_cli commands from the prompt file.
    llm_cli_cmds = f"--input {shlex.quote(prompt_file)}"
    _LOG.debug(hprint.to_str("prompt_file llm_cli_cmds"))
    return prompt_file, llm_cli_cmds


def _get_model_files(
    output_dir: str, model: str, benchmark: str = ""
) -> Tuple[str, str]:
    """
    Get output and stat file paths for a model.

    :param output_dir: Output directory
    :param model: Model code
    :param benchmark: Benchmark name (optional, e.g., 'summarization1')
    :return: Tuple of (output_file_path, stat_file_path)
    """
    _LOG.debug(hprint.to_str("output_dir model benchmark"))
    model_basename = os.path.basename(model)
    # Prefix filenames with the benchmark name when running under one.
    if benchmark:
        output_file = os.path.join(
            output_dir, f"{benchmark}.{model_basename}.output.txt"
        )
        stat_file = os.path.join(
            output_dir, f"{benchmark}.{model_basename}.stat.txt"
        )
    else:
        output_file = os.path.join(output_dir, f"{model_basename}.output.txt")
        stat_file = os.path.join(output_dir, f"{model_basename}.stat.txt")
    _LOG.debug(hprint.to_str("output_file stat_file"))
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
    _LOG.debug("\n%s", hprint.func_signature_to_str())
    # Parse models from comma-separated string or file (one per line).
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
    _LOG.debug(hprint.to_str("model output_file stat_file abort_on_error"))
    # Locate llm_cli.py relative to the repo root via git tree.
    llm_cli_path = hgit.find_file_in_git_tree("llm_cli.py")
    # Build the shell command: pass prompt args, model, and output paths.
    cmd = (
        f"{shlex.quote(llm_cli_path)} {llm_cli_cmds} "
        f"--model {shlex.quote(model)} "
        f"--output {shlex.quote(output_file)} "
        f"--stat_file {shlex.quote(stat_file)} "
    )
    _LOG.info("Running model '%s'...", model)
    _LOG.info("Command: %s", cmd)
    # Run the CLI; capture non-zero exit without aborting by default.
    rc = hsystem.system(
        cmd, print_command=False, abort_on_error=False, suppress_output=False
    )
    if rc != 0:
        error_msg = (
            f"llm_cli.py failed with return code {rc} for model '{model}'"
        )
        _LOG.error(error_msg)
        if abort_on_error:
            raise RuntimeError(error_msg)
        _LOG.debug("return=(%s, %s)", False, error_msg)
        return False, error_msg
    _LOG.info("Model '%s' completed successfully", model)
    _LOG.debug("return=(%s, '')", True)
    return True, ""


def _build_comparison_table(
    models: List[str],
    output_dir: str,
    results: Dict[str, Tuple[bool, str]],
    benchmark: str = "",
) -> pd.DataFrame:
    """
    Build a comparison table from model results.

    :param models: List of model codes that were run
    :param output_dir: Output directory containing results
    :param results: Dict mapping model to (success, error) tuple
    :param benchmark: Benchmark name (optional, e.g., 'summarization1')
    :return: DataFrame with comparison data
    """
    _LOG.debug(hprint.to_str("models benchmark"))
    rows = []
    for model in models:
        hdbg.dassert_in(model, results, "Model must be in results")
        success, _ = results[model]
        # For failed models emit a row with zeroed stats and null output.
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
        output_file, stat_file = _get_model_files(output_dir, model, benchmark)
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
    _LOG.debug("Comparison table has %d rows", len(df))
    return df


def _main(parser: argparse.ArgumentParser) -> None:
    _LOG.debug("\n%s", hprint.func_signature_to_str(skip_vars="parser"))
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("Starting LLM model comparison")
    # Determine llm_cli_cmds from benchmark or direct argument.
    if args.benchmark:
        _, llm_cli_cmds = _get_benchmark(args.benchmark)
    elif args.llm_cli_cmds:
        llm_cli_cmds = args.llm_cli_cmds
    else:
        raise ValueError("Either --benchmark or --llm_cli_cmds must be provided")
    models = _load_models(args.models, args.models_from_file)
    output_dir = args.output_dir
    hio.create_dir(output_dir, True)
    _LOG.info("Output directory: %s", output_dir)
    _LOG.info("Running %d models with commands: %s", len(models), llm_cli_cmds)
    results = {}
    benchmark_name = args.benchmark if args.benchmark else ""
    # Iterate over each model: skip if output already exists, otherwise run.
    for model in models:
        output_file, stat_file = _get_model_files(
            output_dir, model, benchmark_name
        )
        # Skip already-completed models so re-runs are idempotent.
        if os.path.exists(output_file):
            stat_data = hllmcli.TokenStats.from_file(stat_file)
            tokens_per_sec = stat_data.tokens_per_second
            _LOG.warning(
                "Skipping model '%s' - output file already exists: %s "
                "(input_tokens=%d, output_tokens=%d, tokens/sec=%.2f)",
                model,
                output_file,
                stat_data.input_tokens,
                stat_data.output_tokens,
                tokens_per_sec,
            )
            results[model] = (True, "")
            continue
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
    df = _build_comparison_table(models, output_dir, results, benchmark_name)
    # Persist comparison as CSV and log to stdout.
    csv_file = os.path.join(output_dir, "comparison.csv")
    df.to_csv(csv_file, index=False)
    _LOG.info("Comparison Results:\n%s", df.to_string(index=False))
    _LOG.info("Results saved to CSV: %s", csv_file)


def _parse() -> argparse.ArgumentParser:
    _LOG.debug("\n%s", hprint.func_signature_to_str())
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
        default="tmp.llm_compare",
        help="Directory to save results and stats (default: 'tmp.llm_compare')",
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
