#!/usr/bin/env python

"""
Process lecture source files to generate PDF slides, scripts, and book chapters.

Orchestrates the generation of multiple outputs from lecture source files including
PDF slides, instructor scripts, LLM-based transformations, and book chapters.
Supports batch processing via pattern matching, lesson ranges, and slide range limiting.

Lecture selection supports:
- Single pattern: '01.1' or '01*'
- Union of patterns: '01*:02*:03.1' (colon-separated)
- Continuous range: '01.1-03.2' (hyphen-separated, inclusive)

For detailed usage, examples, and documentation, see README.md in this directory.
"""

import argparse
import glob
import logging
import os
import re
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

_VALID_ACTIONS = [
    "generate_pdf",
    "generate_script",
    "reduce_slide",
    "check_slide",
    "improve_slide",
    "book_chapter",
    "generate_class_quizzes",
    "generate_class_recap",
]
_DEFAULT_ACTIONS = ["generate_pdf"]


# #############################################################################

def _parse_lecture_patterns(lectures_arg: str) -> Tuple[bool, List[str]]:
    """
    Parse the lectures argument into patterns or range.

    The lectures argument can be:
    - A single pattern: '01.1' or '01*'
    - Multiple patterns separated by colon: '01*:02*:03.1'
    - A range separated by hyphen: '01.1-03.2'

    Range syntax and colon-separated patterns cannot be mixed.

    :param lectures_arg: lectures argument from command line
    :return: tuple of (is_range, patterns_or_range)
        - is_range: True if input is a range, False if patterns
        - patterns_or_range: list with [start, end] if range, else list of patterns
    """
    # Check if this is a range syntax (contains hyphen).
    if "-" in lectures_arg:
        # Validate that colon is not used (cannot mix syntaxes).
        hdbg.dassert(
            ":" not in lectures_arg,
            "Cannot mix range syntax (hyphen) with union syntax (colon):",
            lectures_arg,
        )
        # Parse range bounds.
        parts = lectures_arg.split("-")
        hdbg.dassert_eq(
            len(parts),
            2,
            "Range syntax must have exactly two parts (start-end):",
            lectures_arg,
        )
        _LOG.debug("Parsed lecture range: %s to %s", parts[0], parts[1])
        return True, parts
    # Parse as colon-separated patterns (original behavior).
    patterns = lectures_arg.split(":")
    _LOG.debug("Parsed lecture patterns: %s", patterns)
    return False, patterns


def _expand_lecture_range(
    class_dir: str, start_lesson: str, end_lesson: str
) -> List[Tuple[str, str]]:
    """
    Expand a lesson range to find all matching lecture files.

    :param class_dir: class directory (data605 or msml610)
    :param start_lesson: start of range (e.g., '01.1')
    :param end_lesson: end of range (e.g., '03.2')
    :return: list of tuples (source_path, source_name) for lessons in range
    """
    lectures_source_dir = os.path.join(class_dir, "lectures_source")
    hdbg.dassert_dir_exists(lectures_source_dir)
    # Find all lecture files in the directory.
    all_files_pattern = os.path.join(lectures_source_dir, "Lesson*")
    all_files = sorted(glob.glob(all_files_pattern))
    _LOG.debug("Found %d total lecture files", len(all_files))
    # Extract lesson numbers from filenames and filter to range.
    result = []
    for file_path in all_files:
        basename = os.path.basename(file_path)
        # Extract lesson number from filename (e.g., 'Lesson01.1-Intro.txt' -> '01.1').
        match = re.match(r"Lesson([\d.]+)", basename)
        if not match:
            continue
        lesson_num = match.group(1)
        # Check if lesson is within range (inclusive).
        # Use string comparison which works for lesson numbers like "01.1", "01.2", etc.
        if start_lesson <= lesson_num <= end_lesson:
            result.append((file_path, basename))
            _LOG.debug("Including lesson %s in range", lesson_num)
    # Validate that we found files in the range.
    hdbg.dassert_lt(
        0,
        len(result),
        "No lecture files found in range %s to %s",
        start_lesson,
        end_lesson,
    )
    _LOG.info(
        "Found %d lecture files in range %s to %s",
        len(result),
        start_lesson,
        end_lesson,
    )
    return result


