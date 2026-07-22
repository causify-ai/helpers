"""
Import as:

import dev_scripts_helpers.documentation.lib_notes_to_pdf as dshdlntpd
"""

import logging
import os
import re
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

_SCRIPT: List[str] = []


def _append_script(msg: str) -> None:
    old_len = len(_SCRIPT)
    _SCRIPT.append(msg)
    hdbg.dassert_lt(old_len, len(_SCRIPT))
    _LOG.debug("_SCRIPT=\n%s", "\n".join(_SCRIPT))


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


def _cleanup_before(prefix: str) -> None:
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
    # Map type to output format.
    output_format = "latex" if type_ == "pdf" else "latex"
    cmd = (
        f"{exec_file} --input {file1} --output {file2}"
        + f" --type {type_} --toc_type {toc_type}"
        + f" --output_format {output_format}"
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


def _run_pandoc_to_pdf(
    curr_path: str,
    file_name: str,
    prefix: str,
    toc_type: str,
    no_run_latex_again: bool,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    tex_only: bool = False,
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
    :param tex_only: If True, return the .tex file instead of compiling to PDF
    :return: The path to the generated output file (.tex or .pdf)
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
    # Return the .tex file if tex_only mode is requested.
    if tex_only:
        _LOG.info("tex_only=True: skipping pdflatex, returning .tex file")
        return file2
    # - Run latex.
    _report_phase("latex")
    # pdflatex needs to run in the same dir of `latex_abbrevs.sty` so we copy
    # all the needed files.
    out_dir = os.path.dirname(file_name)
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
    _ = _system(cmd)
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
    # `--include-in-header` is resolved by Pandoc relative to the cwd or the
    # `--resource-path` (set below), so copy `latex_abbrevs.sty` next to the
    # input file, which is where `--resource-path` points.
    latex_abbrevs_file = os.path.join(
        hgit.find_file("dev_scripts_helpers"),
        "documentation",
        "latex_abbrevs.sty",
    )
    hdbg.dassert_file_exists(latex_abbrevs_file)
    out_dir = os.path.dirname(file_name)
    _ = _system(f"cp -f {latex_abbrevs_file} {out_dir}")
    cmd.append("--include-in-header=latex_abbrevs.sty")
    # cmd.append("--pdf-engine=lualatex")
    # cmd.append("--pdf-engine=xelatex")
    cmd.append("--fail-if-warnings")
    # Needed since:
    # ![](tmp.notes_to_pdf.preprocess_notes.txt.figs/tmp.notes_to_pdf.render_image.1.png)
    # which is then saved in
    # ./data605/lectures_pdf/tmp.notes_to_pdf.preprocess_notes.txt.figs/tmp.notes_to_pdf.render_image.1.png
    # Use an absolute path (instead of one relative to `os.getcwd()`) since
    # this is converted to the corresponding path inside the Docker container
    # by `run_dockerized_pandoc()`, which assumes paths are anchored at the
    # Git root and not at the caller's cwd.
    cmd.append(f"--resource-path={out_dir}")
    # cmd.append("--resource-path=/app/data605/lectures_pdf/")
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


def _run_pandoc_to_slides(
    file_name: str,
    toc_type: str,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    debug: bool = False,
    tex_only: bool = False,
) -> str:
    """
    Convert the input file to PDF slides using Pandoc.

    :param file_name: The input file to be converted
    :param tex_only: If True, return the .tex file instead of compiling to PDF
    :return: The path to the generated PDF or .tex file
    """
    cmd, file_out = _build_pandoc_cmd(
        file_name,
        toc_type,
        use_host_tools,
        dockerized_force_rebuild,
        dockerized_use_sudo,
        use_tex=tex_only,
    )
    rc, txt = _system_to_string(cmd, abort_on_error=False)
    # We want to print to screen.
    print(txt)
    # rc = _system(cmd)
    # Return the .tex file if tex_only mode is requested.
    if tex_only:
        _LOG.info("tex_only=True: skipping PDF compilation, returning .tex file")
        _LOG.debug("file_out=%s", file_out)
        hdbg.dassert_path_exists(file_out)
        return file_out
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


def _run_pandoc_to_typst_slides(
    curr_path: str,
    file_name: str,
    use_host_tools: bool,
    dockerized_force_rebuild: bool,
    dockerized_use_sudo: bool,
    *,
    typst_only: bool = False,
) -> str:
    """
    Convert the input file to PDF slides using Pandoc + Typst/Touying.

    The markdown is converted to a Typst file using a Touying template (instead
    of beamer/LaTeX unlike Latex flow) and then compiled to PDF with a single
    `typst compile` pass (no second pass needed, unlike Latex flow).

    :param curr_path: The path where the script is located, used to reference
        `pandoc_touying.typ`
    :param file_name: The input file to be converted
    :param typst_only: If True, return the `.typ` file instead of compiling to
        PDF
    :return: The path to the generated PDF (or `.typ` file)
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Prepare command.
    cmd = []
    typ_file = file_name.replace(".txt", ".typ")
    cmd.append(f"pandoc {file_name}")
    cmd.append("-f markdown")
    cmd.append("--number-sections")
    cmd.append("-s")
    cmd.append("-t typst")
    template = f"{curr_path}/pandoc_touying.typ"
    hdbg.dassert_path_exists(template)
    cmd.append(f"--template {template}")
    # Images are referenced relative to the resource path, mirroring the beamer
    # path.
    rel_path = os.path.relpath(os.path.dirname(file_name), os.getcwd())
    cmd.append(f"--resource-path={rel_path}")
    cmd.append(f"-o {typ_file}")
    cmd = " ".join(cmd)
    _LOG.debug("%s", "before: " + hprint.to_str("cmd"))
    if not use_host_tools:
        container_type = "pandoc_only"
        # container_type = "pandoc_texlive"
        cmd = dshdlipa.run_dockerized_pandoc(
            cmd,
            container_type,
            mode="return_cmd",
            force_rebuild=dockerized_force_rebuild,
            use_sudo=dockerized_use_sudo,
        )
    _LOG.debug("%s", "after: " + hprint.to_str("cmd"))
    _ = _system(cmd)
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
    # Convert paths like "path/to/image.png" to "/path/to/image.png"
    # But preserve paths that are already absolute or start with ../
    typ_file_dir = os.path.dirname(typ_file)

    def convert_image_path(match: "re.Match[str]") -> str:
        # Extract the path from image("...")
        path = match.group(1)
        # If already absolute, leave it alone
        if path.startswith("/"):
            return match.group(0)
        # If it contains relative parent references, leave it alone
        if path.startswith("../"):
            return match.group(0)
        # Check if path is relative to typ_file_dir (e.g., render_images output)
        # or relative to repo root (e.g., source markdown paths)
        rel_to_typ_file_dir = os.path.join(typ_file_dir, path)
        if os.path.exists(rel_to_typ_file_dir):
            # Path is relative to typ_file_dir, make it repo-root relative
            abs_path = os.path.abspath(rel_to_typ_file_dir)
            rel_to_root = os.path.relpath(abs_path, root)
            return f'image("/{rel_to_root}")'
        else:
            # Path is already repo-root relative, just prepend /
            return f'image("/{path}")'

    txt = re.sub(r'image\("([^"]*)"\)', convert_image_path, txt)
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
    # Convert escaped backslashes for math mode.
    txt = re.sub(r"\\\\EE\b", r"\\mathbb{E}", txt)
    txt = re.sub(r"\\\\VV\b", r"\\mathbb{V}", txt)
    hio.to_file(typ_file, txt)
    # Return the `.typ` file if typst_only mode is requested.
    if typst_only:
        _LOG.info("typst_only=True: skipping typst compile, returning .typ file")
        return typ_file
    # - Compile the Typst file to PDF.
    _report_phase("typst compile")
    pdf_file = typ_file.replace(".typ", ".pdf")
    if use_host_tools:
        cmd = f"typst compile --root {root} {typ_file} {pdf_file}"
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


def _compress_pdf(file_name: str) -> str:
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


def _cleanup_after(prefix: str) -> None:
    cmd = f"rm -rf {prefix}*"
    _ = _system(cmd)
