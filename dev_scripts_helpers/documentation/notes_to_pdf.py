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
import re
import sys
from typing import Any, List, Optional, Tuple, cast

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hopen as hopen
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################

_SCRIPT: Optional[List[str]] = None


def _append_script(msg: str) -> None:
    if _SCRIPT is not None:
        _SCRIPT.append(msg)


def _report_phase(phase: str) -> None:
    msg = "# " + phase
    print(hprint.color_highlight(msg, "blue"))
    _LOG.debug("\n%s", hprint.frame(phase, char1="<", char2=">"))
    _append_script(msg)


def _log_system(cmd: str) -> None:
    print("> " + cmd)
    _append_script(cmd)


def _system(cmd: str, *, log_level: int = logging.DEBUG, **kwargs: Any) -> int:
    _log_system(cmd)
    rc = hsystem.system(cmd, log_level=log_level, suppress_output=False, **kwargs)
    return rc  # type: ignore


def _system_to_string(
    cmd: str, *, log_level: int = logging.DEBUG, **kwargs: Any
) -> Tuple[int, str]:
    _log_system(cmd)
    rc, txt = hsystem.system_to_string(cmd, log_level=log_level, **kwargs)
    return rc, txt


def _mark_action(action: str, actions: List[str]) -> Tuple[bool, List[str]]:
    _report_phase(action)
    to_execute, actions = hparser.mark_action(action, actions)
    if not to_execute:
        _append_script("## skipping this action")
    return to_execute, actions


# #############################################################################


def _cleanup_before(prefix: str) -> None:
    """
    Remove all intermediate files.

    :param prefix: The prefix used to identify the files to be removed.
    """
    cmd = f"rm -rf {prefix}*"
    _ = _system(cmd)


# #############################################################################


def _filter_by_header(file_name: str, header: str, prefix: str) -> str:
    """
    Extract a specific header from a file.

    :param file_name: The input file to be processed
    :param header: The header to filter by (e.g., `# Introduction`)
    :param prefix: The prefix used for the output file (e.g., `tmp.pandoc`)
    :return: The path to the processed file
    """
    # Read the file.
    txt = hio.from_file(file_name)
    # Filter by header.
    txt = hmarkdo.extract_section_from_markdown(txt, header)
    # Save the file.
    file_out = f"{prefix}.filter_by_header.txt"
    hio.to_file(file_out, txt)
    return file_out


def _filter_by_lines(file_name: str, filter_by_lines: str, prefix: str) -> str:
    """
    Filter the lines of a file in [start_line, end_line[.

    :param file_name: The input file to be processed
    :param filter_by_lines: a string like `1:10` or `1:None` or `None:10`
    :param prefix: The prefix used for the output file (e.g., `tmp.pandoc`)
    :return: The path to the processed file
    """
    # Read the file.
    txt = hio.from_file(file_name)
    txt = txt.split("\n")
    # E.g., filter_by_lines='1:10'.
    m = re.match(r"^(\S+):(\S+)$", filter_by_lines)
    hdbg.dassert(m, "Invalid filter_by_lines='%s'", filter_by_lines)
    start_line, end_line = m.group(1), m.group(2)
    if start_line.lower() == "none":
        start_line = 1
    else:
        start_line = int(start_line)
    if end_line.lower() == "none":
        end_line = len(txt) + 1
    else:
        end_line = int(end_line)
    # Filter by header.
    hdbg.dassert_lte(start_line, end_line)
    txt = txt[start_line - 1 : end_line - 1]
    txt = "\n".join(txt)
    #
    file_out = f"{prefix}.filter_by_lines.txt"
    hio.to_file(file_out, txt)
    return file_out


# #############################################################################


def _preprocess_notes(
    file_name: str, prefix: str, type_: str, toc_type: str
) -> str:
    """
    Pre-process the file.

    :param file_name: The input file to be processed
    :param prefix: The prefix used for the output file (e.g., `tmp.pandoc`)
    :return: The path to the processed file
    """
    exec_file = hgit.find_file("preprocess_notes.py")
    file1 = file_name
    file2 = f"{prefix}.preprocess_notes.txt"
    cmd = (
        f"{exec_file} --input {file1} --output {file2}"
        + f" --type {type_} --toc_type {toc_type}"
    )
    _ = _system(cmd)
    file_name = file2
    return file_name


# #############################################################################


