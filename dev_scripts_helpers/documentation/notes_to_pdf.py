#!/usr/bin/env python

"""
Convert a txt file into a PDF / HTML / slides using `pandoc`.

# From scratch with TOC:
> notes_to_pdf.py -a pdf --input ...

# For interactive mode:
> notes_to_pdf.py -a pdf --no_cleanup_before --no_cleanup --input ...

# Check that can be compiled:
> notes_to_pdf.py -a pdf --no_toc --no_open_pdf --input ...

> notes_to_pdf.py \
    --input notes/IN_PROGRESS/math.The_hundred_page_ML_book.Burkov.2019.txt \
    -a pdf --no_cleanup --no_cleanup_before --no_run_latex_again --no_open
"""

# TODO(gp): See below.
#  - clean up the file_ file_out logic and make it a pipeline
#  - factor out the logic from linter.py about actions and use it everywhere


import argparse
import logging
import os
import sys
from typing import Any, List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdown
import helpers.hopen as hopen
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

_EXEC_DIR_NAME = os.path.abspath(os.path.dirname(sys.argv[0]))

# #############################################################################

_SCRIPT = None


def _system(cmd: str, log_level: int = logging.INFO, **kwargs: Any) -> int:
    if _SCRIPT is not None:
        _SCRIPT.append(cmd)
    rc = hsystem.system(cmd, log_level=log_level, **kwargs)
    return rc  # type: ignore


def _system_to_string(
    cmd: str, log_level: int = logging.INFO, **kwargs: Any
) -> Tuple[int, str]:
    if _SCRIPT is not None:
        _SCRIPT.append(cmd)
    rc, txt = hsystem.system_to_string(cmd, log_level=log_level, **kwargs)
    return rc, txt


# #############################################################################


def _cleanup_before(prefix: str) -> None:
    """
    Remove all intermediate files.

    :param prefix: The prefix used to identify the files to be removed.
    """
    _LOG.warning("\n%s", hprint.frame("Clean up before", char1="<", char2=">"))
    cmd = f"rm -rf {prefix}*"
    _ = _system(cmd)


def _filter_by_header(file_: str, header: str, prefix: str) -> str:
    """
    Pre-process the file.

    :param file_: The input file to be processed
    :param header: The header to filter by (e.g., `# Introduction`)
    :param prefix: The prefix used for the output file (e.g., `tmp.pandoc`)
    :return: The path to the processed file
    """
    _LOG.info("\n%s", hprint.frame("Filter by header", char1="<", char2=">"))
    txt = hio.from_file(file_)
    # Filter by header.
    txt = hmarkdown.extract_section_from_markdown(txt, header)
    #
    file_out = f"{prefix}.filter_by_header.txt"
    hio.to_file(file_out, txt)
    return file_out


def _preprocess_notes(curr_path: str, file_: str, prefix: str) -> str:
    """
    Pre-process the file.

    :param curr_path: The current path where the script is located
    :param file_: The input file to be processed
    :param prefix: The prefix used for the output file (e.g., `tmp.pandoc`)
    :return: The path to the processed file
    """
    _LOG.info("\n%s", hprint.frame("Preprocess notes", char1="<", char2=">"))
    file1 = file_
    file2 = f"{prefix}.no_spaces.txt"
    cmd = f"{curr_path}/preprocess_notes.py --input {file1} --output {file2}"
    _ = _system(cmd)
    file_ = file2
    return file_


