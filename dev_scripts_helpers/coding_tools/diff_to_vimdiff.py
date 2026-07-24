#!/usr/bin/env python3

r"""
Diff content of two directories using vimdiff, by transform the output of `diff -r
--brief dir1 dir2` into a script using vimdiff.

# To clean up the crap in the dirs:
> git status --ignored
> git clean -fdx --dry-run

# Diff content of dirs using vimdiff:
> diff_to_vimdiff.py \
    --dir1 /Users/saggese/src/...2/amp \
    --dir2 /Users/saggese/src/...3/amp

# Diff only files that are present in both dirs but have different content:
> diff_to_vimdiff.py \
    --dir1 ... --dir2 ... \
    --only_different_file_content

# Diff only files that are not present in both dirs
> diff_to_vimdiff.py \
    --dir1 ... --dir2 ... \
    --only_different_files

# Compare the list of files in the two dirs, instead of the content of the files:
> diff_to_vimdiff.py \
    --dir1 ... --dir2 ... \
    --compare_file_list

Import as:

import dev_scripts_helpers.coding_tools.diff_to_vimdiff as dsditovi
"""

# TODO(ai_gp): Unit test this.
# TODO(ai_gp): Remove __pycache__ and anything else?
# TODO(ai_gp): Improve the interface (e.g., --select_files) to match the more
# modern way.

import argparse
import logging
import os
import re
import sys
from typing import Any, cast, Match, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _remove_files_from_file_list(
    file_name: str,
    regexes_to_ignore: Optional[str],
    do_not_skip_tmp: bool,
) -> None:
    """
    Remove certain files (e.g., `.git`, `tmp.`, ...) from the content of a
    file.

    - Read the file with the list of files (one line per file)
    - Remove certain files (e.g., `.git`, `tmp.`, ...)
    - Write the file back with the files to keep

    :param file_name: Name of the file to remove files from
    :param regexes_to_ignore: Regex to ignore certain files
    :param do_not_skip_tmp: Do not skip `tmp.` files
    """
    _LOG.debug(hprint.func_signature_to_str())
    _LOG.info("Removing files from '%s'", file_name)
    # Read file and parse list of files (one per line).
    txt = hio.from_file(file_name)
    files = txt.split("\n")
    _LOG.debug("Found %d files", len(files))
    # Build regex pattern for files to exclude from results.
    vals = [r"\.git\/", r"\.git:", r"\.idea"]
    if not do_not_skip_tmp:
        vals.append(r"[\/ ]tmp\.")
    if regexes_to_ignore:
        vals.append(regexes_to_ignore)
    regex = "|".join(vals)
    _LOG.debug("regex=%s", regex)
    # Classify files as kept or removed based on regex pattern.
    # remove_cmd = "| grep -v \"\.git/\" | grep -v \.idea | grep -v '[/ ]tmp.'"
    removed_files = []
    kept_files = []
    for file in files:
        keep = not bool(re.search(regex, file))
        if keep:
            kept_files.append(file)
        else:
            removed_files.append(file)
        _LOG.debug("file='%s': -> kept=%s", file, keep)
    _LOG.debug("Found %d files to keep", len(kept_files))
    _LOG.debug("Found %d files to remove", len(removed_files))
    # Persist original, removed, and filtered file lists for inspection.
    hio.to_file(file_name + ".orig", "\n".join(files))
    hio.to_file(file_name + ".removed", "\n".join(removed_files))
    # Update the file with the files to keep.
    hio.to_file(file_name, "\n".join(kept_files))
    # Verify partition is complete (all files accounted for).
    hdbg.dassert_eq(len(files), len(removed_files) + len(kept_files))


def _load_file_list(from_file: str) -> set:
    """
    Load list of files from a file (one per line).

    :param from_file: Path to file containing file paths
    :return: Set of normalized file paths
    """
    _LOG.debug(hprint.func_signature_to_str())
    _LOG.info("Loading file list from '%s'", from_file)
    hdbg.dassert_path_exists(from_file)
    txt = hio.from_file(from_file)
    files = set()
    for line in txt.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            files.add(line)
    _LOG.info("Loaded %d files from list", len(files))
    return files