def _render_images(file_name: str, prefix: str) -> str:
    """
    Render images in the file.

    :param file_name: The input file to be processed
    :param prefix: The prefix used for the output file (e.g., `tmp.pandoc`)
    :return: The path to the processed file
    """
    # helpers_root/./dev_scripts_helpers/documentation/render_images.py
    exec_file = hgit.find_file("render_images.py")
    file1 = file_name
    file2 = f"{prefix}.render_image.txt"
    cmd = f"{exec_file} --in_file_name {file1} --out_file_name {file2}"
    _ = _system(cmd)
    # Remove the commented code introduced by `render_image.py`.
    txt = hio.from_file(file2)
    out = []
    for i, line in enumerate(txt.split("\n")):
        _LOG.debug("%s:line=%s", i, line)
        do_continue = hmarkdo.process_single_line_comment(line)
        if do_continue:
            continue
        out.append(line)
    out = "\n".join(out)
    file3 = f"{prefix}.render_image2.txt"
    hio.to_file(file3, out)
    #
    file_out = file3
    return file_out


# #############################################################################


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
    curr_path: str,
    file_name: str,
    prefix: str,
    toc_type: str,
    no_run_latex_again: bool,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
) -> str:
    """
    Convert the input file to PDF using Pandoc.

    :param curr_path: The current path where the script is located.
        E.g., '/app/helpers_root/dev_scripts_helpers/documentation'
        This is used to reference files with respect to the script location
        (e.g., `pandoc.latex`)
    :param file_name: The input file to be converted
        E.g., '/app/helpers_root/tmp.notes_to_pdf.render_image2.txt'
    :param prefix: The prefix used for the output file
        E.g., '/app/helpers_root/tmp.notes_to_pdf'
    :return: The path to the generated PDF file
    """
    _LOG.debug(hprint.func_signature_to_str())
    file1 = file_name
    # - Run pandoc.
    cmd = []
    cmd.append(f"pandoc {file1}")
    cmd.extend(_COMMON_PANDOC_OPTS[:])
    #
    cmd.append("-t latex")
    #
    template = f"{curr_path}/pandoc.latex"
    hdbg.dassert_path_exists(template)
    cmd.append(f"--template {template}")
    #
    file2 = f"{prefix}.tex"
    cmd.append(f"-o {file2}")
    #
    if toc_type == "pandoc_native":
        cmd.append("--toc")
        cmd.append("--toc-depth 2")
    else:
        no_run_latex_again = True
    # Doesn't work
    # -f markdown+raw_tex
    cmd = " ".join(cmd)
    _LOG.debug("%s", "before: " + hprint.to_str("cmd"))
    if not use_host_tools:
        container_type = "pandoc_texlive"
        cmd = hdocker.run_dockerized_pandoc(
            cmd,
            container_type,
            return_cmd=True,
            force_rebuild=dockerized_force_rebuild,
            use_sudo=dockerized_use_sudo,
        )
    _LOG.debug("%s", "after: " + hprint.to_str("cmd"))
    _ = _system(cmd, suppress_output=False)
    file_name = file2
    # - Run latex.
    _report_phase("latex")
    # pdflatex needs to run in the same dir of latex_abbrevs.sty so we copy
    # all the needed files.
    out_dir = os.path.dirname(file_name)
    latex_file = os.path.join(
        hgit.find_file("dev_scripts_helpers"),
        "documentation",
        "latex_abbrevs.sty",
    )
    hdbg.dassert_file_exists(latex_file)
    cmd = f"cp -f {latex_file} ."
    _ = _system(cmd)
    #
    cmd = ""
    # There is a horrible bug in pdflatex that if the input file is not the last
    # one the output directory is not recognized.
    cmd += (
        "pdflatex"
        + f" -output-directory {out_dir}"
        + " -interaction=nonstopmode"
        + " -halt-on-error"
        + " -shell-escape"
        + f" {file_name}"
    )
    _LOG.debug("%s", "before: " + hprint.to_str("cmd"))
    if not use_host_tools:
        cmd = hdocker.run_dockerized_latex(cmd, return_cmd=True, use_sudo=False)
    _LOG.debug("%s", "after: " + hprint.to_str("cmd"))
    _ = _system(cmd, suppress_output=False)
    # - Run latex again.
    _report_phase("latex again")
    if not no_run_latex_again:
        _ = _system(cmd, suppress_output=False)
    else:
        _LOG.warning("Skipping: run latex again")
    # Remove `latex_abbrevs.sty`.
    os.remove("latex_abbrevs.sty")
    # Get the path of the output file created by Latex.
    file_out = os.path.basename(file_name).replace(".tex", ".pdf")
    file_out = os.path.join(out_dir, file_out)
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    return file_out


