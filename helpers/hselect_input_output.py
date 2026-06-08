"""
Select and process input/output files, handle stdin/stdout, and filter files.

Import as:

import helpers.hselect_input_output as hseinout
"""

import argparse
import logging
import os
import sys
from typing import Any, List, Optional, Tuple, Union

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# _SingleFilesAction
# #############################################################################


class _SingleFilesAction(argparse.Action):
    """
    Custom action that errors if --files is used multiple times.
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str = "",
    ) -> None:
        if getattr(namespace, self.dest, None) is not None:
            msg = (
                f"{option_string} can only be specified once. "
                "Use a single argument with space-separated files: "
                f'{option_string} "file1.py file2.py file3.py"'
            )
            parser.error(msg)
        setattr(namespace, self.dest, values)


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
    file_selection.add_argument(
        "--files",
        action=_SingleFilesAction,
        help="Select specific files (space-separated list in a single argument)",
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
    - --files: files specified as space-separated list
    - --from_files: files listed in a file (one per line)
    - --modified: files modified in the client
    - --branch: files modified with respect to the branch point
    - --last_commit: files part of the previous commit
    - --all: all repo files

    :param args: Parsed command-line arguments from add_file_selection_args
    :param remove_dirs: Whether to exclude directories from results
    :param dir_name: Directory to search (default: current directory)
    :return: List of file paths to process
    """
    import helpers.hgit as hgit

    files = hgit.get_files_to_process(
        getattr(args, "files", ""),
        getattr(args, "from_file", ""),
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
# Command line options for input/output processing.
# #############################################################################


def add_input_output_args(
    parser: argparse.ArgumentParser,
    *,
    in_default: str = "",
    in_required: bool = True,
    out_default: str = "",
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
        default="",
        help="One or more files (space-separated, shell globs supported) or comma-separated list",
    )
    parser.add_argument(
        "--from_file",
        action="store",
        type=str,
        default="",
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
        files = []
        for token in args.input_files:
            files.extend(token.replace(",", " ").split())
        return files
    elif args.from_file:
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
    if not out_file_name:
        out_file_name = in_file_name
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
        output is printed and avoid to print log messages
    """
    verbosity = args.log_level
    if not verbose:
        if args.log_level == "INFO":
            verbosity = "CRITICAL"
    else:
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
        txt = []
        for line in sys.stdin:
            txt.append(line.rstrip("\n"))
    elif file_name == "pb":
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
        if hserver.is_host_mac():
            _LOG.info("Writing to clipboard")
            txt_str = "\n".join(txt)
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
    in_lines = from_file(in_file_name)
    if in_file_name == "-":
        tmp_in_file_name = f"tmp.{tag}.in.txt"
        in_txt = "\n".join(in_lines)
        hio.to_file(tmp_in_file_name, in_txt)
    else:
        tmp_in_file_name = in_file_name
    tmp_out_file_name = f"tmp.{tag}.out.txt"
    return tmp_in_file_name, tmp_out_file_name


def add_dst_dir_arg(
    parser: argparse.ArgumentParser,
    dst_dir_required: bool,
    dst_dir_default: str = "",
) -> argparse.ArgumentParser:
    """
    Add command line options related to destination directory.

    Adds `--dst_dir` and `--overwrite` flags. If the destination directory
    already exists and `--overwrite` is not specified, an error is raised.

    E.g., `--dst_dir`, `--overwrite`
    """
    hdbg.dassert_imply(
        dst_dir_required,
        not dst_dir_default,
        "Since dst_dir_required='%s', you need to specify a default "
        "destination dir, instead of dst_dir_default='%s'",
        dst_dir_required,
        dst_dir_default,
    )
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
    _LOG.debug("Items to process:")
    for i, item in enumerate(items):
        _LOG.debug("  [%s]: %s", i, item)
    return items


# #############################################################################
# Select multiple file input.
# #############################################################################


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
    if hasattr(args, "files") and args.files:
        _LOG.debug("Using --files option")
        file_list = [f.strip() for f in args.files.split(",")]
        file_list = [f for f in file_list if f]
    elif hasattr(args, "from_files") and args.from_files:
        _LOG.debug("Using --from_files option")
        hdbg.dassert_path_exists(args.from_files)
        content = hio.from_file(args.from_files)
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                file_list.append(line)
    elif hasattr(args, "input") and args.input:
        if isinstance(args.input, list):
            _LOG.debug("Using --input option (repeated argument)")
            file_list = args.input
        else:
            _LOG.debug(
                "Using -i/--input option (single file, backward compatibility)"
            )
            file_list = [args.input]
    else:
        hdbg.dfatal("No input files specified")
    hdbg.dassert_isinstance(file_list, list)
    hdbg.dassert_lt(
        0, len(file_list), "No input files specified after parsing arguments"
    )
    for file_path in file_list:
        hdbg.dassert_path_exists(file_path)
    _LOG.info("Found %s file(s) to process", len(file_list))
    return file_list


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
    hdbg.dassert_lte(
        int(file_types_str != "") + int(skip_file_types_str != ""), 1
    )
    if file_types_str == "" and skip_file_types_str == "":
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
            ext.strip() for ext in skip_file_types_str.split(",") if ext.strip()
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
    if skip_file_types:
        file_types = ""
    filtered_files = filter_files_by_extensions(
        files,
        file_types_str=file_types,
        skip_file_types_str=skip_file_types,
    )
    return filtered_files
