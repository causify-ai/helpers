#!/usr/bin/env python

"""
Compress PNG images embedded in a Jupyter notebook (`.ipynb`) or nbconvert HTML
export (`.html`) using `pngquant`.

Notebooks that use ipywidgets `interact()` embed each captured plot twice
over: once as the normal cell output, and again inside the ipywidgets
`OutputModel` state (an `application/vnd.jupyter.widget-state+json` blob), so
those PNGs are usually the largest contributor to file size. This script
re-compresses PNGs in every place they can appear:
- `.ipynb`: `outputs[].data["image/png"]` in each cell, and the
  `metadata.widgets["application/vnd.jupyter.widget-state+json"]` blob
- `.html`: inline `data:image/png;base64,...` URIs anywhere in the HTML, and
  the `<script type="application/vnd.jupyter.widget-state+json">` blob above

`pngquant` performs lossy palette quantization: fine for the flat-color line
plots and tables typical of tutorial notebooks, since it only re-encodes an
image when the quantized version is smaller, and never touches image
dimensions, surrounding markup, or non-PNG content.

# Usage Example

- Compress a notebook in place (`.ipynb` or `.html`, detected from the
  extension):
> compress_notebook.py --input L06_01_exact_inference.ipynb

- Compress an nbconvert HTML export instead:
> compress_notebook.py --input L06_01_exact_inference.html

- Compress and write the result to a new file:
> compress_notebook.py --input L06_01_exact_inference.ipynb --output L06_01_exact_inference.small.ipynb

- Use a different `pngquant` quality range:
> compress_notebook.py --input L06_01_exact_inference.ipynb --quality 60-90

- Preview the size reduction without writing any file:
> compress_notebook.py --input L06_01_exact_inference.ipynb --dry_run

Import as:

import dev_scripts_helpers.notebooks.compress_notebook as dsnocono
"""

import argparse
import base64
import json
import logging
import os
import re
import shutil
from typing import Any, Dict, Match

import nbformat

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hselect_input_output as hseinout
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

# `pngquant` exit code meaning "can't reach the requested quality"; not a
# real failure, just a signal to keep the original PNG.
_PNGQUANT_QUALITY_TOO_LOW_RC = 99

_WIDGET_STATE_RE = re.compile(
    r'(<script type="application/vnd\.jupyter\.widget-state\+json">)'
    r"(.*?)"
    r"(</script>)",
    re.DOTALL,
)

_INLINE_PNG_DATA_URI_RE = re.compile(
    r"(data:image/png;base64,)([A-Za-z0-9+/=]+)"
)


# #############################################################################
# pngquant
# #############################################################################


def _find_pngquant_binary() -> str:
    """
    Locate the `pngquant` binary.

    :return: absolute path to the `pngquant` binary
    """
    pngquant_path = shutil.which("pngquant")
    hdbg.dassert_is_not(
        pngquant_path,
        None,
        "No `pngquant` binary found; install it (e.g., `brew install "
        "pngquant` or `apt install pngquant`) to compress embedded PNGs",
    )
    return pngquant_path  # type: ignore[return-value]


def _quantize_png(
    png_bytes: bytes, *, pngquant_binary: str, quality: str
) -> bytes:
    """
    Re-compress one PNG through `pngquant`, keeping the result only if it shrinks
    the image.

    :param png_bytes: raw PNG file content
    :param pngquant_binary: absolute path to the `pngquant` binary
    :param quality: `pngquant` `--quality` range (e.g., `"70-95"`)
    :return: quantized PNG bytes, or the original bytes unchanged if
        `pngquant` cannot reach `quality` or does not shrink the image
    """
    # `pngquant` only takes file paths, not stdin/stdout bytes, so round-trip
    # through scratch files (same idiom as `compress_pdf.py`/
    # `compress_figures.py`).
    tmp_in_file = "tmp.compress_notebook.quantize_in.png"
    tmp_out_file = "tmp.compress_notebook.quantize_out.png"
    with open(tmp_in_file, "wb") as f:
        f.write(png_bytes)
    cmd = (
        f"{pngquant_binary} --quality {quality} --speed 1 --force "
        f"--output {tmp_out_file} {tmp_in_file}"
    )
    rc = hsystem.system(
        cmd,
        suppress_error={_PNGQUANT_QUALITY_TOO_LOW_RC},
        suppress_output="ON_DEBUG_LEVEL",
    )
    if rc == _PNGQUANT_QUALITY_TOO_LOW_RC or not os.path.exists(tmp_out_file):
        return png_bytes
    with open(tmp_out_file, "rb") as f:
        new_png_bytes = f.read()
    if len(new_png_bytes) >= len(png_bytes):
        return png_bytes
    return new_png_bytes


