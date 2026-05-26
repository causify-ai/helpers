"""
Import as:

import helpers.hparser as hparser
"""

import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

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
    help_: Optional[str] = None,
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
# File selection arguments
# #############################################################################


def add_file_selection_args(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """
    Add file selection arguments to a parser.

    Adds the following mutually exclusive arguments:
    - --files: Specify specific files
    - --from_files: Select files listed in a file
    - --modified: Select files modified in the client
    - --branch: Select files modified with respect to the branch point
    - --last_commit: Select files part of the previous commit
    - --all: Select all files

    :param parser: ArgumentParser to add arguments to
    :return: The same parser with arguments added
    """
    file_selection = parser.add_mutually_exclusive_group()
    # TODO(gp): Use -f and -i and --input as alternative
    file_selection.add_argument(
        "--files",
        type=str,
        help="Select specific files (space-separated list)",
    )
    file_selection.add_argument(
        "--from_file",
        type=str,
        help="Path to file containing one file path per line",
    )
    file_selection.add_argument(
        "--modified",
        action="store_true",
        help="Select only files modified in the client (staged and unstaged)",
    )
    file_selection.add_argument(
        "--branch",
        action="store_true",
        help="Select only files modified with respect to the branch point",
    )
    file_selection.add_argument(
        "--last_commit",
        action="store_true",
        help="Select only files part of the previous commit",
    )
    file_selection.add_argument(
        "--all",
        action="store_true",
        dest="all_files",
        help="Select all repo files",
    )
    return parser


def parse_file_selection_args(
    args: argparse.Namespace,
    *,
    remove_dirs: bool = True,
    dir_name: str = ".",
) -> List[str]:
    """
    Parse file selection arguments and return list of files to process.

    Handles these mutually exclusive options:
    - --modified: files modified in the client
    - --branch: files modified with respect to the branch point
    - --last_commit: files part of the previous commit
    - --all: all repo files
    - --files: files specified as space-separated list
    - --from_files: files listed in a file (one per line)

    :param args: Parsed command-line arguments from add_file_selection_args
    :param remove_dirs: Whether to exclude directories from results
    :param dir_name: Directory to search (default: current directory)
    :return: List of file paths to process
    """
    # Import here to avoid circular dependency.
    import helpers.hgit as hgit

    # TODO(gp): Can we use args.files?
    files = hgit.get_files_to_process(
        getattr(args, "files", None) or "",
        getattr(args, "from_file", None) or "",
        getattr(args, "modified", False),
        getattr(args, "branch", False),
        getattr(args, "last_commit", False),
        getattr(args, "all_files", False),
        mutually_exclusive=True,
        remove_dirs=remove_dirs,
        dir_name=dir_name,
    )
    return files


# #############################################################################
# Command line for `@hcache_simple.simple_cache` functions.
# #############################################################################


# TODO(gp): Use the ones from hcache_simple.py for DRY.
_CACHE_MODE_CHOICES = ("REFRESH_CACHE", "DISABLE_CACHE", "HIT_CACHE_OR_ABORT")


def add_cache_control_arg(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """
    Add `--cache_mode` switch controlling every
    `@hcache_simple.simple_cache`-decorated function in the process.

    The resolved mode is applied globally via
    `hcache_simple.set_global_cache_mode` in `parse_cache_control_args()`.
    """
    parser.add_argument(
        "--cache_mode",
        action="store",
        default=None,
        choices=list(_CACHE_MODE_CHOICES),
        help=(
            "Override cache behavior for all @simple_cache functions. "
            "REFRESH_CACHE repopulates, DISABLE_CACHE bypasses, "
            "HIT_CACHE_OR_ABORT raises on miss."
        ),
    )
    parser.add_argument(
        "--cache_debug",
        action="store_true",
        help=(
            "Log at WARNING level for every @simple_cache call whether the "
            "result was served from cache, computed on miss, or recomputed "
            "because of `cache_mode`"
        ),
    )
    return parser


def parse_cache_control_args(args: argparse.Namespace) -> None:
    """
    Apply `--cache_mode`,  `--cache_debug` by setting the `hcache_simple`
    process-wide globals.
    """
    # Import lazily to avoid a circular dependency at module load time.
    import helpers.hcache_simple as hcacsimp

    mode = getattr(args, "cache_mode", None)
    if mode is not None:
        _LOG.info("Setting global cache_mode=%s", mode)
    hcacsimp.set_global_cache_mode(mode)
    cache_debug = bool(getattr(args, "cache_debug", False))
    if cache_debug:
        _LOG.info("Enabling cache_debug logging")
    hcacsimp.set_cache_debug(cache_debug)


# #############################################################################
# Select actions.
# #############################################################################

# # Define valid and default actions.
# valid_actions = ["download", "process", "upload", "cleanup"]
# default_actions = ["download", "process"]
# # Create parser and add action arguments.
# parser = argparse.ArgumentParser(...
# hparser.add_action_arg(parser, valid_actions, default_actions)
# args = parser.parse_args()
# # Select which actions to execute based on CLI arguments.
# actions = hparser.select_actions(args, valid_actions, default_actions)
# # Display the selected actions in a formatted table.
# print(hparser.actions_to_string(actions, valid_actions, add_frame=True))
# # mark_action() handles tracking which actions remain and logs skipped ones.
# while actions:
#     # Current action to check
#     action = actions[0]
#     # Determine if this action should execute and get remaining actions
#     # to_execute: True if action is in the list, False otherwise
#     # actions: updated list with current action removed if to_execute=True
#     to_execute, actions = hparser.mark_action(action, actions)
#     if to_execute:
#         # Execute the action
#         if action == "download":
#             print("Downloading data...")
#         elif action == "process":


def add_action_arg(
    parser: argparse.ArgumentParser,
    valid_actions: List[str],
    default_actions: Optional[List[str]],
) -> argparse.ArgumentParser:
    """
    Add command line options to select actions to execute, skip, or enable.

    The function creates a mutually exclusive group with three options:
    - `-a/--action`: specify exact actions to execute
    - `-sa/--skip_action`: skip specific actions from default set
    - `-e/--enable`: enable additional actions on top of defaults

    Available actions are listed once in the help epilog to avoid repetition.

    :param parser: parser to add the option to
    :param valid_actions: list of valid actions
    :param default_actions: list of default actions to execute
    :return: parser with the option added
    """
    # Add epilog with list of available actions to avoid repeating them.
    actions_list = ", ".join(valid_actions)
    if parser.epilog:
        parser.epilog += f"\n\nAvailable actions: {actions_list}"
    else:
        parser.epilog = f"Available actions: {actions_list}"
    # Create mutually exclusive group for action selection.
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-a",
        "--action",
        action="append",
        dest="action",
        help="Actions to execute (see available actions below)",
    )
    group.add_argument(
        "-sa",
        "--skip_action",
        action="append",
        dest="skip_action",
        help="Actions to skip from default set (see available actions below)",
    )
    group.add_argument(
        "-e",
        "--enable",
        action="append",
        dest="enable_action",
        help="Enable additional actions on top of defaults (see available actions below)",
    )
    if default_actions is not None:
        hdbg.dassert_is_subset(default_actions, valid_actions)
        parser.add_argument(
            "--all",
            action="store_true",
            help=f"Run all the actions ({' '.join(default_actions)})",
        )
    return parser


def actions_to_string(
    actions: List[str], valid_actions: List[str], add_frame: bool
) -> str:
    """
    Convert a list of actions to a string.

    :param actions: list of actions to convert
    :param valid_actions: list of valid actions
    :param add_frame: if `True`, add a frame around the actions
    :return: string of the actions
    """
    space = max(len(a) for a in valid_actions) + 2
    format_ = "%" + str(space) + "s: %s"
    actions = [
        format_ % (a, "Yes" if a in actions else "-") for a in valid_actions
    ]
    actions_as_str = "\n".join(actions)
    if add_frame:
        ret = hprint.frame("# Action selected:") + "\n"
        ret += hprint.indent(actions_as_str)
    else:
        ret = actions_as_str
    return ret  # type: ignore


def select_actions(
    args: argparse.Namespace,
    valid_actions: List[str],
    default_actions: List[str],
) -> List[str]:
    """
    Select actions based on the command line arguments.

    Supports three mutually exclusive modes:
    - `--action`: run only specified actions
    - `--skip_action`: run default actions minus specified ones
    - `--enable`: run default actions plus specified additional ones

    :param args: command line arguments
    :param valid_actions: list of valid actions
    :param default_actions: list of default actions to execute
    :return: list of selected actions
    """
    hdbg.dassert(
        not (args.action and args.all),
        "You can't specify together --action and --all",
    )
    hdbg.dassert(
        not (args.action and args.skip_action),
        "You can't specify together --action and --skip_action",
    )
    # TODO(ai_gp): Try to remove this.
    # Needed because add_action_arg() is optional and might not be called.
    # Check for enable_action attribute (added for backward compatibility).
    has_enable = hasattr(args, "enable_action")
    if has_enable:
        hdbg.dassert(
            not (args.action and args.enable_action),
            "You can't specify together --action and --enable",
        )
        hdbg.dassert(
            not (args.skip_action and args.enable_action),
            "You can't specify together --skip_action and --enable",
        )
    # Select actions.
    if not args.action or args.all:
        if default_actions is None:
            default_actions = valid_actions[:]
        hdbg.dassert_is_subset(default_actions, valid_actions)
        # Convert it into list since through some code paths it can be a tuple.
        actions = list(default_actions)
    else:
        # Validate actions specified by user.
        for action in args.action:
            hdbg.dassert_in(
                action,
                valid_actions,
                "Invalid action '%s'",
                action,
            )
        actions = args.action[:]
    hdbg.dassert_isinstance(actions, list)
    hdbg.dassert_no_duplicates(actions)
    # Remove actions, if needed.
    if args.skip_action:
        hdbg.dassert_isinstance(args.skip_action, list)
        for skip_action in args.skip_action:
            # Validate that skip_action is a valid action.
            hdbg.dassert_in(
                skip_action,
                valid_actions,
                "Invalid action '%s'",
                skip_action,
            )
            # Validate that skip_action is in the current action list.
            if skip_action not in actions:
                _LOG.warning(
                    "Skipping action '%s' since it's already not in actions='%s'",
                    skip_action,
                    actions,
                )
            actions = [a for a in actions if a != skip_action]
    # Add enabled actions on top of defaults.
    if has_enable and args.enable_action:
        hdbg.dassert_isinstance(args.enable_action, list)
        for enable_action in args.enable_action:
            hdbg.dassert_in(
                enable_action,
                valid_actions,
                "Invalid action '%s'",
                enable_action,
            )
            if enable_action not in actions:
                actions.append(enable_action)
    # Reorder actions according to 'valid_actions'.
    actions = [action for action in valid_actions if action in actions]
    return actions


def mark_action(
    action: str, actions: Optional[List[str]]
) -> Tuple[bool, Optional[List[str]]]:
    """
    Mark an action as to be executed or skipped.

    :param action: action to mark
    :param actions: list of actions, or None to execute all actions
    :return: tuple of (to_execute, actions)
    """
    if actions is None:
        # If actions is None, execute all actions.
        to_execute = True
    else:
        to_execute = action in actions
    _LOG.debug("\n%s", hprint.frame(f"action={action}"))
    if to_execute:
        if actions is not None:
            actions = [a for a in actions if a != action]
    else:
        _LOG.warning("Skip action='%s'", action)
    return to_execute, actions


# #############################################################################
# Command line options for input/output processing.
# #############################################################################

# For non-dockerized scripts the following idiom is used:
#
# ```python
# # Add input/output arguments to parser.
# hparser.add_input_output_args(parser)
# # Handle input/output arguments, including stdin/stdout.
# in_file_name, out_file_name = hparser.parse_input_output_args(args)
# ...
# # Read input file, handling stdin.
# in_lines = hparser.from_file(in_file_name)
# ...
# # Write output, handling stdout.
# hparser.to_file(txt, out_file_name)
# ```
# See helpers_root/dev_scripts_helpers/coding_tools/transform_template.py as an
# example.

# For dockerized scripts the following idiom is used inside the wrapper, which
# calls the dockerized script:
#
# ```python
# # Add input/output arguments to parser.
# hparser.add_input_output_args(parser)
# # Handle input/output arguments, including stdin/stdout.
# in_file_name, out_file_name = hparser.parse_input_output_args(args)
# tmp_in_file_name, tmp_out_file_name = hparser.adapt_input_output_args_for_dockerized_scripts(
#   in_file_name, "llm_transform")
# ...
# # For stdin/stdout, suppress the output of the container.
# suppress_output = in_file_name == "-" or out_file_name == "-"
# _run_dockerized_llm_transform(
#     tmp_in_file_name,
#     cmd_line_opts,
#     tmp_out_file_name,
#     mode="system",
#     force_rebuild=args.dockerized_force_rebuild,
#     use_sudo=args.dockerized_use_sudo,
#     suppress_output=suppress_output,
# )
# ...
# # Write output, handling stdout.
# hparser.to_file(txt, out_file_name)
# ```
#
# See helpers_root/dev_scripts_helpers/llms/llm_transform.py as an example.


def add_input_output_args(
    parser: argparse.ArgumentParser,
    *,
    in_default: Optional[str] = None,
    in_required: bool = True,
    out_default: Optional[str] = None,
    out_required: bool = False,
) -> argparse.ArgumentParser:
    """
    Add options to parse input and output file name, and handle stdin / stdout.

    Supports three methods for specifying input files:
    - `-i/--input`: single input file or `-` for stdin
    - `--input_files`: space or comma-separated list of files
    - `--from_file`: file containing one file per line

    :param in_default: default file to be used for input
        - If `None`, it must be specified by the user
    :param in_required: whether the input file is required
    :param out_default: default file to be used for output
        - If `None`, it must be specified by the user
    :param out_required: whether the output file is required
    """
    parser.add_argument(
        "-i",
        "--input",
        dest="input",
        required=in_required,
        type=str,
        default=in_default,
        help="Input file or `-` for stdin",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        required=out_required,
        type=str,
        default=out_default,
        help="Output file or `-` for stdout",
    )
    parser.add_argument(
        "--input_files",
        nargs="+",
        default=None,
        help="One or more files (space-separated, shell globs supported) or comma-separated list",
    )
    parser.add_argument(
        "--from_file",
        action="store",
        type=str,
        default=None,
        help="Path to a file containing a list of files to process (one per line)",
    )
    return parser


def parse_input_output_files(args: argparse.Namespace) -> Optional[List[str]]:
    """
    Parse files from --input_files or --from_file arguments.

    Supports shell glob expansion (e.g., `--input_files books/chapters/*`)
    and comma-separated lists for backward compatibility (e.g.,
    `--input_files "a.md,b.md,c.md"`).

    :param args: Parsed arguments.
    :return: List of files to process, or None if neither option is provided.
    """
    if args.input_files:
        # nargs='+' gives a list; flatten any comma-separated tokens for
        # backward compatibility with the old "--input_files=a.md,b.md" style.
        files = []
        for token in args.input_files:
            files.extend(token.replace(",", " ").split())
        return files
    elif args.from_file:
        # Read files from the specified file.
        if not os.path.exists(args.from_file):
            _LOG.error("File not found: %s", args.from_file)
            raise FileNotFoundError(f"File not found: {args.from_file}")
        with open(args.from_file, "r") as f:
            files = [line.strip() for line in f if line.strip()]
        return files
    return None


def parse_input_output_args(
    args: argparse.Namespace, *, clear_screen: bool = False
) -> Tuple[str, str]:
    """
    Parse input and output file name, handling stdin / stdout.

    If --files or --from_file is specified, use the first file as input
    and the output file remains as specified.

    If a single file is passed in -i/--input, then --output represents
    the output file.

    :return input and output file name.
    """
    in_file_name = args.input
    out_file_name = args.output
    if out_file_name is None:
        # If the output file is not specified, use the input file name, i.e.,
        # in place.
        out_file_name = in_file_name
    # Print summary. If we are using stdin / stdout, don't print anything since
    # we don't want to pollute the output.
    if in_file_name != "-":
        if clear_screen:
            os.system("clear")
        _LOG.info(hprint.to_str("in_file_name"))
        _LOG.info(hprint.to_str("out_file_name"))
    return in_file_name, out_file_name


def init_logger_for_input_output_transform(
    args: argparse.Namespace, *, verbose: bool = True
) -> None:
    """
    Initialize the logger when input/output transformation is used.

    :param verbose: if `False`, set the log level to `CRITICAL` so that no
        output is printed and avoid to print:
        ```
        09:34:24 - INFO  hdbg.py init_logger:1013                 Saving log to file '/User...
        09:34:24 - INFO  hdbg.py init_logger:1018                 > cmd='/Users/saggese/src...
        09:34:24 - INFO  hparser.py parse_input_output_args:368   in_file_name='lectures_source/Les...
        09:34:24 - INFO  hparser.py parse_input_output_args:369   out_file_name='-'
    ```
    """
    verbosity = args.log_level
    if not verbose:
        # Unless user has specified DEBUG level, set the log level to `CRITICAL`
        # so that no output is printed.
        if args.log_level == "INFO":
            verbosity = "CRITICAL"
    else:
        # If the input is stdin, we don't want to print the command line or any
        # other log messages, unless the user specified a more verbose log level.
        if args.input == "-":
            if args.log_level == "INFO":
                verbosity = "CRITICAL"
        else:
            print("cmd line: " + hdbg.get_command_line())
    hdbg.init_logger(verbosity=verbosity, use_exec_path=True, force_white=False)


def from_file(file_name: str) -> List[str]:
    """
    Read file or stdin (represented by `-`), returning an array of lines.

    If file_name is "pb" and the platform is macOS, read from clipboard.
    """
    if file_name == "-":
        _LOG.info("Reading from stdin")
        # Read.
        txt = []
        for line in sys.stdin:
            txt.append(line.rstrip("\n"))
    elif file_name == "pb":
        # Read from clipboard (macOS only).
        if hserver.is_host_mac():
            _LOG.info("Reading from clipboard")
            cmd = "pbpaste"
            rc, txt_str = hsystem.system_to_string(cmd)
            txt = txt_str.split("\n")
        else:
            hdbg.dfatal("Reading from clipboard (pb) only works on macOS")
    else:
        txt = hio.from_file(file_name)
        txt = txt.split("\n")
    return txt


def to_file(txt: Union[str, List[str]], file_name: str) -> None:
    """
    Write txt in a file or stdout (represented by `-`).

    If file_name is "pb" and the platform is macOS, write to clipboard.
    """
    if isinstance(txt, str):
        txt = [txt]
    if file_name == "-":
        _LOG.debug("Saving to stdout")
        print("\n".join(txt))
    elif file_name == "pb":
        # Write to clipboard (macOS only).
        if hserver.is_host_mac():
            _LOG.info("Writing to clipboard")
            txt_str = "\n".join(txt)
            # Use echo with pbcopy, escaping single quotes.
            txt_str_escaped = txt_str.replace("'", "'\\''")
            cmd = f"echo -n '{txt_str_escaped}' | pbcopy"
            hsystem.system(cmd)
            _LOG.info("Written to clipboard")
        else:
            hdbg.dfatal("Writing to clipboard (pb) only works on macOS")
    else:
        _LOG.debug("Saving to file")
        with open(file_name, "w") as f:
            f.write("\n".join(txt))
        _LOG.info("Written file '%s'", file_name)


def adapt_input_output_args_for_dockerized_scripts(
    in_file_name: str, tag: str
) -> Tuple[str, str]:
    """
    Adapt input and output file name for dockerized scripts.

    Since we need to call a container and passing stdin/stdout is tricky,
    we read the input and save it in a temporary file.

    :param tag: tag to be used for the temporary file name (e.g., `llm_transform`)
    """
    # Since we need to call a container and passing stdin/stdout is tricky,
    # we read the input and save it in a temporary file.
    in_lines = from_file(in_file_name)
    if in_file_name == "-":
        tmp_in_file_name = f"tmp.{tag}.in.txt"
        in_txt = "\n".join(in_lines)
        hio.to_file(tmp_in_file_name, in_txt)
    else:
        tmp_in_file_name = in_file_name
    #
    tmp_out_file_name = f"tmp.{tag}.out.txt"
    return tmp_in_file_name, tmp_out_file_name


# TODO(ai_gp): Merge this in the input_output_args functions.
def add_dst_dir_arg(
    parser: argparse.ArgumentParser,
    dst_dir_required: bool,
    dst_dir_default: Optional[str] = None,
) -> argparse.ArgumentParser:
    """
    Add command line options related to destination directory.

    Adds `--dst_dir` and `--overwrite` flags. If the destination directory
    already exists and `--overwrite` is not specified, an error is raised.

    E.g., `--dst_dir`, `--overwrite`
    """
    # A required dst_dir implies no default dst_dir.
    hdbg.dassert_imply(
        dst_dir_required,
        not dst_dir_default,
        "Since dst_dir_required='%s', you need to specify a default "
        "destination dir, instead of dst_dir_default='%s'",
        dst_dir_required,
        dst_dir_default,
    )
    # If dst_dir is not required, then a default dst_dir must be specified.
    hdbg.dassert_imply(
        not dst_dir_required,
        dst_dir_default,
        "Since dst_dir_required='%s', you can't specify a default "
        "destination dir, dst_dir_default='%s'",
        dst_dir_required,
        dst_dir_default,
    )
    parser.add_argument(
        "--dst_dir",
        action="store",
        default=dst_dir_default,
        required=dst_dir_required,
        help="Directory storing the results",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete existing destination directory if it already exists",
    )
    return parser


def parse_dst_dir_arg(args: argparse.Namespace) -> str:
    """
    Process the command line options related to destination directory.

    If the destination directory already exists and `--overwrite` is not set,
    raises an error. If `--overwrite` is set and the directory exists, it is
    used as-is (not deleted).

    :return: the destination directory path
    """
    dst_dir = args.dst_dir
    _LOG.debug("dst_dir=%s", dst_dir)
    if os.path.exists(dst_dir):
        if not args.overwrite:
            raise ValueError(
                f"Output directory already exists: {dst_dir} "
                "(use --overwrite to replace)"
            )
        _LOG.info("Reusing existing dst_dir='%s'", dst_dir)
    else:
        hio.create_dir(dst_dir, incremental=True)
    return dst_dir


# #############################################################################
# Command line options for parallel processing.
# #############################################################################


# pylint: disable=line-too-long
# TODO(gp): These should go in hjoblib.py
def add_parallel_processing_arg(
    parser: argparse.ArgumentParser,
    *,
    num_threads_default: Optional[str] = None,
) -> argparse.ArgumentParser:
    """
    Add parallel processing args.

    The "incremental idiom" means skipping processing computation that has
    already been performed. E.g., if we need to transform files from one dir to
    another we skip the files already processed (assuming that a file present
    in the destination dir is an indication that it has already been
    processed).

    The default behavior should always be incremental since "incremental mode"
    is not destructive like the non-incremental, i.e., delete and restart

    The incremental behavior  is disabled with `--no_incremental`. This implies
    performing the computation in any case
    - It is often implemented by deleting the destination dir and then running
      again, even in incremental mode
    - If the destination dir already exists, then we require the user to
      explicitly use `--force` to confirm that the user knows what is doing
    """
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print the workload and exit without running it",
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help="Skip workload already performed",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Confirm that one wants to remove the previous results. It works only together with --no_incremental",
    )
    #
    help = """
    Number of threads to use:
    - '-1' to use all CPUs;
    - '1' to use one-thread at the time but using the parallel execution (mainly used
    for debugging)
    - 'serial' to serialize the execution without using parallel execution"""
    if num_threads_default is None:
        parser.add_argument(
            "--num_threads",
            action="store",
            help=help,
            required=True,
        )
    else:
        parser.add_argument(
            "--num_threads",
            action="store",
            help=help,
            default=num_threads_default,
        )
    parser.add_argument("--no_keep_order", action="store_true", help="")
    parser.add_argument(
        "--num_func_per_task",
        action="store",
        type=int,
        default=None,
        help="Number of function execute in a (parallel) task of the workload. `None` means automatically decided by the function",
    )
    parser.add_argument(
        "--skip_on_error",
        action="store_true",
        help="Continue execution after encountering an error",
    )
    parser.add_argument(
        "--num_attempts",
        default=1,
        type=int,
        help="Repeat running an experiment up to `num_attempts` times",
        required=False,
    )
    return parser


