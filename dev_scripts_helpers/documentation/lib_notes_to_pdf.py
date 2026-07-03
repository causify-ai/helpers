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

import hashlib
import logging
import os
import re
import time
from typing import Any, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hselect_action as hselacti
import helpers.hsystem as hsystem
import dev_scripts_helpers.dockerize.lib_latex as dshdlila
import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa
import dev_scripts_helpers.dockerize.lib_typst as dshdlity

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
    hdbg.dassert_isinstance(cmd, str)
    print("> " + cmd)
    _append_script(cmd)


def _system(cmd: str, *, log_level: int = logging.DEBUG, **kwargs: Any) -> int:
    _log_system(cmd)
    rc = hsystem.system(
        cmd, log_level=log_level, suppress_output=False, **kwargs
    )
    return rc  # type: ignore


def _system_to_string(
    cmd: str, *, log_level: int = logging.DEBUG, **kwargs: Any
) -> Tuple[int, str]:
    _log_system(cmd)
    rc, txt = hsystem.system_to_string(cmd, log_level=log_level, **kwargs)
    return rc, txt


def _mark_action(
    action: str, actions: Optional[List[str]]
) -> Tuple[bool, Optional[List[str]]]:
    _report_phase(action)
    to_execute, actions = hselacti.mark_action(action, actions)
    if not to_execute:
        _append_script("## skipping this action")
    return to_execute, actions


# #############################################################################
# Daemon Logic
# #############################################################################


