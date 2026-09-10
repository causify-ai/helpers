#!/usr/bin/env python

import logging
import os
import unittest.mock as umock
from typing import Callable, List, Optional

import pytest

# Skip this test suite if requests is not installed (skip for tutorials).
pytest.importorskip("requests")

import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.bookmark_utils as dshdbou
import dev_scripts_helpers.download.update_bookmarks_from_raindrop as dsbfr

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_update_bookmarks_from_raindrop_py
# #############################################################################


class Test_update_bookmarks_from_raindrop_py(hunitest.TestCase):
    """
    Test `update_bookmarks_from_raindrop._main()` function.
    """

    def helper(self, argv: List[str]) -> None:
        """
        Helper for testing `_main()` with mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `umock.patch("sys.argv", ...)`
        """
        parser = dsbfr._parse()
        with umock.patch("sys.argv", argv):
            dsbfr._main(parser)

    def test1(self) -> None:
        """
        Test `--target local_csv` end-to-end: `download_raindrop_data` +
        `combine_data` merge new bookmarks into `--local_csv` in place,
        leaving the existing `Done=yes` row untouched.
        """
        scratch_dir = self.get_scratch_space()
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            # Prepare inputs.
            local_csv = os.path.join(scratch_dir, "local.csv")
            columns = ["Title", "Hn_url", "Article_url", "Timestamp", "Done"]
            existing_rows = [
                {
                    "Title": "Existing",
                    "Hn_url": "https://news.ycombinator.com/item?id=0",
                    "Article_url": "",
                    "Timestamp": "2024-01-01 00:00:00",
                    "Done": "yes",
                },
            ]
            dshdbou.write_csv(local_csv, existing_rows, fieldnames=columns)
            items = [
                {
                    "_id": "1",
                    "title": "New | Hacker News",
                    "link": "https://news.ycombinator.com/item?id=1",
                    "created": "2024-06-01T00:00:00.000Z",
                },
            ]
            response = umock.MagicMock()
            response.status_code = 200
            response.json.return_value = {"items": items}
            argv = [
                "update_bookmarks_from_raindrop.py",
                "--target",
                "local_csv",
                "--local_csv",
                local_csv,
                "--clear_actions",
                "--action",
                "download_raindrop_data",
                "--action",
                "combine_data",
            ]
            # Prepare outputs. The existing `Done=yes` row is untouched; the
            # new row is prepended ahead of it.
            expected_rows = [
                {
                    "Title": "New",
                    "Hn_url": "https://news.ycombinator.com/item?id=1",
                    "Article_url": "",
                    "Timestamp": "2024-06-01 00:00:00",
                    "Done": "",
                },
                existing_rows[0],
            ]
            # Run test.
            with (
                umock.patch.dict(
                    os.environ, {"RAINDROP_API_TOKEN": "fake_token"}
                ),
                umock.patch.object(
                    dsbfr.requests, "get", return_value=response
                ),
            ):
                self.helper(argv)
            actual_rows = dshdbou.read_csv(local_csv)
        finally:
            os.chdir(cwd)
        # Check outputs.
        self.assert_equal(str(actual_rows), str(expected_rows))


# #############################################################################
# Test__combine_raindrop_with_gsheet_links
# #############################################################################


