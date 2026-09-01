#!/usr/bin/env python

"""
Compress a PDF file using Ghostscript to reduce its file size.

# Usage Example

- Compress a PDF in place:
> compress_pdf.py --input lecture.pdf

- Compress a PDF and write the result to a new file:
> compress_pdf.py --input lecture.pdf --output lecture.compressed.pdf

- Use a lower-quality, higher-compression preset:
> compress_pdf.py --input lecture.pdf --quality /ebook

- Compress using `gs` running inside Docker instead of the host binary:
> compress_pdf.py --input lecture.pdf --backend ghostscript_dockerized
"""

import argparse
import logging
import os
import shutil

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Backends
# #############################################################################

# - `ghostscript_global`: run the `gs` binary installed on the host machine
# - `ghostscript_dockerized`: run `gs` inside the `minidocks/ghostscript`
#   Docker container
_VALID_BACKENDS = ["ghostscript_global", "ghostscript_dockerized"]
_DEFAULT_BACKEND = "ghostscript_global"

# Pre-built public image: no local Dockerfile/build is involved, `gs` is run
# directly inside it.
_GHOSTSCRIPT_DOCKER_IMAGE = "minidocks/ghostscript"

# Common Ghostscript install locations, tried before falling back to a plain
# `PATH` lookup: this repo's thin client puts `dev_scripts_helpers/git/gs` (a
# `git status` alias, not Ghostscript) ahead of the real `gs` binary on
# `PATH`, so a bare `shutil.which("gs")` can silently resolve to the wrong
# executable.
_GS_CANDIDATE_PATHS = [
    "/opt/homebrew/bin/gs",  # macOS, Homebrew on Apple Silicon.
    "/usr/local/bin/gs",  # macOS, Homebrew on Intel.
    "/usr/bin/gs",  # Linux, system package.
]


def _build_gs_cmd_opts(quality: str) -> str:
    """
    Build the Ghostscript command line options shared by both backends.

    :param quality: Ghostscript `-dPDFSETTINGS` preset (e.g., `/screen`,
        `/ebook`, `/printer`, `/prepress`)
    :return: space-separated `gs` options, without the binary, input, or
        output file
    """
    opts = [
        "-sDEVICE=pdfwrite",
        f"-dPDFSETTINGS={quality}",
        # Target PDF 1.4 for broad compatibility with PDF readers.
        "-dCompatibilityLevel=1.4",
        "-dNOPAUSE -dQUIET -dBATCH",
    ]
    return " ".join(opts)


def _find_gs_binary() -> str:
    """
    Locate the Ghostscript `gs` binary.

    :return: absolute path to the `gs` binary
    """
    for candidate in _GS_CANDIDATE_PATHS:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    gs_path = shutil.which("gs")
    hdbg.dassert_is_not(
        gs_path,
        None,
        "No `gs` (Ghostscript) binary found; install Ghostscript or use "
        "`--backend ghostscript_dockerized`",
    )
    return gs_path  # type: ignore[return-value]


def _compress_pdf_ghostscript_global(
    input_file: str, output_file: str, *, quality: str = "/printer"
) -> None:
    """
    Compress a PDF using the `gs` binary installed on the host machine.

    :param input_file: PDF file to compress
    :param output_file: path to write the compressed PDF to (can be the
        same as `input_file` to compress in place)
    :param quality: Ghostscript `-dPDFSETTINGS` preset (e.g., `/screen`,
        `/ebook`, `/printer`, `/prepress`)
    """
    _LOG.debug(hprint.to_str("input_file output_file quality"))
    gs_binary = _find_gs_binary()
    # Compress to a temporary file since `gs` cannot write to the same path
    # it reads from, then move it into place (works whether `output_file`
    # is the same as `input_file` or not).
    tmp_output_file = output_file + ".compressed.tmp"
    gs_opts = _build_gs_cmd_opts(quality)
    cmd = f"{gs_binary} {gs_opts} -sOutputFile={tmp_output_file} {input_file}"
    hsystem.system(cmd)
    shutil.move(tmp_output_file, output_file)


