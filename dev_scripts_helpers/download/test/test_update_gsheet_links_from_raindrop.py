#!/usr/bin/env python

# TODO(ai_gp): Add 'import logging' and '_LOG = logging.getLogger(__name__)' to match the template structure (testing.rules.md:## Unit Test Code Structure)
import os
import unittest.mock as umock
from typing import Callable, Optional

import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.bookmark_utils as dshdbou
import dev_scripts_helpers.download.update_gsheet_links_from_raindrop as dsglfr


# #############################################################################
# Test__parse_timestamp
# #############################################################################

# TODO(ai_gp): Test public-facing behavior before testing internal helpers (_parse_timestamp is a private function) (testing.rules.md:## Test From the Outside-In)

class Test__parse_timestamp(hunitest.TestCase):
    """
    Test `update_gsheet_links_from_raindrop._parse_timestamp()`.
    """
    # TODO(ai_gp): Add tests for edge cases (e.g., empty input, malformed timestamps, None values) (testing.rules.md:## What to Test)

    def helper(self, ts_str: str, expected: str) -> None:
        """
        Run `_parse_timestamp()` and check the output.

        :param ts_str: input timestamp string
        :param expected: expected parsed value, as `"YYYY-MM-DD HH:MM:SS"`
        """
        # Run test.
        actual = dsglfr._parse_timestamp(ts_str)
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


# #############################################################################
# Test__get_latest_timestamp_from_file
# #############################################################################

# TODO(ai_gp): Test public-facing behavior before testing internal helpers (_get_latest_timestamp_from_file is a private function) (testing.rules.md:## Test From the Outside-In)

