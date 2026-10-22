#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "pdfCropMargins",
# ]
# ///

"""
Crop the pages of a PDF file, removing white margins or fixed-size borders.

The cropping is done by `pdfCropMargins`, run as a module of the interpreter
that runs this script. `uv` creates an isolated environment with the dependency
declared above on the first run (no `pip install` and no Docker needed). The
`helpers` package must be importable, as for the other scripts of the repo.

Two cropping modes are supported:
- Auto (default): find the bounding box of the non-white pixels of each page,
  and crop the page to it, plus `--padding` points on every side
  - `--uniform` crops all the selected pages by the same amount (the smallest
    white margin found on each side), so that the content stays aligned across
    pages, e.g., for slides
- Fixed (`--margins`): remove the given number of points from the left, top,
  right, and bottom of every selected page

All the distances are in PDF points (1 pt = 1/72 inch).

The page boxes (`MediaBox`, `CropBox`) are rewritten, so every viewer and
LaTeX `includegraphics` show the cropped page. The page content is not
modified.

Known limitations of `pdfCropMargins` (version 2.2.1):
- A blank page is left unchanged, with a warning, except with `--padding`,
  which shrinks it to an empty square of `2 * padding` points
- With `--margins`, the left and right margins (and the top and bottom ones) are
  swapped on the pages rotated by 90 or 270 degrees
- With `--padding`, the cropped page can extend beyond the original page when
  the content touches its edge

# Usage Example

- Crop the white margins of all the pages, writing `figure.cropped.pdf`:
> crop_pdf.py --input figure.pdf

- Crop the white margins and keep 5 points of padding around the content:
> crop_pdf.py --input figure.pdf --output figure_tight.pdf --padding 5

- Crop all the pages by the same amount, to keep the slides aligned:
> crop_pdf.py --input slides.pdf --output slides_tight.pdf --uniform

- Crop only pages 1-3 and 7 to 9 (1-based) and leave the others unchanged:
> crop_pdf.py --input paper.pdf --output paper_tight.pdf --pages "1-3,7-9"

- Remove 20 points from the left and 36 points from the top of every page:
> crop_pdf.py --input paper.pdf --output paper_trimmed.pdf --margins 20 36 0 0

- Show the `pdfCropMargins` command that would be run, without running it:
> crop_pdf.py --input figure.pdf --dry_run

- Crop a PDF in place (the original file is overwritten):
> crop_pdf.py --input figure.pdf --output figure.pdf
"""

import argparse
import logging
import os
import shlex
import sys

import helpers.hselect_input_output as hseinout
from helpers import hdbg, hparser, hsystem

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hselect_input_output as hseinout
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Crop PDF
# #############################################################################


def _build_crop_cmd(
    input_path: str,
    output_path: str,
    *,
    pages: str,
    margins: list[float],
    padding: float,
    uniform: bool,
    dpi: int,
    threshold: int,
) -> list[str]:
    """
    Build the `pdfCropMargins` command that crops a PDF.

    `pdfCropMargins` is run as a module of the interpreter that runs this
    script, so that the dependency declared inline for `uv run` is used,
    whatever `$PATH` contains.

    :param input_path: path of the PDF to crop
    :param output_path: path of the cropped PDF; it must differ from
        `input_path`
    :param pages: 1-based pages to crop, e.g., `1-3,7-9`; an empty string
        selects all the pages
    :param margins: points to remove from the left, top, right, bottom of
        every page; an empty list crops the white space instead
    :param padding: points of white space to keep around the content when
        cropping the white space
    :param uniform: if True, crop all the pages by the same amount
    :param dpi: resolution used to render the pages and find the content
    :param threshold: gray level (0-255) over which a pixel is white
    :return: command, as a list of arguments
    """
    _LOG.debug(
        "input_path=%s output_path=%s pages=%s margins=%s padding=%s "
        "uniform=%s dpi=%s threshold=%s",
        input_path,
        output_path,
        pages,
        margins,
        padding,
        uniform,
        dpi,
        threshold,
    )
    cmd = [sys.executable, "-m", "pdfCropMargins"]
    if margins:
        left, top, right, bottom = margins
        # Pre-crop the page by the given amounts, which `pdfCropMargins` takes
        # as left, bottom, right, top. Then retain 100% of the margins that are
        # left, so that nothing else is cropped.
        cmd += ["-ap4", str(left), str(bottom), str(right), str(top)]
        cmd += ["-p", "100"]
    else:
        # Retain 0% of the margins to get the tight bounding box.
        cmd += ["-p", "0"]
        if padding > 0:
            # A negative absolute offset adds space around the bounding box.
            cmd += ["-a", str(-padding)]
        if uniform:
            cmd += ["-u"]
        cmd += ["-t", str(threshold), "-x", str(dpi), "-y", str(dpi)]
    if pages:
        cmd += ["-g", pages]
    cmd += ["-o", output_path, input_path]
    _LOG.debug("return=%s", cmd)
    return cmd


