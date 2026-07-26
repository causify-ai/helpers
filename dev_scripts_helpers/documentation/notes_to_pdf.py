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
    -t pdf \
    --no_cleanup --no_cleanup_before --no_run_latex_again --no_open
"""

import argparse
import logging
import os
import sys
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hopen as hopen
import helpers.hdocker as hdocker
import helpers.hparser as hparser
import helpers.hselect_action as hselacti
import helpers.hprint as hprint
import dev_scripts_helpers.documentation.lib_notes_to_pdf as dshdlntpd

_LOG = logging.getLogger(__name__)

# #############################################################################

_VALID_ACTIONS = [
    "cleanup_before",
    "preprocess_notes",
    "render_images",
    "run_pandoc",
    "compress_pdf",
    "copy_to_gdrive",
    "open",
    "cleanup_after",
]


_DEFAULT_ACTIONS = [
    # "cleanup_before",
    "preprocess_notes",
    "render_images",
    "run_pandoc",
    # "compress_pdf",
    "open",
    # "cleanup_after",
]


# #############################################################################


def _run_all(args: argparse.Namespace) -> None:
    _LOG.debug("type=%s", args.type)
    # Print actions.
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    add_frame = True
    actions_as_str = hselacti.actions_to_string(
        actions, _VALID_ACTIONS, add_frame
    )
    _LOG.info("\n%s", actions_as_str)
    if args.preview_actions:
        return
    # E.g., curr_path='/app/helpers_root/dev_scripts_helpers/documentation'
    curr_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    _LOG.debug("curr_path=%s", curr_path)
    #
    if args.script:
        _LOG.info("Logging the actions into a script")
        dshdlntpd._append_script("#!/bin/bash -xe")
    #
    file_name = args.input
    hdbg.dassert_path_exists(file_name)
    # E.g., prefix='/app/helpers_root/tmp.notes_to_pdf'
    out_dir = os.path.abspath(os.path.dirname(args.output))
    hio.create_dir(out_dir, incremental=True)
    prefix = os.path.join(out_dir, "tmp.notes_to_pdf")
    _LOG.debug("prefix=%s", prefix)
    # - Cleanup_before
    action = "cleanup_before"
    to_execute, actions = dshdlntpd._mark_action(action, actions)
    if to_execute:
        dshdlntpd._cleanup_before(prefix)
    # - Filter
    hdbg.dassert_lte(
        int(args.filter_by_header is not None)
        + int(args.filter_by_lines is not None)
        + int(args.filter_by_slides is not None)
        + int(args.filter_by_name is not None),
        1,
        "You can specify at most one between --filter_by_header, --filter_by_lines, --filter_by_slides, --filter_by_name",
    )
    if (
        args.filter_by_header
        or args.filter_by_lines
        or args.filter_by_slides
        or args.filter_by_name
    ):
        text = hio.from_file(file_name)
        text = text.split("\n")
        filtered_text: List[str] = []
        if args.filter_by_header:
            filtered_text = hmarkdo.filter_by_header(text, args.filter_by_header)
            file_name = f"{prefix}.filter_by_header.txt"
        if args.filter_by_lines:
            filtered_text = hmarkdo.filter_by_lines(text, args.filter_by_lines)
            file_name = f"{prefix}.filter_by_lines.txt"
        if args.filter_by_slides:
            filtered_text = hmarkdo.filter_by_slides(text, args.filter_by_slides)
            file_name = f"{prefix}.filter_by_slides.txt"
        if args.filter_by_name:
            filtered_text = hmarkdo.filter_by_name(
                text, args.filter_by_name, num_slides=args.num_slides
            )
            file_name = f"{prefix}.filter_by_name.txt"
        filtered_text_str = "\n".join(filtered_text)
        hio.to_file(file_name, filtered_text_str)
    # - Preprocess_notes
    action = "preprocess_notes"
    to_execute, actions = dshdlntpd._mark_action(action, actions)
    if to_execute:
        file_name = dshdlntpd._preprocess_notes(
            file_name, prefix, args.type, args.toc_type
        )
    # - Render_images
    action = "render_images"
    to_execute, actions = dshdlntpd._mark_action(action, actions)
    if to_execute:
        file_name = dshdlntpd._render_images(file_name, prefix)
    # - Run_pandoc
    action = "run_pandoc"
    to_execute, actions = dshdlntpd._mark_action(action, actions)
    file_out = file_name
    if to_execute:
        if args.type == "pdf":
            file_out = dshdlntpd._run_pandoc_to_pdf(
                curr_path,
                file_name,
                prefix,
                args.toc_type,
                args.no_run_latex_again,
                args.use_host_tools,
                args.dockerized_force_rebuild,
                args.dockerized_use_sudo,
                tex_only=args.tex_only,
            )
        elif args.type == "html":
            file_out = dshdlntpd._run_pandoc_to_html(
                file_name,
                prefix,
                args.toc_type,
            )
        elif args.type == "slides":
            if args.slides_engine == "typst":
                file_out = dshdlntpd._run_pandoc_to_typst_slides(
                    curr_path,
                    file_name,
                    args.use_host_tools,
                    args.dockerized_force_rebuild,
                    args.dockerized_use_sudo,
                    typst_only=args.tex_only,
                )
            else:
                file_out = dshdlntpd._run_pandoc_to_slides(
                    file_name,
                    args.toc_type,
                    args.use_host_tools,
                    args.dockerized_force_rebuild,
                    args.dockerized_use_sudo,
                    debug=args.debug_on_error,
                    tex_only=args.tex_only,
                )
        else:
            raise ValueError(f"Invalid type='{args.type}'")
    file_in = file_out
    # - Compress_pdf
    action = "compress_pdf"
    to_execute, actions = dshdlntpd._mark_action(action, actions)
    if to_execute:
        if args.type == "pdf":
            file_in = dshdlntpd._compress_pdf(file_in)
        else:
            _LOG.warning("Compression is only supported for PDF files")
    file_final = dshdlntpd._copy_to_output(file_in, args.output)
    # - Copy_to_gdrive
    action = "copy_to_gdrive"
    to_execute, actions = dshdlntpd._mark_action(action, actions)
    if to_execute:
        ext = args.type
        dshdlntpd._copy_to_gdrive(file_final, ext, args.input, args.gdrive_dir)
    # - Open
    action = "open"
    to_execute, actions = dshdlntpd._mark_action(action, actions)
    if to_execute:
        hopen.open_file(file_final)
    # - Cleanup_after
    action = "cleanup_after"
    to_execute, actions = dshdlntpd._mark_action(action, actions)
    if to_execute:
        dshdlntpd._cleanup_after(prefix)
    # Save script, if needed.
    if args.script:
        txt = "\n".join(dshdlntpd._SCRIPT)
        hio.to_file(args.script, txt)
        _LOG.info("Saved script into '%s'", args.script)
    # Check that everything was executed.
    if actions:
        _LOG.error("actions=%s were not processed", str(actions))
    _LOG.info("\n%s", hprint.frame("SUCCESS"))


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--input", action="store", type=str, required=True)
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        type=str,
        required=True,
        help="Output file",
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["pdf", "html", "slides"],
        action="store",
        help="Type of output to generate",
    )
    parser.add_argument(
        "--filter_by_header", action="store", help="Filter by header"
    )
    parser.add_argument(
        "--filter_by_lines",
        action="store",
        help="Filter by lines (e.g., `0:10`, `1:None`, `None:10`)",
    )
    parser.add_argument(
        "--filter_by_slides",
        action="store",
        help="Filter by slides (e.g., `0:10`, `1:None`, `None:10`)",
    )
    parser.add_argument(
        "--filter_by_name",
        action="store",
        help="Filter by slide name (partial match, case-sensitive)",
    )
    parser.add_argument(
        "--num_slides",
        action="store",
        type=int,
        default=5,
        help="Number of slides to keep when using --filter_by_name (default: 5)",
    )
    # TODO(gp): -> out_action_script
    parser.add_argument(
        "--script",
        action="store",
        default="tmp.notes_to_pdf.sh",
        help="Bash script to generate with all the executed sub-commands",
    )
    parser.add_argument(
        "--preview_actions",
        action="store_true",
        default=False,
        help="Print the actions and exit",
    )
    parser.add_argument(
        "--toc_type",
        action="store",
        default="none",
        choices=["none", "pandoc_native", "navigation", "remove_headers"],
        help=(
            "Type of table of contents to generate: "
            "'none': no TOC; "
            "'pandoc_native': use pandoc's native --toc option (depth 2); "
            "'navigation': add custom navigation slides for headers (levels 1-3); "
            "'remove_headers': remove headers smaller than level 3"
        ),
    )
    parser.add_argument(
        "--slides_engine",
        action="store",
        default="beamer",
        choices=["beamer", "typst"],
        help=(
            "Engine used to render slides (only for `--type slides`): "
            "'beamer': pandoc -> LaTeX/beamer -> pdflatex (default); "
            "'typst': pandoc -> Typst/Touying -> typst compile"
        ),
    )
    parser.add_argument(
        "--no_run_latex_again", action="store_true", default=False
    )
    parser.add_argument(
        "--tex_only",
        action="store_true",
        default=False,
        help=(
            "Generate only the intermediate source file (`.tex` for beamer, "
            "`.typ` for typst) without compiling to PDF"
        ),
    )
    parser.add_argument("--debug_on_error", action="store_true", default=False)
    parser.add_argument(
        "--gdrive_dir",
        action="store",
        default="",
        help="Directory where to save the output to share on Google Drive",
    )
    parser.add_argument(
        "--use_host_tools",
        action="store_true",
        default=False,
        help="Use the host tools instead of the dockerized ones",
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hdocker.add_dockerized_script_arg(parser)
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
