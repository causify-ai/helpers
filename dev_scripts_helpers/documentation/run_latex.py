#!/usr/bin/env python

"""
Compile a LaTeX file to PDF inside a Docker container.

The script drives `pdflatex` (and, for multi-pass builds, `bibtex`) through
`dev_scripts_helpers/dockerize/lib_latex.py`, so no local LaTeX installation
is required. It also reports any `LaTeX`/`Package`/`Class` warnings found in
the resulting `.log` file, and can copy the PDF to Google Drive and open it
in Skim on macOS.

Usage examples:

# Two-pass build (resolves cross-references), default.
> run_latex.py --input book.tex

# Quick single-pass build.
> run_latex.py --input book.tex --num_passes 1

# Full build with bibliography (two passes, bibtex, two more passes).
> run_latex.py --input book.tex --num_passes 3

# Build, copy to Google Drive, and open the PDF in Skim.
> run_latex.py --input book.tex --open

Import as:

import dev_scripts_helpers.documentation.run_latex as dshdrula
"""

import argparse
import glob
import logging
import os
import re
import shutil
from typing import List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_latex as dshdlila

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

# Google Drive folders that `run_latex.sh` copies the resulting PDF to, if
# they are mounted on the host.
_GDRIVE_PAPERS_DIR = (
    "/Users/saggese/Library/CloudStorage/GoogleDrive-gp@causify.ai/"
    "Shared drives/Eng - External (GP)/Papers"
)
_GDRIVE_INTERNAL_DIR = (
    "/Users/saggese/Library/CloudStorage/GoogleDrive-gp@causify.ai/"
    "Shared drives/Eng - External (GP)/Internal_Papers_Latest"
)

# Matches the LaTeX log warning lines that `run_latex.sh` greps for.
_WARNING_REGEX = re.compile(
    r"^(LaTeX Warning:|Package .* Warning:|Class .* Warning:)"
)


# #############################################################################
# Post-build helpers
# #############################################################################


def _report_log_warnings(log_file_path: str) -> List[str]:
    """
    Log any `LaTeX`/`Package`/`Class` warnings found in a `pdflatex` log.

    :param log_file_path: path to the `.log` file produced by `pdflatex`
    :return: list of matched warning lines
    """
    _LOG.debug(hprint.to_str("log_file_path"))
    if not os.path.exists(log_file_path):
        _LOG.warning(
            "Log file '%s' not found; skipping warning check", log_file_path
        )
        return []
    lines = hio.from_file(log_file_path).splitlines()
    warnings = [line for line in lines if _WARNING_REGEX.match(line)]
    for warning in warnings:
        _LOG.warning("%s", warning)
    return warnings


def _copy_to_google_drive(out_file_path: str) -> None:
    """
    Copy the compiled PDF to the Google Drive folders used for `run_latex.sh`.

    Mirrors the shell script's behavior: copy only into folders that are
    actually mounted on the host, warning and skipping otherwise.

    :param out_file_path: path to the compiled PDF to copy
    """
    for gdrive_dir in (_GDRIVE_PAPERS_DIR, _GDRIVE_INTERNAL_DIR):
        if os.path.isdir(gdrive_dir):
            _LOG.info("Copying '%s' to '%s'", out_file_path, gdrive_dir)
            shutil.copy2(out_file_path, gdrive_dir)
        else:
            _LOG.warning(
                "Google Drive folder '%s' not found, skipping copy", gdrive_dir
            )


# #############################################################################
# Compilation
# #############################################################################


def _compile_latex(
    in_file_path: str,
    out_file_path: str,
    num_passes: int,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Compile a `.tex` file to PDF with the requested number of `pdflatex` passes.

    - 1: single `pdflatex` pass (quick, no cross-references resolved)
    - 2: two `pdflatex` passes (resolves cross-references, no bibliography)
    - 3: two `pdflatex` passes + `bibtex` + two more `pdflatex` passes (full
      build with bibliography and cross-references), only if a `.bib` file
      is present next to the input

    :param in_file_path: path to the `.tex` file to compile
    :param out_file_path: path to the resulting PDF
    :param num_passes: number of `pdflatex` compilation passes (1, 2, or 3)
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(hprint.func_signature_to_str())
    in_dir_name = os.path.dirname(os.path.abspath(in_file_path))
    base_name = os.path.splitext(os.path.basename(in_file_path))[0]
    # `run_basic_latex()` hardwires `pdflatex -output-directory=.`, which
    # resolves relative to the *host* process's cwd, so it must match the
    # `.tex` file's directory for the compiled artifacts (`.aux`, `.log`, ...)
    # to land next to the source file.
    os.chdir(in_dir_name)
    cmd_opts: List[str] = []
    # First 1 or 2 passes.
    run_latex_again = num_passes >= 2
    dshdlila.run_basic_latex(
        in_file_path,
        cmd_opts,
        run_latex_again,
        out_file_path,
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
    )
    if num_passes >= 3:
        # Only run `bibtex` (and the extra passes it requires) if there is a
        # bibliography to process.
        bib_files = glob.glob(os.path.join(in_dir_name, "*.bib"))
        if bib_files:
            aux_file_path = os.path.join(in_dir_name, f"{base_name}.aux")
            dshdlila.run_dockerized_bibtex(
                aux_file_path,
                force_rebuild=force_rebuild,
                use_sudo=use_sudo,
            )
            run_latex_again = True
            dshdlila.run_basic_latex(
                in_file_path,
                cmd_opts,
                run_latex_again,
                out_file_path,
                force_rebuild=force_rebuild,
                use_sudo=use_sudo,
            )
        else:
            _LOG.warning(
                "No `.bib` file found in '%s', skipping bibtex pass",
                in_dir_name,
            )
    # Report any LaTeX warnings from the final compilation log.
    log_file_path = os.path.join(in_dir_name, f"{base_name}.log")
    _report_log_warnings(log_file_path)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        action="store",
        required=True,
        help="LaTeX file to compile",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        default="",
        help="Output PDF file (default: input file with a `.pdf` extension)",
    )
    parser.add_argument(
        "--num_passes",
        type=int,
        default=2,
        choices=[1, 2, 3],
        help=(
            "Number of `pdflatex` compilation passes: 1 (quick), "
            "2 (resolve cross-references), 3 (full build with bibliography)"
        ),
    )
    parser.add_argument(
        "--copy_to_gdrive",
        action="store_true",
        default=False,
        help=(
            "Copy the resulting PDF to the Google Drive folders used for "
            "`run_latex.sh`"
        ),
    )
    hdocker.add_dockerized_script_arg(parser)
    dshddout.add_open_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    in_file_path = os.path.abspath(args.input)
    hdbg.dassert_file_extension(in_file_path, "tex")
    out_file_path = args.output
    if out_file_path == "":
        out_file_path = hio.change_filename_extension(in_file_path, "tex", "pdf")
    out_file_path = os.path.abspath(out_file_path)
    # Compile.
    _compile_latex(
        in_file_path,
        out_file_path,
        args.num_passes,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", out_file_path)
    if args.copy_to_gdrive:
        _copy_to_google_drive(out_file_path)
    if args.open:
        dshddout.open_file_on_macos(out_file_path)


if __name__ == "__main__":
    _main(_parse())