def _find_lecture_files(
    class_dir: str, is_range: bool, patterns_or_range: List[str]
) -> List[Tuple[str, str]]:
    """
    Find all lecture source files matching patterns or within a range.

    :param class_dir: class directory (data605 or msml610)
    :param is_range: True if patterns_or_range is a range [start, end]
    :param patterns_or_range: list of patterns to match, or [start, end] if is_range
    :return: list of tuples (source_path, source_name)
    """
    # Handle range syntax.
    if is_range:
        hdbg.dassert_eq(
            len(patterns_or_range),
            2,
            "Range must have exactly two elements [start, end]:",
            patterns_or_range,
        )
        start_lesson, end_lesson = patterns_or_range
        _LOG.info("Finding lectures in range: %s to %s", start_lesson, end_lesson)
        return _expand_lecture_range(class_dir, start_lesson, end_lesson)
    # Handle pattern-based matching (original behavior).
    lectures_source_dir = os.path.join(class_dir, "lectures_source")
    hdbg.dassert_dir_exists(lectures_source_dir)
    # Find all matching files.
    _LOG.debug(
        "Finding lecture files for lecture_source_dir='%s' and patterns='%s'",
        lectures_source_dir,
        patterns_or_range,
    )
    all_files = []
    for pattern in patterns_or_range:
        pattern_path = os.path.join(lectures_source_dir, f"Lesson{pattern}*")
        matched_files = sorted(glob.glob(pattern_path))
        _LOG.debug("Pattern '%s' matched %d files", pattern, len(matched_files))
        all_files.extend(matched_files)
    # Convert to tuples of (path, basename).
    result = [(f, os.path.basename(f)) for f in all_files]
    _LOG.info("Found %d lecture files", len(result))
    return result


# #############################################################################


def _generate_pdf(
    class_dir: str,
    source_path: str,
    source_name: str,
    *,
    limit: Optional[str] = None,
    skip_action: str = "open",
) -> None:
    """
    Generate PDF slides from a lecture source file.

    Calls notes_to_pdf.py with appropriate arguments to convert a text source
    file into PDF slides.

    :param class_dir: class directory (data605 or msml610)
    :param source_path: path to source .txt file
    :param source_name: name of source file
    :param limit: optional slide range to process (e.g., '1:3')
    :param skip_action: action to skip (default: 'open')
    """
    # Compute output path.
    dst_name = source_name.replace(".txt", ".pdf")
    lectures_dir = os.path.join(class_dir, "lectures")
    hio.create_dir(lectures_dir, incremental=True)
    output_path = os.path.join(lectures_dir, dst_name)
    # Build command.
    _LOG.info("Processing %s -> %s", source_name, dst_name)
    cmd = [
        "notes_to_pdf.py",
        f"--input {source_path}",
        f"--output {output_path}",
        "--type slides",
        "--toc_type navigation",
        f"--skip_action {skip_action}",
        "--debug_on_error",
    ]
    if limit:
        cmd.extend([f"--limit {limit}"])
    # Execute command.
    cmd_str = " ".join(cmd)
    _LOG.info("Executing: %s", cmd_str)
    hsystem.system(cmd_str, suppress_output=False)


def _generate_script(
    class_dir: str,
    source_path: str,
    source_name: str,
    *,
    limit: Optional[str] = None,
) -> None:
    """
    Generate script from a lecture source file.

    Performs the following steps:
    1. Calls generate_slide_script.py to create the script
    2. Removes 'Transition: ' prefix using perl
    3. Lints the output using lint_txt.py

    :param class_dir: class directory (data605 or msml610)
    :param source_path: path to source .txt file
    :param source_name: name of source file
    """
    # Compute output path.
    dst_name = source_name.replace(".txt", ".script.txt")
    lectures_script_dir = os.path.join(class_dir, "lectures_script")
    hio.create_dir(lectures_script_dir, incremental=True)
    output_path = os.path.join(lectures_script_dir, dst_name)
    # Step 1: Generate slide script.
    _LOG.info("Generating script for %s -> %s", source_name, dst_name)
    cmd = [
        "generate_slide_script.py",
        f"--in_file {source_path}",
        f"--out_file {output_path}",
        "--slides_per_group 3",
    ]
    if limit:
        cmd.extend([f"--limit {limit}"])
    cmd_str = " ".join(cmd)
    _LOG.info("Executing: %s", cmd_str)
    hsystem.system(cmd_str, suppress_output=False)
    # Step 2: Remove 'Transition: ' prefix.
    cmd_str = f"perl -pi -e 's/^Transition: //g' {output_path}"
    _LOG.info("Executing: %s", cmd_str)
    hsystem.system(cmd_str, suppress_output=False)
    # Step 3: Lint the output.
    cmd_str = f"lint_txt.py -i {output_path} --use_dockerized_prettier"
    _LOG.info("Executing: %s", cmd_str)
    hsystem.system(cmd_str, suppress_output=False)


