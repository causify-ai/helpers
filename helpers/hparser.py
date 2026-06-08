"""
Import as:

import helpers.hparser as hparser
"""

import argparse
import logging
from typing import Any, Dict, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio

_LOG = logging.getLogger(__name__)

# TODO(gp): arg -> args


# #############################################################################
# Verbosity
# #############################################################################


def add_bool_arg(
    parser: argparse.ArgumentParser,
    name: str,
    *,
    default_value: bool = False,
    help_: str = "",
) -> argparse.ArgumentParser:
    """
    Add options to a parser like `--xyz` and `--no_xyz`, controlled by
    `args.xyz`.

    E.g., `add_bool_arg(parser, "run_diff_script", default_value=True)` adds
    two options:
    ```
      --run_diff_script     Run the diffing script or not
      --no_run_diff_script
    ```
    corresponding to `args.run_diff_script`, where the default behavior is to have
    that value equal to True unless one specifies `--no_run_diff_script`.
    """
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--" + name, dest=name, action="store_true", help=help_)
    group.add_argument("--no_" + name, dest=name, action="store_false")
    parser.set_defaults(**{name: default_value})
    return parser


def add_verbosity_arg(
    parser: argparse.ArgumentParser, *, log_level: str = "INFO"
) -> argparse.ArgumentParser:
    parser.add_argument(
        "-v",
        dest="log_level",
        default=log_level,
        # TRACE=5
        # DEBUG=10
        # INFO=20
        # WARNING=30
        # CRITICAL=50
        choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--no_report_command_line",
        action="store_true",
        help="Disable printing of executed commands",
    )
    return parser


# TODO(gp): Use this everywhere.
def parse_verbosity_args(
    args: argparse.Namespace, *args_: Any, **kwargs: Any
) -> None:
    if hasattr(args, "no_report_command_line") and args.no_report_command_line:
        report_command_line = False
    else:
        report_command_line = True
    kwargs["report_command_line"] = report_command_line
    # if args.log_level == "VERB_DEBUG":
    #    args.log_level = 5
    hdbg.init_logger(verbosity=args.log_level, *args_, **kwargs)


# #############################################################################
# Command line options for metadata output.
# #############################################################################


def add_json_output_metadata_args(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """
    Add arguments related to storing the output metadata from a script.

    This data can be read / used by other scripts to post-process a
    script results.
    """
    parser.add_argument(
        "--json_output_metadata",
        type=str,
        action="store",
        help="File storing the output metadata of this script in JSON format",
    )
    return parser


# Store the metadata about the output of a script.
OutputMetadata = Dict[str, str]


def process_json_output_metadata_args(
    args: argparse.Namespace,
    output_metadata: OutputMetadata,
) -> Optional[str]:
    """
    Save the output metadata according to the command line options.

    :return: file name with the output metadata
    """
    hdbg.dassert_isinstance(output_metadata, dict)
    if args.json_output_metadata is None:
        return None
    file_name: str = args.json_output_metadata
    _LOG.info("Saving output metadata into file '%s'", file_name)
    if not file_name.endswith(".json"):
        _LOG.warning(
            "The output metadata file '%s' doesn't end in .json: adding it",
            file_name,
        )
        file_name += ".json"
    hio.to_json(file_name, output_metadata)
    _LOG.info("Saved output metadata into file '%s'", file_name)
    return file_name


def read_output_metadata(output_metadata_file: str) -> OutputMetadata:
    """
    Read the output metadata.
    """
    output_metadata: OutputMetadata = hio.from_json(output_metadata_file)
    return output_metadata


def str_to_bool(value: str) -> bool:
    """
    Convert string representing true or false to the corresponding bool.
    """
    if value.lower() == "true":
        ret = True
    elif value.lower() == "false":
        ret = False
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid boolean value {value}. Use 'true' or 'false'."
        )
    return ret
