#!/usr/bin/env python

import logging

import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.download_utils as dshddut

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_detect_blocked_page
# #############################################################################


class Test_detect_blocked_page(hunitest.TestCase):
    """
    Test `download_utils.detect_blocked_page()`.
    """

    def helper(self, html_content: str, expected: str) -> None:
        """
        Test helper for `detect_blocked_page()`.

        :param html_content: HTML of the downloaded page
        :param expected: expected marker, "" if the page is not blocked
        """
        # Prepare inputs.
        html_content = hprint.dedent(html_content)
        # Run test.
        actual = dshddut.detect_blocked_page(html_content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a Cloudflare challenge page is detected.
        """
        # Prepare inputs.
        html_content = """
        <html><head><title>Just a moment...</title></head>
        <body><h1>Just a moment...</h1>
        <p>Enable JavaScript and cookies to continue</p></body></html>
        """
        # Prepare outputs.
        expected = "just a moment"
        # Run test.
        self.helper(html_content, expected)

    def test2(self) -> None:
        """
        Test an Elsevier page is detected even when most of the HTML is script.
        """
        # Prepare inputs.
        html_content = """
        <html><head><script>var junk = "%s";</script></head>
        <body><p>We have detected that you may be using an automated script
        or search engine our site does not support.</p></body></html>
        """ % ("x " * 5000)
        # Prepare outputs.
        expected = "you may be using an automated script"
        # Run test.
        self.helper(html_content, expected)

    def test3(self) -> None:
        """
        Test a marker in the text of a long article is not flagged.
        """
        # Prepare inputs.
        html_content = """
        <html><body><p>This article explains what a captcha is. %s</p>
        </body></html>
        """ % ("It has a lot of text. " * 200)
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(html_content, expected)

    def test4(self) -> None:
        """
        Test a short page without markers is not flagged.
        """
        # Prepare inputs.
        html_content = """
        <html><head><title>Hello</title></head>
        <body><p>Hello, world.</p></body></html>
        """
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(html_content, expected)

    def test5(self) -> None:
        """
        Test an empty page is not flagged.
        """
        # Prepare inputs.
        html_content = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(html_content, expected)

    def test6(self) -> None:
        """
        Test a marker that is only in a script is not flagged.
        """
        # Prepare inputs.
        html_content = """
        <html><body><p>Hello</p>
        <script>var msg = "Just a moment";</script></body></html>
        """
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(html_content, expected)


# #############################################################################
# Test_get_ssrn_id
# #############################################################################


class Test_get_ssrn_id(hunitest.TestCase):
    """
    Test `download_utils.get_ssrn_id()`.
    """

    def helper(self, input_arg: str, expected: str) -> None:
        """
        Test helper for `get_ssrn_id()`.

        :param input_arg: URL or DOI
        :param expected: expected SSRN id, "" if not an SSRN paper
        """
        # Run test.
        actual = dshddut.get_ssrn_id(input_arg)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test an SSRN abstract page URL.
        """
        # Prepare inputs.
        input_arg = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"
        # Prepare outputs.
        expected = "5277078"
        # Run test.
        self.helper(input_arg, expected)

    def test2(self) -> None:
        """
        Test an SSRN delivery URL.
        """
        # Prepare inputs.
        input_arg = (
            "https://papers.ssrn.com/sol3/Delivery.cfm/5277078.pdf"
            "?abstractid=5277078&mirid=1"
        )
        # Prepare outputs.
        expected = "5277078"
        # Run test.
        self.helper(input_arg, expected)

    def test3(self) -> None:
        """
        Test an SSRN short URL.
        """
        # Prepare inputs.
        input_arg = "https://www.ssrn.com/abstract=5277078"
        # Prepare outputs.
        expected = "5277078"
        # Run test.
        self.helper(input_arg, expected)

    def test4(self) -> None:
        """
        Test an SSRN DOI.
        """
        # Prepare inputs.
        input_arg = "10.2139/ssrn.5277078"
        # Prepare outputs.
        expected = "5277078"
        # Run test.
        self.helper(input_arg, expected)

    def test5(self) -> None:
        """
        Test a URL of another site with a similar query is not SSRN.
        """
        # Prepare inputs.
        input_arg = "https://example.com/papers.cfm?abstract_id=5277078"
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(input_arg, expected)

    def test6(self) -> None:
        """
        Test a DOI of another publisher is not SSRN.
        """
        # Prepare inputs.
        input_arg = "10.1038/nature12373"
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(input_arg, expected)


# #############################################################################
# Test_is_academic_paper_url
# #############################################################################


class Test_is_academic_paper_url(hunitest.TestCase):
    """
    Test `download_utils.is_academic_paper_url()`.
    """

    def helper(self, url: str, expected: bool) -> None:
        """
        Test helper for `is_academic_paper_url()`.

        :param url: URL, DOI, or path to classify
        :param expected: expected result
        """
        # Run test.
        actual = dshddut.is_academic_paper_url(url)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test an SSRN abstract page is an academic paper.
        """
        # Prepare inputs.
        url = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(url, expected)

    def test2(self) -> None:
        """
        Test an arXiv URL is an academic paper.
        """
        # Prepare inputs.
        url = "https://arxiv.org/abs/1706.03762"
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(url, expected)

    def test3(self) -> None:
        """
        Test a generic web page is not an academic paper.
        """
        # Prepare inputs.
        url = "https://example.com/some/article"
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(url, expected)
