#!/usr/bin/env python
# TODO(ai_gp): Add missing import logging and _LOG = logging.getLogger(__name__) to match template structure (testing.rules.md:## Unit Test Code Structure)

import pytest

pytest.importorskip("feedparser")
pytest.importorskip("fitz")

import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.download_to_md as dshddtomd


# #############################################################################
# Test_detect_input_type
# #############################################################################


class Test_detect_input_type(hunitest.TestCase):
    """
    Test `download_to_md.detect_input_type()`.
    """
    # TODO(ai_gp): Add edge case tests for empty input, single character, and large input (testing.rules.md:## What to Test)

    def helper(self, input_arg: str, expected: str) -> None:
        """
        Test helper for `detect_input_type()`.

        :param input_arg: URL to classify
        :param expected: expected input type
        """
        # Run test.
        actual = dshddtomd.detect_input_type(input_arg)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a Hacker News submission URL is detected as `hn`.
        """
        # Prepare inputs.
        input_arg = "https://news.ycombinator.com/item?id=12345"
        # Prepare outputs.
        expected = "hn"
        # Run test.
        self.helper(input_arg, expected)

    def test2(self) -> None:
        """
        Test an arXiv abstract URL is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "https://arxiv.org/abs/1706.03762"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        self.helper(input_arg, expected)

    def test3(self) -> None:
        """
        Test a DOI URL is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "https://doi.org/10.1038/nature12373"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        self.helper(input_arg, expected)

    def test4(self) -> None:
        """
        Test a bare DOI is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "10.1038/nature12373"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        self.helper(input_arg, expected)

    def test5(self) -> None:
        """
        Test a generic PDF URL is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "https://example.com/paper.pdf"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        self.helper(input_arg, expected)

    def test6(self) -> None:
        """
        Test a PDF URL with a query string is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "https://example.com/paper.pdf?download=1"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        self.helper(input_arg, expected)

    def test7(self) -> None:
        """
        Test a generic web page URL is detected as `html`.
        """
        # Prepare inputs.
        input_arg = "https://example.com/some/article"
        # Prepare outputs.
        expected = "html"
        # Run test.
        self.helper(input_arg, expected)