def _filter_diff_output(
    diff_file: str, from_file: Optional[str]
) -> None:
    """
    Filter diff output to only include files in from_file.

    - Read the diff file
    - Keep only lines that contain file paths in from_file
    - Write the filtered result back

    :param diff_file: Path to file with diff output
    :param from_file: Path to file containing files to keep, or None
    """
    if from_file is None:
        return
    _LOG.debug(hprint.func_signature_to_str())
    _LOG.info("Filtering diff output using '%s'", from_file)
    # Load set of files to keep.
    files_to_keep = _load_file_list(from_file)
    # Read diff output.
    txt = hio.from_file(diff_file)
    lines = txt.split("\n")
    _LOG.debug("Found %d lines in diff output", len(lines))
    # Filter lines to keep only those matching files in from_file.
    filtered_lines = []
    for line in lines:
        if line == "":
            continue
        keep = False
        # Extract file paths from diff output lines.
        if line.startswith("Only in "):
            # Format: "Only in /path/to/dir: filename"
            m = re.match(r"^Only in (\S+): (\S+)$", line)
            if m:
                file_path = f"{m.group(1)}/{m.group(2)}"
                if _path_matches_any(file_path, files_to_keep):
                    keep = True
        elif line.startswith("Files "):
            # Format: "Files /path/to/file1 and /path/to/file2 differ"
            m = re.match(r"^Files (\S+) and (\S+) differ$", line)
            if m:
                if _path_matches_any(m.group(1), files_to_keep):
                    keep = True
        _LOG.debug("line='%s': -> keep=%s", line, keep)
        if keep:
            filtered_lines.append(line)
    _LOG.debug("Found %d lines to keep", len(filtered_lines))
    # Write filtered output back.
    hio.to_file(diff_file, "\n".join(filtered_lines))


def _path_matches_any(path: str, file_list: set) -> bool:
    """
    Check if path matches any entry in file_list.

    Handles both absolute and relative paths by comparing normalized versions.

    :param path: File path to check
    :param file_list: Set of file paths to match against
    :return: True if path matches any entry in file_list
    """
    # Normalize path for comparison.
    norm_path = os.path.normpath(path)
    for file_to_keep in file_list:
        norm_file = os.path.normpath(file_to_keep)
        # Check if path contains or matches the file path.
        if norm_path.endswith(norm_file) or norm_file in norm_path:
            return True
    return False


# #############################################################################


def _compare_file_list(
    dir1: str, dir2: str, regexes_to_ignore: Optional[str]
) -> None:
    """
    Extract the file list from two dirs and run `sdiff` on the two file lists.

    The output looks like:
    ```
    > sdiff --suppress-common-lines --expand-tabs /tmp/dir1 /tmp/dir2
                                          > ./.dockerignore
                                          > ./.github.OLD
                                          > ./.github.OLD/gh_requirements.txt

      ./.github/workflows/build_image.cma <
      ./.github/workflows/build_image.dev <
      ./.github/workflows/ib_connector.bu <
      ./.github/workflows/import_cycles_d <
      ./dev_scripts/notebooks/test/outcom | ./dev_scripts/notebooks/test/simple
      ./dev_scripts/notebooks/test/outcom | ./dev_scripts/notebooks/test/simple
    ```

    :param dir1: first dir
    :param dir2: second dir
    :param regexes_to_ignore: regex for files to remove
    """
    _LOG.debug("Comparing file lists in dirs '%s' vs '%s'", dir1, dir2)
    print(hprint.frame(f"Compare file list in dirs '{dir1}' vs '{dir2}'"))
    hdbg.dassert_path_exists(dir1)
    hdbg.dassert_path_exists(dir2)
    # Extract sorted file listings from both directories.
    cmd = ""
    # remove_cmd = "| grep -v \"\.git/\" | grep -v \.idea | grep -v '[/ ]tmp.'"
    cmd += f'(cd {dir1} && find . -name "*" | sort >/tmp/dir1) && '
    cmd += f'(cd {dir2} && find . -name "*" | sort >/tmp/dir2)'
    print(cmd)
    hsystem.system(cmd, abort_on_error=True)
    # Filter out files matching ignore patterns (e.g., `.git/`, `.idea`, `tmp.`).
    _remove_files_from_file_list("/tmp/dir1", regexes_to_ignore, do_not_skip_tmp=True)
    _remove_files_from_file_list("/tmp/dir2", regexes_to_ignore, do_not_skip_tmp=True)
    # Display side-by-side diff of filtered file listings.
    opts = []
    opts.append("--suppress-common-lines")
    opts.append("--expand-tabs")
    opts = " ".join(opts)
    cmd = f"sdiff {opts} /tmp/dir1 /tmp/dir2"
    print("# Diff file listing with:\n> " + cmd)
    hsystem.system(cmd, abort_on_error=False, suppress_output=False)


