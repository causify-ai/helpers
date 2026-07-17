#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
# ]
# ///

"""
See instructions at
docs/tools/documentation_toolchain/all.notes_toolchain.how_to_guide.md.

For a description of the architecture of this file, see the file
lint_txt.README.md in the same directory.
"""

import argparse
import logging
import os
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser
import helpers.hselect_action as hselacti
import dev_scripts_helpers.documentation.lib_lint_txt as dshdlilint

_LOG = logging.getLogger(__name__)


# TODO(ai_gp): Move to lib_lint_txt.py
def _process_single_file(
    in_file_name: str,
    out_file_name: str,
    args: argparse.Namespace,
    actions: Optional[List[str]],
) -> None:
    """
    Process a single file.

    :param in_file_name: Input file name.
    :param out_file_name: Output file name.
    :param args: Parsed arguments.
    :param actions: List of actions to perform.
    """
    # If the input is stdin, then user needs to specify the type.
    if in_file_name == "-":
        hdbg.dassert_ne(args.type, "")
    # Create backup before processing (if processing in-place).
    if in_file_name == out_file_name and in_file_name != "-":
        dshdlilint._create_backup(in_file_name)
    # Read input.
    lines = hseinout.from_file(in_file_name)
    _LOG.debug("in_file_name=%s", in_file_name)
    # Process.
    kwargs = {
        "width": args.width,
        "use_dockerized_prettier": args.use_dockerized_prettier,
        "use_dockerized_markdown_toc": args.use_dockerized_markdown_toc,
    }
    # Add backend and mode if specified.
    if args.backend:
        kwargs["backend"] = args.backend
    if args.mode:
        kwargs["mode"] = args.mode
    out_lines = dshdlilint._perform_actions(
        lines,
        in_file_name,
        actions=actions,
        file_type_override=args.type,
        **kwargs,
    )
    # Write output.
    hseinout.to_file(out_lines, out_file_name)


# #############################################################################


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hseinout.add_input_output_args(parser, in_required=False, out_required=False)
    parser.add_argument(
        "--type",
        action="store",
        type=str,
        default="",
        choices=["", "md", "tex", "txt", "emd"],
        help=(
            "Force the file type instead of inferring from extension. "
            "When reading from stdin, this option is required."
        ),
    )
    parser.add_argument(
        "-w",
        "--width",
        action="store",
        type=int,
        default=80,
        help="The maximum line width for the formatted text.",
    )
    parser.add_argument(
        "--backend",
        action="store",
        type=str,
        default="",
        choices=["prettier", "mdformat", "flowmark"],
        help=(
            "The markdown formatting backend to use. "
            "Only applies to markdown files. "
            "Options: prettier, mdformat, flowmark"
        ),
    )
    parser.add_argument(
        "--mode",
        action="store",
        type=str,
        default="",
        help=(
            "The execution mode for the backend. "
            "For prettier: 'dockerized' or 'global'. "
            "For mdformat: 'library', 'uvx', or 'global'. "
            "For flowmark: 'library', 'uvx-rs', 'uvx', 'global', or 'global-rs'."
        ),
    )
    # TODO(gp): Convert to backend "global", "dockerized".
    parser.add_argument(
        "--use_dockerized_prettier",
        dest="use_dockerized_prettier",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no_use_dockerized_prettier",
        dest="use_dockerized_prettier",
        action="store_false",
    )
    parser.add_argument(
        "--use_dockerized_markdown_toc",
        dest="use_dockerized_markdown_toc",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no_use_dockerized_markdown_toc",
        dest="use_dockerized_markdown_toc",
        action="store_false",
    )
    parser.add_argument(
        "--revert",
        action="store_true",
        default=False,
        help="Revert a file from its backup copy",
    )
    hselacti.add_action_arg(
        parser,
        list(dshdlilint._VALID_ACTIONS.keys()),
        dshdlilint.DEFAULT_ACTIONS,
    )
    hdocker.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hseinout.init_logger_for_input_output_transform(args)
    # Handle --revert option.
    if args.revert:
        files = hseinout.parse_input_output_files(args)
        if files:
            for file_path in files:
                dshdlilint._revert_from_backup(file_path)
        else:
            in_file_name, _ = hseinout.parse_input_output_args(
                args, clear_screen=False
            )
            dshdlilint._revert_from_backup(in_file_name)
        return
    # Print actions (once for all files).
    actions = hselacti.select_actions(
        args,
        list(dshdlilint._VALID_ACTIONS.keys()),
        dshdlilint.DEFAULT_ACTIONS,
    )
    add_frame = True
    actions_as_str = hselacti.actions_to_string(
        actions, list(dshdlilint._VALID_ACTIONS.keys()), add_frame
    )
    _LOG.info("\n%s", actions_as_str)
    # Check if processing multiple files or a single file.
    files = hseinout.parse_input_output_files(args)
    if files:
        # Process multiple files.
        _LOG.info("Processing %d file(s)", len(files))
        for file_path in files:
            if not os.path.exists(file_path):
                _LOG.error("File not found: %s", file_path)
                continue
            _LOG.info("Processing: %s", file_path)
            _process_single_file(file_path, file_path, args, actions)
    else:
        # Process single file (original behavior).
        in_file_name, out_file_name = hseinout.parse_input_output_args(
            args, clear_screen=False
        )
        _process_single_file(in_file_name, out_file_name, args, actions)


if __name__ == "__main__":
    _main(_parser())
