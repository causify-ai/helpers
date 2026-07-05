import logging
import os
from unittest import mock

import dev_scripts_helpers.documentation.check_links as dshdchli
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_is_image_or_email
# #############################################################################


class Test_is_image_or_email(hunitest.TestCase):
    """
    Test the _is_image_or_email function.
    """

    def _helper(self, url: str, expected: bool) -> None:
        """
        Test helper for `_is_image_or_email()`.

        :param url: URL to test
        :param expected: Expected result
        """
        # Run test.
        actual = dshdchli._is_image_or_email(url)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that PNG image files are correctly identified.
        """
        # Prepare inputs.
        url = "msml610/lectures_source/figures/UMD_Logo.png"
        # Prepare outputs.
        expected = True
        # Run test.
        self._helper(url, expected)

    def test2(self) -> None:
        """
        Test that JPG image files are correctly identified.
        """
        # Prepare inputs.
        url = (
            "data605/lectures_source/images/lecture_1/lec_1_slide_4_image_1.jpg"
        )
        # Prepare outputs.
        expected = True
        # Run test.
        self._helper(url, expected)

    def test3(self) -> None:
        """
        Test that JPEG image files are correctly identified.
        """
        # Prepare inputs.
        url = "path/to/image.jpeg"
        # Prepare outputs.
        expected = True
        # Run test.
        self._helper(url, expected)

    def test4(self) -> None:
        """
        Test that uppercase PNG extensions are correctly identified.
        """
        # Prepare inputs.
        url = "path/to/IMAGE.PNG"
        # Prepare outputs.
        expected = True
        # Run test.
        self._helper(url, expected)

    def test5(self) -> None:
        """
        Test that email addresses are correctly identified.
        """
        # Prepare inputs.
        url = "gsaggese@umd.edu"
        # Prepare outputs.
        expected = True
        # Run test.
        self._helper(url, expected)

    def test6(self) -> None:
        """
        Test that regular URLs are not identified as images or emails.
        """
        # Prepare inputs.
        url = "https://example.com"
        # Prepare outputs.
        expected = False
        # Run test.
        self._helper(url, expected)

    def test7(self) -> None:
        """
        Test that non-image files are not identified as images.
        """
        # Prepare inputs.
        url = "README.md"
        # Prepare outputs.
        expected = False
        # Run test.
        self._helper(url, expected)

    def test8(self) -> None:
        """
        Test that URLs with @ symbol but starting with http are not emails.
        """
        # Prepare inputs.
        url = "https://example.com/@username"
        # Prepare outputs.
        expected = False
        # Run test.
        self._helper(url, expected)


# #############################################################################
# Test_extract_urls_from_text
# #############################################################################


class Test_extract_urls_from_text(hunitest.TestCase):
    """
    Test the _extract_urls_from_text_with_original_line_numbers function.
    """

    def _helper(self, text: str, expected):
        """
        Test helper for `_extract_urls_from_text_with_original_line_numbers()`.

        :param text: Text to extract URLs from
        :param expected: Expected list of (url, line_number) tuples
        """
        # Prepare inputs.
        filtered_text = hmarkdo.remove_table_of_contents(text)
        # Run test.
        with mock.patch(
            "dev_scripts_helpers.documentation.check_links._get_git_repo_info",
            return_value=("https://github.com/causify-ai/helpers", "HEAD"),
        ):
            actual = dshdchli._extract_urls_from_text_with_original_line_numbers(
                text, filtered_text
            )
        # Check outputs.
        self.assert_equal(str(sorted(actual)), str(sorted(expected)))

    def test1(self) -> None:
        """
        Test extraction of URLs from Markdown-style links.
        """
        # Prepare inputs.
        text = """
        Here are some links:
        [GitHub repo](https://github.com/gpsaggese/umd_classes/tree/master)
        [Google Sheets](https://docs.google.com/spreadsheets/d/1H_Ev1psuPpUrrRcmBrBb2chfurSo5rPcAdd6i2SIUTQ/edit?gid=0#gid=0)
        """
        text = hprint.dedent(text)
        # Prepare outputs.
        expected = [
            ("https://github.com/gpsaggese/umd_classes/tree/master", 2),
            (
                "https://docs.google.com/spreadsheets/d/1H_Ev1psuPpUrrRcmBrBb2chfurSo5rPcAdd6i2SIUTQ/edit?gid=0#gid=0",
                3,
            ),
        ]
        # Run test.
        self._helper(text, expected)

    def test2(self) -> None:
        """
        Test extraction of standalone URLs.
        """
        # Prepare inputs.
        text = """
        Here is a plain URL:
        https://github.com/gpsaggese/umd_classes/blob/master/class_project/DATA605/Spring2025/project_description.md

        And another one:
        http://example.com/path
        """
        text = hprint.dedent(text)
        # Prepare outputs.
        expected = [
            (
                "https://github.com/causify-ai/helpers/blob/HEAD//github.com/gpsaggese/umd_classes/blob/master/class_project/DATA605/Spring2025/project_description.md",
                2,
            ),
            (
                "https://github.com/gpsaggese/umd_classes/blob/master/class_project/DATA605/Spring2025/project_description.md",
                2,
            ),
            ("http://example.com/path", 5),
        ]
        # Run test.
        self._helper(text, expected)

    def test3(self) -> None:
        """
        Test extraction of URLs in mixed formats.
        """
        # Prepare inputs.
        text = """
        Mixed format test:
        [Link 1](https://example.com/link1)
        https://example.com/standalone
        [Another link](http://test.org/path?param=value)
        """
        text = hprint.dedent(text)
        # Prepare outputs.
        expected = [
            ("https://example.com/link1", 2),
            ("https://example.com/standalone", 3),
            ("http://test.org/path?param=value", 4),
        ]
        # Run test.
        self._helper(text, expected)

    def test4(self) -> None:
        """
        Test extraction from text with no URLs.
        """
        # Prepare inputs.
        text = """
        This is just plain text with no URLs.
        Some words and sentences.
        No links here at all.
        """
        text = hprint.dedent(text)
        # Prepare outputs.
        expected = []
        # Run test.
        self._helper(text, expected)

    def test5(self) -> None:
        """
        Test that duplicate URLs are handled correctly.
        """
        # Prepare inputs.
        text = """
        [First link](https://example.com)
        https://example.com
        [Another reference](https://example.com)
        """
        text = hprint.dedent(text)
        # Prepare outputs.
        expected = [
            ("https://example.com", 1),
            ("https://github.com/causify-ai/helpers/blob/HEAD//example.com", 2),
        ]
        # Run test.
        self._helper(text, expected)

    def test6(self) -> None:
        """
        Test that PNG image files are filtered out from URL extraction.
        """
        # Prepare inputs.
        text = """
        Regular link: [GitHub](https://github.com)
        Image link: ![](msml610/lectures_source/figures/UMD_Logo.png)
        Another regular link: [Google](https://google.com)
        """
        text = hprint.dedent(text)
        # Prepare outputs.
        expected = [
            ("https://github.com", 1),
            ("https://google.com", 3),
        ]
        # Run test.
        self._helper(text, expected)

    def test7(self) -> None:
        """
        Test that JPG image files are filtered out from URL extraction.
        """
        # Prepare inputs.
        text = """
        Some text with regular link: [Example](https://example.com)
        Image: ![](data605/lectures_source/images/lecture_1/lec_1_slide_4_image_1.jpg)
        Another link: https://test.org
        """
        text = hprint.dedent(text)
        # Prepare outputs.
        expected = [
            ("https://example.com", 1),
            ("https://github.com/causify-ai/helpers/blob/HEAD//test.org", 3),
            ("https://test.org", 3),
        ]
        # Run test.
        self._helper(text, expected)

    def test8(self) -> None:
        """
        Test that email addresses are filtered out from URL extraction.
        """
        # Prepare inputs.
        text = """
        Contact: [xyz](gsaggese@umd.edu)
        Website: [Example](https://example.com)
        Email: user@domain.com
        """
        text = hprint.dedent(text)
        # Prepare outputs.
        expected = [
            ("https://example.com", 2),
        ]
        # Run test.
        self._helper(text, expected)

    def test9(self) -> None:
        """
        Test filtering of mixed images and emails along with regular URLs.
        """
        # Prepare inputs.
        text = """
        [Link](https://example.com/page)
        ![Image](path/to/image.png)
        ![Photo](photo.jpeg)
        [Contact](admin@site.org)
        https://valid-url.com
        """
        text = hprint.dedent(text)
        # Prepare outputs.
        expected = [
            ("https://example.com/page", 1),
            (
                "https://github.com/causify-ai/helpers/blob/HEAD//valid-url.com",
                5,
            ),
            ("https://valid-url.com", 5),
        ]
        # Run test.
        self._helper(text, expected)


# #############################################################################
# Test_check_url_reachable
# #############################################################################


# TODO(gp): Mock this.
class Test_check_url_reachable(hunitest.TestCase):
    """
    Test the _check_url_reachable function.
    """

    def _helper(self, url: str, expected: bool) -> None:
        """
        Test helper for `_check_url_reachable()`.

        :param url: URL to check for reachability
        :param expected: Expected result
        """
        # Run test.
        actual = dshdchli._check_url_reachable(url)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test checking a known reachable URL.
        """
        # Prepare inputs.
        url = "https://www.google.com"
        # Prepare outputs.
        expected = True
        # Run test.
        self._helper(url, expected)

    def test2(self) -> None:
        """
        Test checking a known unreachable URL.
        """
        # Prepare inputs.
        url = "https://this-domain-does-not-exist-12345.com"
        # Prepare outputs.
        expected = False
        # Run test.
        self._helper(url, expected)

    def test3(self) -> None:
        """
        Test checking an invalid URL format.
        """
        # Prepare inputs.
        url = "not-a-valid-url"
        # Prepare outputs.
        expected = False
        # Run test.
        self._helper(url, expected)


# #############################################################################
# Test_check_links_in_file
# #############################################################################


class Test_check_links_in_file(hunitest.TestCase):
    """
    Test the _check_links_in_file function.
    """

    # TODO(ai_gp): Add type hints
    def _helper(
        self, test_content: str, expected_reachable_urls, expected_broken_count
    ):
        """
        Test helper for `_check_links_in_file()`.

        :param test_content: Markdown content for test file
        :param expected_reachable_urls: Expected reachable URLs
        :param expected_broken_count: Expected number of broken URLs
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "test_links.md")
        hio.to_file(test_file, test_content)
        # Run test.
        with mock.patch(
            "dev_scripts_helpers.documentation.check_links._get_git_repo_info",
            return_value=("https://github.com/causify-ai/helpers", "HEAD"),
        ):
            reachable_urls, broken_urls = dshdchli._check_links_in_file(
                test_file
            )
        # Check outputs.
        self.assert_equal(
            str(len(reachable_urls)), str(len(expected_reachable_urls))
        )
        self.assert_equal(str(len(broken_urls)), str(expected_broken_count))
        self.assert_equal(
            str(sorted(reachable_urls)), str(sorted(expected_reachable_urls))
        )

    def test1(self) -> None:
        """
        Test checking links in a file with reachable URLs.
        """
        # Prepare inputs.
        test_content = """
        # Test Document

        Here are some links:
        [Google](https://www.google.com)
        https://www.github.com
        """
        test_content = hprint.dedent(test_content)
        # Prepare outputs.
        expected_urls = ["https://www.google.com", "https://www.github.com"]
        expected_broken_count = 1
        # Run test.
        self._helper(test_content, expected_urls, expected_broken_count)

    def test2(self) -> None:
        """
        Test checking links in a file with broken URLs.
        """
        # Prepare inputs.
        test_content = """
        # Test Document

        These links should be broken:
        [Broken](https://this-domain-absolutely-does-not-exist-12345.com)
        https://another-non-existent-domain-98765.com
        """
        test_content = hprint.dedent(test_content)
        # Prepare outputs.
        expected_reachable_urls = []
        expected_broken_count = 3
        # Run test.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "test_broken_links.md")
        hio.to_file(test_file, test_content)
        # Run test with mock.
        with mock.patch(
            "dev_scripts_helpers.documentation.check_links._get_git_repo_info",
            return_value=("https://github.com/causify-ai/helpers", "HEAD"),
        ):
            reachable_urls, broken_urls = dshdchli._check_links_in_file(
                test_file
            )
        # Check outputs.
        self.assert_equal(str(len(reachable_urls)), str(0))
        self.assert_equal(str(len(broken_urls)), str(3))
        expected_broken = [
            ("https://this-domain-absolutely-does-not-exist-12345.com", 4),
            ("https://another-non-existent-domain-98765.com", 5),
            (
                "https://github.com/causify-ai/helpers/blob/HEAD//another-non-existent-domain-98765.com",
                5,
            ),
        ]
        self.assert_equal(str(sorted(broken_urls)), str(sorted(expected_broken)))

    def test3(self) -> None:
        """
        Test checking links in a file with no URLs.
        """
        # Prepare inputs.
        test_content = """
        # Test Document

        This document has no links.
        Just plain text content.
        """
        test_content = hprint.dedent(test_content)
        # Prepare outputs.
        expected_urls = []
        expected_broken_count = 0
        # Run test.
        self._helper(test_content, expected_urls, expected_broken_count)

    def test4(self) -> None:
        """
        Test that checking a nonexistent file raises an assertion error.
        """
        # Prepare inputs.
        nonexistent_file = "/path/that/does/not/exist.md"
        # Prepare outputs.
        expected_error_substring = "File"
        # Run test and check outputs.
        with self.assertRaises(AssertionError) as cm:
            dshdchli._check_links_in_file(nonexistent_file)
        actual = str(cm.exception)
        self.assertIn(expected_error_substring, actual)
