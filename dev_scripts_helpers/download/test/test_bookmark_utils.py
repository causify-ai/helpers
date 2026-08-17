#!/usr/bin/env python

import logging
import os
import unittest.mock as umock

import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.download.bookmark_utils as dshdbou

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_resolve_gsheet_url
# #############################################################################


class Test_resolve_gsheet_url(hunitest.TestCase):
    """
    Test `bookmark_utils.resolve_gsheet_url()`.
    """

    def helper(self, url: str, env_url: str, expected: str) -> None:
        """
        Test helper for `resolve_gsheet_url()`.

        :param url: URL passed via the `--url` CLI arg (empty string if
            not passed)
        :param env_url: value to set for the `LINKS_GSHEET` environment
            variable
        :param expected: expected resolved URL
        """
        # Run test.
        with umock.patch.dict(os.environ, {"LINKS_GSHEET": env_url}):
            actual = dshdbou.resolve_gsheet_url(url)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test an explicit URL is returned unchanged, taking precedence over
        the `LINKS_GSHEET` environment variable.
        """
        # Prepare inputs.
        url = "https://docs.google.com/spreadsheets/d/explicit"
        env_url = "https://docs.google.com/spreadsheets/d/env"
        # Prepare outputs.
        expected = url
        # Run test.
        self.helper(url, env_url, expected)

    def test2(self) -> None:
        """
        Test an empty URL falls back to the `LINKS_GSHEET` environment
        variable.
        """
        # Prepare inputs.
        url = ""
        env_url = "https://docs.google.com/spreadsheets/d/env"
        # Prepare outputs.
        expected = env_url
        # Run test.
        self.helper(url, env_url, expected)

    def test3(self) -> None:
        """
        Test an empty URL with no `LINKS_GSHEET` environment variable set
        raises.
        """
        # Prepare inputs.
        url = ""
        # Run test and check outputs.
        with umock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LINKS_GSHEET", None)
            with self.assertRaises(AssertionError):
                dshdbou.resolve_gsheet_url(url)

    def test4(self) -> None:
        """
        Test a very long URL is returned unchanged.
        """
        # Prepare inputs.
        # Use a long URL (5000 chars) to exercise the large-input edge case.
        url = "https://docs.google.com/spreadsheets/d/" + "a" * 5000
        env_url = "https://docs.google.com/spreadsheets/d/env"
        # Prepare outputs.
        expected = url
        # Run test.
        self.helper(url, env_url, expected)


# #############################################################################
# Test_download_from_gsheet
# #############################################################################


class Test_download_from_gsheet(hunitest.TestCase):
    """
    Test `bookmark_utils.download_from_gsheet()`.
    """

    def helper(self, rows: list, columns: list) -> str:
        """
        Run `download_from_gsheet()` with `hsystem.system()` mocked via
        `capture_sys_calls()`.

        Since the underlying `hsystem.system()` call is mocked (i.e., the
        real `from_gsheet.py` command never runs), `rows` are pre-written
        to the output CSV path to simulate what that command would have
        produced.

        :param rows: rows to pre-write to the output CSV, simulating what
            the download command would produce
        :param columns: column names for the fake downloaded CSV
        :return: path to the downloaded CSV file
        """
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "gsheet.csv")
        url = "https://docs.google.com/spreadsheets/d/fake"
        dshdbou.write_csv(output_file, rows, fieldnames=columns)
        # Run test.
        with hunteuti.capture_sys_calls():
            actual = dshdbou.download_from_gsheet(url, output_file)
        return actual

    def test1(self) -> None:
        """
        Test the downloaded CSV path is returned correctly.
        """
        # Prepare inputs.
        columns = ["Title", "Url"]
        rows = [{"Title": "A", "Url": "https://example.com"}]
        # Prepare outputs.
        expected = os.path.join(self.get_scratch_space(), "gsheet.csv")
        # Run test.
        actual = self.helper(rows, columns)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that download_from_gsheet creates a file on disk.
        """
        # Prepare inputs.
        columns = ["Title", "Url"]
        rows = [{"Title": "A", "Url": "https://example.com"}]
        # Run test.
        actual = self.helper(rows, columns)
        # Check outputs.
        self.assertTrue(os.path.exists(actual), "Downloaded file should exist on disk")

    def test3(self) -> None:
        """
        Test an empty downloaded CSV (header only, no data rows) does not
        raise while building the row preview.
        """
        # Prepare inputs.
        columns = ["Title", "Url"]
        rows: list = []
        # Run test - should not raise
        actual = self.helper(rows, columns)
        # Check outputs.
        self.assertTrue(os.path.exists(actual), "File should exist even with empty CSV")

    def test4(self) -> None:
        """
        Test downloading a CSV with a large number of rows.
        """
        # Prepare inputs.
        columns = ["Title", "Url"]
        # Use a large number of rows (5000) to exercise the large-input
        # edge case without slowing down the test suite.
        num_rows = 5000
        rows = [
            {"Title": f"Title {i}", "Url": f"https://example.com/{i}"}
            for i in range(num_rows)
        ]
        # Prepare outputs.
        expected = os.path.join(self.get_scratch_space(), "gsheet.csv")
        # Run test.
        actual = self.helper(rows, columns)
        # Check outputs.
        self.assert_equal(actual, expected)
        actual_rows = dshdbou.read_csv(actual)
        self.assertEqual(len(actual_rows), num_rows)