# #############################################################################


def _find_files_to_diff(
    dir1: str,
    dir2: str,
    regexes_to_ignore: Optional[str],
    do_not_skip_tmp: bool,
) -> str:
    """
    Diff the dirs with `diff -r --brief`, and save the output in a file.

    :return: path of the file with the output of `diff -r --brief`
    """
    _LOG.debug(hprint.func_signature_to_str())
    print(hprint.frame(f"Diff dirs '{dir1}' vs '{dir2}'"))
    # Generate diff output comparing directory contents using `diff -r --brief`.
    dst_file = "./tmp.diff_file_listings.txt"
    cmd = f"diff --brief -r {dir1} {dir2} >{dst_file}"
    hsystem.system(cmd, abort_on_error=False)
    _LOG.info("Diff output saved to '%s'", dst_file)
    # Filter results to remove files matching ignore patterns.
    _remove_files_from_file_list(
        dst_file, regexes_to_ignore, do_not_skip_tmp=True
    )
    # Display filtered diff results to user.
    cmd = f"cat {dst_file}"
    print(f"# To see diff of the dirs:\n> {cmd}")
    hsystem.system(cmd, abort_on_error=False, suppress_output=False)
    return dst_file


def _get_symbolic_filepath(dir1: str, dir2: str, file_name: str) -> str:
    """
    Transform a path like:

        /Users/saggese/src/...2/amp/vendors/first_rate/utils.py
    into:
        $DIR1/amp/vendors/first_rate/utils.py
    """
    # Replace absolute directory paths with symbolic references for portability.
    file_name = file_name.replace(dir1, "$DIR1")
    file_name = file_name.replace(dir2, "$DIR2")
    return file_name


