import logging

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

import dev_scripts_helpers.documentation.check_links as dsdocheli

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_extract_urls_from_text
# #############################################################################


class Test_extract_urls_from_text(hunitest.TestCase):
    def test_markdown_links(self) -> None:
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
        # Run test.
        actual = dsdocheli._extract_urls_from_text(text)
        # Check outputs.
        expected = [
            "https://github.com/gpsaggese/umd_classes/tree/master",
            "https://docs.google.com/spreadsheets/d/1H_Ev1psuPpUrrRcmBrBb2chfurSo5rPcAdd6i2SIUTQ/edit?gid=0#gid=0",
        ]
        self.assert_equal(str(sorted(actual)), str(sorted(expected)))

    def test_standalone_urls(self) -> None:
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
        # Run test.
        actual = dsdocheli._extract_urls_from_text(text)
        # Check outputs.
        expected = [
            "https://github.com/gpsaggese/umd_classes/blob/master/class_project/DATA605/Spring2025/project_description.md",
            "http://example.com/path",
        ]
        self.assert_equal(str(sorted(actual)), str(sorted(expected)))

    def test_mixed_url_formats(self) -> None:
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
        # Run test.
        actual = dsdocheli._extract_urls_from_text(text)
        # Check outputs.
        expected = [
            "https://example.com/link1",
            "https://example.com/standalone",
            "http://test.org/path?param=value",
        ]
        self.assert_equal(str(sorted(actual)), str(sorted(expected)))

    def test_no_urls(self) -> None:
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
        # Run test.
        actual = dsdocheli._extract_urls_from_text(text)
        # Check outputs.
        expected = []
        self.assert_equal(str(actual), str(expected))

    def test_duplicate_urls(self) -> None:
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
        # Run test.
        actual = dsdocheli._extract_urls_from_text(text)
        # Check outputs.
        expected = ["https://example.com"]
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_check_url_reachable
# #############################################################################


class Test_check_url_reachable(hunitest.TestCase):
    def test_reachable_url(self) -> None:
        """
        Test checking a known reachable URL.
        """
        # Prepare inputs.
        url = "https://www.google.com"
        # Run test.
        actual = dsdocheli._check_url_reachable(url)
        # Check outputs.
        expected = True
        self.assert_equal(str(actual), str(expected))

    def test_unreachable_url(self) -> None:
        """
        Test checking a known unreachable URL.
        """
        # Prepare inputs.
        url = "https://this-domain-does-not-exist-12345.com"
        # Run test.
        actual = dsdocheli._check_url_reachable(url)
        # Check outputs.
        expected = False
        self.assert_equal(str(actual), str(expected))

    def test_invalid_url_format(self) -> None:
        """
        Test checking an invalid URL format.
        """
        # Prepare inputs.
        url = "not-a-valid-url"
        # Run test.
        actual = dsdocheli._check_url_reachable(url)
        # Check outputs.
        expected = False
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_check_links_in_file
# #############################################################################


class Test_check_links_in_file(hunitest.TestCase):
    def test_file_with_reachable_links(self) -> None:
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
        scratch_dir = self.get_scratch_space()
        test_file = scratch_dir + "/test_links.md"
        hio.to_file(test_file, test_content)
        # Run test.
        reachable_urls, broken_urls = dsdocheli._check_links_in_file(test_file)
        # Check outputs.
        self.assert_equal(str(len(reachable_urls)), str(2))
        self.assert_equal(str(len(broken_urls)), str(0))
        expected_urls = ["https://www.google.com", "https://www.github.com"]
        self.assert_equal(str(sorted(reachable_urls)), str(sorted(expected_urls)))

    def test_file_with_broken_links(self) -> None:
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
        scratch_dir = self.get_scratch_space()
        test_file = scratch_dir + "/test_broken_links.md"
        hio.to_file(test_file, test_content)
        # Run test.
        reachable_urls, broken_urls = dsdocheli._check_links_in_file(test_file)
        # Check outputs.
        self.assert_equal(str(len(reachable_urls)), str(0))
        self.assert_equal(str(len(broken_urls)), str(2))
        expected_broken = [
            "https://this-domain-absolutely-does-not-exist-12345.com",
            "https://another-non-existent-domain-98765.com"
        ]
        self.assert_equal(str(sorted(broken_urls)), str(sorted(expected_broken)))

    def test_file_with_no_links(self) -> None:
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
        scratch_dir = self.get_scratch_space()
        test_file = scratch_dir + "/test_no_links.md"
        hio.to_file(test_file, test_content)
        # Run test.
        reachable_urls, broken_urls = dsdocheli._check_links_in_file(test_file)
        # Check outputs.
        self.assert_equal(str(len(reachable_urls)), str(0))
        self.assert_equal(str(len(broken_urls)), str(0))

    def test_nonexistent_file(self) -> None:
        """
        Test that checking a nonexistent file raises an assertion error.
        """
        # Prepare inputs.
        nonexistent_file = "/path/that/does/not/exist.md"
        # Run test and check outputs.
        with self.assertRaises(AssertionError) as cm:
            dsdocheli._check_links_in_file(nonexistent_file)
        actual = str(cm.exception)
        self.assertIn("File", actual)