def _run_latex(cmd: str, file_: str) -> None:
    """
    Run the LaTeX command and handle errors.

    :param cmd: The LaTeX command to be executed
    :param file_: The file to be processed by LaTeX
    """
    data: Tuple[int, str] = _system_to_string(cmd, abort_on_error=False)
    rc, txt = data
    log_file = file_ + ".latex1.log"
    hio.to_file(log_file, txt)
    if rc != 0:
        txt_as_arr: List[str] = txt.split("\n")
        for i, line in enumerate(txt_as_arr):
            if line.startswith("!"):
                break
        # pylint: disable=undefined-loop-variable
        txt_as_arr = [
            line for i in range(max(i - 10, 0), min(i + 10, len(txt_as_arr)))
        ]
        txt = "\n".join(txt_as_arr)
        _LOG.error(txt)
        _LOG.error("Log is in %s", log_file)
        _LOG.error("\n%s", hprint.frame(f"cmd is:\n> {cmd}"))
        raise RuntimeError("Latex failed")


_COMMON_PANDOC_OPTS = [
    "-V geometry:margin=1in",
    "-f markdown",
    "--number-sections",
    # - To change the highlight style
    # https://github.com/jgm/skylighting
    "--highlight-style=tango",
    "-s",
]
# --filter /Users/$USER/src/github/pandocfilters/examples/tikz.py \
# -F /Users/$USER/src/github/pandocfilters/examples/lilypond.py \
# --filter pandoc-imagine


def _run_pandoc_to_pdf(
    args: argparse.Namespace, curr_path: str, file_: str, prefix: str
) -> str:
    """
    Convert the input file to PDF using Pandoc.

    :param args: The command-line arguments
    :param curr_path: The current path where the script is located
    :param file_: The input file to be converted
    :param prefix: The prefix used for the output file
    :return: The path to the generated PDF file
    """
    _LOG.info("\n%s", hprint.frame("Pandoc to pdf", char1="<", char2=">"))
    #
    file1 = file_
    cmd = []
    cmd.append(f"pandoc {file1}")
    cmd.extend(_COMMON_PANDOC_OPTS[:])
    #
    cmd.append("-t latex")
    template = f"{curr_path}/pandoc.latex"
    hdbg.dassert_path_exists(template)
    cmd.append(f"--template {template}")
    #
    file2 = f"{prefix}.tex"
    cmd.append(f"-o {file2}")
    if not args.no_toc:
        cmd.append("--toc")
        cmd.append("--toc-depth 2")
    else:
        args.no_run_latex_again = True
    # Doesn't work
    # -f markdown+raw_tex
    cmd = " ".join(cmd)
    _ = _system(cmd, suppress_output=False)
    file_ = file2
    #
    # Run latex.
    #
    _LOG.info("\n%s", hprint.frame("Latex", char1="<", char2=">"))
    # pdflatex needs to run in the same dir of latex_abbrevs.sty so we `cd` to
    # that dir and save the output in the same dir of the input.
    hdbg.dassert_path_exists(_EXEC_DIR_NAME + "/latex_abbrevs.sty")
    cmd = f"cd {_EXEC_DIR_NAME}; "
    cmd += (
        "pdflatex"
        + " -interaction=nonstopmode"
        + " -halt-on-error"
        + " -shell-escape"
        + f" -output-directory {os.path.dirname(file_)}"
        + f" {file_}"
    )
    _run_latex(cmd, file_)
    # Run latex again.
    _LOG.info("\n%s", hprint.frame("Latex again", char1="<", char2=">"))
    if not args.no_run_latex_again:
        _run_latex(cmd, file_)
    else:
        _LOG.warning("Skipping: run latex again")
    #
    file_out = file_.replace(".tex", ".pdf")
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    return file_out


def _run_pandoc_to_html(
    args: argparse.Namespace, file_in: str, prefix: str
) -> str:
    """
    Convert the input file to HTML using Pandoc.

    :param args: The command-line arguments
    :param file_in: The input file to be converted
    :param prefix: The prefix used for the output file
    :return: The path to the generated HTML file
    """
    _LOG.info("\n%s", hprint.frame("Pandoc to html", char1="<", char2=">"))
    #
    cmd = []
    cmd.append(f"pandoc {file_in}")
    cmd.extend(_COMMON_PANDOC_OPTS[:])
    cmd.append("-t html")
    cmd.append(f"--metadata pagetitle='{os.path.basename(file_in)}'")
    #
    file2 = f"{prefix}.html"
    cmd.append(f"-o {file2}")
    if not args.no_toc:
        cmd.append("--toc")
        cmd.append("--toc-depth 2")
    cmd = " ".join(cmd)
    _ = _system(cmd, suppress_output=False)
    #
    file_out = os.path.abspath(file2.replace(".tex", ".html"))
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    return file_out


