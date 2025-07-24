#!/usr/bin/env python3

import argparse
import logging
import os

import dev_scripts_helpers.llms.llm_utils as dshlllut
import dev_scripts_helpers.llms.llm_transform as dshllltr
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# TODO(gp): -> _parser() or _get_parser() everywhere.
def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(
        parser,
        in_default="-",
        in_required=False,
    )
    parser.add_argument(
        "-s",
        "--skip-post-transforms",
        action="store_true",
        help="Skip the post-transforms",
    )
    hparser.add_llm_prompt_arg(parser)
    hparser.add_dockerized_script_arg(parser)
    # Use CRITICAL to avoid logging anything.
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


# TODO(gp): Factor out the common code with `dockerized_llm_transform.py`.
def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hparser.init_logger_for_input_output_transform(args)
    # Parse files.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    # Check that the prompt is valid.
    hdbg.dassert_in(
        args.prompt,
        [
            "review_llm",
            "review_linter",
            "review_correctness",
            "review_refactoring",
        ],
    )
    # Make sure the output file name is `cfile` so that the output is printed
    # to stdout.
    if out_file_name != "cfile":
        _LOG.warning(
            "The output file name is '%s': using `cfile`",
            out_file_name,
        )
        out_file_name = "cfile"
    tag = "ai_review"
    tmp_in_file_name, tmp_out_file_name = (
        hparser.adapt_input_output_args_for_dockerized_scripts(in_file_name, tag)
    )
    # TODO(gp): We should just automatically pass-through the options.
    cmd_line_opts = [f"-p {args.prompt}", f"-v {args.log_level}"]
    # For stdin/stdout, suppress the output of the container.
    suppress_output = in_file_name == "-" or out_file_name == "-"
    dshllltr._run_dockerized_llm_transform(
        tmp_in_file_name,
        cmd_line_opts,
        tmp_out_file_name,
        mode="system",
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
        suppress_output=suppress_output,
    )
    # Run post-transforms outside the container.
    if not args.skip_post_transforms:
        compare = False
        out_txt = dshlllut.run_post_transforms(
            args.prompt,
            compare,
            in_file_name,
            tmp_in_file_name,
            tmp_out_file_name,
        )
    else:
        _LOG.info("Skipping post-transforms")
        out_txt = hio.from_file(tmp_out_file_name)
    # Read the output from the container and write it to the output file from
    # command line (e.g., `-` for stdout).
    hparser.write_file(out_txt, out_file_name)
    if os.path.basename(out_file_name) == "cfile":
        print(out_txt)


if __name__ == "__main__":
    _main(_parse())