def create_incremental_dir(dst_dir: str, args: argparse.Namespace) -> None:
    """
    Create a dir using the "incremental idiom".

    If the dir already exists and the user requested the not
    incremental, we require `--force` to confirm deleting the dir.
    """
    if args.force:
        hdbg.dassert(
            args.no_incremental, "--force only works with --no_incremental"
        )
    _LOG.debug(hprint.to_str("dst_dir args"))
    if args.no_incremental:
        # Create the dir from scratch.
        _LOG.debug("No incremental mode")
        if os.path.exists(dst_dir):
            _LOG.debug("Dir '%s' already exists", dst_dir)
            hdbg.dassert_dir_exists(dst_dir, "'%s' must be a directory")
            if not args.force:
                _LOG.warning(
                    "The directory '%s' already exists. To confirm deleting it use --force",
                    dst_dir,
                )
                sys.exit(-1)
            _LOG.warning("Deleting %s", dst_dir)
        hio.create_dir(dst_dir, incremental=False)
    else:
        _LOG.debug("Incremental mode")
        hio.create_dir(dst_dir, incremental=True)


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


# #############################################################################
# Command line options for dockerized scripts.
# #############################################################################


def add_dockerized_script_arg(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """
    Add common command line arguments for dockerized scripts.
    """
    parser.add_argument(
        "--dockerized_force_rebuild",
        action="store_true",
        help="Force to rebuild the Docker container",
    )
    parser.add_argument(
        "--dockerized_use_sudo",
        action="store_true",
        help="Use sudo inside the container",
    )
    return parser


# #############################################################################
# Command line options for limit range processing.
# #############################################################################


def add_limit_range_arg(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """
    Add argument for limiting processing to a range of items.

    The range format is X:Y where X and Y are 1-indexed integers.
    """
    parser.add_argument(
        "--limit",
        action="store",
        help="Limit processing to item range X:Y (integers >= 1, inclusive)",
    )
    return parser


def parse_limit_range(limit_str: str) -> Tuple[int, int]:
    """
    Parse limit string in format "X:Y" and return tuple (start, end).

    :param limit_str: string in format "X:Y" where X and Y are integers >= 1
    :return: tuple in [start_index, end_index]
    """
    hdbg.dassert(
        ":" in limit_str, "Limit format must be X:Y, got: %s", limit_str
    )
    parts = limit_str.split(":")
    hdbg.dassert_eq(
        len(parts), 2, "Limit format must be X:Y, got: %s", limit_str
    )
    try:
        start = int(parts[0])
        end = int(parts[1])
    except ValueError as e:
        hdbg.dfatal("Invalid limit format, must be integers: %s" % str(e))
    hdbg.dassert_lte(1, start, "Start index must be >= 1, got: %s", start)
    hdbg.dassert_lte(1, end, "End index must be >= 1, got: %s", end)
    hdbg.dassert_lte(
        start, end, "Start index must be <= end index, got: %s:%s", start, end
    )
    return start, end


def parse_limit_range_args(
    args: argparse.Namespace,
) -> Optional[Tuple[int, int]]:
    """
    Parse limit range from command line arguments and log the result.

    :param args: parsed command line arguments containing 'limit'
        attribute
    :return: tuple of (start_index, end_index) as 0-indexed integers, or
        None if no limit
    """
    limit_range = None
    if args.limit:
        limit_range = parse_limit_range(args.limit)
        _LOG.warning(
            "Using limit range: [%s:%s]", limit_range[0], limit_range[1]
        )
    return limit_range


def apply_limit_range(
    items: List[Any],
    limit_range: Optional[Tuple[int, int]] = None,
    *,
    item_name: str = "items",
) -> List[Any]:
    """
    Apply limit range filtering to a list of items.

    :param items: list of items to filter
    :param limit_range: optional tuple (start, end) for 0-indexed range
        filtering
    :param item_name: name of items for logging purposes
    :return: filtered list of items
    """
    if limit_range is not None:
        start_idx, end_idx = limit_range
        total_items = len(items)
        hdbg.dassert_lt(
            start_idx,
            total_items,
            "Start index %s exceeds available %s %s",
            start_idx,
            item_name,
            total_items,
        )
        hdbg.dassert_lt(
            end_idx,
            total_items,
            "End index %s exceeds available %s %s",
            end_idx,
            item_name,
            total_items,
        )
        items = items[start_idx : end_idx + 1]
        _LOG.warning(
            "Found %s %s, limited to range %s:%s (%s %s)",
            total_items,
            item_name,
            start_idx,
            end_idx,
            len(items),
            item_name,
        )
    else:
        _LOG.info("Found %s %s to process", len(items), item_name)
    # Print the items that will be processed.
    _LOG.debug("Items to process:")
    for i, item in enumerate(items):
        _LOG.debug("  [%s]: %s", i, item)
    return items


# #############################################################################
# Select multiple file input.
# #############################################################################


# TODO(gp): Merge with input_output_args and / or add_file_selection_args?
def add_multi_file_args(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """
    Add command line options for specifying multiple input files.

    Three mutually exclusive methods are supported:
    - `--files="file1,file2,..."`: comma-separated list of files
    - `--from_files="file.txt"`: file containing one file per line
    - `--input file1 --input file2`: repeated argument

    These options work alongside the existing `-i/--input` for backward
    compatibility.

    :param parser: parser to add the options to
    :return: parser with the options added
    """
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--files",
        type=str,
        help="Comma-separated list of files to process (e.g., 'file1.txt,file2.txt,file3.txt')",
    )
    group.add_argument(
        "--from_files",
        type=str,
        help="Path to file containing one file path per line",
    )
    group.add_argument(
        "-i",
        "--input",
        action="append",
        help="File to process (can be specified multiple times)",
    )
    return parser


def parse_multi_file_args(
    args: argparse.Namespace,
) -> List[str]:
    """
    Parse multi-file command line arguments and return list of file paths.

    Handles three input methods:
    - `--files="file1,file2,..."`: comma-separated list
    - `--from_files="file.txt"`: file containing one file per line
    - `--input file1 --input file2`: repeated argument

    If none of the multi-file options are specified, falls back to the single
    `-i/--input` argument for backward compatibility.

    :param args: parsed command line arguments
    :return: list of file paths to process
    """
    file_list: List[str] = []
    # Check which multi-file option was specified.
    if hasattr(args, "files") and args.files:
        # Parse comma-separated list.
        _LOG.debug("Using --files option")
        file_list = [f.strip() for f in args.files.split(",")]
        # Remove empty strings.
        file_list = [f for f in file_list if f]
    elif hasattr(args, "from_files") and args.from_files:
        # Read file containing list of files.
        _LOG.debug("Using --from_files option")
        hdbg.dassert_path_exists(args.from_files)
        content = hio.from_file(args.from_files)
        lines = content.split("\n")
        for line in lines:
            # Strip whitespace.
            line = line.strip()
            # Skip empty lines and comments.
            if line and not line.startswith("#"):
                file_list.append(line)
    elif hasattr(args, "input") and args.input:
        # Check if args.input is a list (from --input repeated argument) or a string (from -i/--input single file).
        if isinstance(args.input, list):
            # Use repeated argument from add_multi_file_args.
            _LOG.debug("Using --input option (repeated argument)")
            file_list = args.input
        else:
            # Backward compatibility: support single file via -i/--input from add_input_output_args.
            _LOG.debug(
                "Using -i/--input option (single file, backward compatibility)"
            )
            file_list = [args.input]
    else:
        # No file specified.
        hdbg.dfatal("No input files specified")
    # Validate that we have at least one file.
    hdbg.dassert_isinstance(file_list, list)
    hdbg.dassert_lt(
        0, len(file_list), "No input files specified after parsing arguments"
    )
    # Validate that all files exist.
    for file_path in file_list:
        hdbg.dassert_path_exists(file_path)
    _LOG.info("Found %s file(s) to process", len(file_list))
    return file_list


# #############################################################################
# Command line options for LLM CLI scripts.
# #############################################################################


# TODO(ai_gp): Replace this with the more general parsing logic below.
def add_llm_prompt_arg(
    parser: argparse.ArgumentParser,
    *,
    default_prompt: str = "",
    is_required: bool = True,
) -> argparse.ArgumentParser:
    """
    Add common command line arguments for `*llm_transform.py` scripts.

    :param default_prompt: default prompt to use
    :param is_required: whether the prompt is required
    :return: parser with the option added
    """
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print before/after the transform",
    )
    if default_prompt != "":
        is_required = False
    parser.add_argument(
        "-p",
        "--prompt",
        required=is_required,
        type=str,
        help="Prompt to apply",
        default=default_prompt,
    )
    parser.add_argument(
        "-f",
        "--fast_model",
        action="store_true",
        help="Use a fast LLM model vs a high-quality one",
    )
    return parser


def add_llm_args(
    parser: argparse.ArgumentParser,
    *,
    input_required: bool = True,
    output_required: bool = False,
    system_prompt_required: bool = False,
    model_default: str = "gpt-4o-mini",
    include_model: bool = True,
    include_llm_executable: bool = True,
) -> argparse.ArgumentParser:
    """
    Add comprehensive LLM-related command line arguments for LLM CLI scripts.

    This helper function consolidates commonly used arguments for scripts that
    process text with LLM transformations (e.g., llm_cli.py, ai_review.py).

    :param input_required: whether input is required
    :param output_required: whether output is required
    :param system_prompt_required: whether system prompt is required
    :param model_default: default LLM model name
    :param include_model: whether to include --model argument
    :param include_llm_executable: whether to include --use_llm_executable flag
    :return: parser with LLM arguments added
    """
    # Input/Output options with mutually exclusive input sources.
    input_group = parser.add_mutually_exclusive_group(required=input_required)
    input_group.add_argument(
        "-i",
        "--input",
        type=str,
        dest="input",
        help="Path to the input file containing text to process, or '-' for stdin",
    )
    input_group.add_argument(
        "--input_text",
        type=str,
        help="Text input to process directly from command line",
    )
    # Output option.
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        dest="output",
        required=output_required,
        default=None,
        help="Path to the output file where result will be saved (use '-' to "
        "print to screen). If not specified, writes in-place to the input file",
    )
    # System prompt options (mutually exclusive).
    system_prompt_group = parser.add_mutually_exclusive_group(
        required=system_prompt_required
    )
    system_prompt_group.add_argument(
        "-p",
        "--system_prompt",
        type=str,
        default=None,
        dest="system_prompt",
        help="Optional system prompt to guide the LLM's behavior",
    )
    system_prompt_group.add_argument(
        "-pf",
        "--system_prompt_file",
        type=str,
        default=None,
        dest="system_prompt_file",
        help="Optional path to file containing system prompt to guide the LLM's behavior",
    )
    system_prompt_group.add_argument(
        "-r",
        "--rule",
        type=str,
        default=None,
        dest="rule",
        help=(
            "Rule specification used as system prompt. Formats: "
            "'path/to/rules.md' (whole file), "
            "'path/to/rules.md:LINE' (header section at LINE), "
            "'path/to/rules.md:LINE:# Section Name' (with name validation)"
        ),
    )
    # Model selection.
    if include_model:
        parser.add_argument(
            "--model",
            type=str,
            default=model_default,
            help=f"Optional model name to use (e.g., 'gpt-4', 'claude-3-opus'). "
            f"Default: {model_default}",
        )
    # LLM executable option.
    if include_llm_executable:
        parser.add_argument(
            "--use_llm_executable",
            action="store_true",
            default=False,
            help="Use the llm CLI executable instead of the Python library",
        )
    # Progress bar options.
    parser.add_argument(
        "-b",
        "--progress_bar",
        action="store_true",
        default=False,
        help="Enable progress bar with automatic estimation (input length * 1.0)",
    )
    parser.add_argument(
        "--expected_num_chars",
        type=int,
        default=None,
        help="Expected number of characters in output (enables progress bar with explicit size)",
    )
    return parser