def _file_hash(file_path: str) -> str:
    """
    Compute MD5 hash of a file.
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def daemon_watch(
    file_path: str, cmd: str, *, wait_in_sec: int = 1, debounce_sec: int = 2
) -> None:
    """
    Watch a file for changes and re-run command with debouncing.

    Polls the file at regular intervals by computing its MD5 hash. When a
    change is detected, waits for `debounce_sec` seconds with no further
    changes before executing the command. This prevents repeatedly running
    the command while the user is still editing the file.

    :param file_path: Path to file to monitor
    :param cmd: Command to execute when file changes
    :param wait_in_sec: Poll interval in seconds (default: 1)
    :param debounce_sec: Debounce duration in seconds (default: 2)
    """
    _LOG.info(
        "Daemon mode: watching '%s' for changes (poll every 1s, debounce %ds)...",
        file_path,
        debounce_sec,
    )
    hdbg.dassert_file_exists(file_path)

    def _run_cmd() -> None:
        try:
            hsystem.system(cmd)
        except Exception as e:
            _LOG.error("Daemon: command failed: %s", e)

    # Run immediately on first launch.
    _LOG.info("Initial run...")
    _run_cmd()
    prev_hash = _file_hash(file_path)
    stable_hash = None
    time_since_last_change = 0
    while True:
        time.sleep(wait_in_sec)
        cur_hash = _file_hash(file_path)
        if cur_hash != prev_hash:
            # File changed, start debounce.
            _LOG.info(
                "File changed (hash: %s -> %s). Debouncing...",
                prev_hash,
                cur_hash,
            )
            stable_hash = cur_hash
            time_since_last_change = 0
            prev_hash = cur_hash
        elif stable_hash is not None:
            # In debounce period, tracking time without changes.
            time_since_last_change += 1
            if time_since_last_change >= debounce_sec:
                # Debounce complete, regenerate.
                _LOG.info("Debounce complete. Regenerating...")
                _run_cmd()
                stable_hash = None


# #############################################################################


def cleanup_before(prefix: str) -> None:
    """
    Remove all intermediate files and cache files.

    :param prefix: The prefix used to identify the files to be removed.
    """
    cmd = f"rm -rf {prefix}*"
    _ = _system(cmd)
    # Remove cache files that may have been created by render_images.py.
    cmd = "rm -f tmp.cache_simple.*.json tmp.*.pkl"
    _ = _system(cmd)


# #############################################################################


def preprocess_notes(
    file_name: str, prefix: str, type_: str, toc_type: str, output_format: str
) -> str:
    """
    Pre-process the file.

    :param file_name: The input file to be processed
    :param prefix: The prefix used for the output file (e.g., `tmp.pandoc`)
    :param type_: Type of output to generate
    :param toc_type: Type of table of contents to add
    :param output_format: Output format for color commands (latex or typst)
    :return: The path to the processed file
    """
    exec_file = hgit.find_file("preprocess_notes.py")
    file1 = file_name
    file2 = f"{prefix}.preprocess_notes.txt"
    cmd = (
        f"{exec_file} --input {file1} --output {file2}"
        + f" --type {type_} --toc_type {toc_type}"
        + f" --output_format {output_format}"
    )
    _ = _system(cmd)
    file_name = file2
    return file_name


# #############################################################################


def render_images(file_name: str, prefix: str) -> str:
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
    cmd = f"{exec_file} --input {file1} --output {file2} --action render"
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
    _LOG.info("Remove commented code and saved file='%s'", file3)
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
    "--fail-if-warnings",
]
# --filter /Users/$USER/src/github/pandocfilters/examples/tikz.py \
# -F /Users/$USER/src/github/pandocfilters/examples/lilypond.py \
# --filter pandoc-imagine


def _run_pandoc_to_ast(
    file_in: str,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    fail_on_warnings: bool = True,
) -> str:
    """
    Convert markdown to pandoc AST in JSON.

    Example commands run:
    > pandoc input.md -t json --fail-if-warnings -o input.md.ast.json
    > docker run ... pandoc input.md -t json ... -o input.md.ast.json

    :param file_in: Input markdown file
    :param use_host_tools: Use host pandoc instead of dockerized
    :param fail_on_warnings: Fail on pandoc warnings
    :return: Path to generated JSON AST file
    """
    # Build pandoc command for markdown -> JSON AST conversion.
    ast_file = f"{file_in}.ast.json"
    cmd = [f"pandoc {file_in}"]
    cmd.append("-t json")
    if fail_on_warnings:
        cmd.append("--fail-if-warnings")
    cmd.append(f"-o {ast_file}")
    cmd = " ".join(cmd)
    _LOG.debug("%s", "pandoc to AST: " + hprint.to_str("cmd"))
    # Wrap pandoc command in docker if needed, otherwise run natively.
    if not use_host_tools:
        container_type = "pandoc_only"
        cmd = dshdlipa.run_dockerized_pandoc(
            cmd,
            container_type,
            mode="return_cmd",
            force_rebuild=dockerized_force_rebuild,
            use_sudo=dockerized_use_sudo,
        )
    _ = _system(cmd, print_command=True)
    hdbg.dassert_path_exists(ast_file)
    return ast_file


def _run_pandoc_from_ast(
    ast_file: str,
    output_format: str,
    output_file: str,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    extra_opts: Optional[List[str]] = None,
    fail_on_warnings: bool = True,
) -> None:
    """
    Convert pandoc AST in JSON to target format.

    Example commands run:
    > pandoc ast.json -f json -t latex --fail-if-warnings -o output.tex
    > docker run ... pandoc ast.json -f json -t html ... -o output.html

    :param ast_file: Input JSON AST file
    :param output_format: Target format (latex, html, typst, beamer, etc.)
    :param output_file: Output file path
    :param extra_opts: Additional pandoc options to apply
    :param fail_on_warnings: Fail on pandoc warnings
    """
    # Build pandoc command for JSON AST -> target format conversion.
    cmd = [f"pandoc {ast_file}"]
    cmd.append("-f json")
    cmd.append(f"-t {output_format}")
    if fail_on_warnings:
        cmd.append("--fail-if-warnings")
    if extra_opts:
        cmd.extend(extra_opts)
    cmd.append(f"-o {output_file}")
    cmd = " ".join(cmd)
    _LOG.debug("%s", "pandoc from AST: " + hprint.to_str("cmd"))
    # Wrap pandoc command in docker if needed, otherwise run natively.
    if not use_host_tools:
        container_type = "pandoc_only"
        cmd = dshdlipa.run_dockerized_pandoc(
            cmd,
            container_type,
            mode="return_cmd",
            force_rebuild=dockerized_force_rebuild,
            use_sudo=dockerized_use_sudo,
        )
    _ = _system(cmd, print_command=True)
    hdbg.dassert_path_exists(output_file)


def run_pandoc_to_pdf(
    curr_path: str,
    file_name: str,
    prefix: str,
    toc_type: str,
    no_run_latex_again: bool,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    no_pdf: bool = False,
    fail_on_warnings: bool = True,
    use_pandoc_ast_transform: bool = False,
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
    :param no_pdf: If True, return the .tex / .typ file instead of compiling to
        PDF
    :param use_pandoc_ast_transform: If True, use two-stage AST pipeline instead
        of single-shot pandoc
    :return: The path to the generated output file (.tex or .pdf)
    """
    _LOG.debug(hprint.func_signature_to_str())
    file1 = file_name
    file2 = f"{prefix}.tex"
    template = f"{curr_path}/pandoc.latex"
    hdbg.dassert_path_exists(template)
    if use_pandoc_ast_transform:
        # Two-stage pipeline: markdown -> AST -> LaTeX
        _run_pandoc_to_ast(
            file1,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            fail_on_warnings=fail_on_warnings,
        )
        ast_file = f"{file1}.ast.json"
        # Build extra options for LaTeX output (common formatting + LaTeX-specific)
        extra_opts = [
            "-V geometry:margin=1in",
            "--number-sections",
            "--highlight-style=tango",
            "-s",
            f"--template {template}",
        ]
        if toc_type == "pandoc_native":
            extra_opts.extend(["--toc", "--toc-depth 2"])
        else:
            no_run_latex_again = True
        _run_pandoc_from_ast(
            ast_file,
            "latex",
            file2,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            extra_opts=extra_opts,
            fail_on_warnings=fail_on_warnings,
        )
    else:
        # Single-shot pandoc.
        cmd = []
        cmd.append(f"pandoc {file1}")
        common_opts = _COMMON_PANDOC_OPTS[:]
        # Conditionally add --fail-if-warnings
        if not fail_on_warnings and "--fail-if-warnings" in common_opts:
            common_opts.remove("--fail-if-warnings")
        cmd.extend(common_opts)
        cmd.append("-t latex")
        cmd.append(f"--template {template}")
        cmd.append(f"-o {file2}")
        if toc_type == "pandoc_native":
            cmd.append("--toc")
            cmd.append("--toc-depth 2")
        else:
            no_run_latex_again = True
        cmd = " ".join(cmd)
        _LOG.debug("%s", "before: " + hprint.to_str("cmd"))
        if not use_host_tools:
            container_type = "pandoc_texlive"
            cmd = dshdlipa.run_dockerized_pandoc(
                cmd,
                container_type,
                mode="return_cmd",
                force_rebuild=dockerized_force_rebuild,
                use_sudo=dockerized_use_sudo,
            )
        _LOG.debug("%s", "after: " + hprint.to_str("cmd"))
        _ = _system(cmd)
    file_name = file2
    # Return the .tex file if `--no_pdf` mode is requested.
    if no_pdf:
        _LOG.info("no_pdf=True: skipping pdflatex, returning .tex file")
        return file2
    # - Run latex.
    _report_phase("latex")
    # pdflatex needs to run in the same dir of latex_abbrevs.sty so we copy
    # all the needed files.
    out_dir = os.path.dirname(file_name)
    # TODO(ai_gp): Make this more robust by looking for
    # `documentation/latex_abbrevs.sty`.
    latex_file = os.path.join(
        hgit.find_file("dev_scripts_helpers"),
        "documentation",
        "latex_abbrevs.sty",
    )
    hdbg.dassert_file_exists(latex_file)
    # cmd = f"cp -f {latex_file} ."
    cmd = f"cp -f {latex_file} {out_dir}"
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
        cmd = dshdlila.run_dockerized_latex(
            cmd, mode="return_cmd", use_sudo=False
        )
    _LOG.debug("%s", "after: " + hprint.to_str("cmd"))
    _ = _system(cmd)
    # - Run latex again.
    _report_phase("latex again")
    if not no_run_latex_again:
        _ = _system(cmd)
    else:
        _LOG.warning("Skipping: run latex again")
    # Remove `latex_abbrevs.sty`.
    # os.remove("latex_abbrevs.sty")
    # Get the path of the output file created by Latex.
    file_out = os.path.basename(file_name).replace(".tex", ".pdf")
    file_out = os.path.join(out_dir, file_out)
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    return file_out


