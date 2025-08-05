"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging
import re
from typing import Callable, List, Tuple

import helpers.hdbg as hdbg
import helpers.hprint as hprint
from helpers.hmarkdown_comments import process_comment_block
import helpers_root.helpers.hdbg as hdbg
from helpers_root.helpers.hmarkdown_headers import HeaderInfo, HeaderList, is_markdown_line_separator

_LOG = logging.getLogger(__name__)


_TRACE = True


def extract_slides_from_markdown(
    lines: List[str],
) -> Tuple[HeaderList, int]:
    """
    Extract slides (i.e., sections prepended by `*`) from Markdown file and
    return an `HeaderList`.

    :param lines: content of the input Markdown file as list of strings
    :return: tuple containing:
        - generated `HeaderList`
            ```
            [
                (1, "Slide 1", 5),
                (1, "Slide 2", 10), ...]
            ```
        - last line number of the file, e.g., '100'
    """
    hdbg.dassert_isinstance(lines, list)
    header_list: HeaderList = []
    # Process the input file to extract headers.
    for line_number, line in enumerate(lines, start=1):
        _LOG.debug("%d: %s", line_number, line)
        # TODO(gp): Use the iterator.
        # Skip the visual separators.
        if is_markdown_line_separator(line):
            continue
        # Get the header level and title.
        m = re.match(r"^\* (.*)$", line)
        if m:
            title = m.group(1)
            header_info = HeaderInfo(1, title, line_number)
            header_list.append(header_info)
    last_line_number = len(lines)
    # Return results.
    hdbg.dassert_isinstance(header_list, list)
    return header_list, last_line_number


# TODO(gp): Consider passing and returning List[str]
def process_slides(txt: str, transform: Callable[[List[str]], List[str]]) -> str:
    """
    Process markdown text by applying a transform function to each slide.

    - Slides are sections prepended by `*`
    - The text is processed by:
        - Extracting the slides one by one
        - Calling a `transform()` function on each slide (defined by the user)
        - Joining the transformed slides back together
    - Comments are left untouched.

    :param txt: markdown text to process
    :param transform: function to transform each slide
    :return: transformed text
    """
    hdbg.dassert_isinstance(txt, str)
    # Text of the current slide.
    slide_txt: List[str] = []
    # Store all the transformed slides.
    transformed_txt: List[str] = []
    # True inside a block to skip.
    in_skip_block = False
    # True inside a slide.
    in_slide = False
    lines = txt.splitlines()
    for i, line in enumerate(lines):
        _LOG.debug("%s:line='%s'", i, line)
        # 1) Remove comment block.
        do_continue, in_skip_block = process_comment_block(line, in_skip_block)
        if _TRACE:
            _LOG.debug(" -> %s", hprint.to_str("do_continue in_skip_block"))
        if do_continue:
            transformed_txt.append(line)
            continue
        # 2) Process slide.
        if _TRACE:
            _LOG.debug(" -> %s", hprint.to_str("in_slide"))
        if line.startswith("* ") or line.startswith("#### "):
            _LOG.debug("### Found slide")
            # Found a slide or the end of the file.
            if slide_txt:
                _LOG.debug("# Transform slide")
                # Transform the slide.
                transformed_slide = transform(slide_txt)
                hdbg.dassert_isinstance(transformed_slide, list)
                transformed_txt.extend(transformed_slide)
            else:
                _LOG.debug("# First slide")
            # Start a new slide.
            slide_txt = []
            slide_txt.append(line)
            in_slide = True
        elif in_slide:
            _LOG.debug("# Accumulate slide")
            slide_txt.append(line)
        else:
            _LOG.debug("# Accumulate txt outside slide")
            transformed_txt.append(line)
    # Process the last slide, if needed.
    if slide_txt:
        hdbg.dassert(in_slide)
        in_slide = False
        # Transform the slide.
        transformed_slide = transform(slide_txt)
        hdbg.dassert_isinstance(transformed_slide, list)
        transformed_txt.extend(transformed_slide)
        slide_txt = []
        slide_txt.append(line)
    #
    hdbg.dassert(
        not in_skip_block,
        "Found end of file while still parsing a comment block",
    )
    hdbg.dassert(not in_slide, "Found end of file while still parsing a slide")
    # Join the transformed slides back together.
    result = "\n".join(transformed_txt)
    return result