# #############################################################################
# Command line for markdown extraction and selection
# #############################################################################


def add_md_start_end_args(
    parser: argparse.ArgumentParser,
    *,
    start_required: bool = True,
    end_required: bool = False,
) -> argparse.ArgumentParser:
    """
    Add options for markdown header range selection via --md_start and --md_end.

    Both arguments accept header specifications in two formats:
    - Full format: "## Section Title" (includes the # symbols)
    - Partial match: "Section Title" (just the title, matches if unique)

    :param parser: ArgumentParser to add arguments to
    :param start_required: whether the start header is required (default: True)
    :param end_required: whether the end header is required (default: False)
    :return: ArgumentParser with the new arguments added
    """
    parser.add_argument(
        "--md_start",
        type=str,
        required=start_required,
        default=None,
        help=(
            "Starting header: either full format (e.g., '## Section 1') or "
            "partial match (e.g., 'Section 1'). Partial match must be unique."
        ),
    )
    parser.add_argument(
        "--md_end",
        type=str,
        required=end_required,
        default=None,
        help=(
            "Ending header: either full format (e.g., '## Section 2') or "
            "partial match (e.g., 'Section 2'). If not provided, extracts "
            "until the next header at the same or higher level. Partial match "
            "must be unique."
        ),
    )
    return parser