def run_pandoc_to_html(
    file_in: str,
    prefix: str,
    toc_type: str,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    fail_on_warnings: bool = True,
    use_pandoc_ast_transform: bool = False,
) -> str:
    """
    Convert the input file to HTML using Pandoc.

    :param file_in: The input file to be converted
    :param prefix: The prefix used for the output file
    :param fail_on_warnings: Fail if pandoc emits warnings
    :param use_pandoc_ast_transform: If True, use two-stage AST pipeline instead
        of single-shot pandoc
    :return: The path to the generated HTML file
    """
    file2 = f"{prefix}.html"

    if not use_pandoc_ast_transform:
        # Single-shot pandoc invocation (default)
        cmd = []
        cmd.append(f"pandoc {file_in}")
        common_opts = _COMMON_PANDOC_OPTS[:]
        # Conditionally add --fail-if-warnings
        if not fail_on_warnings and "--fail-if-warnings" in common_opts:
            common_opts.remove("--fail-if-warnings")
        cmd.extend(common_opts)
        cmd.append("-t html")
        cmd.append(f"--metadata pagetitle='{os.path.basename(file_in)}'")
        cmd.append(f"-o {file2}")
        if toc_type == "pandoc_native":
            cmd.append("--toc")
            cmd.append("--toc-depth 2")
        cmd = " ".join(cmd)
        _ = _system(cmd)
    else:
        # Two-stage pipeline: markdown -> AST -> HTML
        _run_pandoc_to_ast(
            file_in,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            fail_on_warnings=fail_on_warnings,
        )
        ast_file = f"{file_in}.ast.json"
        # Build extra options for HTML output (common formatting + HTML-specific)
        extra_opts = [
            "--number-sections",
            "--highlight-style=tango",
            "-s",
            f"--metadata pagetitle='{os.path.basename(file_in)}'",
        ]
        if toc_type == "pandoc_native":
            extra_opts.extend(["--toc", "--toc-depth 2"])
        _run_pandoc_from_ast(
            ast_file,
            "html",
            file2,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            extra_opts=extra_opts,
            fail_on_warnings=fail_on_warnings,
        )

    file_out = os.path.abspath(file2.replace(".tex", ".html"))
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    return file_out


