#!/usr/bin/env python

import logging
from typing import Optional
import unittest.mock as umock

import pytest

pytest.importorskip("pandas")

import helpers.hcache_simple as hcacsimp
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.bookmark_utils as dshdbou
import dev_scripts_helpers.download.process_gsheet_links as dsgl

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_update_article_urls
# #############################################################################


class Test_update_article_urls(hunitest.TestCase):
    """
    Test `process_gsheet_links._update_article_urls()`.
    """

    def helper(self, rows: list, expected: Optional[str] = None) -> list:
        """
        Write `rows` as the HN CSV, run `_update_article_urls()`, and
        return the resulting rows.

        Runs inside the test's scratch space (via `hsystem.cd()`) so the
        script's fixed `./tmp.process_gsheet_links.*` paths land there
        instead of polluting (or depending on) the real working directory.

        :param rows: rows to write to the HN CSV (must all share the same
            columns, including `Hn_url` and `Article_url`)
        :param expected: expected `Article_url` of the first row, or
            `None` to skip that check (e.g., when the caller checks
            multiple rows itself)
        :return: rows read back from the URLs CSV
        """
        scratch_dir = self.get_scratch_space()
        columns = list(rows[0].keys())
        with hsystem.cd(scratch_dir):
            hn_csv = dshdbou.get_tmp_file_path(
                dsgl.HN_CSV_FILE, "process_gsheet_links"
            )
            dshdbou.write_csv(hn_csv, rows, fieldnames=columns)
            urls_csv = dsgl._update_article_urls()
            actual_rows = dshdbou.read_csv(urls_csv)
        if expected is not None:
            self.assert_equal(actual_rows[0]["Article_url"], expected)
        return actual_rows

    def helper_mock_hn_api(
        self,
        rows: list,
        extracted_url: str,
        expected: Optional[str],
    ) -> list:
        """
        Same as `helper()`, but also mocks `requests.get()` (the real
        external dependency behind `_extract_article_url()`) to return
        `extracted_url`, and disables on-disk caching so the mock is
        always exercised, even if a prior run already cached a result for
        the same HN item ID.

        :param rows: rows to write to the HN CSV
        :param extracted_url: article URL the mocked HN API responds with
        :param expected: expected `Article_url` of the first row, or
            `None` to skip that check (e.g., when the caller checks
            multiple rows itself)
        :return: rows read back from the URLs CSV
        """
        fake_response = umock.Mock()
        fake_response.json.return_value = {"url": extracted_url}
        hcacsimp.enable_caching(False)
        try:
            with umock.patch.object(
                dsgl.requests, "get", return_value=fake_response
            ):
                actual_rows = self.helper(rows)
        finally:
            hcacsimp.enable_caching(True)
        if expected is not None:
            self.assert_equal(actual_rows[0]["Article_url"], expected)
        return actual_rows

    def test1(self) -> None:
        """
        Test a non-HN `Hn_url` is copied as-is into `Article_url`.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Some article",
                "Hn_url": "https://example.com/a",
                "Article_url": "",
            },
        ]
        # Prepare outputs.
        expected = "https://example.com/a"
        # Run test and check outputs.
        self.helper(rows, expected)

    def test2(self) -> None:
        """
        Test an HN `Hn_url` is resolved through the HN API.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Some article",
                "Hn_url": "https://news.ycombinator.com/item?id=123",
                "Article_url": "",
            },
        ]
        # Prepare outputs.
        expected = "https://example.com/extracted"
        # Run test and check outputs.
        self.helper_mock_hn_api(rows, expected, expected)

    def test3(self) -> None:
        """
        Test a row with an already-filled `Article_url` is left untouched.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Some article",
                "Hn_url": "https://news.ycombinator.com/item?id=123",
                "Article_url": "https://example.com/existing",
            },
        ]
        # Prepare outputs.
        expected = "https://example.com/existing"
        # Run test and check outputs.
        self.helper(rows, expected)

    def test4(self) -> None:
        """
        Test multiple non-HN URLs are each copied as-is into
        `Article_url`.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Article A",
                "Hn_url": "https://example.com/a",
                "Article_url": "",
            },
            {
                "Title": "Article B",
                "Hn_url": "https://example.com/b",
                "Article_url": "",
            },
        ]
        # Prepare outputs.
        expected = ["https://example.com/a", "https://example.com/b"]
        # Run test.
        actual_rows = self.helper(rows)
        actual = [row["Article_url"] for row in actual_rows]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test5(self) -> None:
        """
        Test multiple HN URLs are each resolved independently through the
        HN API.
        """
        # Prepare inputs.
        extracted_url = "https://example.com/extracted"
        rows = [
            {
                "Title": "Article A",
                "Hn_url": "https://news.ycombinator.com/item?id=123",
                "Article_url": "",
            },
            {
                "Title": "Article B",
                "Hn_url": "https://news.ycombinator.com/item?id=456",
                "Article_url": "",
            },
        ]
        # Prepare outputs.
        expected = [extracted_url, extracted_url]
        # Run test.
        actual_rows = self.helper_mock_hn_api(rows, extracted_url, None)
        actual = [row["Article_url"] for row in actual_rows]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test6(self) -> None:
        """
        Test multiple rows with an already-filled `Article_url` are all
        left untouched.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Article A",
                "Hn_url": "https://news.ycombinator.com/item?id=123",
                "Article_url": "https://example.com/existing-a",
            },
            {
                "Title": "Article B",
                "Hn_url": "https://news.ycombinator.com/item?id=456",
                "Article_url": "https://example.com/existing-b",
            },
        ]
        # Prepare outputs.
        expected = [
            "https://example.com/existing-a",
            "https://example.com/existing-b",
        ]
        # Run test.
        actual_rows = self.helper(rows)
        actual = [row["Article_url"] for row in actual_rows]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_update_article_clusters
# #############################################################################


class Test_update_article_clusters(hunitest.TestCase):
    """
    Test `process_gsheet_links._update_article_clusters()`.
    """

    def helper(self, rows: list, expected: Optional[dict]) -> list:
        """
        Write `rows` as the tags CSV, run `_update_article_clusters()`, and
        return the resulting clustered rows.

        Runs inside the test's scratch space (via `hsystem.cd()`) so the
        script's fixed `./tmp.process_gsheet_links.*` paths land there
        instead of polluting (or depending on) the real working directory.

        :param rows: rows to write to the tags CSV (must all share the same
            columns)
        :param expected: expected first row of the clusters CSV, or `None`
            to skip that check (e.g., when the caller checks multiple rows
            itself)
        :return: rows read back from the clusters CSV
        """
        scratch_dir = self.get_scratch_space()
        columns = list(rows[0].keys())
        with hsystem.cd(scratch_dir):
            tags_csv = dshdbou.get_tmp_file_path(
                dsgl.TAGS_CSV_FILE, "process_gsheet_links"
            )
            dshdbou.write_csv(tags_csv, rows, fieldnames=columns)
            clusters_csv = dsgl._update_article_clusters()
            actual_rows = dshdbou.read_csv(clusters_csv)
        if expected is not None:
            self.assert_equal(str(actual_rows[0]), str(expected))
        return actual_rows

    def test1(self) -> None:
        """
        Test a tag wrapped in an explanatory sentence is normalized before
        the cluster lookup, instead of being left unclustered.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Some article",
                "Article_url": "https://example.com/a",
                "Article_tag": (
                    "The best tag for this article is **AI Agents**."
                ),
                "Article_cluster": "",
            },
        ]
        # Prepare outputs. The raw tag is left as-is; only the cluster is
        # filled in via the normalized tag.
        expected = {
            "Title": "Some article",
            "Article_url": "https://example.com/a",
            "Article_tag": rows[0]["Article_tag"],
            "Article_cluster": "AI",
        }
        # Run test and check outputs.
        self.helper(rows, expected)

    def test2(self) -> None:
        """
        Test a row with an already-filled `Article_cluster` is left
        untouched.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Some article",
                "Article_url": "https://example.com/a",
                "Article_tag": "Open Source",
                "Article_cluster": "Dev tools",
            },
        ]
        # Prepare outputs. The row is already fully filled in, so it is
        # left unchanged.
        expected = rows[0]
        # Run test and check outputs.
        self.helper(rows, expected)

    def test3(self) -> None:
        """
        Test a tag not present in `topic_to_cluster` (even after
        normalization) is left with an empty cluster instead of raising.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Some article",
                "Article_url": "https://example.com/a",
                "Article_tag": "Programming Languages",
                "Article_cluster": "",
            },
        ]
        # Prepare outputs. The tag is unrecognized, so the row is left
        # unchanged.
        expected = rows[0]
        # Run test and check outputs.
        self.helper(rows, expected)

    def test4(self) -> None:
        """
        Test multiple rows with a wrapped tag are each normalized and
        clustered independently.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Article A",
                "Article_url": "https://example.com/a",
                "Article_tag": (
                    "The best tag for this article is **AI Agents**."
                ),
                "Article_cluster": "",
            },
            {
                "Title": "Article B",
                "Article_url": "https://example.com/b",
                "Article_tag": (
                    "The best tag for this article is **Open Source**."
                ),
                "Article_cluster": "",
            },
        ]
        # Prepare outputs.
        expected = ["AI", "Dev tools"]
        # Run test.
        actual_rows = self.helper(rows, None)
        actual = [row["Article_cluster"] for row in actual_rows]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test5(self) -> None:
        """
        Test multiple rows with an already-filled `Article_cluster` are
        all left untouched.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Article A",
                "Article_url": "https://example.com/a",
                "Article_tag": "Open Source",
                "Article_cluster": "Dev tools",
            },
            {
                "Title": "Article B",
                "Article_url": "https://example.com/b",
                "Article_tag": "AI Agents",
                "Article_cluster": "AI",
            },
        ]
        # Prepare outputs.
        expected = ["Dev tools", "AI"]
        # Run test.
        actual_rows = self.helper(rows, None)
        actual = [row["Article_cluster"] for row in actual_rows]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test6(self) -> None:
        """
        Test multiple rows with an unrecognized tag are all left with an
        empty cluster.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Article A",
                "Article_url": "https://example.com/a",
                "Article_tag": "Programming Languages",
                "Article_cluster": "",
            },
            {
                "Title": "Article B",
                "Article_url": "https://example.com/b",
                "Article_tag": "Some Other Topic",
                "Article_cluster": "",
            },
        ]
        # Prepare outputs.
        expected = ["", ""]
        # Run test.
        actual_rows = self.helper(rows, None)
        actual = [row["Article_cluster"] for row in actual_rows]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_normalize_tag
# #############################################################################


class Test_normalize_tag(hunitest.TestCase):
    """
    Test `process_gsheet_links._normalize_tag()`.
    """

    def helper(self, raw_tag: str, expected: str) -> None:
        """
        Test helper for `_normalize_tag()`.

        :param raw_tag: raw text returned by the LLM
        :param expected: expected normalized tag
        """
        # Run test.
        actual = dsgl._normalize_tag(raw_tag)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a bare tag that already matches exactly.
        """
        # Prepare inputs.
        raw_tag = "AI Agents"
        # Prepare outputs.
        expected = raw_tag
        # Run test.
        self.helper(raw_tag, expected)

    def test2(self) -> None:
        """
        Test a case-insensitive exact match is normalized to the canonical
        casing.
        """
        # Prepare inputs.
        raw_tag = "open source"
        # Prepare outputs.
        expected = "Open Source"
        # Run test.
        self.helper(raw_tag, expected)

    def test3(self) -> None:
        """
        Test a tag wrapped in an explanatory sentence with markdown bold.
        """
        # Prepare inputs.
        raw_tag = (
            "The best tag for the article with the title and URL provided "
            "is **Open Source**."
        )
        # Prepare outputs.
        expected = "Open Source"
        # Run test.
        self.helper(raw_tag, expected)

    def test4(self) -> None:
        """
        Test a tag wrapped in a colon-style sentence.
        """
        # Prepare inputs.
        raw_tag = "The best tag for this article is: Open Source."
        # Prepare outputs.
        expected = "Open Source"
        # Run test.
        self.helper(raw_tag, expected)

    def test5(self) -> None:
        """
        Test a tag wrapped in double quotes inside a sentence.
        """
        # Prepare inputs.
        raw_tag = (
            'The best tag to represent the article is "Developer Tools."'
        )
        # Prepare outputs.
        expected = "Developer Tools"
        # Run test.
        self.helper(raw_tag, expected)

    def test6(self) -> None:
        """
        Test a tag invented by the LLM that is not in `topic_to_cluster` is
        returned unchanged (after stripping whitespace).
        """
        # Prepare inputs.
        raw_tag = "Programming Languages"
        # Prepare outputs.
        expected = raw_tag
        # Run test.
        self.helper(raw_tag, expected)

    def test7(self) -> None:
        """
        Test surrounding whitespace and trailing punctuation are stripped
        even when no known tag can be recognized.
        """
        # Prepare inputs.
        raw_tag = "  Some Unknown Tag.  "
        # Prepare outputs.
        expected = "Some Unknown Tag"
        # Run test.
        self.helper(raw_tag, expected)

    def test8(self) -> None:
        """
        Test the longest matching tag is preferred when a shorter tag would
        otherwise be a substring of a longer one.
        """
        # Prepare inputs.
        fake_tag_map = {
            "Agents": "X",
            "AI Agents": "Y",
        }
        raw_tag = "This article is about AI Agents in production."
        # Prepare outputs.
        expected = "AI Agents"
        # Run test. Pass a local `tag_map` through the public interface
        # instead of monkey-patching the internal `topic_to_cluster` dict.
        actual = dsgl._normalize_tag(raw_tag, tag_map=fake_tag_map)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test9(self) -> None:
        """
        Test an empty string input returns an empty string.
        """
        # Prepare inputs.
        raw_tag = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(raw_tag, expected)