def _slide_reduce(
    source_path: str, source_name: str, *, limit: Optional[str] = None
) -> None:
    """
    Reduce slides by applying LLM transformation.

    This transforms the data in place using process_slides.py.

    :param source_path: path to source .txt file
    :param source_name: name of source file
    """
    _LOG.info("Reducing slides for %s", source_name)
    cmd = [
        "process_slides.py",
        f"--in_file {source_path}",
        "--action slide_reduce",
        "--use_llm_transform",
    ]
    if limit:
        cmd.extend([f"--limit {limit}"])
    cmd_str = " ".join(cmd)
    _LOG.info("Executing: %s", cmd_str)
    hsystem.system(cmd_str, suppress_output=False)


def _slide_check(
    source_path: str, source_name: str, *, limit: Optional[str] = None
) -> None:
    """
    Check slides by applying LLM transformation.

    Creates a check report in a separate output file.

    :param source_path: path to source .txt file
    :param source_name: name of source file
    """
    # Compute output path.
    output_path = f"{source_path}.slide_check.txt"
    _LOG.info("Checking slides for %s -> %s", source_name, output_path)
    cmd = [
        "process_slides.py",
        f"--in_file {source_path}",
        "--action text_check",
        f"--out_file {output_path}",
        "--use_llm_transform",
    ]
    if limit:
        cmd.extend([f"--limit {limit}"])
    cmd_str = " ".join(cmd)
    _LOG.info("Executing: %s", cmd_str)
    hsystem.system(cmd_str, suppress_output=False)


def _generate_book_chapter(
    class_dir: str,
    source_path: str,
    source_name: str,
) -> None:
    """
    Generate book chapter from a lecture source file.

    Uses gen_book_chapter.py Python script which:
    1. Generates a PDF from the lecture source
    2. Creates book chapter using generate_book_chapter.py
    3. Converts to PDF using pandoc
    4. Opens the resulting PDF

    :param class_dir: class directory (data605 or msml610)
    :param source_path: path to source .txt file
    :param source_name: name of source file
    """
    # Extract lesson number from source name (e.g., Lesson01.1-Intro.txt -> 01.1)
    match = re.match(r"Lesson([\d.]+)", source_name)
    if not match:
        hdbg.dfatal("Could not extract lesson number from:", source_name)
    lesson_number = match.group(1)
    # Build command using Python script.
    _LOG.info(
        "Generating book chapter for %s (lesson %s)", source_name, lesson_number
    )
    cmd_str = f"gen_book_chapter.py {class_dir} {lesson_number}"
    _LOG.info("Executing: %s", cmd_str)
    hsystem.system(cmd_str, suppress_output=False)


def _generate_class_quizzes(
    class_dir: str,
    source_path: str,
    source_name: str,
) -> None:
    """
    Generate multiple choice quizzes from a lecture source file.

    Uses gen_quizzes.py Python script with --for_class_quizzes flag which
    generates 20 multiple choice questions with 5 answers each from the
    lecture content. The script outputs the quizzes to the lectures_quizzes
    directory.

    :param class_dir: class directory (data605 or msml610)
    :param source_path: path to source .txt file
    :param source_name: name of source file
    """
    # Extract lesson number from source name (e.g., Lesson01.1-Intro.txt -> 01.1)
    match = re.match(r"Lesson([\d.]+)", source_name)
    if not match:
        hdbg.dfatal("Could not extract lesson number from:", source_name)
    lesson_number = match.group(1)
    # Build command using Python script.
    _LOG.info(
        "Generating class quizzes for %s (lesson %s)", source_name, lesson_number
    )
    cmd_str = (
        f"gen_quizzes.py --for_class_quizzes "
        f"{class_dir} {lesson_number}"
    )
    _LOG.info("Executing: %s", cmd_str)
    hsystem.system(cmd_str, suppress_output=False)