def _build_pandoc_latex_cmd(
    file_name: str,
    toc_type: str,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    no_pdf: bool = False,
    fail_on_warnings: bool = True,
) -> Tuple[str, str]:
    # TODO(ai_gp): Add docstring.
    cmd = []
    cmd.append(f"pandoc {file_name}")
    #
    cmd.append("-t beamer")
    cmd.append("--slide-level 4")
    cmd.append("-V theme:SimplePlus")
    cmd.append("--include-in-header=latex_abbrevs.sty")
    # cmd.append("--pdf-engine=lualatex")
    # cmd.append("--pdf-engine=xelatex")
    if fail_on_warnings:
        cmd.append("--fail-if-warnings")
    # Needed since:
    # ![](tmp.notes_to_pdf.preprocess_notes.txt.figs/tmp.notes_to_pdf.render_image.1.png)
    # which is then saved in
    # ./data605/lectures_pdf/tmp.notes_to_pdf.preprocess_notes.txt.figs/tmp.notes_to_pdf.render_image.1.png
    # Find the relative path to the resource path.
    rel_path = os.path.relpath(os.path.dirname(file_name), os.getcwd())
    cmd.append(f"--resource-path={rel_path}")
    # cmd.append("--resource-path=/app/data605/lectures_pdf/")
    if toc_type == "pandoc_native":
        cmd.append("--toc")
        cmd.append("--toc-depth 2")
    if no_pdf:
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
        cmd = dshdlipa.run_dockerized_pandoc(
            cmd,
            container_type,
            mode="return_cmd",
            force_rebuild=dockerized_force_rebuild,
            use_sudo=dockerized_use_sudo,
        )
    _LOG.debug("%s", "after: " + hprint.to_str("cmd"))
    hdbg.dassert_isinstance(cmd, str)
    hdbg.dassert_isinstance(file_out, str)
    return cmd, file_out


