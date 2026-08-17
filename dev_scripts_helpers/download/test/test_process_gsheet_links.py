#!/usr/bin/env python

import os
import unittest.mock as umock

import pytest

pytest.importorskip("pandas")

import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.bookmark_utils as dshdbou
import dev_scripts_helpers.download.process_gsheet_links as dsgl


# #############################################################################
# Test__normalize_tag
# #############################################################################


class Test__normalize_tag(hunitest.TestCase):
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
        expected = "AI Agents"
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
        expected = "Programming Languages"
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
        fake_topic_to_cluster = {
            "Agents": "X",
            "AI Agents": "Y",
        }
        raw_tag = "This article is about AI Agents in production."
        # Prepare outputs.
        expected = "AI Agents"
        # Run test.
        with umock.patch.object(
            dsgl, "topic_to_cluster", fake_topic_to_cluster
        ):
            actual = dsgl._normalize_tag(raw_tag)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test__update_article_urls
# #############################################################################


class Test__update_article_urls(hunitest.TestCase):
    """
    Test `process_gsheet_links._update_article_urls()`.
    """

    def helper(self, rows: list) -> list:
        """
        Write `rows` as the HN CSV, run `_update_article_urls()`, and
        return the resulting rows.

        Redirects the script's fixed `./tmp.process_gsheet_links.*` paths
        into the test's scratch space so the test does not pollute (or
        depend on) the current working directory.

        :param rows: rows to write to the HN CSV (must all share the same
            columns, including `Hn_url` and `Article_url`)
        :return: rows read back from the URLs CSV
        """
        scratch_dir = self.get_scratch_space()

        def _get_tmp_file_path(filename: str, prefix: str) -> str:
            return os.path.join(scratch_dir, f"tmp.{prefix}.{filename}")

        columns = list(rows[0].keys())
        hn_csv = _get_tmp_file_path(dsgl.HN_CSV_FILE, "process_gsheet_links")
        dshdbou.write_csv(hn_csv, rows, fieldnames=columns)
        with umock.patch.object(
            dsgl.dshdbou,
            "get_tmp_file_path",
            side_effect=_get_tmp_file_path,
        ):
            urls_csv = dsgl._update_article_urls()
        actual_rows = dshdbou.read_csv(urls_csv)
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
        # TODO(ai_gp): Add "Prepare outputs." section to define expected values explicitly (testing.rules.md:## Use Three Sections in Testing Methods)
        # Run test.
        actual_rows = self.helper(rows)
        # Check outputs.
        self.assert_equal(
            actual_rows[0]["Article_url"], "https://example.com/a"
        )

    def test2(self) -> None:
        """
        Test an HN `Hn_url` is resolved through `_extract_article_url()`.
        """
        # Prepare inputs.
        rows = [
            {
                "Title": "Some article",
                "Hn_url": "https://news.ycombinator.com/item?id=123",
                "Article_url": "",
            },
        ]
        # TODO(ai_gp): Add "Prepare outputs." section to define expected values explicitly (testing.rules.md:## Use Three Sections in Testing Methods)
        # Run test.
        with umock.patch.object(
            dsgl,
            "_extract_article_url",
            return_value="https://example.com/extracted",
        ):
            actual_rows = self.helper(rows)
        # Check outputs.
        self.assert_equal(
            actual_rows[0]["Article_url"], "https://example.com/extracted"
        )

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
        # TODO(ai_gp): Add "Prepare outputs." section to define expected values explicitly (testing.rules.md:## Use Three Sections in Testing Methods)
        # Run test.
        actual_rows = self.helper(rows)
        # Check outputs.
        self.assert_equal(
            actual_rows[0]["Article_url"], "https://example.com/existing"
        )


# #############################################################################
# Test__update_article_clusters
# #############################################################################


class Test__update_article_clusters(hunitest.TestCase):
    """
    Test `process_gsheet_links._update_article_clusters()`.
    """

    # TODO(ai_gp): Rename helper method from `_run_with_tags` to `helper` to follow naming convention for helper methods (testing.rules.md:## Order Helper Methods First in Test Classes)
    def _run_with_tags(self, rows: list) -> list:
        """
        Write `rows` as the tags CSV, run `_update_article_clusters()`, and
        return the resulting clustered rows.

        Redirects the script's fixed `./tmp.process_gsheet_links.*` paths
        into the test's scratch space so the test does not pollute (or
        depend on) the current working directory.

        :param rows: rows to write to the tags CSV (must all share the same
            columns)
        :return: rows read back from the clusters CSV
        """
        scratch_dir = self.get_scratch_space()

        def _get_tmp_file_path(filename: str, prefix: str) -> str:
            return os.path.join(scratch_dir, f"tmp.{prefix}.{filename}")

        columns = list(rows[0].keys())
        tags_csv = _get_tmp_file_path(
            dsgl.TAGS_CSV_FILE, "process_gsheet_links"
        )
        dshdbou.write_csv(tags_csv, rows, fieldnames=columns)
        with umock.patch.object(
            dsgl.dshdbou,
            "get_tmp_file_path",
            side_effect=_get_tmp_file_path,
        ):
            clusters_csv = dsgl._update_article_clusters()
        actual_rows = dshdbou.read_csv(clusters_csv)
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
        # TODO(ai_gp): Add "Prepare outputs." section to define expected values explicitly (testing.rules.md:## Use Three Sections in Testing Methods)
        # Run test.
        actual_rows = self._run_with_tags(rows)
        # Check outputs. The raw tag is left as-is; only the cluster is
        # filled in via the normalized tag.
        self.assert_equal(
            actual_rows[0]["Article_tag"],
            "The best tag for this article is **AI Agents**.",
        )
        self.assert_equal(actual_rows[0]["Article_cluster"], "AI")

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
        # TODO(ai_gp): Add "Prepare outputs." section to define expected values explicitly (testing.rules.md:## Use Three Sections in Testing Methods)
        # Run test.
        actual_rows = self._run_with_tags(rows)
        # Check outputs.
        self.assert_equal(actual_rows[0]["Article_cluster"], "Dev tools")

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
        # TODO(ai_gp): Add "Prepare outputs." section to define expected values explicitly (testing.rules.md:## Use Three Sections in Testing Methods)
        # Run test.
        actual_rows = self._run_with_tags(rows)
        # Check outputs.
        self.assert_equal(actual_rows[0]["Article_cluster"], "")