def _run_pandoc_to_html(
    file_in: str,
    prefix: str,
    toc_type: str,
) -> str:
    """
    Convert the input file to HTML using Pandoc.

    :param file_in: The input file to be converted
    :param prefix: The prefix used for the output file
    :return: The path to the generated HTML file
    """
    cmd = []
    cmd.append(f"pandoc {file_in}")
    cmd.extend(_COMMON_PANDOC_OPTS[:])
    cmd.append("-t html")
    cmd.append(f"--metadata pagetitle='{os.path.basename(file_in)}'")
    #
    file2 = f"{prefix}.html"
    cmd.append(f"-o {file2}")
    if toc_type == "pandoc_native":
        cmd.append("--toc")
        cmd.append("--toc-depth 2")
    cmd = " ".join(cmd)
    _ = _system(cmd, suppress_output=False)
    #
    file_out = os.path.abspath(file2.replace(".tex", ".html"))
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    return file_out


def _build_pandoc_cmd(
    file_name: str,
    toc_type: str,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    use_tex: bool = False,
) -> Tuple[str, str]:
    cmd = []
    cmd.append(f"pandoc {file_name}")
    #
    cmd.append("-t beamer")
    cmd.append("--slide-level 4")
    cmd.append("-V theme:SimplePlus")
    cmd.append("--include-in-header=latex_abbrevs.sty")
    # cmd.append("--pdf-engine=lualatex")
    # cmd.append("--pdf-engine=xelatex")
    if toc_type == "pandoc_native":
        cmd.append("--toc")
        cmd.append("--toc-depth 2")
    if use_tex:
        ext = ".tex"
    else:
        ext = ".pdf"
    file_out = file_name.replace(".txt", ext)
    cmd.append(f"-o {file_out}")
    #
    cmd = " ".join(cmd)
    _LOG.debug("%s", "before: " + hprint.to_str("cmd"))
    if not use_host_tools:
        container_type = "pandoc_texlive"
        cmd = hdocker.run_dockerized_pandoc(
            cmd,
            container_type,
            return_cmd=True,
            force_rebuild=dockerized_force_rebuild,
            use_sudo=dockerized_use_sudo,
        )
    _LOG.debug("%s", "after: " + hprint.to_str("cmd"))
    return cmd, file_out


def _run_pandoc_to_slides(
    file_name: str,
    toc_type: str,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    debug: bool = False,
) -> str:
    """
    Convert the input file to PDF slides using Pandoc.

    :param file_name: The input file to be converted
    :return: The path to the generated PDF file
    """
    cmd, file_out = _build_pandoc_cmd(
        file_name,
        toc_type,
        use_host_tools,
        dockerized_force_rebuild,
        dockerized_use_sudo,
    )
    rc, txt = _system_to_string(cmd, abort_on_error=False)
    # We want to print to screen.
    print(txt)
    # rc = _system(cmd, suppress_output=False)
    if rc != 0:
        _LOG.error("Log is in %s", file_out + ".log")
        if debug:
            _LOG.error("Pandoc failed")
            # Generate the tex version of the file.
            cmd, file_out = _build_pandoc_cmd(
                file_name,
                toc_type,
                use_host_tools,
                dockerized_force_rebuild,
                dockerized_use_sudo,
                use_tex=True,
            )

            _system(cmd, abort_on_error=False)
            # Error producing PDF.
            # ! Package enumitem Error: 1) undefined.

            # See the enumitem package documentation for explanation.
            # Type  H <return>  for immediate help.
            #  ...

            # l.979 \end{frame}
            for line in txt.split("\n"):
                _LOG.debug("line=%s", line)
                m = re.match(r"^l\.(\d+)", line)
                if m:
                    line_num = int(m.group(1))
                    cmd = f"vim {file_out} +{line_num}"
                    print(hprint.frame(cmd))
        raise RuntimeError("Pandoc failed")
    #
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    return file_out


# #############################################################################


def _copy_to_output(file_in: str, output: str) -> str:
    """
    Copy the processed file to the output location.

    :param file_in: The input file to be copied
    :param prefix: The prefix used for the output file
    :return: The path to the copied output file
    """
    hdbg.dassert_is_not(output, None)
    file_out = output
    _LOG.debug("file_out=%s", file_out)
    cmd = rf"\cp -af {file_in} {file_out}"
    _ = _system(cmd)
    return file_out


def _copy_to_gdrive(
    file_name: str, ext: str, input_: str, gdrive_dir: str
) -> None:
    """
    Copy the processed file to Google Drive.

    :param file_name: The name of the file to be copied
    :param ext: The extension of the file to be copied
    """
    hdbg.dassert(not ext.startswith("."), "Invalid file_name='%s'", file_name)
    if gdrive_dir is None:
        gdrive_dir = "/Users/saggese/GoogleDrive/pdf_notes"
    # Copy.
    hdbg.dassert_dir_exists(gdrive_dir)
    _LOG.debug("gdrive_dir=%s", gdrive_dir)
    basename = os.path.basename(input_).replace(".txt", "." + ext)
    _LOG.debug("basename=%s", basename)
    dst_file = os.path.join(gdrive_dir, basename)
    cmd = rf"\cp -af {file_name} {dst_file}"
    _ = _system(cmd)
    _LOG.debug("Saved file='%s' to gdrive", dst_file)