def _crop_pdf(
    input_path: str,
    output_path: str,
    *,
    pages: str,
    margins: list[float],
    padding: float,
    uniform: bool,
    dpi: int,
    threshold: int,
    dry_run: bool,
) -> None:
    """
    Crop a PDF with `pdfCropMargins`, also when it overwrites the input.

    `pdfCropMargins` refuses to write over its input, so the cropped PDF is
    first written to a temporary file in the same dir as the output and then
    moved in place.

    :param input_path: path of the PDF to crop
    :param output_path: path of the cropped PDF; it can be `input_path`
    :param pages: 1-based pages to crop, e.g., `1-3,7-9`; an empty string
        selects all the pages
    :param margins: points to remove from the left, top, right, bottom of
        every page; an empty list crops the white space instead
    :param padding: points of white space to keep around the content when
        cropping the white space
    :param uniform: if True, crop all the pages by the same amount
    :param dpi: resolution used to render the pages and find the content
    :param threshold: gray level (0-255) over which a pixel is white
    :param dry_run: if True, show what would be done without executing
    """
    _LOG.debug(
        "input_path=%s output_path=%s dry_run=%s",
        input_path,
        output_path,
        dry_run,
    )
    tmp_path = os.path.join(
        os.path.dirname(os.path.abspath(output_path)),
        "tmp.crop_pdf._crop_pdf.pdf",
    )
    cmd = _build_crop_cmd(
        input_path,
        tmp_path,
        pages=pages,
        margins=margins,
        padding=padding,
        uniform=uniform,
        dpi=dpi,
        threshold=threshold,
    )
    if dry_run:
        _LOG.warning(
            "[DRY_RUN] Would run '%s' and move the result to '%s'",
            shlex.join(cmd),
            output_path,
        )
    else:
        _LOG.info("Cropping '%s' with: %s", input_path, shlex.join(cmd))
        # Let a failure raise: `hsystem.system()` aborts and `tmp_path` is left
        # for inspection. Show the output, since `pdfCropMargins` reports the
        # pages it cannot crop as warnings.
        hsystem.system(shlex.join(cmd), suppress_output=False)
        os.replace(tmp_path, output_path)
        _LOG.info("Cropped PDF written to '%s'", output_path)


# #############################################################################
# CLI / entry points
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    # `--input` is the PDF to crop and `--output` is the cropped PDF, which is
    # `<input>.cropped.pdf` next to the input when not specified, and the same
    # as `--input` to crop in place.
    hseinout.add_input_output_args(parser, in_required=True, out_required=False)
    parser.add_argument(
        "--pages",
        action="store",
        default="",
        help="Pages to crop, 1-based, e.g., '1-3,7-9'; "
        "the other pages are kept unchanged. Default: all the pages",
    )
    parser.add_argument(
        "--margins",
        action="store",
        nargs=4,
        type=float,
        default=[],
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        help="Remove fixed margins (in points) instead of cropping the "
        "white space",
    )
    parser.add_argument(
        "--padding",
        action="store",
        type=float,
        default=0.0,
        help="Points of white space to keep around the content in auto mode",
    )
    parser.add_argument(
        "--uniform",
        action="store_true",
        help="Crop all the pages by the same amount (auto mode only)",
    )
    parser.add_argument(
        "--dpi",
        action="store",
        type=int,
        default=150,
        help="Resolution used to find the content in auto mode: higher is "
        "more precise but slower",
    )
    parser.add_argument(
        "--threshold",
        action="store",
        type=int,
        default=191,
        help="Gray level (0-255) over which a pixel is white in auto mode: "
        "lower ignores faint marks, 255 keeps everything non-white",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate the options.
    hdbg.dassert(
        not args.input_files and not args.from_file,
        "Only a single PDF is supported: use `--input`",
    )
    hdbg.dassert_file_exists(args.input, "Input PDF to crop must exist")
    if args.margins:
        hdbg.dassert(
            all(margin >= 0 for margin in args.margins),
            "Margins must be non-negative: %s",
            args.margins,
        )
        hdbg.dassert(
            args.padding == 0.0 and not args.uniform,
            "`--padding` and `--uniform` only apply to auto mode, "
            "not to `--margins`",
        )
    hdbg.dassert_lte(0, args.padding, "Padding must be non-negative")
    output_path = args.output
    if not output_path:
        stem, _ = os.path.splitext(args.input)
        output_path = stem + ".cropped.pdf"
    _crop_pdf(
        args.input,
        output_path,
        pages=args.pages,
        margins=args.margins,
        padding=args.padding,
        uniform=args.uniform,
        dpi=args.dpi,
        threshold=args.threshold,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    _main(_parse())