# TODO(gp): We should use the `sdiff` between files, instead of the output of
#  `diff -r --brief` to compare, since the second doesn't work for dirs that are
#  present only on one side.
def _parse_diff_output(
    input_file: str, dir1: str, dir2: str, args: argparse.Namespace
) -> None:
    """
    Process the output of diff and create a script to diff the different files.

    :param input_file: the output of `diff -r --brief`, e.g.,
        ```
        Only in /Users/saggese/src/amp1/dataflow_amp: features
        Only in /Users/saggese/src/amp1/dataflow_amp/real_time/test: TestReal...
        ```
    """
    print(hprint.frame(f"Compare file content in dirs '{dir1}' vs '{dir2}'"))
    # Read and parse diff output from `diff -r --brief`.
    hdbg.dassert_path_exists(input_file)
    _LOG.info("Reading '%s'", input_file)
    txt = hio.from_file(input_file)
    txt = txt.split("\n")
    # Process each diff line to generate vimdiff commands and optional comments.
    out = []
    for line in txt:
        _LOG.debug("# line='%s'", line)
        if line == "":
            continue
        comment = None
        out_line = None
        skip = False
        if line.startswith("Only in "):
            # Handle files that exist in only one directory.
            m = re.match(r"^Only in (\S+): (\S+)$", line)
            hdbg.dassert(m, "Invalid line='%s'", line)
            m = cast(Match[Any], m)
            file_name = f"{m.group(1)}/{m.group(2)}"
            # Convert absolute paths to symbolic references ($DIR1/$DIR2).
            dir_ = _get_symbolic_filepath(dir1, dir2, m.group(1))
            dirs = dir_.split("/")
            dir_ = dirs[0]
            file_ = os.path.join(
                *dirs[1:], _get_symbolic_filepath(dir1, dir2, m.group(2))
            )
            # Determine which directory contains the file: < for DIR1, > for DIR2.
            sign = ""
            if "$DIR1" in dir_:
                sign = "<"
            elif "$DIR2" in dir_:
                sign = ">"
            else:
                hdbg.dfatal(f"Invalid dir_='{dir_}'")
            # Apply user-supplied directory name substitutions for display.
            if args.dir1_name is not None:
                dir_ = dir_.replace("$DIR1", args.dir1_name)
            if args.dir2_name is not None:
                dir_ = dir_.replace("$DIR2", args.dir2_name)
            comment = line + "\n"
            comment += f"{sign}: ONLY: {file_} in '{dir_}'\n"
            # Generate vimdiff command to compare against empty/missing file.
            if args.dir1 in file_name:
                out_line = "vimdiff %s %s" % (
                    file_name,
                    file_name.replace(args.dir1, args.dir2),
                )
            else:
                hdbg.dassert_in(args.dir2, file_name)
                out_line = "vimdiff %s %s" % (
                    file_name.replace(args.dir2, args.dir1),
                    file_name,
                )
            # Skip directory entries since we only diff file content.
            if os.path.isdir(file_name):
                _LOG.debug("Skipping dir '%s'", file_name)
                skip = True
            # Skip if user only wants files with different content (not just different structure).
            if args.only_different_file_content:
                _LOG.debug("  -> Skipping line")
                skip = True
        elif line.startswith("Files "):
            # Handle files that exist in both dirs but have different content.
            m = re.match(r"^Files (\S+) and (\S+) differ$", line)
            hdbg.dassert(m, "Invalid line='%s'", line)
            m = cast(Match[Any], m)
            # Verify both files exist before generating diff command.
            hdbg.dassert_path_exists(m.group(1))
            hdbg.dassert_path_exists(m.group(2))
            # Extract and normalize file paths for display in comments.
            file1 = _get_symbolic_filepath(dir1, dir2, m.group(1))
            file1 = file1.replace("$DIR1/", "")
            file2 = _get_symbolic_filepath(dir1, dir2, m.group(2))
            file2 = file2.replace("$DIR2/", "")
            hdbg.dassert_eq(file1, file2)
            sign = "-"
            comment = "\n" + line + "\n"
            comment += f"{sign}: DIFF: {file1}"
            # Generate vimdiff command to compare both file versions.
            out_line = f"vimdiff {m.group(1)} {m.group(2)}"
            # Skip if user only wants files that exist in only one dir (not content differences).
            if args.only_different_files:
                _LOG.debug("  -> Skipping line")
                skip = True
        elif line.startswith("File "):
            _LOG.warning(line)
            continue
        else:
            hdbg.dfatal(f"Invalid line='{line}'")
        # Add comment to output script if enabled by user.
        if not args.skip_comments:
            if comment:
                out.append(hprint.prepend(comment, "#       "))
        # Add vimdiff command to output script if enabled by user.
        if not args.skip_vim:
            if out_line:
                _LOG.debug("    -> out='%s'", out_line)
                if skip:
                    out_line = "# " + out_line
                out.append(out_line)
    # Assemble output script.
    out = "\n".join(out)
    output_file = args.output_file
    if output_file is None:
        # Print to screen instead of generating script file.
        print(out)
    else:
        # Write script file and optionally execute it.
        _LOG.info("Writing '%s'", output_file)
        hio.to_file(output_file, out)
        cmd = f"chmod +x {output_file}"
        hsystem.system(cmd)
        _LOG.debug("Made script executable: '%s'", output_file)
        # Press enter to continue.
        hsystem.press_enter_to_continue()
        # Run the diff script.
        cmd = f"./{output_file}"
        print("Run script with:\n> " + cmd)
        # Start the script automatically if user requested.
        if args.run_diff_script:
            _LOG.info("Running diff script: '%s'", output_file)
            os.system(cmd)
        else:
            _LOG.warning("Skipping running script: %s", cmd)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Required: paths to the two directories to compare.
    parser.add_argument(
        "--dir1", action="store", required=True, help="First dir to compare"
    )
    parser.add_argument(
        "--dir2", action="store", required=True, help="Second dir to compare"
    )
    parser.add_argument("--subdir", action="store", help="subdir to compare")
    # Optional: user-friendly labels for directories in output.
    parser.add_argument(
        "--dir1_name",
        action="store",
        help="A symbolic name for the dir1, e.g., branch_ABC",
    )
    parser.add_argument(
        "--dir2_name",
        action="store",
        help="A symbolic name for the dir2, e.g., branch_XYZ",
    )
    # Output file configuration.
    parser.add_argument(
        "-o",
        "--output_file",
        action="store",
        default="tmp.diff_to_vimdiff.sh",
        help="Output script file. Don't specify anything for stdout",
    )
    parser.add_argument(
        "--compare_file_list",
        action="store_true",
        help="Diff the list of files between the dirs and exit",
    )
    parser.add_argument(
        "--only_different_file_content",
        action="store_true",
        help="Diff content of only files that are present in both dirs but have "
        "different content",
    )
    parser.add_argument(
        "--only_different_files",
        action="store_true",
        help="Diff content of only files that are not present in both dirs",
    )
    parser.add_argument(
        "--from_file",
        action="store",
        default=None,
        help="Specify a file that contains the files to actually consider "
        "for the diff (one per line)",
    )
    parser.add_argument(
        "--ignore_files",
        action="store",
        default=None,
        help="Regex to skip certain files",
    )
    parser.add_argument(
        "--skip_tmp",
        action="store_true",
        help="Skip `tmp.` files",
    )
    hparser.add_bool_arg(
        parser,
        "run_diff_script",
        default_value=True,
        help_="Run automatically the diffing script or not",
    )
    parser.add_argument(
        "--skip_comments",
        action="store_true",
        help="Do not print comments in the diff script",
    )
    parser.add_argument(
        "--skip_vim",
        action="store_true",
        help="Do not print vim commands in the diff script",
    )
    hparser.add_verbosity_arg(parser)
    return parser


# #############################################################################


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=False)
    # Resolve target directories to absolute paths.
    dir1 = os.path.abspath(args.dir1)
    dir2 = os.path.abspath(args.dir2)
    if args.subdir:
        dir1 = os.path.join(dir1, args.subdir)
        dir2 = os.path.join(dir2, args.subdir)
    _LOG.info("Dir1: '%s', Dir2: '%s'", dir1, dir2)
    # Compare file listings if requested; exit early.
    if args.compare_file_list:
        _LOG.info("Comparing file lists only (not content)")
        _compare_file_list(dir1, dir2, args.ignore_files)
        sys.exit(0)
    # Generate diff summary and parse for vimdiff commands.
    diff_file = _find_files_to_diff(
        dir1,
        dir2,
        args.ignore_files,
        not args.skip_tmp,
    )
    # Filter diff output if from_file is specified.
    _filter_diff_output(diff_file, args.from_file)
    _LOG.info("Processing diff output to generate vimdiff script")
    _parse_diff_output(diff_file, dir1, dir2, args)
    _LOG.info("Done")


if __name__ == "__main__":
    _main(_parse())
