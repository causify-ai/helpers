#!/usr/bin/env python

r"""
Detect the type of `--input` and dispatch to the matching `download_*_to_md.py`
script.
    - **hn**: Hacker News submission URL (`news.ycombinator.com/item?id=...`)
      -> dispatches to `download_hn_article_to_md.py`
    - **academic_paper**: arXiv URL, DOI (URL or bare), or generic `.pdf` URL
      -> dispatches to `download_academic_paper_to_md.py`
    - **html**: anything else (generic web page) -> dispatches to
      `download_html_to_md.py`

- `--output` is only forwarded to the dispatched script when specified,
  otherwise dispatched script derives its own output name from the input
  otherwise (see their docstrings for the exact naming convention).

# Usage Example

- Download a generic web page (auto-detected as html):
> download_to_md.py --input "https://example.com/article"

- Download an arXiv paper (auto-detected as academic_paper):
> download_to_md.py --input "https://arxiv.org/abs/1706.03762"

- Download a Hacker News submission (auto-detected as hn):
> download_to_md.py --input "https://news.ycombinator.com/item?id=12345"

- Specify an explicit output path/base name, forwarded to the dispatched script:
> download_to_md.py --input "https://arxiv.org/abs/1706.03762" --output ./papers/attention

- Show what the dispatched script would do without executing it:
> download_to_md.py --input "https://arxiv.org/abs/1706.03762" --dry_run

- Overwrite existing output files instead of skipping:
> download_to_md.py --input "https://arxiv.org/abs/1706.03762" --no_incremental

Import as:

import dev_scripts_helpers.download.download_to_md as dsdtm
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import dev_scripts_helpers.download.download_academic_paper_to_md as dsdapt
import dev_scripts_helpers.download.download_utils as dsdlut
import dev_scripts_helpers.download.link_gsheet_utils as dslgsut

_LOG = logging.getLogger(__name__)


# #############################################################################
# Input type detection
# #############################################################################

# TODO(ai_gp): Inline these constants
_TYPE_HN = "hn"
_TYPE_ACADEMIC_PAPER = "academic_paper"
_TYPE_HTML = "html"


def _is_pdf_url(url: str) -> bool:
    """
    Check if a URL points directly to a PDF file.

    :param url: input URL
    :return: True if the URL path (ignoring query string/fragment) ends in
        `.pdf`
    """
    _LOG.debug(hprint.to_str("url"))
    # Strip query string and fragment before checking the file extension.
    path = url.split("?")[0].split("#")[0]
    result = path.lower().endswith(".pdf")
    _LOG.debug("return=%s", result)
    return result


def detect_input_type(input_arg: str) -> str:
    """
    Detect the type of `input_arg` to select the script to dispatch to.

    :param input_arg: URL to classify
    :return: `_TYPE_HN`, `_TYPE_ACADEMIC_PAPER`, or `_TYPE_HTML`
    """
    _LOG.debug(hprint.to_str("input_arg"))
    # Classify the input in priority order: Hacker News submissions first,
    # then academic-paper-like URLs (arXiv/DOI/PDF), else a generic web page.
    if dslgsut.is_hackernews_url(input_arg):
        input_type = _TYPE_HN
    elif (
        dsdlut.is_arxiv_url(input_arg)
        or dsdapt.detect_doi(input_arg)
        or _is_pdf_url(input_arg)
    ):
        input_type = _TYPE_ACADEMIC_PAPER
    else:
        input_type = _TYPE_HTML
    _LOG.info("Detected input type '%s' for: '%s'", input_type, input_arg)
    _LOG.debug("return=%s", input_type)
    return input_type


# #############################################################################
# Dispatch
# #############################################################################


def _dispatch(
    input_arg: str,
    output_arg: str,
    input_type: str,
    *,
    dry_run: bool = False,
    no_incremental: bool = False,
) -> None:
    """
    Dispatch to the `download_*_to_md.py` script matching `input_type`.

    :param input_arg: URL to download
    :param output_arg: output path/base name to forward, empty if not
        specified
    :param input_type: `_TYPE_HN`, `_TYPE_ACADEMIC_PAPER`, or `_TYPE_HTML`
    :param dry_run: if True, forward `--dry_run` to the dispatched script
    :param no_incremental: if True, forward `--no_incremental` to the
        dispatched script
    """
    _LOG.debug(
        hprint.to_str(
            "input_arg output_arg input_type dry_run no_incremental"
        )
    )
    # Resolve the script to dispatch to based on the detected input type; all
    # 3 target scripts share the same `--input` CLI flag.
    if input_type == _TYPE_HN:
        script_name = "download_hn_article_to_md.py"
    elif input_type == _TYPE_ACADEMIC_PAPER:
        script_name = "download_academic_paper_to_md.py"
    elif input_type == _TYPE_HTML:
        script_name = "download_html_to_md.py"
    else:
        raise ValueError(f"Unsupported input type: '{input_type}'")
    # Resolve the dispatched script's path and build its command line,
    # forwarding `--output` only when the caller specified one.
    script_path = hgit.find_file_in_git_tree(script_name)
    cmd = [
        script_path,
        f'--input "{input_arg}"',
    ]
    if output_arg:
        cmd.append(f'--output "{output_arg}"')
    if dry_run:
        cmd.append("--dry_run")
    if no_incremental:
        cmd.append("--no_incremental")
    cmd = " ".join(cmd)
    _LOG.debug("cmd=%s", cmd)
    _LOG.info("Dispatching to '%s'", script_name)
    hsystem.system(cmd, print_command=True)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    _LOG.debug(hprint.func_signature_to_str())
    parser = argparse.ArgumentParser(
        formatter_class=hparser.CustomHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help=(
            "URL to download: academic paper (arXiv/DOI/PDF), Hacker News "
            "submission, or generic web page"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="",
        help=(
            "Output path/base name forwarded to the dispatched script. If "
            "not specified, the dispatched script derives one on its own"
        ),
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help=(
            "Dry run mode: forward --dry_run to the dispatched script so it "
            "shows what would be done without actually executing actions"
        ),
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help=(
            "Forward --no_incremental to the dispatched script to overwrite "
            "existing output files instead of skipping"
        ),
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Detect the input type and dispatch to the matching downloader.
    """
    _LOG.debug(hprint.func_signature_to_str())
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    input_type = detect_input_type(args.input)
    _dispatch(
        args.input,
        args.output,
        input_type,
        dry_run=args.dry_run,
        no_incremental=args.no_incremental,
    )


if __name__ == "__main__":
    _main(_parse())
