import logging
import os
import pprint
from typing import Any, List, Tuple

import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_format_compressed_markdown1
# #############################################################################


class Test_format_compressed_markdown1(hunitest.TestCase):

    def test1(self) -> None:
        # Prepare inputs.
        # ...
        # Evaluate the function.
        # ...
        # Check output.
        # ...
        pass

    def test2(self) -> None:
        """
        Test basic case with single first level bullet.
        """
        text = """
        Some text
        - First bullet
        More text"""
        expected = """
        Some text

        - First bullet
        More text"""
        self._format_and_compare_markdown(text, expected)

    def test3(self) -> None:
        """
        Test multiple first level bullets.
        """
        text = """
        - First bullet
        - Second bullet
        - Third bullet"""
        expected = """
        - First bullet

        - Second bullet

        - Third bullet"""
        self._format_and_compare_markdown(text, expected)

    def _format_and_compare_markdown(self, text: str, expected: str) -> None:
        text = hprint.dedent(text)
        expected = hprint.dedent(expected)
        #
        actual = hmarkdo.format_compressed_markdown(text)
        self.assert_equal(actual, expected)
