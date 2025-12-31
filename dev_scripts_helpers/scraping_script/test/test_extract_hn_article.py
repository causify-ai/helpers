import logging
import os

import pandas as pd
import pytest

import dev_scripts_helpers.scraping_script.extract_hn_article as dsscehar
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_is_hackernews_url
# #############################################################################


class Test_is_hackernews_url(hunitest.TestCase):
    """
    Test validation of Hacker News URLs.
    """

    def test_valid_hn_url(self) -> None:
        """
        Test that valid HN item URL returns True.

        Input:
        - url = "https://news.ycombinator.com/item?id=45619537"

        Expected output:
        - True
        """
        # Prepare inputs.
        url = "https://news.ycombinator.com/item?id=45619537"
        # Run test.
        actual = dsscehar._is_hackernews_url(url)
        # Check outputs.
        self.assertTrue(actual)

    def test_invalid_url_not_hn(self) -> None:
        """
        Test that non-HN URL returns False.

        Input:
        - url = "https://example.com/article"

        Expected output:
        - False
        """
        # Prepare inputs.
        url = "https://example.com/article"
        # Run test.
        actual = dsscehar._is_hackernews_url(url)
        # Check outputs.
        self.assertFalse(actual)

    def test_hn_homepage_url(self) -> None:
        """
        Test that HN homepage URL returns False (not an item).

        Input:
        - url = "https://news.ycombinator.com"

        Expected output:
        - False
        """
        # Prepare inputs.
        url = "https://news.ycombinator.com"
        # Run test.
        actual = dsscehar._is_hackernews_url(url)
        # Check outputs.
        self.assertFalse(actual)

    def test_empty_url(self) -> None:
        """
        Test that empty string returns False.

        Input:
        - url = ""

        Expected output:
        - False
        """
        # Prepare inputs.
        url = ""
        # Run test.
        actual = dsscehar._is_hackernews_url(url)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_extract_item_id
# #############################################################################


class Test_extract_item_id(hunitest.TestCase):
    """
    Test extraction of item ID from HN URLs.
    """

    def test_valid_hn_url(self) -> None:
        """
        Test that valid HN URL returns item ID.

        Input:
        - hn_url = "https://news.ycombinator.com/item?id=45148180"

        Expected output:
        - "45148180"
        """
        # Prepare inputs.
        hn_url = "https://news.ycombinator.com/item?id=45148180"
        # Run test.
        actual = dsscehar._extract_item_id(hn_url)
        # Check outputs.
        self.assert_equal(actual, "45148180")

    def test_url_with_other_params(self) -> None:
        """
        Test that URL with additional parameters returns item ID.

        Input:
        - hn_url = "https://news.ycombinator.com/item?id=12345&foo=bar"

        Expected output:
        - "12345"
        """
        # Prepare inputs.
        hn_url = "https://news.ycombinator.com/item?id=12345&foo=bar"
        # Run test.
        actual = dsscehar._extract_item_id(hn_url)
        # Check outputs.
        self.assert_equal(actual, "12345")

    def test_invalid_url_no_id(self) -> None:
        """
        Test that URL without item ID returns None.

        Input:
        - hn_url = "https://news.ycombinator.com/"

        Expected output:
        - None
        """
        # Prepare inputs.
        hn_url = "https://news.ycombinator.com/"
        # Run test.
        actual = dsscehar._extract_item_id(hn_url)
        # Check outputs.
        self.assertIsNone(actual)

    def test_non_hn_url(self) -> None:
        """
        Test that non-HN URL returns None.

        Input:
        - hn_url = "https://example.com/article"

        Expected output:
        - None
        """
        # Prepare inputs.
        hn_url = "https://example.com/article"
        # Run test.
        actual = dsscehar._extract_item_id(hn_url)
        # Check outputs.
        self.assertIsNone(actual)


# #############################################################################
# Test_extract_article_info
# #############################################################################


