#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
# ]
# ///

"""
See instructions at
`docs/tools/documentation_toolchain/all.notes_toolchain.how_to_guide.md`

For a description of the architecture of this file, see the file
`lint_text.README.md` in the same directory.
"""

import argparse
import logging
import os
from typing import Optional

import helpers.hdocker as hdocker
import helpers.hprint as hprint
import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser
import helpers.hselect_action as hselacti
import dev_scripts_helpers.documentation.lib_lint_text as dshdllite

_LOG = logging.getLogger(__name__)

_VALID_ACTIONS = list(dshdllite.VALID_ACTIONS.keys())

# Default actions (excluding some that need explicit opt-in).
_DEFAULT_ACTIONS = [
    action
    for action in _VALID_ACTIONS
    if action
    not in [
        "frame_chapters",
        "refresh_toc",
        "check_links",
        "remove_markdown_formatting",
    ]
]


def _resolve_extension(args: argparse.Namespace) -> Optional[str]:
    """
    Determine the file extension to use to filter the available actions.

    Use `--type` if specified, otherwise infer it from the input file(s), as
    long as all of them share the same extension.

    :param args: command line arguments
    :return: extension (e.g., "typ"), or `None` if it can't be determined
        (e.g., stdin with no `--type`, or files with mixed extensions)
    """
    if args.type:
        return args.type
    files = hseinout.parse_input_output_files(args)
    if not files and args.input and args.input != "-":
        files = [args.input]
    if not files:
        return None
    extensions = {os.path.splitext(f)[1].lstrip(".") for f in files}
    if len(extensions) != 1:
        return None
    return extensions.pop()


# #############################################################################


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hseinout.add_input_output_args(parser, in_required=False, out_required=False)
    parser.add_argument(
        "--type",
        action="store",
        type=str,
        default="",
        choices=["", "md", "tex", "txt", "smd", "typ"],
        help=(
            "Force the file type instead of inferring from extension. "
            "When reading from stdin, this option is required. "
        ),
    )
    parser.add_argument(
        "-w",
        "--width",
        action="store",
        type=int,
        default=85,
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
        _VALID_ACTIONS,
        _DEFAULT_ACTIONS,
    )
    hdocker.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hseinout.init_logger_for_input_output_transform(args)
    # Print the backend and mode used to format markdown files.
    _LOG.info(hprint.to_str("args.backend args.mode"))
    # Handle --revert option.
    if args.revert:
        files = hseinout.parse_input_output_files(args)
        if files:
            for file_path in files:
                dshdllite._revert_from_backup(file_path)
        else:
            in_file_name, _ = hseinout.parse_input_output_args(
                args, clear_screen=False
            )
            dshdllite._revert_from_backup(in_file_name)
        return
    # Restrict the actions offered to the ones supported by the file format,
    # so e.g. a `.typ` file only lists `typstyle_format` instead of every
    # markdown-only action that would just be skipped with a warning.
    extension = _resolve_extension(args)
    if extension:
        valid_actions = dshdllite.get_actions_for_format(extension)
        default_actions = [a for a in _DEFAULT_ACTIONS if a in valid_actions]
    else:
        valid_actions = _VALID_ACTIONS
        default_actions = _DEFAULT_ACTIONS
    # Print actions (once for all files).
    actions = hselacti.select_actions(
        args,
        valid_actions,
        default_actions,
    )
    add_frame = True
    actions_as_str = hselacti.actions_to_string(
        actions, valid_actions, add_frame
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
            dshdllite._process_single_file(file_path, file_path, args, actions)
    else:
        # Process single file (original behavior).
        in_file_name, out_file_name = hseinout.parse_input_output_args(
            args, clear_screen=False
        )
        dshdllite._process_single_file(
            in_file_name, out_file_name, args, actions
        )


if __name__ == "__main__":
    _main(_parser())