def _generate_class_recap(
    class_dir: str,
    source_path: str,
    source_name: str,
) -> None:
    """
    Generate class recap questions from a lecture source file.

    Uses gen_quizzes.py Python script with --for_class_recap flag which
    generates 5 open-ended discussion/review questions from the lecture
    content. The script outputs the questions to the lectures_recap directory.

    :param class_dir: class directory (data605 or msml610)
    :param source_path: path to source .txt file
    :param source_name: name of source file
    """
    # Extract lesson number from source name (e.g., Lesson01.1-Intro.txt -> 01.1)
    match = re.match(r"Lesson([\d.]+)", source_name)
    if not match:
        hdbg.dfatal("Could not extract lesson number from:", source_name)
    lesson_number = match.group(1)
    # Build command using Python script.
    _LOG.info(
        "Generating class recap for %s (lesson %s)", source_name, lesson_number
    )
    cmd_str = (
        f"gen_quizzes.py --for_class_recap "
        f"{class_dir} {lesson_number}"
    )
    _LOG.info("Executing: %s", cmd_str)
    hsystem.system(cmd_str, suppress_output=False)


def _process_lecture_file(
    class_dir: str,
    source_path: str,
    source_name: str,
    actions: List[str],
    *,
    limit: Optional[str] = None,
) -> None:
    """
    Process a single lecture file for specified actions.

    :param class_dir: class directory (data605 or msml610)
    :param source_path: path to source .txt file
    :param source_name: name of source file
    :param actions: list of actions to execute ('generate_pdf', 'generate_script',
        'reduce_slide', 'check_slide', 'improve_slide', 'book_chapter',
        'generate_class_quizzes', 'generate_class_recap')
    :param limit: optional slide range to process
    """
    _LOG.info("Processing file: %s", source_path)
    # Process each action.
    for action in actions:
        if action == "generate_pdf":
            _generate_pdf(class_dir, source_path, source_name, limit=limit)
        elif action == "generate_script":
            _generate_script(class_dir, source_path, source_name, limit=limit)
        elif action == "reduce_slide":
            _slide_reduce(source_path, source_name, limit=limit)
        elif action == "check_slide":
            _slide_check(source_path, source_name, limit=limit)
        elif action == "improve_slide":
            # TODO: Implement _slide_improve function.
            hdbg.dfatal("improve_slide action not yet implemented")
        elif action == "book_chapter":
            _generate_book_chapter(class_dir, source_path, source_name)
        elif action == "generate_class_quizzes":
            _generate_class_quizzes(class_dir, source_path, source_name)
        elif action == "generate_class_recap":
            _generate_class_recap(class_dir, source_path, source_name)
        else:
            hdbg.dfatal("Unknown action:", action)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.

    :return: configured argument parser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--lectures",
        action="store",
        required=True,
        help=(
            "Lecture(s) to process. Supports multiple formats: "
            "- Single pattern: '01.1' or '01*' "
            "- Union (colon-separated): '01*:02*:03.1' "
            "- Range (hyphen-separated): '01.1-03.2' (inclusive). "
            "Note: Range and union syntax cannot be mixed."
        ),
    )
    parser.add_argument(
        "--limit",
        action="store",
        help="Slide range to process when single lecture specified (e.g., '1:3')",
    )
    parser.add_argument(
        "--class",
        dest="class_name",
        action="store",
        required=True,
        choices=["data605", "msml610"],
        help="Class directory name",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print the commands that would be executed without running them",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main execution function.

    Orchestrates the lesson generation process:
    1. Parse and validate arguments
    2. Find matching lecture files
    3. Process each file for specified actions

    :param parser: configured argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Parse arguments.
    is_range, patterns_or_range = _parse_lecture_patterns(args.lectures)
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info("Selected actions: %s", actions)
    # Find matching lecture files.
    files = _find_lecture_files(args.class_name, is_range, patterns_or_range)
    hdbg.dassert_lt(
        0,
        len(files),
        "No lecture files found for input: %s",
        args.lectures,
    )
    # Validate if --limit is specified.
    if args.limit:
        hdbg.dassert_eq(
            len(files), 1, "Need exactly one file when using --limit"
        )
    # Print the commands that would be executed without running them.
    if args.dry_run:
        _LOG.info(
            "Dry run mode enabled. Will print the commands that would be executed without running them."
        )
        for source_path, source_name in files:
            _LOG.info("Processing file: %s", source_path)
        return
    # Process each file.
    for source_path, source_name in files:
        _process_lecture_file(
            args.class_name, source_path, source_name, actions, limit=args.limit
        )
    _LOG.info("All files processed successfully")


if __name__ == "__main__":
    _main(_parse())