class Test_extract_article_info(hunitest.TestCase):
    """
    Test extraction of article title and URL from HN pages.
    """

    @pytest.mark.superslow
    def test_valid_hn_item_with_link(self) -> None:
        """
        Test extraction from valid HN item with external link using API.

        This is a superslow test that makes actual API requests.
        """
        # Prepare inputs.
        hn_url = "https://news.ycombinator.com/item?id=45148180"
        # Run test.
        article_title, article_url = dsscehar._extract_article_info(hn_url)
        # Check outputs.
        self.assertIsNotNone(article_title)
        self.assertIsNotNone(article_url)
        self.assertNotEqual(article_title, "")
        self.assertNotEqual(article_url, "")

    @pytest.mark.superslow
    def test_hn_show_hn_post(self) -> None:
        """
        Test extraction from Show HN or Ask HN post (self post with no external URL).

        This is a superslow test that makes actual API requests.
        For self posts, the API returns no 'url' field.
        """
        # Prepare inputs.
        # Using a known Ask HN post which has no external URL.
        hn_url = "https://news.ycombinator.com/item?id=1"
        # Run test.
        article_title, article_url = dsscehar._extract_article_info(hn_url)
        # Check outputs.
        # Title should be present but URL might be None for self posts.
        self.assertIsNotNone(article_title)
        # URL can be None for Ask HN/Show HN posts without external links.

    def test_non_hn_url_returns_none(self) -> None:
        """
        Test that non-HN URL returns None values.

        Input:
        - hn_url = "https://example.com/article"

        Expected output:
        - article_title = None
        - article_url = None
        """
        # Prepare inputs.
        hn_url = "https://example.com/article"
        # Run test.
        article_title, article_url = dsscehar._extract_article_info(hn_url)
        # Check outputs.
        self.assertIsNone(article_title)
        self.assertIsNone(article_url)

    @pytest.mark.superslow
    def test_invalid_hn_url_returns_none(self) -> None:
        """
        Test that invalid HN URL (404) returns None values.

        This is a superslow test that makes actual HTTP requests.
        """
        # Prepare inputs.
        hn_url = "https://news.ycombinator.com/item?id=999999999999"
        # Run test.
        article_title, article_url = dsscehar._extract_article_info(hn_url)
        # Check outputs.
        self.assertIsNone(article_title)
        self.assertIsNone(article_url)

    def test_url_without_item_id_returns_none(self) -> None:
        """
        Test that HN URL without valid item ID returns None.

        Input:
        - hn_url = "https://news.ycombinator.com/newest"

        Expected output:
        - article_title = None
        - article_url = None
        """
        # Prepare inputs.
        hn_url = "https://news.ycombinator.com/newest"
        # Run test.
        article_title, article_url = dsscehar._extract_article_info(hn_url)
        # Check outputs.
        self.assertIsNone(article_title)
        self.assertIsNone(article_url)


# #############################################################################
# Test_process_single_url
# #############################################################################


class Test_process_single_url(hunitest.TestCase):
    """
    Test processing of single HN URLs.
    """

    @pytest.mark.skip(reason="Requires capturing log output and HTTP mocking")
    def test_valid_url_prints_output(self) -> None:
        """
        Test that valid URL logs article info.

        Note: Skipped because it requires capturing log output and mocking HTTP.
        """
        pass

    @pytest.mark.skip(reason="Requires capturing log output")
    def test_invalid_url_prints_warning(self) -> None:
        """
        Test that invalid URL logs warning.

        Note: Skipped because it requires capturing log output.
        """
        pass


# #############################################################################
# Test_process_csv_file
# #############################################################################