def _run_pandoc_to_slides(args: argparse.Namespace, file_: str) -> str:
    """
    Convert the input file to PDF slides using Pandoc.

    :param args: The command-line arguments
    :param file_: The input file to be converted
    :return: The path to the generated PDF file
    """
    _LOG.info("\n%s", hprint.frame("Pandoc to PDF slides", char1="<", char2=">"))
    _ = args
    #
    cmd = []
    cmd.append(f"pandoc {file_}")
    #
    cmd.append("-t beamer")
    cmd.append("--slide-level 4")
    cmd.append("-V theme:SimplePlus")
    cmd.append("--include-in-header=latex_abbrevs.sty")
    if not args.no_toc:
        cmd.append("--toc")
        cmd.append("--toc-depth 2")
    file_out = file_.replace(".txt", ".pdf")
    cmd.append(f"-o {file_out}")
    #
    cmd = " ".join(cmd)
    _ = _system(cmd, suppress_output=False)
    #
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    return file_out


def _copy_to_output(args: argparse.Namespace, file_in: str, prefix: str) -> str:
    """
    Copy the processed file to the output location.

    :param args: The command-line arguments
    :param file_in: The input file to be copied
    :param prefix: The prefix used for the output file
    :return: The path to the copied output file
    """
    if args.output is not None:
        _LOG.debug("Using file_out from command line")
        file_out = args.output
    else:
        _LOG.debug("Leaving file_out in the tmp dir")
        file_out = f"{prefix}.{os.path.basename(args.input)}.{args.type}"
    _LOG.debug("file_out=%s", file_out)
    cmd = rf"\cp -af {file_in} {file_out}"
    _ = _system(cmd)
    return file_out  # type: ignore


def _copy_to_gdrive(args: argparse.Namespace, file_name: str, ext: str) -> None:
    """
    Copy the processed file to Google Drive.

    :param args: The command-line arguments
    :param file_name: The name of the file to be copied
    :param ext: The extension of the file to be copied
    """
    _LOG.info("\n%s", hprint.frame("Copy to gdrive", char1="<", char2=">"))
    hdbg.dassert(not ext.startswith("."), "Invalid file_name='%s'", file_name)
    if args.gdrive_dir is not None:
        gdrive_dir = args.gdrive_dir
    else:
        gdrive_dir = "/Users/saggese/GoogleDrive/pdf_notes"
    # Copy.
    hdbg.dassert_dir_exists(gdrive_dir)
    _LOG.debug("gdrive_dir=%s", gdrive_dir)
    basename = os.path.basename(args.input).replace(".txt", "." + ext)
    _LOG.debug("basename=%s", basename)
    dst_file = os.path.join(gdrive_dir, basename)
    cmd = rf"\cp -af {file_name} {dst_file}"
    _ = _system(cmd)
    _LOG.debug("Saved file='%s' to gdrive", dst_file)


def _cleanup_after(prefix: str) -> None:
    _LOG.info("\n%s", hprint.frame("Clean up after", char1="<", char2=">"))
    cmd = f"rm -rf {prefix}*"
    _ = _system(cmd)


# #############################################################################


