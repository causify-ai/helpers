#!/usr/bin/env python

"""
Download Google Docs using gws (Google Workspace CLI).

This script downloads a Google Doc from a URL and saves it to a specified file
path. The output format is automatically detected from the file extension.

Supported formats (inferred from output file extension):
- .pdf: PDF format
- .docx: Microsoft Word format
- .odt: OpenDocument format
- .rtf: Rich Text format
- .txt: Plain text format
- .html: HTML format
- .md: Markdown format
- .epub: EPUB format
- .zip: ZIP format (for web archive)

Prerequisites:
- gws CLI tool installed: https://github.com/googleworkspace/cli
- gws authentication configured (run 'gws auth login' if not authenticated)

Basic usage:
> gws_download_doc.py --from_url https://docs.google.com/document/d/ABC123/edit \\
>                     --to_file document.pdf

Export as different formats:
> gws_download_doc.py --from_url https://docs.google.com/document/d/ABC123/edit \\
>                     --to_file document.docx
> gws_download_doc.py --from_url https://docs.google.com/document/d/ABC123/edit \\
>                     --to_file document.md
> gws_download_doc.py --from_url https://docs.google.com/document/d/ABC123/edit \\
>                     --to_file document.txt
"""

import argparse
import json
import logging
import os
import re

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Mapping of file extensions to gws drive files export MIME types.
_FORMAT_MAP = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "odt": "application/vnd.oasis.opendocument.text",
    "rtf": "application/rtf",
    "txt": "text/plain",
    "html": "text/html",
    "md": "text/markdown",
    "epub": "application/epub+zip",
    "zip": "application/zip",
}

# #############################################################################
# Helper functions
# #############################################################################


def _extract_doc_id(url: str) -> str:
    """
    Extract Google Docs document ID from a URL.

    :param url: Google Docs URL
    :return: document ID
    """
    # Pattern to match Google Docs URLs.
    pattern = r"/document/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, url)
    hdbg.dassert_is_not(
        match,
        None,
        "Invalid Google Docs URL format; expected /document/d/{ID}:",
        url,
    )
    doc_id = match.group(1)  # type: ignore
    return doc_id


def _get_format_from_suffix(file_path: str) -> str:
    """
    Get export format from file extension.

    :param file_path: output file path
    :return: MIME type for gws export
    """
    # Get file extension without the dot.
    _, ext = os.path.splitext(file_path)
    ext = ext.lstrip(".").lower()
    hdbg.dassert_in(
        ext,
        _FORMAT_MAP,
        "Unsupported file format; supported formats are: %s",
        ", ".join(_FORMAT_MAP.keys()),
    )
    mime_type = _FORMAT_MAP[ext]
    return mime_type


def _check_gws_authentication() -> None:
    """
    Check if gws is authenticated.

    If not authenticated, log an error and abort with instructions.
    """
    _LOG.debug("Checking gws authentication")
    try:
        hsystem.system("gws auth status", suppress_output=True)
        _LOG.debug("gws authentication verified")
    except Exception as e:
        _LOG.error(
            "gws authentication check failed; please run: gws auth login"
        )
        hdbg.dfatal(
            f"gws is not authenticated; cannot proceed: {e}"
        )


def _download_doc(doc_id: str, mime_type: str, output_file: str) -> None:
    """
    Download Google Doc using gws drive files export command.

    :param doc_id: Google Docs document ID
    :param mime_type: MIME type for export format
    :param output_file: path to save downloaded file
    """
    _LOG.info("Downloading document %s to %s", doc_id, output_file)
    # Build params JSON.
    params = {
        "fileId": doc_id,
        "mimeType": mime_type,
    }
    params_json = json.dumps(params)
    # Build gws command.
    cmd = (
        f"gws drive files export "
        f"--params '{params_json}' "
        f"--output {output_file}"
    )
    _LOG.debug("Running command: %s", cmd)
    # Execute command (abort_on_error=True will raise exception if command fails).
    hsystem.system(cmd, abort_on_error=True)
    _LOG.info("Document successfully saved to: %s", output_file)


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the script workflow.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("Starting Google Docs download")
    # Check gws authentication.
    _check_gws_authentication()
    # Validate and extract document ID from URL.
    doc_id = _extract_doc_id(args.from_url)
    _LOG.info("Extracted document ID: %s", doc_id)
    # Get export format from file extension.
    mime_type = _get_format_from_suffix(args.to_file)
    _LOG.info("Exporting as format: %s", mime_type)
    # Create parent directories if needed.
    parent_dir = os.path.dirname(args.to_file)
    if parent_dir:
        hio.create_dir(parent_dir, incremental=True)
    # Download the document.
    _download_doc(doc_id, mime_type, args.to_file)
    _LOG.info("Download complete")


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--from_url",
        action="store",
        required=True,
        help="Google Docs URL to download from",
    )
    parser.add_argument(
        "--to_file",
        action="store",
        required=True,
        help="Output file path (format inferred from extension)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


if __name__ == "__main__":
    _main(_parse())