# #############################################################################
# HTML transform
# #############################################################################


def _compress_output_png(
    output: Dict[str, Any], *, pngquant_binary: str, quality: str
) -> bool:
    """
    Re-compress the `image/png` entry of one cell/widget output, in place.

    :param output: one Jupyter `output` dict (from a cell or from an
        ipywidgets `OutputModel` state)
    :param pngquant_binary: absolute path to the `pngquant` binary
    :param quality: `pngquant` `--quality` range
    :return: whether `output` contained an `image/png` entry
    """
    png_b64 = output.get("data", {}).get("image/png")
    if not png_b64:
        return False
    png_bytes = base64.b64decode(png_b64)
    new_png_bytes = _quantize_png(
        png_bytes, pngquant_binary=pngquant_binary, quality=quality
    )
    if new_png_bytes is not png_bytes:
        output["data"]["image/png"] = base64.b64encode(new_png_bytes).decode(
            "ascii"
        )
    return True


def _compress_widget_state_payload(
    payload: Dict[str, Any], *, pngquant_binary: str, quality: str
) -> int:
    """
    Re-compress every PNG stored inside a parsed ipywidgets widget-state payload,
    in place.

    :param payload: parsed
        `application/vnd.jupyter.widget-state+json` payload
    :param pngquant_binary: absolute path to the `pngquant` binary
    :param quality: `pngquant` `--quality` range
    :return: number of `image/png` outputs found
    """
    num_images = 0
    for model in payload.get("state", {}).values():
        if model.get("model_name") != "OutputModel":
            continue
        for output in model.get("state", {}).get("outputs", []):
            if _compress_output_png(
                output, pngquant_binary=pngquant_binary, quality=quality
            ):
                num_images += 1
    return num_images


def _compress_widget_state_images(
    html: str, *, pngquant_binary: str, quality: str
) -> str:
    """
    Re-compress every PNG stored inside the ipywidgets widget-state JSON blob.

    :param html: full HTML content
    :param pngquant_binary: absolute path to the `pngquant` binary
    :param quality: `pngquant` `--quality` range
    :return: `html` with widget-state PNGs re-compressed in place
    """
    match = _WIDGET_STATE_RE.search(html)
    if match is None:
        _LOG.debug("No ipywidgets widget-state blob found")
        return html
    payload = json.loads(match.group(2))
    num_images = _compress_widget_state_payload(
        payload, pngquant_binary=pngquant_binary, quality=quality
    )
    _LOG.info("Compressed %s image(s) in the widget-state blob", num_images)
    new_payload = json.dumps(payload, separators=(",", ":"))
    return (
        html[: match.start()]
        + match.group(1)
        + new_payload
        + match.group(3)
        + html[match.end() :]
    )


def _compress_inline_images(
    html: str, *, pngquant_binary: str, quality: str
) -> str:
    """
    Re-compress every inline `data:image/png;base64,...` URI in `html`.

    :param html: full HTML content
    :param pngquant_binary: absolute path to the `pngquant` binary
    :param quality: `pngquant` `--quality` range
    :return: `html` with inline PNGs re-compressed in place
    """

    def _replace(match: Match) -> str:
        prefix, png_b64 = match.group(1), match.group(2)
        png_bytes = base64.b64decode(png_b64)
        new_png_bytes = _quantize_png(
            png_bytes, pngquant_binary=pngquant_binary, quality=quality
        )
        if new_png_bytes is png_bytes:
            return match.group(0)
        return prefix + base64.b64encode(new_png_bytes).decode("ascii")

    return _INLINE_PNG_DATA_URI_RE.sub(_replace, html)