def _run_all(args: argparse.Namespace) -> None:
    #
    _LOG.info("type=%s", args.type)
    # Print actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    add_frame = True
    actions_as_str = hparser.actions_to_string(actions, _VALID_ACTIONS, add_frame)
    _LOG.info("\n%s", actions_as_str)
    #
    curr_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    _LOG.debug("curr_path=%s", curr_path)
    #
    if args.script:
        _LOG.info("Logging the actions into a script")
        global _SCRIPT
        _SCRIPT = ["#/bin/bash -xe"]
    #
    file_ = args.input
    hdbg.dassert_path_exists(file_)
    prefix = args.tmp_dir + "/tmp.pandoc"
    prefix = os.path.abspath(prefix)
    # - Cleanup_before
    action = "cleanup_before"
    to_execute, actions = hparser.mark_action(action, actions)
    if to_execute:
        _cleanup_before(prefix)
    # - Filter
    if args.filter_by_header:
        file_ = _filter_by_header(file_, args.filter_by_header, prefix)
    # - Preprocess_notes
    action = "preprocess_notes"
    to_execute, actions = hparser.mark_action(action, actions)
    if to_execute:
        file_ = _preprocess_notes(curr_path, file_, prefix)
    # - Run_pandoc
    action = "run_pandoc"
    to_execute, actions = hparser.mark_action(action, actions)
    if to_execute:
        if args.type == "pdf":
            file_out = _run_pandoc_to_pdf(args, curr_path, file_, prefix)
        elif args.type == "html":
            file_out = _run_pandoc_to_html(args, file_, prefix)
        elif args.type == "slides":
            file_out = _run_pandoc_to_slides(args, file_)
        else:
            raise ValueError(f"Invalid type='{args.type}'")
    file_in = file_out
    file_final = _copy_to_output(args, file_in, prefix)
    # - Copy_to_gdrive
    action = "copy_to_gdrive"
    to_execute, actions = hparser.mark_action(action, actions)
    if to_execute:
        ext = args.type
        _copy_to_gdrive(args, file_final, ext)
    # - Open
    action = "open"
    to_execute, actions = hparser.mark_action(action, actions)
    if to_execute:
        hopen.open_file(file_final)
    # - Cleanup_after
    action = "cleanup_after"
    to_execute, actions = hparser.mark_action(action, actions)
    if to_execute:
        _cleanup_after(prefix)
    # Save script, if needed.
    if args.script:
        txt = "\n".join(_SCRIPT)
        hio.to_file(args.script, txt)
        _LOG.info("Saved script into '%s'", args.script)
    # Check that everything was executed.
    if actions:
        _LOG.error("actions=%s were not processed", str(actions))
    _LOG.info("\n%s", hprint.frame("SUCCESS"))


# #############################################################################

_VALID_ACTIONS = [
    "cleanup_before",
    "preprocess_notes",
    "run_pandoc",
    "copy_to_gdrive",
    "open",
    "cleanup_after",
]


_DEFAULT_ACTIONS = _VALID_ACTIONS[:]


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-i", "--input", action="store", type=str, required=True)
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        type=str,
        default=None,
        help="Output file",
    )
    parser.add_argument(
        "--tmp_dir",
        action="store",
        type=str,
        default=".",
        help="Directory where to save artifacts",
    )
    parser.add_argument(
        "-t",
        "--type",
        required=True,
        choices=["pdf", "html", "slides"],
        action="store",
        help="Type of output to generate",
    )
    parser.add_argument(
        "-f", "--filter_by_header", action="store", help="Filter by header"
    )
    parser.add_argument(
        "-n",
        "--filter_by_lines",
        action="store",
        help="Filter by lines (e.g., `1-10`)",
    )
    parser.add_argument(
        "--script", action="store", help="Bash script to generate"
    )
    parser.add_argument("--no_toc", action="store_true", default=False)
    parser.add_argument(
        "--no_run_latex_again", action="store_true", default=False
    )
    parser.add_argument(
        "--gdrive_dir",
        action="store",
        default=None,
        help="Directory where to save the output",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    cmd_line = " ".join(map(str, sys.argv))
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("cmd line=%s", cmd_line)
    _run_all(args)


if __name__ == "__main__":
    _main(_parse())