def _compress_pdf_ghostscript_dockerized(
    input_file: str,
    output_file: str,
    *,
    quality: str = "/printer",
    use_sudo: bool = False,
) -> None:
    """
    Compress a PDF using `gs` running inside the `minidocks/ghostscript`
    Docker container (pulled automatically if missing).

    The container is mounted at the Git root (see
    `helpers.hdocker.get_docker_mount_context()`), so `input_file` and
    `output_file` must live underneath the current Git repo.

    :param input_file: PDF file to compress
    :param output_file: path to write the compressed PDF to (can be the
        same as `input_file` to compress in place)
    :param quality: Ghostscript `-dPDFSETTINGS` preset (e.g., `/screen`,
        `/ebook`, `/printer`, `/prepress`)
    :param use_sudo: whether to use `sudo` for Docker commands
    """
    _LOG.debug(hprint.to_str("input_file output_file quality use_sudo"))
    # Compress to a temporary file, same rationale as
    # `_compress_pdf_ghostscript_global()`.
    tmp_output_file = output_file + ".compressed.tmp"
    # Convert the host paths to the paths seen inside the Docker container.
    (
        is_caller_host,
        use_sibling_container_for_callee,
        caller_mount_path,
        callee_mount_path,
        mount,
    ) = hdocker.get_docker_mount_context()
    docker_input_file = hdocker.convert_caller_to_callee_docker_path(
        input_file,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    docker_tmp_output_file = hdocker.convert_caller_to_callee_docker_path(
        tmp_output_file,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    gs_opts = _build_gs_cmd_opts(quality)
    gs_cmd = (
        f"gs {gs_opts} -sOutputFile={docker_tmp_output_file} "
        f"{docker_input_file}"
    )
    # `minidocks/ghostscript` has no fixed entrypoint, so the full `gs`
    # command is passed as-is (mirrors `docker run ... minidocks/ghostscript
    # gs ...`).
    hdocker.build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        _GHOSTSCRIPT_DOCKER_IMAGE,
        "",
        gs_cmd,
        "system",
    )
    shutil.move(tmp_output_file, output_file)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        action="store",
        required=True,
        type=str,
        help="PDF file to compress",
    )
    parser.add_argument(
        "--output",
        "-o",
        action="store",
        default="",
        type=str,
        help="Compressed PDF file to write (default: overwrite `--input` "
        "in place)",
    )
    parser.add_argument(
        "--quality",
        action="store",
        default="/printer",
        type=str,
        help="Ghostscript `-dPDFSETTINGS` quality preset (e.g., `/screen`, "
        "`/ebook`, `/printer`, `/prepress`)",
    )
    parser.add_argument(
        "--backend",
        action="store",
        choices=_VALID_BACKENDS,
        default=_DEFAULT_BACKEND,
        help="How to run `gs`: `ghostscript_global` uses the host `gs` "
        "binary, `ghostscript_dockerized` runs `gs` inside Docker",
    )
    # `--dockerized_force_rebuild` is accepted for CLI consistency but is a
    # no-op here: the `ghostscript_dockerized` backend uses the pre-built
    # public `minidocks/ghostscript` image, not a locally-built one.
    hdocker.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    input_file = args.input
    output_file = args.output or input_file
    quality = args.quality
    backend = args.backend
    hdbg.dassert_file_exists(input_file, "PDF file to compress does not exist")
    hdbg.dassert(
        input_file.endswith(".pdf"),
        "Input file must be a PDF; got input_file='%s'",
        input_file,
    )
    if backend == "ghostscript_global":
        _compress_pdf_ghostscript_global(
            input_file, output_file, quality=quality
        )
    else:
        _compress_pdf_ghostscript_dockerized(
            input_file,
            output_file,
            quality=quality,
            use_sudo=args.dockerized_use_sudo,
        )
    _LOG.info(
        "Compressed '%s' to '%s' using backend='%s'.",
        input_file,
        output_file,
        backend,
    )


if __name__ == "__main__":
    _main(_parse())
