#!/usr/bin/env python

import logging
import os
import unittest.mock as umock
from typing import Dict, List, Tuple

import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.bookmark_utils as dshdbou
import dev_scripts_helpers.download.process_bookmarks as dshdprbo

_LOG = logging.getLogger(__name__)


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
            "--dest_dir",
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
            "--dest_dir",
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
        self.assert_equal(str(actual_selected_rows), str(expected_selected_rows))

    def test3(self) -> None:
        """
        Test `--limit 0` runs reconciliation only: a `Done=yes` row whose
        merged file is cached locally but missing from the destination
        gets copied there, without processing any new rows.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_csv = os.path.join(scratch_dir, "bookmarks.csv")
        output_dir = os.path.join(scratch_dir, "output")
        dest_dir = os.path.join(scratch_dir, "dest")
        columns = ["Title", "Hn_url", "Article_url", "Timestamp", "Done"]
        rows = [
            {
                "Title": "Already processed",
                "Hn_url": "https://news.ycombinator.com/item?id=1",
                "Article_url": "",
                "Timestamp": "2024-01-01 00:00:00",
                "Done": "yes",
            },
        ]
        dshdbou.write_csv(input_csv, rows, fieldnames=columns)
        merged_filename = "2024-01-01.hn_1.title.summary.md"
        hio.create_dir(output_dir, incremental=True)
        hio.to_file(
            os.path.join(output_dir, merged_filename), "cached content"
        )
        argv = [
            "process_bookmarks.py",
            "--input",
            input_csv,
            "--output_dir",
            output_dir,
            "--dest_type",
            "obsidian",
            "--dest_dir",
            dest_dir,
            "--limit",
            "0",
        ]
        # Prepare outputs.
        expected_content = "cached content"
        # Run test.
        self._run_main(argv)
        actual_content = hio.from_file(
            os.path.join(dest_dir, merged_filename)
        )
        # Check outputs.
        self.assert_equal(actual_content, expected_content)

    def test4(self) -> None:
        """
        Test `--dest_type none` skips reconciliation without creating any
        destination dir (and without requiring `--dest_dir`).
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_csv = os.path.join(scratch_dir, "bookmarks.csv")
        output_dir = os.path.join(scratch_dir, "output")
        columns = ["Title", "Hn_url", "Article_url", "Timestamp", "Done"]
        rows = [
            {
                "Title": "Already processed",
                "Hn_url": "https://news.ycombinator.com/item?id=1",
                "Article_url": "",
                "Timestamp": "2024-01-01 00:00:00",
                "Done": "yes",
            },
        ]
        dshdbou.write_csv(input_csv, rows, fieldnames=columns)
        merged_filename = "2024-01-01.hn_1.title.summary.md"
        hio.create_dir(output_dir, incremental=True)
        hio.to_file(
            os.path.join(output_dir, merged_filename), "cached content"
        )
        argv = [
            "process_bookmarks.py",
            "--input",
            input_csv,
            "--output_dir",
            output_dir,
            "--dest_type",
            "none",
            "--limit",
            "0",
        ]
        # Run test and check outputs: should complete without error despite no --dest_dir.
        self._run_main(argv)

    def test5(self) -> None:
        """
        Test a valid HN item URL is selected for processing (happy path).
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_csv = os.path.join(scratch_dir, "bookmarks.csv")
        columns = ["Title", "Hn_url", "Article_url", "Timestamp", "Done"]
        rows = [
            {
                "Title": "Valid HN item",
                "Hn_url": "https://news.ycombinator.com/item?id=12345",
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
            "--dest_dir",
            os.path.join(scratch_dir, "gdrive"),
            "--limit",
            "1",
            "--dry_run",
        ]
        # Prepare outputs: valid HN item should not be marked skipped.
        # Run test.
        self._run_main(argv)
        actual_rows = dshdbou.read_csv(input_csv)
        # Check outputs: the row should NOT be marked "skipped".
        self.assertNotEqual(actual_rows[0]["Done"], "skipped")


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
        `script`/`output_dir` are unused placeholders.

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
            model="",
            no_incremental=False,
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
        self.assert_equal(status, expected_status)
        self.assert_equal(row["Done"], expected_done)

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
        self.assert_equal(status, expected_status)
        self.assert_equal(row["Done"], expected_done)

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
        self.assert_equal(status, expected_status)
        self.assert_equal(row["Done"], expected_done)

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
        self.assert_equal(status, expected_status)
        self.assert_equal(row["Done"], expected_done)


# #############################################################################
# Test__resolve_dest_dir
# #############################################################################


class Test__resolve_dest_dir(hunitest.TestCase):
    """
    Test `process_bookmarks._resolve_dest_dir()`.
    """

    def helper(self, dest_type: str, dest_dir: str, expected: str) -> None:
        """
        Run `_resolve_dest_dir()` and check the output.

        :param dest_type: `--dest_type` value
        :param dest_dir: `--dest_dir` value
        :param expected: expected resolved dir, or `"None"` for
            `dest_type="none"`
        """
        # Run test.
        actual = dshdprbo._resolve_dest_dir(dest_type, dest_dir)
        # Check outputs.
        self.assert_equal(str(actual), expected)

    def test1(self) -> None:
        """
        Test `dest_type="gdrive"` with no override resolves to the
        built-in default gdrive dir.
        """
        # Prepare inputs.
        dest_type = "gdrive"
        dest_dir = ""
        # Prepare outputs.
        expected = dshdprbo._DEFAULT_GDRIVE_DIR
        # Run test.
        self.helper(dest_type, dest_dir, expected)

    def test2(self) -> None:
        """
        Test `dest_type="obsidian"` with no override resolves to the
        built-in default Obsidian dir.
        """
        # Prepare inputs.
        dest_type = "obsidian"
        dest_dir = ""
        # Prepare outputs.
        expected = dshdprbo._DEFAULT_OBSIDIAN_DIR
        # Run test.
        self.helper(dest_type, dest_dir, expected)

    def test3(self) -> None:
        """
        Test `dest_type="none"` always resolves to None, ignoring
        `dest_dir`.
        """
        # Prepare inputs.
        dest_type = "none"
        dest_dir = "/some/override"
        # Prepare outputs.
        expected = "None"
        # Run test.
        self.helper(dest_type, dest_dir, expected)

    def test4(self) -> None:
        """
        Test `--dest_dir` overrides the built-in default for a real
        `--dest_type`.
        """
        # Prepare inputs.
        dest_type = "gdrive"
        dest_dir = "/custom/path"
        # Prepare outputs.
        expected = "/custom/path"
        # Run test.
        self.helper(dest_type, dest_dir, expected)


# #############################################################################
# Test__find_cached_merged_summary
# #############################################################################


class Test__find_cached_merged_summary(hunitest.TestCase):
    """
    Test `process_bookmarks._find_cached_merged_summary()`.
    """

    def test1(self) -> None:
        """
        Test the merged summary file is found, and per-item summary files
        sharing the same `item_id` (which also end in `.summary.md`) are
        excluded.
        """
        # Prepare inputs.
        output_dir = self.get_scratch_space()
        item_id = "123"
        base = f"2024-01-01.hn_{item_id}.title"
        merged_file = os.path.join(output_dir, f"{base}.summary.md")
        hio.to_file(merged_file, "merged content")
        hio.to_file(
            os.path.join(output_dir, f"{base}.2.article_url.summary.md"),
            "article content",
        )
        hio.to_file(
            os.path.join(output_dir, f"{base}.4.hn_url.summary.md"),
            "hn content",
        )
        # Prepare outputs.
        expected = merged_file
        # Run test.
        actual = dshdprbo._find_cached_merged_summary(output_dir, item_id)
        # Check outputs.
        self.assert_equal(str(actual), expected)

    def test2(self) -> None:
        """
        Test a missing merged summary returns None.
        """
        # Prepare inputs.
        output_dir = self.get_scratch_space()
        item_id = "999"
        # Prepare outputs.
        expected = "None"
        # Run test.
        actual = dshdprbo._find_cached_merged_summary(output_dir, item_id)
        # Check outputs.
        self.assert_equal(str(actual), expected)


# #############################################################################
# Test__reconcile_destination
# #############################################################################


class Test__reconcile_destination(hunitest.TestCase):
    """
    Test `process_bookmarks._reconcile_destination()`.
    """

    def test1(self) -> None:
        """
        Test a `Done=yes` row whose merged file is missing from the
        destination gets copied there.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_dir = os.path.join(scratch_dir, "output")
        dest_dir = os.path.join(scratch_dir, "dest")
        hio.create_dir(output_dir, incremental=True)
        hio.create_dir(dest_dir, incremental=True)
        merged_filename = "2024-01-01.hn_123.title.summary.md"
        hio.to_file(
            os.path.join(output_dir, merged_filename), "merged content"
        )
        rows = [
            {
                "Hn_url": "https://news.ycombinator.com/item?id=123",
                "Done": "yes",
            },
        ]
        # Prepare outputs.
        expected_copied = [merged_filename]
        # Run test.
        actual_copied = dshdprbo._reconcile_destination(
            rows, output_dir=output_dir, dest_dir=dest_dir, dry_run=False
        )
        # Check outputs.
        self.assert_equal(str(actual_copied), str(expected_copied))
        self.assertTrue(
            os.path.exists(os.path.join(dest_dir, merged_filename))
        )

    def test2(self) -> None:
        """
        Test a `Done=yes` row whose merged file already exists at the
        destination is not re-copied.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_dir = os.path.join(scratch_dir, "output")
        dest_dir = os.path.join(scratch_dir, "dest")
        hio.create_dir(output_dir, incremental=True)
        hio.create_dir(dest_dir, incremental=True)
        merged_filename = "2024-01-01.hn_123.title.summary.md"
        hio.to_file(
            os.path.join(output_dir, merged_filename), "merged content"
        )
        hio.to_file(
            os.path.join(dest_dir, merged_filename), "already there"
        )
        rows = [
            {
                "Hn_url": "https://news.ycombinator.com/item?id=123",
                "Done": "yes",
            },
        ]
        # Prepare outputs.
        expected_copied: list = []
        # Run test.
        actual_copied = dshdprbo._reconcile_destination(
            rows, output_dir=output_dir, dest_dir=dest_dir, dry_run=False
        )
        # Check outputs.
        self.assert_equal(str(actual_copied), str(expected_copied))

    def test3(self) -> None:
        """
        Test `dest_dir=None` (`--dest_type none`) reconciles nothing.
        """
        # Prepare inputs.
        rows = [
            {
                "Hn_url": "https://news.ycombinator.com/item?id=123",
                "Done": "yes",
            },
        ]
        # Prepare outputs.
        expected_copied: list = []
        # Run test.
        actual_copied = dshdprbo._reconcile_destination(
            rows, output_dir="unused", dest_dir=None, dry_run=False
        )
        # Check outputs.
        self.assert_equal(str(actual_copied), str(expected_copied))

    def test4(self) -> None:
        """
        Test `dry_run=True` reports the row to copy but doesn't touch the
        filesystem.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_dir = os.path.join(scratch_dir, "output")
        dest_dir = os.path.join(scratch_dir, "dest")
        hio.create_dir(output_dir, incremental=True)
        merged_filename = "2024-01-01.hn_123.title.summary.md"
        hio.to_file(
            os.path.join(output_dir, merged_filename), "merged content"
        )
        rows = [
            {
                "Hn_url": "https://news.ycombinator.com/item?id=123",
                "Done": "yes",
            },
        ]
        # Prepare outputs.
        expected_copied = [merged_filename]
        # Run test.
        actual_copied = dshdprbo._reconcile_destination(
            rows, output_dir=output_dir, dest_dir=dest_dir, dry_run=True
        )
        # Check outputs.
        self.assert_equal(str(actual_copied), str(expected_copied))
        self.assertFalse(os.path.exists(dest_dir))

    def test5(self) -> None:
        """
        Test a row that isn't `Done=yes` is ignored by reconciliation.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_dir = os.path.join(scratch_dir, "output")
        dest_dir = os.path.join(scratch_dir, "dest")
        rows = [
            {
                "Hn_url": "https://news.ycombinator.com/item?id=123",
                "Done": "",
            },
        ]
        # Prepare outputs.
        expected_copied: list = []
        # Run test.
        actual_copied = dshdprbo._reconcile_destination(
            rows, output_dir=output_dir, dest_dir=dest_dir, dry_run=False
        )
        # Check outputs.
        self.assert_equal(str(actual_copied), str(expected_copied))