class Test__get_latest_timestamp_from_file(hunitest.TestCase):
    """
    Test `update_gsheet_links_from_raindrop._get_latest_timestamp_from_file()`.
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
        actual = dsglfr._get_latest_timestamp_from_file(gsheet_csv)
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
# Test__get_action_output_file
# #############################################################################

# TODO(ai_gp): Test public-facing behavior before testing internal helpers (_get_action_output_file is a private function) (testing.rules.md:## Test From the Outside-In)

class Test__get_action_output_file(hunitest.TestCase):
    """
    Test `update_gsheet_links_from_raindrop._get_action_output_file()`.
    """
    # TODO(ai_gp): Add tests for edge cases (e.g., unknown/invalid action names) (testing.rules.md:## What to Test)

    def helper(self, action: str, expected: str) -> None:
        """
        Run `_get_action_output_file()` and check the output.

        :param action: action name
        :param expected: expected output file path, or `"None"` if the
            action has no local output file
        """
        # Run test.
        actual = dsglfr._get_action_output_file(action)
        # Check outputs.
        self.assert_equal(str(actual), expected)

    def test1(self) -> None:
        """
        Test `download_gsheet_links` resolves to the gsheet CSV path.
        """
        # Prepare inputs.
        action = "download_gsheet_links"
        # Prepare outputs.
        expected = dshdbou.get_tmp_file_path(
            dsglfr.GSHEET_CSV_FILE, "update_gsheet_links_from_raindrop"
        )
        # Run test.
        self.helper(action, expected)

    def test2(self) -> None:
        """
        Test `combine_data` resolves to the combined CSV path.
        """
        # Prepare inputs.
        action = "combine_data"
        # Prepare outputs.
        expected = dshdbou.get_tmp_file_path(
            dsglfr.COMBINED_CSV_FILE, "update_gsheet_links_from_raindrop"
        )
        # Run test.
        self.helper(action, expected)

    def test3(self) -> None:
        """
        Test `upload_gsheet_links` has no local output file to check.
        """
        # Prepare inputs.
        action = "upload_gsheet_links"
        # Prepare outputs.
        expected = "None"
        # Run test.
        self.helper(action, expected)


# #############################################################################
# Test__combine_raindrop_with_gsheet_links
# #############################################################################

# TODO(ai_gp): Test public-facing behavior before testing internal helpers (_combine_raindrop_with_gsheet_links is a private function) (testing.rules.md:## Test From the Outside-In)

class Test__combine_raindrop_with_gsheet_links(hunitest.TestCase):
    """
    Test `update_gsheet_links_from_raindrop._combine_raindrop_with_gsheet_links()`.
    """
    # TODO(ai_gp): Add tests for edge cases (e.g., empty raindrop rows, empty gsheet rows, single item) (testing.rules.md:## What to Test)

    def helper(
        self, gsheet_columns: list, gsheet_rows: list, raindrop_rows: list
    ) -> list:
        """
        Write `gsheet_rows`/`raindrop_rows` as the two input CSVs, run
        `_combine_raindrop_with_gsheet_links()`, and return the resulting
        rows.

        Redirects the script's fixed `./tmp.update_gsheet_links_from_raindrop.*`
        paths into the test's scratch space so the test does not pollute (or
        depend on) the current working directory.

        :param gsheet_columns: column names of the gsheet CSV
        :param gsheet_rows: pre-existing rows in the gsheet CSV
        :param raindrop_rows: rows to write to the Raindrop CSV (with `id`,
            `title`, `url`, `created` columns)
        :return: rows read back from the combined CSV
        """
        scratch_dir = self.get_scratch_space()

        def _get_tmp_file_path(filename: str, prefix: str) -> str:
            return os.path.join(scratch_dir, f"tmp.{prefix}.{filename}")

        gsheet_csv = _get_tmp_file_path(
            dsglfr.GSHEET_CSV_FILE, "update_gsheet_links_from_raindrop"
        )
        dshdbou.write_csv(
            gsheet_csv, gsheet_rows, fieldnames=gsheet_columns
        )
        raindrop_csv = _get_tmp_file_path(
            dsglfr.RAINDROP_CSV_FILE, "update_gsheet_links_from_raindrop"
        )
        dshdbou.write_csv(
            raindrop_csv,
            raindrop_rows,
            fieldnames=["id", "title", "url", "created"],
        )
        # TODO(ai_gp): Avoid mocking internal helper dshdbou.get_tmp_file_path; instead use test infrastructure to redirect paths without mocking internal functions (testing.rules.md:## Mock Only External Dependencies)
        with umock.patch.object(
            dsglfr.dshdbou,
            "get_tmp_file_path",
            side_effect=_get_tmp_file_path,
        ):
            combined_csv = dsglfr._combine_raindrop_with_gsheet_links()
        actual_rows = dshdbou.read_csv(combined_csv)
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
        # TODO(ai_gp): Add "# Prepare outputs." section with expected values before "# Run test." (testing.rules.md:## Use Three Sections in Testing Methods)
        # Run test.
        actual_rows = self.helper(gsheet_columns, gsheet_rows, raindrop_rows)
        # TODO(ai_gp): Compare whole output with assert_equal instead of piecewise checks on individual fields (testing.rules.md:## Compare Whole Output with `assert_equal`, Not Piecewise)
        # Check outputs. The raindrop row is prepended before the existing
        # gsheet row.
        self.assertEqual(len(actual_rows), 2)
        self.assert_equal(actual_rows[0]["Title"], "Some Title")
        self.assert_equal(
            actual_rows[0]["Hn_url"],
            "https://news.ycombinator.com/item?id=1",
        )
        self.assert_equal(actual_rows[0]["Article_url"], "")
        self.assert_equal(actual_rows[0]["Timestamp"], "2024-06-01 12:30:00")

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
        # TODO(ai_gp): Add "# Prepare outputs." section with expected values before "# Run test." (testing.rules.md:## Use Three Sections in Testing Methods)
        # Run test.
        actual_rows = self.helper(gsheet_columns, gsheet_rows, raindrop_rows)
        # TODO(ai_gp): Compare whole output with assert_equal instead of piecewise checks on individual fields (testing.rules.md:## Compare Whole Output with `assert_equal`, Not Piecewise)
        # Check outputs.
        self.assertEqual(len(actual_rows), 2)
        self.assert_equal(actual_rows[0]["Title"], "New")
        self.assert_equal(actual_rows[1]["Title"], "Old")


# #############################################################################
# Test__download_raindrop_data
# #############################################################################

# TODO(ai_gp): Test public-facing behavior before testing internal helpers (_download_raindrop_data is a private function) (testing.rules.md:## Test From the Outside-In)

class Test__download_raindrop_data(hunitest.TestCase):
    """
    Test `update_gsheet_links_from_raindrop._download_raindrop_data()`.
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

        :param gsheet_timestamp: `Timestamp` value written to the gsheet
            CSV, used as the cutoff for filtering Raindrop bookmarks
        :param get_return_value: fixed response for the mocked
            `requests.get()` (mutually exclusive with `get_side_effect`)
        :param get_side_effect: `side_effect` callable for the mocked
            `requests.get()` (mutually exclusive with `get_return_value`)
        :return: rows read back from the Raindrop CSV
        """
        scratch_dir = self.get_scratch_space()

        def _get_tmp_file_path(filename: str, prefix: str) -> str:
            return os.path.join(scratch_dir, f"tmp.{prefix}.{filename}")

        gsheet_csv = _get_tmp_file_path(
            dsglfr.GSHEET_CSV_FILE, "update_gsheet_links_from_raindrop"
        )
        dshdbou.write_csv(
            gsheet_csv,
            [{"Timestamp": gsheet_timestamp}],
            fieldnames=["Timestamp"],
        )
        # TODO(ai_gp): Avoid mocking internal helper dshdbou.get_tmp_file_path; instead use test infrastructure to redirect paths without mocking internal functions (testing.rules.md:## Mock Only External Dependencies)
        with (
            umock.patch.object(
                dsglfr.dshdbou,
                "get_tmp_file_path",
                side_effect=_get_tmp_file_path,
            ),
            umock.patch.dict(os.environ, {"RAINDROP_API_TOKEN": "fake_token"}),
            umock.patch.object(
                dsglfr.requests,
                "get",
                return_value=get_return_value,
                side_effect=get_side_effect,
            ),
        ):
            raindrop_csv = dsglfr._download_raindrop_data()
        actual_rows = dshdbou.read_csv(raindrop_csv)
        return actual_rows

    @staticmethod
    def _build_response(items: list) -> umock.MagicMock:
        """
        Build a fake `requests.Response` returning `items` as `.json()`.

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
        response = self._build_response(items)
        # TODO(ai_gp): Add "# Prepare outputs." section with expected values before "# Run test." (testing.rules.md:## Use Three Sections in Testing Methods)
        # Run test.
        actual_rows = self.helper(gsheet_timestamp, get_return_value=response)
        # TODO(ai_gp): Compare whole output with assert_equal instead of piecewise checks on individual fields (testing.rules.md:## Compare Whole Output with `assert_equal`, Not Piecewise)
        # Check outputs.
        self.assertEqual(len(actual_rows), 1)
        self.assert_equal(actual_rows[0]["title"], "New bookmark")
        self.assert_equal(
            actual_rows[0]["url"], "https://news.ycombinator.com/item?id=1"
        )

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
        response = self._build_response(items)
        # TODO(ai_gp): Add "# Prepare outputs." section with expected values before "# Run test." (testing.rules.md:## Use Three Sections in Testing Methods)
        # Run test.
        actual_rows = self.helper(gsheet_timestamp, get_return_value=response)
        # TODO(ai_gp): Compare whole output with assert_equal instead of piecewise checks (testing.rules.md:## Compare Whole Output with `assert_equal`, Not Piecewise)
        # Check outputs.
        self.assertEqual(len(actual_rows), 0)

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
            return self._build_response(items)

        # Prepare outputs.
        expected_num_rows = 51
        # Run test.
        actual_rows = self.helper(
            gsheet_timestamp, get_side_effect=get_side_effect
        )
        # TODO(ai_gp): Compare whole output with assert_equal instead of only checking length (testing.rules.md:## Compare Whole Output with `assert_equal`, Not Piecewise)
        # Check outputs.
        self.assertEqual(len(actual_rows), expected_num_rows)
