"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import abc
import logging
from typing import Callable, List

import helpers.hdbg as hdbg
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.


# #############################################################################
# SlideProcessor
# #############################################################################

# TODO(gp): -> hmarkdown_slides.py

_TRACE = True

# #############################################################################
# SlideProcessor
# #############################################################################


class SlideProcessor(abc.ABC):
    """
    Given a markdown text, process the slides one by one, and return the text.

    - Slides are sections prepended by `*`
    - The text is processed by:
        - Extracting the slides one by one
        - Calling a `transforrm()` function on each slide (defined by the user)
        - Joining the transformed slides back together
    - Comments are left untouched.

    :param text: The markdown text to process.
    :return: The transformed text
    """

    def __init__(self):
        pass

    # @abc.abstractmethod
    # def transform(self, slide_text: List[str]) -> List[str]:
    #     """
    #     Process a slide.
    #     """
    #     hdbg.dassert_isinstance(slide_text, list)
    #     slide_text_out = super().transform(slide_text)
    #     hdbg.dassert_isinstance(slide_text_out, list)
    #     return slide_text_out

    def process(
        self, txt: str, transform: Callable[[List[str]], List[str]]
    ) -> str:
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
            do_continue, in_skip_block = process_comment_block(
                line, in_skip_block
            )
            if _TRACE:
                _LOG.debug(" -> " + hprint.to_str("do_continue in_skip_block"))
            if do_continue:
                transformed_txt.append(line)
                continue
            # 2) Process slide.
            if _TRACE:
                _LOG.debug(" -> " + hprint.to_str("in_slide"))
            if line.startswith("* "):
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
        hdbg.dassert(
            not in_slide, "Found end of file while still parsing a slide"
        )
        # Join the transformed slides back together.
        transformed_txt = "\n".join(transformed_txt)
        return transformed_txt