# #############################################################################


def _cleanup_after(prefix: str) -> None:
    cmd = f"rm -rf {prefix}*"
    _ = _system(cmd)


# #############################################################################


def _run_all(args: argparse.Namespace) -> None:
    _LOG.debug("type=%s", args.type)
    # Print actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    add_frame = True
    actions_as_str = hparser.actions_to_string(actions, _VALID_ACTIONS, add_frame)
    _LOG.info("\n%s", actions_as_str)
    if args.preview_actions:
        return
    # E.g., curr_path='/app/helpers_root/dev_scripts_helpers/documentation'
    curr_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    _LOG.debug("curr_path=%s", curr_path)
    #
    if args.script:
        _LOG.info("Logging the actions into a script")
        global _SCRIPT
        _SCRIPT = ["#/bin/bash -xe"]
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
    to_execute, actions = _mark_action(action, actions)
    if to_execute:
        _cleanup_before(prefix)
    # - Filter
    if args.filter_by_header:
        file_name = _filter_by_header(file_name, args.filter_by_header, prefix)
    if args.filter_by_lines:
        file_name = _filter_by_lines(file_name, args.filter_by_lines, prefix)
    # E.g., file_='/app/helpers_root/tmp.notes_to_pdf.render_image2.txt'
    # - Preprocess_notes
    action = "preprocess_notes"
    to_execute, actions = _mark_action(action, actions)
    if to_execute:
        file_name = _preprocess_notes(file_name, prefix, args.type, args.toc_type)
    # - Render_images
    action = "render_images"
    to_execute, actions = _mark_action(action, actions)
    if to_execute:
        file_name = _render_images(file_name, prefix)
    # - Run_pandoc
    action = "run_pandoc"
    to_execute, actions = _mark_action(action, actions)
    if to_execute:
        if args.type == "pdf":
            file_out = _run_pandoc_to_pdf(
                curr_path,
                file_name,
                prefix,
                args.toc_type,
                args.no_run_latex_again,
                args.use_host_tools,
                args.dockerized_force_rebuild,
                args.dockerized_use_sudo,
            )
        elif args.type == "html":
            file_out = _run_pandoc_to_html(
                file_name,
                prefix,
                args.toc_type,
            )
        elif args.type == "slides":
            file_out = _run_pandoc_to_slides(
                file_name,
                args.toc_type,
                args.use_host_tools,
                args.dockerized_force_rebuild,
                args.dockerized_use_sudo,
                debug=args.debug_on_error,
            )
        else:
            raise ValueError(f"Invalid type='{args.type}'")
    file_in = file_out  # pylint: disable=possibly-used-before-assignment
    file_final = _copy_to_output(file_in, args.output)
    # - Copy_to_gdrive
    action = "copy_to_gdrive"
    to_execute, actions = _mark_action(action, actions)
    if to_execute:
        ext = args.type
        _copy_to_gdrive(file_final, ext, args.input, args.gdrive_dir)
    # - Open
    action = "open"
    to_execute, actions = _mark_action(action, actions)
    if to_execute:
        hopen.open_file(file_final)
    # - Cleanup_after
    action = "cleanup_after"
    to_execute, actions = _mark_action(action, actions)
    if to_execute:
        _cleanup_after(prefix)
    # Save script, if needed.
    if args.script:
        hdbg.dassert_is_not(_SCRIPT, None)
        _SCRIPT = cast(List[str], _SCRIPT)
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
    "render_images",
    "run_pandoc",
    "copy_to_gdrive",
    "open",
    "cleanup_after",
]


_DEFAULT_ACTIONS = [
    "cleanup_before",
    "preprocess_notes",
    "render_images",
    "run_pandoc",
    "open",
    "cleanup_after",
]


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
        choices=["none", "pandoc_native", "navigation"],
    )
    parser.add_argument(
        "--no_run_latex_again", action="store_true", default=False
    )
    parser.add_argument("--debug_on_error", action="store_true", default=False)
    parser.add_argument(
        "--gdrive_dir",
        action="store",
        default=None,
        help="Directory where to save the output to share on Google Drive",
    )
    parser.add_argument(
        "--use_host_tools",
        action="store_true",
        default=False,
        help="Use the host tools instead of the dockerized ones",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_dockerized_script_arg(parser)
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