# #############################################################################
# Command line options for file type filtering
# #############################################################################


def add_file_type_filter_args(
    parser: argparse.ArgumentParser,
    *,
    file_types_default: str,
) -> argparse.ArgumentParser:
    """
    Add command line arguments for filtering files by type.

    Adds the following mutually exclusive arguments:
    - `--file_types`: comma-separated list of file extensions to include
      (e.g., 'py,ipynb,md'). Empty string means keep all extensions.
    - `--skip_file_types`: comma-separated list of file extensions to skip
      (e.g., 'txt'). Empty string means skip no extensions.

    :param parser: ArgumentParser to add arguments to
    :param file_types_default: default file types to process
    :return: ArgumentParser with the arguments added
    """
    file_type_group = parser.add_mutually_exclusive_group()
    file_type_group.add_argument(
        "--file_types",
        type=str,
        default=file_types_default,
        help="Comma-separated list of file extensions to process (e.g., 'py,ipynb,md,txt')\n"
        "  Available: py (Python), ipynb (Jupyter), md (Markdown), txt (Text)\n"
        f"  Default: '{file_types_default}'",
    )
    file_type_group.add_argument(
        "--skip_file_types",
        type=str,
        default="",
        help="Comma-separated list of file extensions to skip (e.g., 'txt')\n"
        "  Empty string means skip no extensions",
    )
    return parser


