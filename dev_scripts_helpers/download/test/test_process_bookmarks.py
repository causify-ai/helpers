#!/usr/bin/env python

import logging
import os
import unittest.mock as umock
from typing import Dict, List, Tuple

import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.bookmark_utils as dshdbou
import dev_scripts_helpers.download.process_bookmarks as dshdprbo

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__process_row
# #############################################################################


class Test__process_row(hunitest.TestCase):
    """
    Test `process_bookmarks._process_row()`'s handling of a row whose
    `Hn_url` is not a real Hacker News item URL.
    """

    def helper(
        self, hn_url: str, *, dry_run: bool = False
    ) -> Tuple[str, Dict[str, str]]:
        """
        Run `_process_row()` on a minimal row with the given `Hn_url`.

        The row is never actually downloaded by these tests (either it's
        skipped, or `dry_run=True` short-circuits before any download), so
        `script`/`output_dir`/`gdrive_dir` are unused placeholders.

        :param hn_url: value to put in the row's `Hn_url` column
        :param dry_run: `--dry_run` value to pass through
        :return: `(status, row)`, where `row` is the (possibly mutated) row
            dict passed to `_process_row()`
        """
        row = {"Title": "Some title", "Hn_url": hn_url, "Done": ""}
        status, row_stats = dshdprbo._process_row(
            row,
            script="unused",
            output_dir="unused",
            gdrive_dir="unused",
            no_incremental=False,
            no_save_to_google_drive=False,
            dry_run=dry_run,
        )
        self.assertIsNone(row_stats)
        return status, row

    def test1(self) -> None:
        """
        Test a plain article URL (not a HN item URL) is marked skipped.
        """
        # Prepare inputs.
        hn_url = "https://example.com/some-article"
        # Prepare outputs.
        expected_status = "skipped"
        expected_done = "skipped"
        # Run test.
        status, row = self.helper(hn_url)
        # Check outputs.
        self.assertEqual(status, expected_status)
        self.assertEqual(row["Done"], expected_done)

    def test2(self) -> None:
        """
        Test an empty `Hn_url` is marked skipped.
        """
        # Prepare inputs.
        hn_url = ""
        # Prepare outputs.
        expected_status = "skipped"
        expected_done = "skipped"
        # Run test.
        status, row = self.helper(hn_url)
        # Check outputs.
        self.assertEqual(status, expected_status)
        self.assertEqual(row["Done"], expected_done)

    def test3(self) -> None:
        """
        Test a valid HN item URL is not skipped.
        """
        # Prepare inputs.
        hn_url = "https://news.ycombinator.com/item?id=12345"
        # Prepare outputs. `dry_run=True` short-circuits before any
        # download, so the row is neither skipped nor marked Done.
        expected_status = "dry_run"
        expected_done = ""
        # Run test.
        status, row = self.helper(hn_url, dry_run=True)
        # Check outputs.
        self.assertEqual(status, expected_status)
        self.assertEqual(row["Done"], expected_done)

    def test4(self) -> None:
        """
        Test `--dry_run` detects a non-HN `Hn_url` as skippable but does
        not mutate the row's `Done` (dry_run must not mutate the CSV).
        """
        # Prepare inputs.
        hn_url = "https://example.com/some-article"
        # Prepare outputs.
        expected_status = "skipped"
        expected_done = ""
        # Run test.
        status, row = self.helper(hn_url, dry_run=True)
        # Check outputs.
        self.assertEqual(status, expected_status)
        self.assertEqual(row["Done"], expected_done)


# #############################################################################
# Test_process_bookmarks_py
# #############################################################################


class Test_process_bookmarks_py(hunitest.TestCase):
    """
    End-to-end tests for the `process_bookmarks.py` executable's handling
    of rows with a non-HN `Hn_url`.
    """

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `dshdprbo._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `umock.patch("sys.argv", ...)`
        """
        parser = dshdprbo._parse()
        with umock.patch("sys.argv", argv):
            dshdprbo._main(parser)

    def test1(self) -> None:
        """
        Test a row with a non-HN `Hn_url` is marked `Done=skipped` and the
        CSV on disk is updated after a single run, without downloading
        anything.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_csv = os.path.join(scratch_dir, "bookmarks.csv")
        columns = ["Title", "Hn_url", "Article_url", "Timestamp", "Done"]
        rows = [
            {
                "Title": "Plain article",
                "Hn_url": "https://example.com/article",
                "Article_url": "",
                "Timestamp": "2024-01-01 00:00:00",
                "Done": "",
            },
        ]
        dshdbou.write_csv(input_csv, rows, fieldnames=columns)
        argv = [
            "process_bookmarks.py",
            "--input",
            input_csv,
            "--output_dir",
            os.path.join(scratch_dir, "output"),
            "--gdrive_dir",
            os.path.join(scratch_dir, "gdrive"),
            "--limit",
            "10",
        ]
        # Prepare outputs.
        expected_rows = [{**rows[0], "Done": "skipped"}]
        # Run test.
        self._run_main(argv)
        actual_rows = dshdbou.read_csv(input_csv)
        # Check outputs.
        self.assert_equal(str(actual_rows), str(expected_rows))

    def test2(self) -> None:
        """
        Test a previously-skipped row is not re-selected (and so doesn't
        occupy a `--limit` slot) on a subsequent run.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_csv = os.path.join(scratch_dir, "bookmarks.csv")
        columns = ["Title", "Hn_url", "Article_url", "Timestamp", "Done"]
        rows = [
            {
                "Title": "Plain article",
                "Hn_url": "https://example.com/article",
                "Article_url": "",
                "Timestamp": "2024-01-01 00:00:00",
                "Done": "",
            },
        ]
        dshdbou.write_csv(input_csv, rows, fieldnames=columns)
        argv = [
            "process_bookmarks.py",
            "--input",
            input_csv,
            "--output_dir",
            os.path.join(scratch_dir, "output"),
            "--gdrive_dir",
            os.path.join(scratch_dir, "gdrive"),
            "--limit",
            "10",
        ]
        # Run test: the first run marks the row skipped.
        self._run_main(argv)
        # Prepare outputs: nothing is left to select on a later run.
        expected_selected_rows: list = []
        # Run test: a later row-selection pass picks up 0 rows.
        actual_selected_rows = dshdprbo._select_rows(
            dshdbou.read_csv(input_csv), no_incremental=False, limit=10
        )
        # Check outputs.
        self.assertEqual(actual_selected_rows, expected_selected_rows)