def _compress_notebook_html(html: str, *, quality: str) -> str:
    """
    Re-compress every embedded PNG in a notebook HTML export.

    :param html: full HTML content
    :param quality: `pngquant` `--quality` range
    :return: `html` with all embedded PNGs re-compressed
    """
    pngquant_binary = _find_pngquant_binary()
    html = _compress_widget_state_images(
        html, pngquant_binary=pngquant_binary, quality=quality
    )
    html = _compress_inline_images(
        html, pngquant_binary=pngquant_binary, quality=quality
    )
    return html


def _compress_ipynb_cell_outputs(
    nb: nbformat.NotebookNode, *, pngquant_binary: str, quality: str
) -> int:
    """
    Re-compress every PNG stored in a cell `outputs[].data["image/png"]`, in
    place.

    :param nb: parsed notebook
    :param pngquant_binary: absolute path to the `pngquant` binary
    :param quality: `pngquant` `--quality` range
    :return: number of `image/png` outputs found
    """
    num_images = 0
    for cell in nb.get("cells", []):
        for output in cell.get("outputs", []):
            if _compress_output_png(
                output, pngquant_binary=pngquant_binary, quality=quality
            ):
                num_images += 1
    return num_images


def _compress_notebook_ipynb(nb_text: str, *, quality: str) -> str:
    """
    Re-compress every embedded PNG in a Jupyter notebook.

    :param nb_text: full `.ipynb` JSON content
    :param quality: `pngquant` `--quality` range
    :return: `nb_text` with all embedded PNGs re-compressed
    """
    pngquant_binary = _find_pngquant_binary()
    nb = nbformat.reads(nb_text, as_version=4)
    num_cell_images = _compress_ipynb_cell_outputs(
        nb, pngquant_binary=pngquant_binary, quality=quality
    )
    _LOG.info("Compressed %s image(s) in cell outputs", num_cell_images)
    widget_state = (
        nb.get("metadata", {})
        .get("widgets", {})
        .get("application/vnd.jupyter.widget-state+json")
    )
    if widget_state is not None:
        num_widget_images = _compress_widget_state_payload(
            widget_state, pngquant_binary=pngquant_binary, quality=quality
        )
        _LOG.info(
            "Compressed %s image(s) in the widget-state blob",
            num_widget_images,
        )
    else:
        _LOG.debug("No ipywidgets widget-state blob found")
    # `nbformat.writes()` does not add the trailing newline that
    # `nbformat.write()` (and Jupyter itself) always writes to disk.
    return nbformat.writes(nb) + "\n"


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hseinout.add_input_output_args(parser)
    parser.add_argument(
        "--quality",
        action="store",
        default="70-95",
        type=str,
        help="`pngquant` `--quality min-max` range",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Report the size reduction without writing any file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    in_file_name, out_file_name = hseinout.parse_input_output_args(args)
    hdbg.dassert_file_exists(in_file_name)
    text = hio.from_file(in_file_name)
    size_before = len(text.encode("utf-8"))
    if in_file_name.endswith(".ipynb"):
        text = _compress_notebook_ipynb(text, quality=args.quality)
    else:
        text = _compress_notebook_html(text, quality=args.quality)
    size_after = len(text.encode("utf-8"))
    reduction = hprint.perc(
        size_after, size_before, invert=True, allow_increase=True
    )
    if args.dry_run:
        _LOG.warning(
            "[DRY_RUN] Would write '%s': %s -> %s bytes (%s smaller)",
            out_file_name,
            size_before,
            size_after,
            reduction,
        )
    else:
        hio.to_file(out_file_name, text)
        _LOG.info(
            "Compressed '%s' to '%s': %s -> %s bytes (%s smaller)",
            in_file_name,
            out_file_name,
            size_before,
            size_after,
            reduction,
        )


if __name__ == "__main__":
    _main(_parse())
