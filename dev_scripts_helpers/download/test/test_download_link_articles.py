#!/usr/bin/env python

import logging
import os

import pytest

pytest.importorskip("pandas")

import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.bookmark_utils as dshdbou
import dev_scripts_helpers.download.download_link_articles as dssdla

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__parse_row_idx
# #############################################################################


class Test__parse_row_idx(hunitest.TestCase):
    """
    Test `download_link_articles._parse_row_idx()`.
    """

    def helper(self, row_idx_str: str, num_rows: int, expected: list) -> None:
        """
        Test helper for `_parse_row_idx()`.

        :param row_idx_str: row index specification to parse
        :param num_rows: total number of rows available
        :param expected: expected list of 0-indexed row indices
        """
        # Run test.
        actual = dssdla._parse_row_idx(row_idx_str, num_rows)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test an empty string selects every row.
        """
        # Prepare inputs.
        row_idx_str = ""
        num_rows = 3
        # Prepare outputs.
        expected = [0, 1, 2]
        # Run test.
        self.helper(row_idx_str, num_rows, expected)

    def test2(self) -> None:
        """
        Test a single index selects only that row.
        """
        # Prepare inputs.
        row_idx_str = "1"
        num_rows = 3
        # Prepare outputs.
        expected = [1]
        # Run test.
        self.helper(row_idx_str, num_rows, expected)

    def test3(self) -> None:
        """
        Test a range selects rows with an exclusive end.
        """
        # Prepare inputs.
        row_idx_str = "0:2"
        num_rows = 3
        # Prepare outputs.
        expected = [0, 1]
        # Run test.
        self.helper(row_idx_str, num_rows, expected)

    def test4(self) -> None:
        """
        Test an out-of-range single index raises.
        """
        # Prepare inputs.
        row_idx_str = "5"
        num_rows = 3
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            dssdla._parse_row_idx(row_idx_str, num_rows)


# #############################################################################
# Test__load_rows_from_csv
# #############################################################################


class Test__load_rows_from_csv(hunitest.TestCase):
    """
    Test `download_link_articles._load_rows_from_csv()`.
    """

    def test1(self) -> None:
        """
        Test rows are loaded back unchanged from a valid local bookmarks CSV.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Article A",
                "Article_url": "https://example.com/a",
                "Hn_url": "https://news.ycombinator.com/item?id=1",
                "Timestamp": "2024-01-01 00:00:00",
                "Article_tag": "Open Source",
                "Article_cluster": "Dev tools",
            },
        ]
        scratch_dir = self.get_scratch_space()
        csv_path = os.path.join(scratch_dir, "bookmarks.csv")
        dshdbou.write_csv(csv_path, rows, fieldnames=list(rows[0].keys()))
        # Prepare outputs.
        expected = rows
        # Run test.
        actual = dssdla._load_rows_from_csv(csv_path)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test a CSV missing a required column raises.
        """
        # Prepare inputs.
        rows = [{"Title": "Article A"}]
        scratch_dir = self.get_scratch_space()
        csv_path = os.path.join(scratch_dir, "bookmarks.csv")
        dshdbou.write_csv(csv_path, rows, fieldnames=list(rows[0].keys()))
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            dssdla._load_rows_from_csv(csv_path)
