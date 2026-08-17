#!/usr/bin/env python

import os
import unittest.mock as umock

import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.bookmark_utils as dshdbou


# #############################################################################
# Test_resolve_gsheet_url
# #############################################################################


class Test_resolve_gsheet_url(hunitest.TestCase):
    """
    Test `bookmark_utils.resolve_gsheet_url()`.
    """

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
        with umock.patch.dict(os.environ, {"LINKS_GSHEET": env_url}):
            actual = dshdbou.resolve_gsheet_url(url)
        # Check outputs.
        self.assert_equal(actual, expected)

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
        with umock.patch.dict(os.environ, {"LINKS_GSHEET": env_url}):
            actual = dshdbou.resolve_gsheet_url(url)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test an empty URL with no `LINKS_GSHEET` environment variable set
        raises.
        """
        # Prepare inputs.
        url = ""
        # Run test.
        with umock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LINKS_GSHEET", None)
            with self.assertRaises(AssertionError):
                dshdbou.resolve_gsheet_url(url)


# #############################################################################
# Test_download_from_gsheet
# #############################################################################


class Test_download_from_gsheet(hunitest.TestCase):
    """
    Test `bookmark_utils.download_from_gsheet()`.
    """

    def helper(self, rows: list, columns: list) -> str:
        """
        Run `download_from_gsheet()` against a mocked `hsystem.system()`
        call that writes `rows` to the output CSV, simulating what
        `from_gsheet.py` would produce.

        :param rows: rows the fake download writes to the output CSV
        :param columns: column names for the fake downloaded CSV
        :return: path to the downloaded CSV file
        """
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "gsheet.csv")
        url = "https://docs.google.com/spreadsheets/d/fake"

        def _fake_system(cmd: str, **kwargs) -> int:
            _ = cmd, kwargs
            dshdbou.write_csv(output_file, rows, fieldnames=columns)
            return 0

        # Run test.
        with umock.patch.object(
            dshdbou.hsystem, "system", side_effect=_fake_system
        ):
            actual = dshdbou.download_from_gsheet(url, output_file)
        return actual

    def test1(self) -> None:
        """
        Test the downloaded CSV path is returned and the file exists on
        disk.
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
        self.assertTrue(os.path.exists(actual))

    def test2(self) -> None:
        """
        Test an empty downloaded CSV (header only, no data rows) does not
        raise while building the row preview.
        """
        # Prepare inputs.
        columns = ["Title", "Url"]
        rows: list = []
        # Prepare outputs.
        expected = os.path.join(self.get_scratch_space(), "gsheet.csv")
        # Run test.
        actual = self.helper(rows, columns)
        # Check outputs.
        self.assert_equal(actual, expected)