def filter_files_by_extensions(
    files: List[str],
    file_types_str: str,
    skip_file_types_str: str,
) -> List[str]:
    """
    Filter files by their extensions based on include or exclude patterns.

    This helper function can be called with strings to filter files by type,
    making it useful for both command-line interfaces and programmatic use
    (e.g., from invoke tasks).

    :param files: List of file paths to filter
    :param file_types_str: Comma-separated string of extensions to include
        (e.g., 'py,ipynb,md'). If provided, only files with these extensions
        are included.
    :param skip_file_types_str: Comma-separated string of extensions to skip
        (e.g., 'txt,log'). If provided, files with these extensions are
        excluded.
    :return: Filtered list of file paths
    """
    hdbg.dassert_lte(int(file_types_str != "") + int(skip_file_types_str != ""), 1)
    if file_types_str == "" and skip_file_types_str == "":
        # Nothing to do.
        return files
    filtered_files = []
    _LOG.debug("File to process: %s", files)
    if file_types_str != "":
        file_extensions = {
            ext.strip() for ext in file_types_str.split(",") if ext.strip()
        }
        _LOG.debug("File extensions to process: %s", file_extensions)
        for file_path in files:
            ext = file_path.split(".")[-1] if "." in file_path else ""
            if ext in file_extensions:
                filtered_files.append(file_path)
    elif skip_file_types_str != "":
        skip_extensions = {
            ext.strip()
            for ext in skip_file_types_str.split(",")
            if ext.strip()
        }
        _LOG.debug("File extensions to skip: %s", skip_extensions)
        for file_path in files:
            ext = file_path.split(".")[-1] if "." in file_path else ""
            if ext not in skip_extensions:
                filtered_files.append(file_path)
    _LOG.debug("Filtered files: %d -> %d", len(files), len(filtered_files))
    return filtered_files


def parse_file_type_filter_args(
    args: argparse.Namespace,
    files: List[str],
) -> List[str]:
    """
    Parse file type filter arguments and return filtered list of files.

    Parses both `--file_types` and `--skip_file_types` arguments, returning
    the list of files to process after filtering by extension.

    :param args: Parsed command line arguments from add_file_type_filter_args
    :param files: List of file paths to filter
    :return: List of file paths after extension filtering
    """
    file_types = getattr(args, "file_types", "")
    skip_file_types = getattr(args, "skip_file_types", "")
    # Since args have mutually exclusive defaults, if skip_file_types is set,
    # clear file_types (which would have its default value)
    if skip_file_types:
        file_types = ""
    filtered_files = filter_files_by_extensions(
        files,
        file_types_str=file_types,
        skip_file_types_str=skip_file_types,
    )
    return filtered_files