class Test__combine_raindrop_with_gsheet_links(hunitest.TestCase):
    """
    Test `update_bookmarks_from_raindrop._combine_raindrop_with_gsheet_links()`.
    """

    def helper(
        self, gsheet_columns: list, gsheet_rows: list, raindrop_rows: list
    ) -> list:
        """
        Write `gsheet_rows`/`raindrop_rows` as the two input CSVs, run
        `_combine_raindrop_with_gsheet_links()` with a separate `output_csv`
        (the `--target gsheet` case), and return the resulting rows.

        Changes the current directory to the test's scratch space so that
        the fixed relative `./tmp.update_bookmarks_from_raindrop.*`
        paths produced by `dshdbou.get_tmp_file_path()` land in the
        scratch space instead of the current working directory. This
        redirects I/O without mocking the internal helper.

        :param gsheet_columns: column names of the gsheet CSV
        :param gsheet_rows: pre-existing rows in the gsheet CSV
        :param raindrop_rows: rows to write to the Raindrop CSV (with `id`,
            `title`, `url`, `created` columns)
        :return: rows read back from the combined CSV
        """
        scratch_dir = self.get_scratch_space()
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            gsheet_csv = dshdbou.get_tmp_file_path(
                dsbfr.GSHEET_CSV_FILE, "update_bookmarks_from_raindrop"
            )
            dshdbou.write_csv(
                gsheet_csv, gsheet_rows, fieldnames=gsheet_columns
            )
            raindrop_csv = dshdbou.get_tmp_file_path(
                dsbfr.RAINDROP_CSV_FILE, "update_bookmarks_from_raindrop"
            )
            dshdbou.write_csv(
                raindrop_csv,
                raindrop_rows,
                fieldnames=["id", "title", "url", "created"],
            )
            output_csv = dshdbou.get_tmp_file_path(
                dsbfr.COMBINED_CSV_FILE, "update_bookmarks_from_raindrop"
            )
            combined_csv = dsbfr._combine_raindrop_with_gsheet_links(
                gsheet_csv, output_csv
            )
            actual_rows = dshdbou.read_csv(combined_csv)
        finally:
            os.chdir(cwd)
        return actual_rows

    def test1(self) -> None:
        """
        Test the "| Hacker News" title suffix is stripped and the Raindrop
        `url` is mapped to the gsheet's `Hn_url` column.
        """
        # Prepare inputs. `gsheet_columns` is derived by the function from
        # the keys of the first existing row, so the gsheet CSV needs at
        # least one row to establish the schema.
        gsheet_columns = ["Title", "Hn_url", "Article_url", "Timestamp"]
        gsheet_rows = [
            {
                "Title": "Existing",
                "Hn_url": "https://news.ycombinator.com/item?id=0",
                "Article_url": "",
                "Timestamp": "2023-01-01 00:00:00",
            },
        ]
        raindrop_rows = [
            {
                "id": "1",
                "title": "Some Title | Hacker News",
                "url": "https://news.ycombinator.com/item?id=1",
                "created": "2024-06-01T12:30:00.000Z",
            },
        ]
        # Prepare outputs. The raindrop row is prepended before the
        # existing gsheet row.
        expected_rows = [
            {
                "Title": "Some Title",
                "Hn_url": "https://news.ycombinator.com/item?id=1",
                "Article_url": "",
                "Timestamp": "2024-06-01 12:30:00",
            },
            gsheet_rows[0],
        ]
        # Run test.
        actual_rows = self.helper(gsheet_columns, gsheet_rows, raindrop_rows)
        # Check outputs.
        self.assert_equal(str(actual_rows), str(expected_rows))

    def test2(self) -> None:
        """
        Test Raindrop rows are prepended (newest first) before the existing
        gsheet rows.
        """
        # Prepare inputs.
        gsheet_columns = ["Title", "Hn_url", "Article_url", "Timestamp"]
        gsheet_rows = [
            {
                "Title": "Old",
                "Hn_url": "https://news.ycombinator.com/item?id=0",
                "Article_url": "",
                "Timestamp": "2024-01-01 00:00:00",
            },
        ]
        raindrop_rows = [
            {
                "id": "1",
                "title": "New",
                "url": "https://news.ycombinator.com/item?id=1",
                "created": "2024-06-01T00:00:00.000Z",
            },
        ]
        # Prepare outputs.
        expected_rows = [
            {
                "Title": "New",
                "Hn_url": "https://news.ycombinator.com/item?id=1",
                "Article_url": "",
                "Timestamp": "2024-06-01 00:00:00",
            },
            gsheet_rows[0],
        ]
        # Run test.
        actual_rows = self.helper(gsheet_columns, gsheet_rows, raindrop_rows)
        # Check outputs.
        # TODO(ai_gp): Move the assert_equal in the helper
        self.assert_equal(str(actual_rows), str(expected_rows))

    def test3(self) -> None:
        """
        Test empty Raindrop rows leave the existing gsheet rows unchanged.
        """
        # Prepare inputs.
        gsheet_columns = ["Title", "Hn_url", "Article_url", "Timestamp"]
        gsheet_rows = [
            {
                "Title": "Existing",
                "Hn_url": "https://news.ycombinator.com/item?id=0",
                "Article_url": "",
                "Timestamp": "2023-01-01 00:00:00",
            },
        ]
        raindrop_rows: list = []
        # Prepare outputs.
        expected_rows = gsheet_rows
        # Run test.
        actual_rows = self.helper(gsheet_columns, gsheet_rows, raindrop_rows)
        # Check outputs.
        self.assert_equal(str(actual_rows), str(expected_rows))

    def test4(self) -> None:
        """
        Test the in-place merge (`output_csv == base_csv`, the `--target
        local_csv` case): new Raindrop rows are prepended into the same
        file and every existing row (`Done` included) is left untouched.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            local_csv = os.path.join(scratch_dir, "local.csv")
            gsheet_columns = [
                "Title",
                "Hn_url",
                "Article_url",
                "Timestamp",
                "Done",
            ]
            gsheet_rows = [
                {
                    "Title": "Existing",
                    "Hn_url": "https://news.ycombinator.com/item?id=0",
                    "Article_url": "",
                    "Timestamp": "2023-01-01 00:00:00",
                    "Done": "yes",
                },
            ]
            dshdbou.write_csv(
                local_csv, gsheet_rows, fieldnames=gsheet_columns
            )
            raindrop_csv = dshdbou.get_tmp_file_path(
                dsbfr.RAINDROP_CSV_FILE, "update_bookmarks_from_raindrop"
            )
            raindrop_rows = [
                {
                    "id": "1",
                    "title": "New | Hacker News",
                    "url": "https://news.ycombinator.com/item?id=1",
                    "created": "2024-06-01T00:00:00.000Z",
                },
            ]
            dshdbou.write_csv(
                raindrop_csv,
                raindrop_rows,
                fieldnames=["id", "title", "url", "created"],
            )
            # Prepare outputs. The existing `Done=yes` row is untouched; the
            # new row is prepended ahead of it.
            expected_rows = [
                {
                    "Title": "New",
                    "Hn_url": "https://news.ycombinator.com/item?id=1",
                    "Article_url": "",
                    "Timestamp": "2024-06-01 00:00:00",
                    "Done": "",
                },
                gsheet_rows[0],
            ]
            # Run test.
            combined_csv = dsbfr._combine_raindrop_with_gsheet_links(
                local_csv, local_csv
            )
            actual_rows = dshdbou.read_csv(local_csv)
        finally:
            os.chdir(cwd)
        # Check outputs.
        self.assert_equal(combined_csv, local_csv)
        self.assert_equal(str(actual_rows), str(expected_rows))


# #############################################################################
# Test__download_raindrop_data
# #############################################################################


class Test__download_raindrop_data(hunitest.TestCase):
    """
    Test `update_bookmarks_from_raindrop._download_raindrop_data()`.
    """

    def helper(
        self,
        gsheet_timestamp: str,
        *,
        get_return_value: Optional[umock.MagicMock] = None,
        get_side_effect: Optional[Callable] = None,
    ) -> list:
        """
        Run `_download_raindrop_data()` against a mocked `requests.get()`
        and return the rows written to the Raindrop CSV.

        Changes the current directory to the test's scratch space so that
        the fixed relative `./tmp.update_bookmarks_from_raindrop.*`
        paths produced by `dshdbou.get_tmp_file_path()` land in the
        scratch space instead of the current working directory. This
        redirects I/O without mocking the internal helper; only the
        external `requests.get()` call and the `RAINDROP_API_TOKEN`
        environment variable are mocked.

        :param gsheet_timestamp: `Timestamp` value written to the gsheet
            CSV, used as the cutoff for filtering Raindrop bookmarks
        :param get_return_value: fixed response for the mocked
            `requests.get()` (mutually exclusive with `get_side_effect`)
        :param get_side_effect: `side_effect` callable for the mocked
            `requests.get()` (mutually exclusive with `get_return_value`)
        :return: rows read back from the Raindrop CSV
        """
        scratch_dir = self.get_scratch_space()
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            gsheet_csv = dshdbou.get_tmp_file_path(
                dsbfr.GSHEET_CSV_FILE, "update_bookmarks_from_raindrop"
            )
            dshdbou.write_csv(
                gsheet_csv,
                [{"Timestamp": gsheet_timestamp}],
                fieldnames=["Timestamp"],
            )
            with (
                umock.patch.dict(
                    os.environ, {"RAINDROP_API_TOKEN": "fake_token"}
                ),
                umock.patch.object(
                    dsbfr.requests,
                    "get",
                    return_value=get_return_value,
                    side_effect=get_side_effect,
                ),
            ):
                raindrop_csv = dsbfr._download_raindrop_data(gsheet_csv)
            actual_rows = dshdbou.read_csv(raindrop_csv)
        finally:
            os.chdir(cwd)
        return actual_rows

    @staticmethod
    def helper2(items: list) -> umock.MagicMock:
        """
        Helper for building a fake `requests.Response` returning `items`.

        :param items: fake Raindrop API `items` for the page
        :return: mocked response with `status_code=200`
        """
        response = umock.MagicMock()
        response.status_code = 200
        response.json.return_value = {"items": items}
        return response

    def test1(self) -> None:
        """
        Test a bookmark created after the gsheet cutoff is downloaded.
        """
        # Prepare inputs.
        gsheet_timestamp = "2024-01-01 00:00:00"
        items = [
            {
                "_id": "1",
                "title": "New bookmark",
                "link": "https://news.ycombinator.com/item?id=1",
                "created": "2024-06-01T00:00:00.000Z",
            },
        ]
        response = self.helper2(items)
        # Prepare outputs.
        expected_rows = [
            {
                "id": "1",
                "title": "New bookmark",
                "url": "https://news.ycombinator.com/item?id=1",
                "created": "2024-06-01T00:00:00.000Z",
            },
        ]
        # Run test.
        actual_rows = self.helper(gsheet_timestamp, get_return_value=response)
        # Check outputs.
        self.assert_equal(str(actual_rows), str(expected_rows))

    def test2(self) -> None:
        """
        Test a bookmark created before the gsheet cutoff is filtered out.
        """
        # Prepare inputs.
        gsheet_timestamp = "2024-06-01 00:00:00"
        items = [
            {
                "_id": "1",
                "title": "Old bookmark",
                "link": "https://news.ycombinator.com/item?id=1",
                "created": "2024-01-01T00:00:00.000Z",
            },
        ]
        response = self.helper2(items)
        # Prepare outputs.
        expected_rows: list = []
        # Run test.
        actual_rows = self.helper(gsheet_timestamp, get_return_value=response)
        # Check outputs.
        # TODO(ai_gp): Move the assert_equal in the helper
        self.assert_equal(str(actual_rows), str(expected_rows))

    def test3(self) -> None:
        """
        Test pagination continues past a full first page (`perpage=50`
        items) and stops at the following short page.
        """
        # Prepare inputs.
        gsheet_timestamp = "2024-01-01 00:00:00"

        def _make_item(idx: int) -> dict:
            return {
                "_id": str(idx),
                "title": f"Bookmark {idx}",
                "link": f"https://news.ycombinator.com/item?id={idx}",
                "created": "2024-06-01T00:00:00.000Z",
            }

        def get_side_effect(*args, **kwargs):
            _ = args
            page = kwargs["params"]["page"]
            if page == 0:
                items = [_make_item(i) for i in range(50)]
            else:
                items = [_make_item(50)]
            return self.helper2(items)

        # Prepare outputs. Build the expected rows the same way as the
        # source's field mapping (`id`, `title`, `url`, `created`) instead
        # of hardcoding 51 rows by hand.
        expected_rows = [
            {
                "id": str(idx),
                "title": f"Bookmark {idx}",
                "url": f"https://news.ycombinator.com/item?id={idx}",
                "created": "2024-06-01T00:00:00.000Z",
            }
            for idx in range(51)
        ]
        # Run test.
        actual_rows = self.helper(
            gsheet_timestamp, get_side_effect=get_side_effect
        )
        # Check outputs.
        self.assert_equal(str(actual_rows), str(expected_rows))


# #############################################################################
# Test__get_action_output_file
# #############################################################################


class Test__get_action_output_file(hunitest.TestCase):
    """
    Test `update_bookmarks_from_raindrop._get_action_output_file()`.
    """

    def helper(self, action: str, target: str, expected: str) -> None:
        """
        Run `_get_action_output_file()` and check the output.

        :param action: action name
        :param target: `--target` value (`gsheet` or `local_csv`)
        :param expected: expected output file path, or `"None"` if the
            action has no local output file
        """
        # Run test.
        actual = dsbfr._get_action_output_file(action, target)
        # Check outputs.
        self.assert_equal(str(actual), expected)

    def test1(self) -> None:
        """
        Test `download_gsheet_links` resolves to the gsheet CSV path for
        `--target gsheet`.
        """
        # Prepare inputs.
        action = "download_gsheet_links"
        target = "gsheet"
        # Prepare outputs.
        expected = dshdbou.get_tmp_file_path(
            dsbfr.GSHEET_CSV_FILE, "update_bookmarks_from_raindrop"
        )
        # Run test.
        self.helper(action, target, expected)

    def test2(self) -> None:
        """
        Test `combine_data` resolves to the combined CSV path for `--target
        gsheet`.
        """
        # Prepare inputs.
        action = "combine_data"
        target = "gsheet"
        # Prepare outputs.
        expected = dshdbou.get_tmp_file_path(
            dsbfr.COMBINED_CSV_FILE, "update_bookmarks_from_raindrop"
        )
        # Run test.
        self.helper(action, target, expected)

    def test3(self) -> None:
        """
        Test `upload_gsheet_links` has no local output file to check for
        `--target gsheet`.
        """
        # Prepare inputs.
        action = "upload_gsheet_links"
        target = "gsheet"
        # Prepare outputs.
        expected = "None"
        # Run test.
        self.helper(action, target, expected)

    def test4(self) -> None:
        """
        Test an unknown action name has no local output file to check,
        same as `upload_gsheet_links`.
        """
        # Prepare inputs.
        action = "unknown_action"
        target = "gsheet"
        # Prepare outputs.
        expected = "None"
        # Run test.
        self.helper(action, target, expected)

    def test5(self) -> None:
        """
        Test `download_raindrop_data` resolves to the raindrop CSV path for
        `--target local_csv`, same as for `--target gsheet`.
        """
        # Prepare inputs.
        action = "download_raindrop_data"
        target = "local_csv"
        # Prepare outputs.
        expected = dshdbou.get_tmp_file_path(
            dsbfr.RAINDROP_CSV_FILE, "update_bookmarks_from_raindrop"
        )
        # Run test.
        self.helper(action, target, expected)

    def test6(self) -> None:
        """
        Test `combine_data` has no local output file to check for `--target
        local_csv`, since it merges into `--local_csv` in place (which
        always already exists, so an existence check would wrongly skip it
        every run).
        """
        # Prepare inputs.
        action = "combine_data"
        target = "local_csv"
        # Prepare outputs.
        expected = "None"
        # Run test.
        self.helper(action, target, expected)

    def test7(self) -> None:
        """
        Test `download_gsheet_links` has no local output file to check for
        `--target local_csv`, since it's not a valid action for that
        target.
        """
        # Prepare inputs.
        action = "download_gsheet_links"
        target = "local_csv"
        # Prepare outputs.
        expected = "None"
        # Run test.
        self.helper(action, target, expected)


# #############################################################################
# Test__get_latest_timestamp_from_file
# #############################################################################


class Test__get_latest_timestamp_from_file(hunitest.TestCase):
    """
    Test `update_bookmarks_from_raindrop._get_latest_timestamp_from_file()`.
    """

    def helper(self, rows: list, expected: str) -> None:
        """
        Write `rows` to a scratch gsheet CSV and check the resolved cutoff
        timestamp.

        :param rows: rows to write to the gsheet CSV (must include a
            `Timestamp` column)
        :param expected: expected latest timestamp, as
            `"YYYY-MM-DD HH:MM:SS"`
        """
        scratch_dir = self.get_scratch_space()
        gsheet_csv = os.path.join(scratch_dir, "gsheet.csv")
        dshdbou.write_csv(gsheet_csv, rows, fieldnames=list(rows[0].keys()))
        # Run test.
        actual = dsbfr._get_latest_timestamp_from_file(gsheet_csv)
        # Check outputs.
        self.assert_equal(str(actual), expected)

    def test1(self) -> None:
        """
        Test the max timestamp is picked among multiple rows.
        """
        # Prepare inputs.
        rows = [
            {"Timestamp": "2024-01-01 00:00:00"},
            {"Timestamp": "2024-06-15 10:30:00"},
            {"Timestamp": "2024-03-01 00:00:00"},
        ]
        # Prepare outputs.
        expected = "2024-06-15 10:30:00"
        # Run test.
        self.helper(rows, expected)

    def test2(self) -> None:
        """
        Test rows with an empty `Timestamp` value are ignored.
        """
        # Prepare inputs.
        rows = [
            {"Timestamp": "2024-01-01 00:00:00"},
            {"Timestamp": ""},
        ]
        # Prepare outputs.
        expected = "2024-01-01 00:00:00"
        # Run test.
        self.helper(rows, expected)


# #############################################################################
# Test__parse_timestamp
# #############################################################################


class Test__parse_timestamp(hunitest.TestCase):
    """
    Test `update_bookmarks_from_raindrop._parse_timestamp()`.
    """

    def helper(self, ts_str: str, expected: str) -> None:
        """
        Run `_parse_timestamp()` and check the output.

        :param ts_str: input timestamp string
        :param expected: expected parsed value, as `"YYYY-MM-DD HH:MM:SS"`
        """
        # Run test.
        actual = dsbfr._parse_timestamp(ts_str)
        # Check outputs.
        self.assert_equal(str(actual), expected)

    def test1(self) -> None:
        """
        Test a Raindrop-style ISO 8601 timestamp with a `Z` suffix.
        """
        # Prepare inputs.
        ts_str = "2024-06-01T12:30:00.000Z"
        # Prepare outputs.
        expected = "2024-06-01 12:30:00"
        # Run test.
        self.helper(ts_str, expected)

    def test2(self) -> None:
        """
        Test a gsheet-style "YYYY-MM-DD HH:MM:SS" timestamp.
        """
        # Prepare inputs.
        ts_str = "2024-06-01 12:30:00"
        # Prepare outputs.
        expected = "2024-06-01 12:30:00"
        # Run test.
        self.helper(ts_str, expected)

    def test3(self) -> None:
        """
        Test an ISO 8601 date-only string (no time component) defaults to
        midnight.
        """
        # Prepare inputs.
        ts_str = "2024-06-01"
        # Prepare outputs.
        expected = "2024-06-01 00:00:00"
        # Run test.
        self.helper(ts_str, expected)
