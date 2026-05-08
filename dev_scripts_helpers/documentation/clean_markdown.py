#!/usr/bin/env python

"""
Clean up HTML markup in markdown files.

> clean_markdown.py --input INPUT --output OUTPUT
"""

import argparse
import logging
import re

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Clean up HTML markup in markdown files."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=str,
        help="Path to the input markdown file",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=str,
        help="Path to the output markdown file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _remove_span_with_multiple_attributes(content: str) -> str:
    """
    Remove span tags that have multiple attributes (completely remove the tag).

    Matches span tags with 2 or more attribute assignments (indicated by `=`).
    This pattern identifies spans like:
    `<span id="foo" class="bar">content</span>`

    :param content: the markdown content
    :return: content with multi-attribute span tags removed
    """
    # Pattern matches span tags with at least 2 attributes.
    pattern = r"<span\s+[^>]*=[^>]*\s+[^>]*=[^>]*>.*?</span>"
    content = re.sub(pattern, "", content, flags=re.DOTALL)
    return content


def _remove_label_span_tags(content: str) -> str:
    """
    Remove only class="label" span tags but keep their content.

    Matches span tags with only `class="label"` attribute and replaces them
    with their content (e.g., `<span class="label">Part I. </span>` becomes
    `Part I. `).

    :param content: the markdown content
    :return: content with class="label" span tags removed but content kept
    """
    # Pattern matches span tags with only class="label" attribute.
    # Handles both single and double quotes.
    pattern = r'<span\s+class=["\']label["\']>([^<]*)</span>'
    content = re.sub(pattern, r"\1", content)
    return content


def _remove_keep_together_span_tags(content: str) -> str:
    """
    Remove only class="keep-together" span tags but keep their content.

    Matches span tags with only `class="keep-together"` attribute and
    replaces them with their content (e.g.,
    `<span class="keep-together">causation</span>` becomes `causation`).

    :param content: the markdown content
    :return: content with class="keep-together" span tags removed but content
        kept
    """
    # Pattern matches span tags with only class="keep-together" attribute.
    # Handles both single and double quotes.
    pattern = r'<span\s+class=["\']keep-together["\']>([^<]*)</span>'
    content = re.sub(pattern, r"\1", content)
    return content


def _remove_html_link_span_tags(content: str) -> str:
    """
    Remove span tags with id attributes containing .html pattern (chapter links).

    These are anchor/link spans like `<span id="ch12.html"></span>` that are
    used for cross-references and should be completely removed.

    :param content: the markdown content
    :return: content with HTML link span tags removed
    """
    # Pattern matches span tags with id attribute containing .html pattern.
    # Handles both single and double quotes.
    pattern = r'<span\s+id=["\'][^"\']*\.html["\'][^>]*>\s*</span>'
    content = re.sub(pattern, "", content)
    return content


def _remove_pre_span_tags(content: str) -> str:
    """
    Remove only class="pre" span tags but keep their content.

    Matches span tags with only `class="pre"` attribute and replaces them
    with their content (e.g., `<span class="pre">`is_on_sale`</span>` becomes
    `` `is_on_sale` ``).

    :param content: the markdown content
    :return: content with class="pre" span tags removed but content kept
    """
    # Pattern matches span tags with only class="pre" attribute.
    # Handles both single and double quotes.
    pattern = r'<span\s+class=["\']pre["\']>([^<]*)</span>'
    content = re.sub(pattern, r"\1", content)
    return content


def _remove_anchor_tags(content: str) -> str:
    """
    Remove anchor tags but keep their content.

    Matches anchor tags like `<a href="#part03.html_part-3" data-type="xref">
    Part III</a>` and replaces them with just the content (`Part III`).

    :param content: the markdown content
    :return: content with anchor tags removed but content kept
    """
    # Pattern matches anchor tags with any attributes and captures the content.
    pattern = r"<a\s+[^>]*>([^<]*)</a>"
    content = re.sub(pattern, r"\1", content)
    return content


def _remove_backticks_in_math(content: str) -> str:
    """
    Remove backticks from LaTeX math expressions.

    Matches LaTeX math delimited by `$` with backticks inside
    (e.g., `$`Y(1)`$`) and removes the backticks (e.g., `$Y(1)$`).

    :param content: the markdown content
    :return: content with backticks removed from LaTeX math
    """
    # Pattern matches $`...`$ and removes the backticks.
    pattern = r"\$`([^`]*)`\$"
    content = re.sub(pattern, r"$\1$", content)
    return content


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to clean markdown files.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Read input file.
    _LOG.info("Reading input file: %s", args.input)
    content = hio.from_file(args.input)
    # Remove span tags with multiple attributes (completely remove them).
    _LOG.info("Removing span tags with multiple attributes")
    content = _remove_span_with_multiple_attributes(content)
    # Remove only class="label" span tags but keep their content.
    _LOG.info("Removing class='label' span tags (keeping content)")
    content = _remove_label_span_tags(content)
    # Remove only class="keep-together" span tags but keep their content.
    _LOG.info("Removing class='keep-together' span tags (keeping content)")
    content = _remove_keep_together_span_tags(content)
    # Remove HTML link span tags (e.g., <span id="ch12.html"></span>).
    _LOG.info("Removing HTML link span tags")
    content = _remove_html_link_span_tags(content)
    # Remove only class="pre" span tags but keep their content.
    _LOG.info("Removing class='pre' span tags (keeping content)")
    content = _remove_pre_span_tags(content)
    # Remove anchor tags but keep their content.
    _LOG.info("Removing anchor tags (keeping content)")
    content = _remove_anchor_tags(content)
    # Remove backticks from LaTeX math expressions.
    _LOG.info("Removing backticks from LaTeX math expressions")
    content = _remove_backticks_in_math(content)
    # Write output file.
    _LOG.info("Writing output file: %s", args.output)
    hio.to_file(args.output, content)
    _LOG.info("Done")


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