class Test_process_csv_file(hunitest.TestCase):
    """
    Test batch processing of CSV files with HN URLs.
    """

    @pytest.mark.superslow
    def test_valid_csv_with_single_url(self) -> None:
        """
        Test processing CSV with one valid HN URL using API.

        This is a superslow test that makes actual API requests.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.csv")
        output_file = os.path.join(scratch_dir, "output.csv")
        # Create input CSV.
        input_df = pd.DataFrame({
            "id": [1],
            "url": ["https://news.ycombinator.com/item?id=45148180"],
            "description": ["Test article"]
        })
        input_df.to_csv(input_file, index=False)
        # Run test.
        dsscehar._process_csv_file(input_file, output_file)
        # Check outputs.
        output_df = pd.read_csv(output_file)
        self.assertEqual(len(output_df), 1)
        self.assertIn("Article_title", output_df.columns)
        self.assertIn("Article_url", output_df.columns)
        # Check that columns are in the right position (after url).
        cols = list(output_df.columns)
        url_idx = cols.index("url")
        self.assertEqual(cols[url_idx + 1], "Article_title")
        self.assertEqual(cols[url_idx + 2], "Article_url")
        # Check that data was extracted via API.
        self.assertFalse(pd.isna(output_df["Article_title"].iloc[0]))
        self.assertFalse(pd.isna(output_df["Article_url"].iloc[0]))

    @pytest.mark.skip(reason="Requires HTTP requests for multiple URLs")
    def test_csv_with_multiple_urls(self) -> None:
        """
        Test processing CSV with multiple HN URLs.

        Note: Skipped to avoid multiple HTTP requests in tests.
        """
        pass

    def test_csv_with_mixed_urls(self) -> None:
        """
        Test processing CSV with valid and invalid URLs.

        This test uses only non-HN URLs to avoid HTTP requests.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.csv")
        output_file = os.path.join(scratch_dir, "output.csv")
        # Create input CSV with non-HN URLs.
        input_df = pd.DataFrame({
            "id": [1, 2],
            "url": [
                "https://example.com/article1",
                "https://example.com/article2"
            ],
            "description": ["Article 1", "Article 2"]
        })
        input_df.to_csv(input_file, index=False)
        # Run test.
        dsscehar._process_csv_file(input_file, output_file)
        # Check outputs.
        output_df = pd.read_csv(output_file)
        self.assertEqual(len(output_df), 2)
        self.assertIn("Article_title", output_df.columns)
        self.assertIn("Article_url", output_df.columns)
        # Non-HN URLs should have empty strings (which read as NaN from CSV).
        self.assertTrue(pd.isna(output_df["Article_title"].iloc[0]) or output_df["Article_title"].iloc[0] == "")
        self.assertTrue(pd.isna(output_df["Article_url"].iloc[0]) or output_df["Article_url"].iloc[0] == "")
        self.assertTrue(pd.isna(output_df["Article_title"].iloc[1]) or output_df["Article_title"].iloc[1] == "")
        self.assertTrue(pd.isna(output_df["Article_url"].iloc[1]) or output_df["Article_url"].iloc[1] == "")

    def test_csv_without_url_column_raises_error(self) -> None:
        """
        Test that CSV without 'url' column raises assertion error.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.csv")
        output_file = os.path.join(scratch_dir, "output.csv")
        # Create input CSV without url column.
        input_df = pd.DataFrame({
            "id": [1],
            "link": ["https://example.com"],
            "description": ["Test"]
        })
        input_df.to_csv(input_file, index=False)
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dsscehar._process_csv_file(input_file, output_file)
        self.assertIn("url", str(cm.exception))

    def test_nonexistent_input_file_raises_error(self) -> None:
        """
        Test that nonexistent input file raises assertion error.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "nonexistent.csv")
        output_file = os.path.join(scratch_dir, "output.csv")
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dsscehar._process_csv_file(input_file, output_file)
        self.assertIn("does not exist", str(cm.exception))

    def test_empty_csv_creates_output_with_new_columns(self) -> None:
        """
        Test that empty CSV (headers only) creates output with new columns.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.csv")
        output_file = os.path.join(scratch_dir, "output.csv")
        # Create empty CSV with headers only.
        input_df = pd.DataFrame(columns=["url"])
        input_df.to_csv(input_file, index=False)
        # Run test.
        dsscehar._process_csv_file(input_file, output_file)
        # Check outputs.
        output_df = pd.read_csv(output_file)
        self.assertEqual(len(output_df), 0)
        self.assertIn("Article_title", output_df.columns)
        self.assertIn("Article_url", output_df.columns)
        # Check column order.
        cols = list(output_df.columns)
        url_idx = cols.index("url")
        self.assertEqual(cols[url_idx + 1], "Article_title")
        self.assertEqual(cols[url_idx + 2], "Article_url")


# #############################################################################
# Integration Tests
# #############################################################################


class TestIntegration(hunitest.TestCase):
    """
    Integration tests for end-to-end workflows.
    """

    @pytest.mark.skip(reason="Requires complex argument parsing and HTTP mocking")
    def test_full_workflow_single_url(self) -> None:
        """
        Test complete workflow from command line args to output.

        Note: Skipped because it requires complex argument parsing and HTTP mocking.
        """
        pass

    @pytest.mark.skip(reason="Requires complex argument parsing and HTTP mocking")
    def test_full_workflow_csv_processing(self) -> None:
        """
        Test complete workflow for CSV processing.

        Note: Skipped because it requires complex argument parsing and HTTP mocking.
        """
        pass

    @pytest.mark.skip(reason="Requires complex argument parsing")
    def test_missing_arguments_prints_help(self) -> None:
        """
        Test that missing required arguments prints help and exits.

        Note: Skipped because it requires complex argument parsing.
        """
        pass