def run_pandoc_to_latex_slides(
    file_name: str,
    toc_type: str,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    debug: bool = False,
    no_pdf: bool = False,
    fail_on_warnings: bool = True,
    use_pandoc_ast_transform: bool = False,
) -> str:
    """
    Convert the input file to PDF slides using Pandoc.

    :param file_name: The input file to be converted
    :param no_pdf: If True, return the .tex / .typ file instead of compiling to
        PDF
    :param use_pandoc_ast_transform: If True, use two-stage AST pipeline instead
        of single-shot pandoc
    :return: The path to the generated PDF or .tex file
    """
    file_out = file_name.replace(".txt", ".tex" if no_pdf else ".pdf")
    if use_pandoc_ast_transform:
        # Two-stage pandoc pipeline (markdown -> AST -> beamer).
        _run_pandoc_to_ast(
            file_name,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            fail_on_warnings=fail_on_warnings,
        )
        ast_file = f"{file_name}.ast.json"
        tex_file = file_name.replace(".txt", ".tex")
        rel_path = os.path.relpath(os.path.dirname(file_name), os.getcwd())
        extra_opts = [
            "--number-sections",
            "--highlight-style=tango",
            "-s",
            "--slide-level 4",
            "-V theme:SimplePlus",
            "--include-in-header=latex_abbrevs.sty",
            f"--resource-path={rel_path}",
        ]
        if toc_type == "pandoc_native":
            extra_opts.extend(["--toc", "--toc-depth 2"])
        _run_pandoc_from_ast(
            ast_file,
            "beamer",
            tex_file,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            extra_opts=extra_opts,
            fail_on_warnings=fail_on_warnings,
        )
        file_out = tex_file
        rc = 0
        txt = ""
    else:
        # Default: single-shot pandoc.
        cmd, file_out = _build_pandoc_latex_cmd(
            file_name,
            toc_type,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            no_pdf=no_pdf,
            fail_on_warnings=fail_on_warnings,
        )
        rc, txt = _system_to_string(cmd, abort_on_error=False)
    # We want to print to screen.
    print(txt)
    # Return the .tex file if `--no_pdf` mode is requested.
    if no_pdf:
        hdbg.dassert_ne(rc, 0)
        _LOG.info("no_pdf=True: skipping PDF compilation, returning .tex file")
        _LOG.debug("file_out=%s", file_out)
        hdbg.dassert_path_exists(file_out)
        return file_out
    if rc != 0:
        _LOG.error("Log is in %s", file_out + ".log")
        if debug:
            _LOG.error("Pandoc failed")
            # Generate the tex version of the file.
            cmd, file_out = _build_pandoc_latex_cmd(
                file_name,
                toc_type,
                use_host_tools,
                dockerized_force_rebuild,
                dockerized_use_sudo,
                no_pdf=True,
                fail_on_warnings=fail_on_warnings,
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


def _extract_latex_math_defs() -> str:
    r"""
    Extract the math macro definitions from `latex_abbrevs.sty`.

    Problem:
    - Pandoc cannot carry an unknown control sequence (e.g., `\vx`) forward
      into Typst math
    - It rejects `$\vx$` with "unexpected control sequence" and emits it as
      escaped literal text

    Solution:
    - The macros must be expanded
    - Prepending these definitions as a raw-LaTeX block lets pandoc's
      `latex_macros` extension expand `\vx` -> `\boldsymbol{\underline{x}}`
      before converting the fully-expanded LaTeX math to Typst

    :return: The math macro definitions, one per line
    """
    latex_file = os.path.join(
        hgit.find_file("dev_scripts_helpers"),
        "documentation",
        "latex_abbrevs.sty",
    )
    hdbg.dassert_file_exists(latex_file)
    lines = []
    for line in hio.from_file(latex_file).split("\n"):
        # Only `\newcommand` / `\def` math macros are kept. Other macros
        # (e.g., `\usepackage`, `\definecolor`, `\setlist`) are dropped.
        if not (
            line.startswith("\\newcommand") or line.startswith("\\def")
        ):
            continue
        # Drop the `\textcolor`-based helpers; they are handled by a dedicated
        # post-conversion regex instead.
        if "\\textcolor" in line:
            continue
        lines.append(line)
    return "\n".join(lines)


def run_pandoc_to_typst_slides(
    curr_path: str,
    file_name: str,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    typst_only: bool = False,
    fail_on_warnings: bool = True,
    use_pandoc_ast_transform: bool = True,
) -> str:
    """
    Convert the input file to PDF slides using Pandoc + Typst/Touying.

    The markdown is converted to a Typst file using a Touying template (instead
    of beamer/LaTeX unlike Latex flow) and then compiled to PDF with a single
    `typst compile` pass (no second pass needed, unlike Latex flow).

    The flow always uses a 3-step pipeline for typst to support multi-column
    divved fence layouts:
      1. pandoc markdown -> JSON AST
      2. convert_pandoc_divved_fence.py: transform Div[columns] -> RawBlock[#grid()]
      3. pandoc JSON AST -> typst

    :param curr_path: The path where the script is located, used to reference
        `pandoc_touying.typ`
    :param file_name: The input file to be converted
    :param typst_only: If True, return the `.typ` file instead of compiling to
        PDF
    :param use_pandoc_ast_transform: Unused for typst; kept for interface
        consistency
    :return: The path to the generated PDF (or `.typ` file)
    """
    # 3-step pipeline is always used.
    hdbg.dassert_eq(use_pandoc_ast_transform, True)
    _LOG.debug(hprint.func_signature_to_str())
    _LOG.debug(
        "use_pandoc_ast_transform=%s (typst always uses 3-step pipeline)",
        use_pandoc_ast_transform,
    )
    typ_file = file_name.replace(".txt", ".typ")
    template = f"{curr_path}/pandoc_touying.typ"
    hdbg.dassert_path_exists(template)
    rel_path = os.path.relpath(os.path.dirname(file_name), os.getcwd())
    # TODO(gp): Consider using 1 stage pipeline with
    # --filter=convert_pandoc_divved_fence.py
    # Step 1: markdown -> JSON AST.
    # Prepend the LaTeX math abbreviation definitions so pandoc's
    # `latex_macros` extension expands macros like `\vx` into their full LaTeX
    # form before converting math to Typst.
    math_defs = _extract_latex_math_defs()
    file_with_defs = f"{file_name}.with_defs.txt"
    hio.to_file(file_with_defs, math_defs + "\n\n" + hio.from_file(file_name))
    _run_pandoc_to_ast(
        file_with_defs,
        use_host_tools,
        dockerized_force_rebuild,
        dockerized_use_sudo,
        fail_on_warnings=fail_on_warnings,
    )
    ast_file = f"{file_with_defs}.ast.json"
    # Step 2: transform Div[columns] -> RawBlock[typst #grid()] for multi-column layouts.
    transformed_ast_file = f"{file_name}.divved.ast.json"
    convert_script = hgit.find_file("convert_pandoc_divved_fence.py")
    cmd = f"{convert_script} -i {ast_file} -o {transformed_ast_file}"
    _ = _system(cmd)
    hdbg.dassert_path_exists(transformed_ast_file)
    # Step 3: JSON AST -> typst.
    extra_opts = [
        "--number-sections",
        "-s",
        f"--template {template}",
        f"--resource-path={rel_path}",
    ]
    _run_pandoc_from_ast(
        transformed_ast_file,
        "typst",
        typ_file,
        use_host_tools,
        dockerized_force_rebuild,
        dockerized_use_sudo,
        extra_opts=extra_opts,
        fail_on_warnings=fail_on_warnings,
    )
    hdbg.dassert_path_exists(typ_file)
    # 1) `pandoc` emits image paths relative to the current dir (the repo root)
    # - E.g., `image("data605/lectures_source/images/foo.png")`.
    # 2) Image references from render_images are relative to the output file's dir.
    # 3) Typst resolves relative image paths against the directory of the `.typ`
    # file (which lives in the output dir) and forbids `..` escapes above its
    # project root.
    # 4) So we rewrite the paths to be root-absolute and compile with `--root`
    #    set to the repo root so they resolve correctly.
    root = os.getcwd()
    txt = hio.from_file(typ_file)
    # `pandoc_touying.typ` includes `typst_abbrevs.typ` via a relative path that
    # assumes the generated `.typ` sits exactly 2 levels below the repo root.
    # That breaks for deeper output dirs (e.g., test scratch dirs). Rewrite the
    # include to a root-absolute Typst path (resolved against `--root` below),
    # matching how image paths are handled.
    abbrevs_path = os.path.join(
        hgit.find_file("dev_scripts_helpers"),
        "documentation",
        "typst_abbrevs.typ",
    )
    hdbg.dassert_file_exists(abbrevs_path)
    abbrevs_rel = os.path.relpath(abbrevs_path, root)
    txt = re.sub(
        r'#include\s+"[^"]*typst_abbrevs\.typ"',
        f'#include "/{abbrevs_rel}"',
        txt,
    )
    # Convert paths like "path/to/image.png" to "/path/to/image.png"
    # But preserve paths that are already absolute or start with ../
    typ_file_dir = os.path.dirname(typ_file)

    def convert_image_path(match: "re.Match[str]") -> str:
        # Extract path and parameters from image("...") or image("...", ...).
        path = match.group(1)
        params = match.group(2) or ""
        # If already absolute, leave it alone.
        if path.startswith("/"):
            return match.group(0)
        # If it contains relative parent references, leave it alone.
        if path.startswith("../"):
            return match.group(0)
        # Check if path is relative to typ_file_dir (e.g., render_images
        # output) or relative to repo root (e.g., source markdown paths).
        rel_to_typ_file_dir = os.path.join(typ_file_dir, path)
        if os.path.exists(rel_to_typ_file_dir):
            # Path is relative to typ_file_dir, make it repo-root relative.
            abs_path = os.path.abspath(rel_to_typ_file_dir)
            rel_to_root = os.path.relpath(abs_path, root)
            return f'image("/{rel_to_root}"{params})'
        else:
            # Path is already repo-root relative, just prepend `/`.
            return f'image("/{path}"{params})'

    txt = re.sub(r'image\s*\(\s*"([^"]*)"\s*([^)]*)\)', convert_image_path, txt)
    # Fix LaTeX color commands that pandoc couldn't convert to typst. Convert
    # \textcolor{blue}{...} to typst blue text.
    txt = re.sub(
        r"\\textcolor\{blue\}\{([^}]+)\}",
        r"#text(fill: blue, \1)",
        txt,
    )
    txt = re.sub(
        r"\\textcolor\{red\}\{([^}]+)\}",
        r"#text(fill: red, \1)",
        txt,
    )
    hio.to_file(typ_file, txt)
    # Return the `.typ` file if typst_only mode is requested.
    if typst_only:
        _LOG.info("typst_only=True: skipping typst compile, returning .typ file")
        return typ_file
    # - Compile the Typst file to PDF.
    _report_phase("typst compile")
    pdf_file = typ_file.replace(".typ", ".pdf")
    if use_host_tools:
        # cmd = f"typst compile --font-path /usr/share/fonts --root {root} {typ_file} {pdf_file}"
        cmd = f"typst compile --root {root} {typ_file} {pdf_file}"
        _LOG.info("cmd=%s", cmd)
        _ = _system(cmd)
    else:
        dshdlity.run_dockerized_typst(
            typ_file,
            pdf_file,
            [],
            typst_root_dir=root,
            force_rebuild=dockerized_force_rebuild,
            use_sudo=dockerized_use_sudo,
        )
    _LOG.debug("pdf_file=%s", pdf_file)
    hdbg.dassert_path_exists(pdf_file)
    return pdf_file


# #############################################################################


def copy_to_output(file_in: str, output: str) -> str:
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
    _LOG.info("File written to '%s'", file_out)
    return file_out


def copy_to_gdrive(
    file_name: str, ext: str, input_: str, gdrive_dir: str
) -> None:
    """
    Copy the processed file to Google Drive.

    :param file_name: The name of the file to be copied
    :param ext: The extension of the file to be copied
    """
    hdbg.dassert(not ext.startswith("."), "Invalid file_name='%s'", file_name)
    if not gdrive_dir:
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


def compress_pdf(file_name: str) -> str:
    """
    Compress a PDF file using ghostscript.

    :param file_name: The PDF file to compress
    :return: The path to the compressed PDF file
    """
    hdbg.dassert_path_exists(file_name)
    hdbg.dassert(
        file_name.endswith(".pdf"),
        "Input file must be a PDF; got file_name='%s'",
        file_name,
    )
    # Create a temporary output file.
    out_dir = os.path.dirname(file_name)
    basename = os.path.basename(file_name)
    compressed_file = os.path.join(out_dir, f"compressed-{basename}")
    # Compress the PDF using ghostscript.
    quality = "/printer"
    cmd = (
        f"/opt/homebrew/bin/gs -sDEVICE=pdfwrite"
        f" -dPDFSETTINGS={quality}"
        f" -dNOPAUSE -dQUIET -dBATCH"
        f" -sOutputFile={compressed_file} {file_name}"
    )
    _ = _system(cmd)
    # Replace original with compressed version.
    cmd = f"mv {compressed_file} {file_name}"
    _ = _system(cmd)
    return file_name


def cleanup_after(prefix: str) -> None:
    cmd = f"rm -rf {prefix}*"
    _ = _system(cmd)
