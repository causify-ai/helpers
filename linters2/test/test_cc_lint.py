import argparse
import os
import pprint
import unittest.mock as umock
from typing import Any, Dict, List, Tuple

import helpers.hio as hio
import helpers.hmarkdown_headers as hmarhead
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

import pytest

pytest.importorskip("claude_agent_sdk")

import claude_agent_sdk

import dev_scripts_helpers.ai.cc_lib as dshaccli
import linters2.cc_lint as lcclint


# #############################################################################
# Test_infer_topic_from_filename
# #############################################################################


class Test_infer_topic_from_filename(hunitest.TestCase):
    """
    Tests for `cc_lint._infer_topic_from_filename()` function.
    """

    def helper(self, filename: str, expected: str) -> None:
        """
        Test helper for `_infer_topic_from_filename()`.

        :param filename: Input filename to test
        :param expected: Expected topic result
        """
        # Run test.
        topic = lcclint._infer_topic_from_filename(filename)
        # Check outputs.
        self.assert_equal(topic, expected)

    def test1(self) -> None:
        """
        Test detection of Jupyter notebook files.
        """
        # Prepare inputs.
        filename = "example.ipynb"
        # Prepare outputs.
        expected = "notebook"
        # Run test.
        self.helper(filename, expected)

    def test2(self) -> None:
        """
        Test detection of README markdown files.
        """
        # Prepare inputs.
        filename = "README.md"
        # Prepare outputs.
        expected = "readme"
        # Run test.
        self.helper(filename, expected)

    def test3(self) -> None:
        """
        Test detection of tool-in-30-mins markdown files.
        """
        # Prepare inputs.
        filename = "tutorials/tool_X_in_30_mins.md"
        # Prepare outputs.
        expected = "tool_X_in_30_mins"
        # Run test.
        self.helper(filename, expected)

    def test4(self) -> None:
        """
        Test detection of tool-in-60-mins markdown files.
        """
        # Prepare inputs.
        filename = "tutorials/tool_X_in_60_mins.md"
        # Prepare outputs.
        expected = "tool_X_in_60_mins"
        # Run test.
        self.helper(filename, expected)

    def test5(self) -> None:
        """
        Test detection of skill markdown files.
        """
        # Prepare inputs.
        filename = ".claude/skills/coding.rules.md"
        # Prepare outputs.
        expected = "skill"
        # Run test.
        self.helper(filename, expected)

    def test6(self) -> None:
        """
        Test detection of regular markdown files.
        """
        # Prepare inputs.
        filename = "docs/guide.md"
        # Prepare outputs.
        expected = "markdown"
        # Run test.
        self.helper(filename, expected)

    def test7(self) -> None:
        """
        Test detection of Python test files.
        """
        # Prepare inputs.
        filename = "test_example.py"
        # Prepare outputs.
        expected = "testing"
        # Run test.
        self.helper(filename, expected)

    def test8(self) -> None:
        """
        Test detection of regular Python files.
        """
        # Prepare inputs.
        filename = "example.py"
        # Prepare outputs.
        expected = "coding"
        # Run test.
        self.helper(filename, expected)

    def test9(self) -> None:
        """
        Test detection of bash script files.
        """
        # Prepare inputs.
        filename = "script.sh"
        # Prepare outputs.
        expected = "bash"
        # Run test.
        self.helper(filename, expected)

    def test10(self) -> None:
        """
        Test detection of LaTeX files.
        """
        # Prepare inputs.
        filename = "document.tex"
        # Prepare outputs.
        expected = "latex"
        # Run test.
        self.helper(filename, expected)

    def test11(self) -> None:
        """
        Test detection of slides (txt) files.
        """
        # Prepare inputs.
        filename = "slides.txt"
        # Prepare outputs.
        expected = "slides"
        # Run test.
        self.helper(filename, expected)

    def test12(self) -> None:
        """
        Test that invalid file extensions raise ValueError.
        """
        # Prepare inputs.
        filename = "unsupported.xyz"
        # Run test and check outputs.
        with self.assertRaises(ValueError):
            lcclint._infer_topic_from_filename(filename)

    def test13(self) -> None:
        """
        Test that function correctly extracts basename from full paths.
        """
        # Prepare inputs.
        filename = "/path/to/directory/test_module.py"
        # Prepare outputs.
        expected = "testing"
        # Run test.
        self.helper(filename, expected)

    def test14(self) -> None:
        """
        Test README detection works from any directory.
        """
        # Prepare inputs.
        filename = "subdir/README.md"
        # Prepare outputs.
        expected = "readme"
        # Run test.
        self.helper(filename, expected)


# #############################################################################
# Test_get_rules_for_topic
# #############################################################################


class Test_get_rules_for_topic(hunitest.TestCase):
    """
    Tests for `cc_lint._get_rules_for_topic()` function.
    """

    def helper(self, topic: str, expected: str) -> Dict[str, Any]:
        """
        Test helper for `_get_rules_for_topic()`.

        :param topic: topic name to retrieve rules for
        :param expected: expected string representation of `topic_info`
        :return: `topic_info` dict, for tests that need additional checks
        """
        # Run test.
        topic_info = lcclint._get_rules_for_topic(topic)
        # Check outputs.
        actual = pprint.pformat(topic_info)
        self.assert_equal(actual, expected, dedent=True)
        return topic_info

    def test1(self) -> None:
        """
        Test retrieval of coding topic rules.
        """
        # Prepare inputs.
        topic = "coding"
        # Prepare outputs.
        expected = """
        {'role': '.claude/skills/role.coding.md',
         'rules': ['.claude/skills/coding.rules.md'],
         'run_jupytext': False,
         'run_lint': False,
         'templates': ['.claude/templates/coding.template.py']}
        """
        # Run test.
        self.helper(topic, expected)

    def test2(self) -> None:
        """
        Test retrieval of testing topic rules.
        """
        # Prepare inputs.
        topic = "testing"
        # Prepare outputs.
        expected = """
        {'role': '.claude/skills/role.coding.md',
         'rules': ['.claude/skills/testing.rules.md'],
         'run_jupytext': False,
         'run_lint': False,
         'templates': ['.claude/templates/testing.template.py']}
        """
        # Run test.
        topic_info = self.helper(topic, expected)
        # Check outputs.
        self.assertIn("rules", topic_info)
        self.assertTrue(any("testing" in r for r in topic_info["rules"]))

    def test3(self) -> None:
        """
        Test retrieval of markdown topic rules.
        """
        # Prepare inputs.
        topic = "markdown"
        # Prepare outputs.
        expected = """
        {'role': '.claude/skills/role.ai_researcher.md',
         'rules': ['.claude/skills/markdown.rules.md', '.claude/skills/text.rules.md'],
         'run_jupytext': False,
         'run_lint': True,
         'templates': []}
        """
        # Run test.
        topic_info = self.helper(topic, expected)
        # Check outputs.
        self.assertGreater(len(topic_info["rules"]), 0)

    def test4(self) -> None:
        """
        Test retrieval of notebook topic rules.
        """
        # Prepare inputs.
        topic = "notebook"
        # Prepare outputs.
        expected = """
        {'role': '.claude/skills/role.notebook.md',
         'rules': ['.claude/skills/notebook.rules.md'],
         'run_jupytext': True,
         'run_lint': False,
         'templates': ['.claude/templates/notebook.template.ipynb',
                       '.claude/templates/notebook_utils_template.py']}
        """
        # Run test.
        topic_info = self.helper(topic, expected)
        # Check outputs.
        self.assertTrue(topic_info["run_jupytext"])

    def test5(self) -> None:
        """
        Test that readme topic has run_lint flag set.
        """
        # Prepare inputs.
        topic = "readme"
        # Prepare outputs.
        expected = """
        {'role': '.claude/skills/role.ai_researcher.md',
         'rules': ['.claude/skills/readme.rules.md'],
         'run_jupytext': False,
         'run_lint': True,
         'templates': []}
        """
        # Run test.
        topic_info = self.helper(topic, expected)
        # Check outputs.
        self.assertTrue(topic_info["run_lint"])

    def test6(self) -> None:
        """
        Test that markdown topic has run_lint flag set.
        """
        # Prepare inputs.
        topic = "markdown"
        # Prepare outputs.
        expected = """
        {'role': '.claude/skills/role.ai_researcher.md',
         'rules': ['.claude/skills/markdown.rules.md', '.claude/skills/text.rules.md'],
         'run_jupytext': False,
         'run_lint': True,
         'templates': []}
        """
        # Run test.
        topic_info = self.helper(topic, expected)
        # Check outputs.
        self.assertTrue(topic_info["run_lint"])

    def test7(self) -> None:
        """
        Test that invalid topic raises AssertionError.
        """
        # Prepare inputs.
        topic = "invalid_topic"
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            lcclint._get_rules_for_topic(topic)

    def test8(self) -> None:
        """
        Test that topic paths are prefixed with .claude paths.
        """
        # Prepare inputs.
        topic = "coding"
        # Prepare outputs.
        expected = """
        {'role': '.claude/skills/role.coding.md',
         'rules': ['.claude/skills/coding.rules.md'],
         'run_jupytext': False,
         'run_lint': False,
         'templates': ['.claude/templates/coding.template.py']}
        """
        # Run test.
        self.helper(topic, expected)

    def test9(self) -> None:
        """
        Test that all known topics can be retrieved.
        """
        # Prepare inputs.
        topics = [
            "bash",
            "blog",
            "book",
            "coding",
            "latex",
            "markdown",
            "notebook",
            "readme",
            "skill",
            "slides",
            "testing",
            "tool_X_in_30_mins",
            "tool_X_in_60_mins",
        ]
        # Run test and check outputs.
        for topic in topics:
            topic_info = lcclint._get_rules_for_topic(topic)
            self.assertIsNotNone(topic_info)


# #############################################################################
# Test_merge_small_chunks
# #############################################################################


class Test_merge_small_chunks(hunitest.TestCase):
    """
    Tests for `cc_lint._merge_small_chunks()` function.
    """

    def test1(self) -> None:
        """
        Test that two small chunks under the same parent H1 are packed
        into one, with the repeated H1 header line stripped.
        """
        # Prepare inputs.
        chunks = [
            lcclint.RuleChunk(
                title="A", content="# Chapter\n\n## A\nshort", order=0
            ),
            lcclint.RuleChunk(
                title="B", content="# Chapter\n\n## B\nshort", order=1
            ),
        ]
        max_tokens = 1500
        # Prepare outputs.
        expected = [
            lcclint.RuleChunk(
                title="A / B",
                content="# Chapter\n\n## A\nshort\n\n## B\nshort",
                order=0,
            )
        ]
        # Run test.
        actual = lcclint._merge_small_chunks(chunks, max_tokens=max_tokens)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test that chunks are kept unmerged when the combined size would
        exceed the token budget.
        """
        # Prepare inputs.
        chunks = [
            lcclint.RuleChunk(
                title="A", content="# Chapter\n\n## A\nshort", order=0
            ),
            lcclint.RuleChunk(
                title="B", content="# Chapter\n\n## B\nshort", order=1
            ),
        ]
        max_tokens = 1
        # Prepare outputs.
        expected = chunks
        # Run test.
        actual = lcclint._merge_small_chunks(chunks, max_tokens=max_tokens)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test that chunks under different parent H1s are never merged, even
        when both fit within the token budget.
        """
        # Prepare inputs.
        chunks = [
            lcclint.RuleChunk(
                title="A", content="# Chapter One\n\n## A\nshort", order=0
            ),
            lcclint.RuleChunk(
                title="B", content="# Chapter Two\n\n## B\nshort", order=1
            ),
        ]
        max_tokens = 1500
        # Prepare outputs.
        expected = chunks
        # Run test.
        actual = lcclint._merge_small_chunks(chunks, max_tokens=max_tokens)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test that an empty chunk list returns an empty list.
        """
        # Prepare inputs.
        chunks: List[lcclint.RuleChunk] = []
        max_tokens = 1500
        # Prepare outputs.
        expected: List[lcclint.RuleChunk] = []
        # Run test.
        actual = lcclint._merge_small_chunks(chunks, max_tokens=max_tokens)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_build_rule_chunks
# #############################################################################


class Test_build_rule_chunks(hunitest.TestCase):
    """
    Tests for `cc_lint._build_rule_chunks()` function.
    """

    def test1(self) -> None:
        """
        Test that the default level (H2) splits a two-H1, two-H2-each rule
        file into one chunk per H2 section, in file order.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        rules_content = """
            # Chapter One
            ## Section A
            Content A

            ## Section B
            Content B

            # Chapter Two
            ## Section C
            Content C
            """
        rules_content = hprint.dedent(rules_content)
        rule_file = os.path.join(scratch_dir, "test.rules.md")
        hio.to_file(rule_file, rules_content)
        topic_info = {"rules": [rule_file]}
        # Prepare outputs.
        expected = [
            lcclint.RuleChunk(
                title="Section A",
                content="# Chapter One\n## Section A\nContent A",
                order=0,
            ),
            lcclint.RuleChunk(
                title="Section B",
                content="# Chapter One\n\n## Section B\nContent B",
                order=1,
            ),
            lcclint.RuleChunk(
                title="Section C",
                content="# Chapter Two\n## Section C\nContent C",
                order=2,
            ),
        ]
        # Run test.
        actual = lcclint._build_rule_chunks(topic_info)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test that `merge_small_rules=True` packs the two H2 chunks under
        `# Chapter One` into one, leaving `# Chapter Two` unmerged.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        rules_content = """
            # Chapter One
            ## Section A
            Content A

            ## Section B
            Content B

            # Chapter Two
            ## Section C
            Content C
            """
        rules_content = hprint.dedent(rules_content)
        rule_file = os.path.join(scratch_dir, "test.rules.md")
        hio.to_file(rule_file, rules_content)
        topic_info = {"rules": [rule_file]}
        # Prepare outputs.
        expected = [
            lcclint.RuleChunk(
                title="Section A / Section B",
                content=(
                    "# Chapter One\n## Section A\nContent A\n\n"
                    "## Section B\nContent B"
                ),
                order=0,
            ),
            lcclint.RuleChunk(
                title="Section C",
                content="# Chapter Two\n## Section C\nContent C",
                order=1,
            ),
        ]
        # Run test.
        actual = lcclint._build_rule_chunks(
            topic_info, merge_small_rules=True, max_tokens=1500
        )
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test that `level=1` yields one chunk per H1 section, matching
        `hmarhead.extract_h1_sections_from_lines()`'s output.
        """
        # Prepare inputs.
        rule_file = ".claude/skills/testing.rules.md"
        topic_info = {"rules": [rule_file]}
        lines = hio.from_file(rule_file).split("\n")
        expected_sections = hmarhead.extract_h1_sections_from_lines(lines)
        # Prepare outputs.
        expected = [
            lcclint.RuleChunk(title=title, content=content, order=idx)
            for idx, (title, content) in enumerate(expected_sections)
        ]
        # Run test.
        actual = lcclint._build_rule_chunks(topic_info, level=1)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_filter_relevant_chunks
# #############################################################################


class Test_filter_relevant_chunks(hunitest.TestCase):
    """
    Tests for `cc_lint._filter_relevant_chunks()` function.
    """

    def helper(self, llm_reply: str, expected_titles: List[str]) -> None:
        """
        Filter a fixed 3-chunk candidate list with a mocked LLM reply and
        check the kept titles.

        :param llm_reply: raw text returned by the mocked
            `hllmcli.apply_llm()`
        :param expected_titles: expected `chunk.title` for every chunk kept
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "example.py")
        hio.to_file(file_path, "x = 1\n")
        chunks = [
            lcclint.RuleChunk(
                title="AWS Mocking", content="# Mocking\n\ncontent1", order=0
            ),
            lcclint.RuleChunk(
                title="Syscall Mocking",
                content="# Mocking\n\ncontent2",
                order=1,
            ),
            lcclint.RuleChunk(
                title="Test One Thing",
                content="# Testing Philosophy\n\ncontent3",
                order=2,
            ),
        ]
        # Run test.
        with umock.patch.object(
            lcclint.hllmcli, "apply_llm", return_value=(llm_reply, None)
        ):
            actual = lcclint._filter_relevant_chunks(file_path, chunks)
        # Check outputs.
        actual_titles = [chunk.title for chunk in actual]
        self.assert_equal(str(actual_titles), str(expected_titles))
        self.assert_equal(
            str([chunk.order for chunk in actual]),
            str(list(range(len(actual)))),
        )

    def test1(self) -> None:
        """
        Test that only the chunks named in the JSON list reply are kept.
        """
        # Prepare inputs.
        llm_reply = '["Test One Thing"]'
        # Prepare outputs.
        expected_titles = ["Test One Thing"]
        # Run test.
        self.helper(llm_reply, expected_titles)

    def test2(self) -> None:
        """
        Test that every chunk is kept when the reply is not valid JSON
        (fail open).
        """
        # Prepare inputs.
        llm_reply = "not json at all"
        # Prepare outputs.
        expected_titles = [
            "AWS Mocking",
            "Syscall Mocking",
            "Test One Thing",
        ]
        # Run test.
        self.helper(llm_reply, expected_titles)

    def test3(self) -> None:
        """
        Test that every chunk is kept when the reply selects zero chunks
        (fail open).
        """
        # Prepare inputs.
        llm_reply = "[]"
        # Prepare outputs.
        expected_titles = [
            "AWS Mocking",
            "Syscall Mocking",
            "Test One Thing",
        ]
        # Run test.
        self.helper(llm_reply, expected_titles)

    def test4(self) -> None:
        """
        Test that a JSON list reply wrapped in a Markdown code fence is
        still parsed correctly.
        """
        # Prepare inputs.
        llm_reply = '```json\n["AWS Mocking", "Syscall Mocking"]\n```'
        # Prepare outputs.
        expected_titles = ["AWS Mocking", "Syscall Mocking"]
        # Run test.
        self.helper(llm_reply, expected_titles)


# #############################################################################
# Test_order_chunks_by_dependency
# #############################################################################


class Test_order_chunks_by_dependency(hunitest.TestCase):
    """
    Tests for `cc_lint._order_chunks_by_dependency()` function.
    """

    def helper(self, llm_reply: str, expected_titles: List[str]) -> None:
        """
        Reorder a fixed 4-chunk candidate list with a mocked LLM reply and
        check the resulting title order.

        :param llm_reply: raw text returned by the mocked
            `hllmcli.apply_llm()`
        :param expected_titles: expected `chunk.title` order after sorting
        """
        # Prepare inputs.
        chunks = [
            lcclint.RuleChunk(
                title="Fix Formatting",
                content="# Style\n\ncontent1",
                order=0,
            ),
            lcclint.RuleChunk(
                title="Change Behavior",
                content="# Style\n\ncontent2",
                order=1,
            ),
            lcclint.RuleChunk(
                title="Reorg Code", content="# Style\n\ncontent3", order=2
            ),
            lcclint.RuleChunk(
                title="Checklist",
                content="# Verification\n\ncontent4",
                order=3,
            ),
        ]
        # Run test.
        with umock.patch.object(
            lcclint.hllmcli, "apply_llm", return_value=(llm_reply, None)
        ):
            actual = lcclint._order_chunks_by_dependency(chunks)
        # Check outputs.
        actual_titles = [chunk.title for chunk in actual]
        self.assert_equal(str(actual_titles), str(expected_titles))
        self.assert_equal(
            str([chunk.order for chunk in actual]),
            str(list(range(len(actual)))),
        )

    def test1(self) -> None:
        """
        Test that chunks sort semantic, then structural, then formatting,
        with the `# Verification` chunk always last even though it was
        categorized as `semantic`.
        """
        # Prepare inputs.
        llm_reply = """
        {"Fix Formatting": "formatting",
         "Change Behavior": "semantic",
         "Reorg Code": "structural",
         "Checklist": "semantic"}
        """
        # Prepare outputs.
        expected_titles = [
            "Change Behavior",
            "Reorg Code",
            "Fix Formatting",
            "Checklist",
        ]
        # Run test.
        self.helper(llm_reply, expected_titles)

    def test2(self) -> None:
        """
        Test that file order is preserved (a stable sort with every chunk
        defaulting to `structural`) when the reply is not valid JSON.
        """
        # Prepare inputs.
        llm_reply = "nonsense reply"
        # Prepare outputs.
        expected_titles = [
            "Fix Formatting",
            "Change Behavior",
            "Reorg Code",
            "Checklist",
        ]
        # Run test.
        self.helper(llm_reply, expected_titles)

    def test3(self) -> None:
        """
        Test that a chunk missing from the reply's category mapping
        defaults to `structural`.
        """
        # Prepare inputs.
        llm_reply = '{"Change Behavior": "semantic"}'
        # Prepare outputs.
        # `Fix Formatting` and `Reorg Code` both fall back to
        # `structural`, so they keep their relative file order after the
        # `semantic` chunk; `Checklist` stays last.
        expected_titles = [
            "Change Behavior",
            "Fix Formatting",
            "Reorg Code",
            "Checklist",
        ]
        # Run test.
        self.helper(llm_reply, expected_titles)


# #############################################################################
# Test_journal
# #############################################################################


class Test_journal(hunitest.TestCase):
    """
    Tests for `cc_lint`'s chunk journal helpers.
    """

    def test_load_journal_missing_file(self) -> None:
        """
        Test that loading a journal that does not exist yet returns `[]`.
        """
        # Prepare inputs.
        journal_file = os.path.join(self.get_scratch_space(), "journal.json")
        # Run test and check outputs.
        self.assertEqual(lcclint._load_journal(journal_file), [])

    def test_append_and_load_round_trip(self) -> None:
        """
        Test that entries appended across two calls round-trip through
        `_load_journal()` in append order.
        """
        # Prepare inputs.
        journal_file = os.path.join(self.get_scratch_space(), "journal.json")
        entry1 = {
            "file_path": "a.py",
            "chunk_title": "Rule One",
            "status": "done",
            "cost_usd": 0.01,
            "num_turns": 2,
        }
        entry2 = {
            "file_path": "a.py",
            "chunk_title": "Rule Two",
            "status": "no_op",
            "cost_usd": 0.02,
            "num_turns": 1,
        }
        # Run test.
        lcclint._append_journal_entries(journal_file, [entry1])
        lcclint._append_journal_entries(journal_file, [entry2])
        # Check outputs.
        self.assertEqual(lcclint._load_journal(journal_file), [entry1, entry2])

    def test_append_empty_is_a_no_op(self) -> None:
        """
        Test that appending an empty entry list does not create a file.
        """
        # Prepare inputs.
        journal_file = os.path.join(self.get_scratch_space(), "journal.json")
        # Run test.
        lcclint._append_journal_entries(journal_file, [])
        # Check outputs.
        self.assertFalse(os.path.exists(journal_file))

    def test_latest_status_uses_the_most_recent_entry(self) -> None:
        """
        Test that `_latest_journal_status()` returns the last entry when the
        same `(file_path, chunk_title)` appears more than once.
        """
        # Prepare inputs.
        journal = [
            {
                "file_path": "a.py",
                "chunk_title": "Rule One",
                "status": "failed",
                "cost_usd": None,
                "num_turns": 15,
            },
            {
                "file_path": "a.py",
                "chunk_title": "Rule One",
                "status": "done",
                "cost_usd": 0.01,
                "num_turns": 2,
            },
        ]
        # Run test and check outputs.
        self.assertEqual(
            lcclint._latest_journal_status(journal, "a.py", "Rule One"),
            "done",
        )

    def test_latest_status_missing_pair(self) -> None:
        """
        Test that `_latest_journal_status()` returns `None` for a pair with
        no entry.
        """
        # Run test and check outputs.
        self.assertIsNone(lcclint._latest_journal_status([], "a.py", "Rule One"))

    def test_status_from_chunk_stats(self) -> None:
        """
        Test that `_status_from_chunk_stats()` covers all four outcomes.
        """
        # Prepare inputs/outputs and run test.
        cases = [
            ({"is_error": True, "outcome": "NO-OP"}, "failed"),
            ({"is_error": False, "outcome": "NO-OP"}, "no_op"),
            (
                {"is_error": False, "outcome": "CHANGED: fixed x"},
                "done",
            ),
            ({"is_error": False, "outcome": "UNKNOWN"}, "failed"),
        ]
        for stats, expected_status in cases:
            actual_status = lcclint._status_from_chunk_stats(stats)
            self.assertEqual(actual_status, expected_status)

    def test_filter_resumable_drops_done_and_no_op(self) -> None:
        """
        Test that `_filter_resumable()` drops `done`/`no_op` chunks, keeps
        `failed`/unseen chunks, and journals a `"skipped"` entry for each
        dropped chunk.
        """
        # Prepare inputs.
        journal_file = os.path.join(self.get_scratch_space(), "journal.json")
        journal = [
            {
                "file_path": "a.py",
                "chunk_title": "Rule One",
                "status": "done",
                "cost_usd": 0.01,
                "num_turns": 2,
            },
            {
                "file_path": "a.py",
                "chunk_title": "Rule Two",
                "status": "no_op",
                "cost_usd": 0.0,
                "num_turns": 1,
            },
            {
                "file_path": "a.py",
                "chunk_title": "Rule Three",
                "status": "failed",
                "cost_usd": None,
                "num_turns": 15,
            },
        ]
        titled_messages = [
            ("Rule One", "msg one"),
            ("Rule Two", "msg two"),
            ("Rule Three", "msg three"),
            ("Rule Four", "msg four"),
        ]
        # Run test.
        kept = lcclint._filter_resumable(
            "a.py", titled_messages, journal, journal_file
        )
        # Check outputs.
        self.assertEqual(
            kept, [("Rule Three", "msg three"), ("Rule Four", "msg four")]
        )
        skipped = [
            entry["chunk_title"] for entry in lcclint._load_journal(journal_file)
        ]
        self.assertEqual(skipped, ["Rule One", "Rule Two"])


# #############################################################################
# Test_build_incremental_system_prompt
# #############################################################################


class Test_build_incremental_system_prompt(hunitest.TestCase):
    """
    Tests for `cc_lint._build_incremental_system_prompt()` function.
    """

    def helper(self, topic: str) -> Tuple[Dict[str, Any], str]:
        """
        Build `topic_info` and the corresponding system prompt for `topic`.

        :param topic: topic name passed to `_get_rules_for_topic()`
        :return: `(topic_info, system_prompt)`
        """
        topic_info = lcclint._get_rules_for_topic(topic)
        system_prompt = lcclint._build_incremental_system_prompt(topic_info)
        return topic_info, system_prompt

    def test1(self) -> None:
        """
        Test that the role content and the "do not change behavior" instruction
        are both included.
        """
        # Prepare inputs.
        topic = "coding"
        topic_info, system_prompt = self.helper(topic)
        role_content = hio.from_file(topic_info["role"])
        #
        instruction = (
            "You MUST make sure not to change the behavior or the intent "
            "of the passed file"
        )
        # Prepare outputs.
        expected = role_content + instruction
        # Run test.
        actual = system_prompt[: len(expected)]
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that templates are listed when the topic defines any.
        """
        # Prepare inputs.
        topic = "coding"
        topic_info, system_prompt = self.helper(topic)
        role_content = hio.from_file(topic_info["role"])
        instruction = (
            "You MUST make sure not to change the behavior or the intent "
            "of the passed file"
        )
        prefix_len = len(role_content) + len(instruction)
        # Prepare outputs.
        expected = (
            "You MUST follow the templates below:\n"
            f"- {topic_info['templates'][0]}"
        )
        # Run test.
        actual = system_prompt[prefix_len:]
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that no template section is added when the topic has none.
        """
        # Prepare inputs.
        topic = "bash"
        topic_info, system_prompt = self.helper(topic)
        role_content = hio.from_file(topic_info["role"])
        # Prepare outputs.
        expected = role_content + (
            "You MUST make sure not to change the behavior or the intent "
            "of the passed file"
        )
        # Run test and check outputs.
        self.assert_equal(system_prompt, expected)


# #############################################################################
# Test_build_rule_message
# #############################################################################


class Test_build_rule_message(hunitest.TestCase):
    """
    Tests for `cc_lint._build_rule_message()` function.
    """

    def helper(self, file_path: str, rule_content: str, expected: str) -> None:
        """
        Build the rule message and check it against `expected`.

        :param file_path: path of the file the rule applies to
        :param rule_content: H1 rule section content to apply
        :param expected: expected rule message
        """
        # Run test.
        actual = lcclint._build_rule_message(file_path, rule_content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test that the file path is named in every instruction line.
        """
        # Prepare inputs.
        file_path = "linters2/test/test_cc_lint.py"
        rule_content = "# Some Rule\nDo the thing."
        # Prepare outputs.
        # TODO(ai_gp): Use _expected_message
        header = f"""
        - Re-read `{file_path}` from disk
        - Apply ONLY the rule below to `{file_path}`
        - Do not revisit rules applied earlier
        """
        header = hprint.dedent(header)
        footer = """
        - Reply with exactly one line:
          - `LLM> NO-OP` if the file already complies with the rule
          - `LLM> CHANGED: <one-line summary>` if you made an edit
        """
        footer = hprint.dedent(footer)
        expected = f"{header}\n```\n{rule_content}\n```\n{footer}"
        # Run test.
        self.helper(file_path, rule_content, expected)

    def test2(self) -> None:
        """
        Test that the message requires the no-op contract reply.
        """
        # Prepare inputs.
        file_path = "example.py"
        rule_content = "# Rule\nContent"
        # Prepare outputs.
        # TODO(ai_gp): Use _expected_message
        header = f"""
        - Re-read `{file_path}` from disk
        - Apply ONLY the rule below to `{file_path}`
        - Do not revisit rules applied earlier
        """
        header = hprint.dedent(header)
        footer = """
        - Reply with exactly one line:
          - `LLM> NO-OP` if the file already complies with the rule
          - `LLM> CHANGED: <one-line summary>` if you made an edit
        """
        footer = hprint.dedent(footer)
        expected = f"{header}\n```\n{rule_content}\n```\n{footer}"
        # Run test.
        self.helper(file_path, rule_content, expected)


# #############################################################################
# Test_build_incremental_messages
# #############################################################################


def _expected_message(file_path: str, section_content: str) -> str:
    msg = []
    header = f"""
    - Re-read `{file_path}` from disk
    - Apply ONLY the rule below to `{file_path}`
    - Do not revisit rules applied earlier
    """
    header = hprint.dedent(header)
    msg.append(header)
    #
    msg.append("```")
    msg.append(section_content)
    msg.append("```")
    #
    footer = """
    - Reply with exactly one line:
      - `LLM> NO-OP` if the file already complies with the rule
      - `LLM> CHANGED: <one-line summary>` if you made an edit
    """
    footer = hprint.dedent(footer)
    msg.append(footer)
    #
    msg_as_str = "\n".join(msg)
    return msg_as_str


# #############################################################################
# Test_build_incremental_messages
# #############################################################################


class Test_build_incremental_messages(hunitest.TestCase):
    """
    Tests for `cc_lint._build_incremental_messages()` function.
    """

    def test1(self) -> None:
        """
        Test that one message is built per H1 rule section, each naming the
        file, and that the role content is not repeated in any message.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        rules_content = """
            # Rule One
            Content one

            # Rule Two
            Content two
            """
        rules_content = hprint.dedent(rules_content)
        rule_file = os.path.join(scratch_dir, "test.rules.md")
        hio.to_file(rule_file, rules_content)
        file_path = os.path.join(scratch_dir, "example.py")
        hio.to_file(file_path, "x = 1\n")
        topic_info = {
            "role": ".claude/skills/role.coding.md",
            "rules": [rule_file],
            "templates": [],
        }
        # Prepare outputs.
        expected = [
            (
                "Rule One",
                _expected_message(file_path, "# Rule One\nContent one"),
            ),
            (
                "Rule Two",
                _expected_message(file_path, "# Rule Two\nContent two"),
            ),
        ]
        # Run test.
        titled_messages = lcclint._build_incremental_messages(
            file_path, topic_info
        )
        # Check outputs.
        self.assert_equal(str(titled_messages), str(expected))
        role_content = hio.from_file(topic_info["role"])
        for _, msg in titled_messages:
            self.assertNotIn(role_content, msg)


# #############################################################################
# Test_build_incremental_messages_for_rule
# #############################################################################


class Test_build_incremental_messages_for_rule(hunitest.TestCase):
    """
    Tests for `cc_lint._build_incremental_messages_for_rule()` function.
    """

    def helper(
        self,
        file_path: str,
        rule_content: str,
        rule_spec: str,
        expected: List[Tuple[str, str]],
    ) -> None:
        """
        Build messages for `rule_content` and check them against `expected`.

        :param file_path: path of the file the rule applies to
        :param rule_content: rule text as returned by
            `hmarsele.extract_rule_from_file()`
        :param rule_spec: `--rule` value the messages are built for
        :param expected: expected list of `(chunk_title, message)` pairs
        """
        # Run test.
        actual = lcclint._build_incremental_messages_for_rule(
            file_path, rule_content, rule_spec
        )
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that a whole-file rule spec with two H1 sections is split into
        one message per section, titled by its own H1.
        """
        # Prepare inputs.
        file_path = "example.py"
        rule_spec = "test.rules.md"
        rule_content = """
            # Rule One
            Content one

            # Rule Two
            Content two
            """
        rule_content = hprint.dedent(rule_content)
        # Prepare outputs.
        expected = [
            (
                "Rule One",
                lcclint._build_rule_message(
                    file_path, "# Rule One\nContent one"
                ),
            ),
            (
                "Rule Two",
                lcclint._build_rule_message(
                    file_path, "# Rule Two\nContent two"
                ),
            ),
        ]
        # Run test.
        self.helper(file_path, rule_content, rule_spec, expected)

    def test2(self) -> None:
        """
        Test that a rule spec with zero H1 sections (a line-anchored extract
        starting below H1 level) is kept as a single message titled by
        `rule_spec`.
        """
        # Prepare inputs.
        file_path = "example.py"
        rule_spec = "test.rules.md:5"
        rule_content = "## Mark Private Functions\nSome content here."
        # Prepare outputs.
        expected = [
            (rule_spec, lcclint._build_rule_message(file_path, rule_content))
        ]
        # Run test.
        self.helper(file_path, rule_content, rule_spec, expected)

    def test3(self) -> None:
        """
        Test that a whole-file rule spec with a single H1 section is kept as
        a single message titled by `rule_spec`.
        """
        # Prepare inputs.
        file_path = "example.py"
        rule_spec = "test.rules.md"
        rule_content = "# Only Rule\nSome content."
        # Prepare outputs.
        expected = [
            (rule_spec, lcclint._build_rule_message(file_path, rule_content))
        ]
        # Run test.
        self.helper(file_path, rule_content, rule_spec, expected)


# #############################################################################
# Test_process_file_incremental_mode
# #############################################################################


class Test_process_file_incremental_mode(hunitest.TestCase):
    """
    Tests for `cc_lint._process_file()` on the `--mode stateless`/`session`
    branch.
    """

    def test1(self) -> None:
        """
        Test that `topic_info` stays populated in dry-run incremental mode.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "example.py")
        hio.to_file(file_path, "x = 1\n")
        args = argparse.Namespace(
            mode="stateless",
            skill="",
            rule="",
            topic="",
            dry_run=True,
            model="",
            rule_level=2,
            max_chunk_tokens=1500,
            merge_small_rules=False,
            filter_rules_by_relevance=False,
            order_rules_by_dependency=False,
            resume=False,
            journal_file=os.path.join(scratch_dir, "journal.json"),
            max_turns_per_chunk=15,
        )
        # Prepare outputs.
        expected_rc = 0
        expected_topic_info = """
        {'role': '.claude/skills/role.coding.md',
         'rules': ['.claude/skills/coding.rules.md'],
         'run_jupytext': False,
         'run_lint': False,
         'templates': ['.claude/templates/coding.template.py']}
        """
        # Run test.
        rc, topic_info = lcclint._process_file(file_path, args)
        # Check outputs.
        self.assertEqual(rc, expected_rc)
        actual_topic_info = pprint.pformat(topic_info)
        self.assert_equal(actual_topic_info, expected_topic_info, dedent=True)


# #############################################################################
# Test_process_file_one_shot
# #############################################################################


class Test_process_file_one_shot(hunitest.TestCase):
    """
    Test `cc_lint._process_file()` in `--mode one_shot` across {topic,
    skill, rule, default}, with the subprocess call mocked out (no network).
    """

    def helper(
        self,
        *,
        topic: str,
        skill: str,
        rule: str,
        expected_prompt_substring: str,
    ) -> None:
        """
        Run `_process_file()` in `one_shot` mode and check the dispatched
        prompt.

        :param topic: `--topic` value, or `""`
        :param skill: `--skill` value, or `""`
        :param rule: `--rule` value, or `""`
        :param expected_prompt_substring: text expected in the prompt written
            to `tmp.cc_lint.prompt.txt`
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "example.py")
        hio.to_file(file_path, "x = 1\n")
        args = argparse.Namespace(
            mode="one_shot",
            topic=topic,
            skill=skill,
            rule=rule,
            dry_run=False,
            model="",
        )
        # Run test.
        with (
            umock.patch.object(lcclint.hsystem, "system") as mock_system,
            umock.patch.object(
                lcclint.hmarsele,
                "find_skill",
                return_value=".claude/skills/coding.fix_inline.md",
            ),
        ):
            rc, topic_info = lcclint._process_file(file_path, args)
        # Check outputs.
        self.assertEqual(rc, 0)
        mock_system.assert_called_once()
        prompt_content = hio.from_file("tmp.cc_lint.prompt.txt")
        self.assertIn(expected_prompt_substring, prompt_content)
        self.assertIn(file_path, prompt_content)
        self.assertTrue(topic_info)

    def test1(self) -> None:
        """
        Test the default (filename-inferred topic) dispatch.
        """
        # Prepare inputs.
        topic = ""
        skill = ""
        rule = ""
        # Prepare outputs.
        expected_prompt_substring = "coding.rules.md"
        # Run test.
        self.helper(
            topic=topic,
            skill=skill,
            rule=rule,
            expected_prompt_substring=expected_prompt_substring,
        )

    def test2(self) -> None:
        """
        Test the explicit `--topic` dispatch.
        """
        # Prepare inputs.
        topic = "markdown"
        skill = ""
        rule = ""
        # Prepare outputs.
        expected_prompt_substring = "markdown.rules.md"
        # Run test.
        self.helper(
            topic=topic,
            skill=skill,
            rule=rule,
            expected_prompt_substring=expected_prompt_substring,
        )

    def test3(self) -> None:
        """
        Test the `--skill` dispatch.
        """
        # Prepare inputs.
        topic = ""
        skill = "coding.fix_inline"
        rule = ""
        # Prepare outputs.
        expected_prompt_substring = "/.claude/skills/coding.fix_inline.md"
        # Run test.
        self.helper(
            topic=topic,
            skill=skill,
            rule=rule,
            expected_prompt_substring=expected_prompt_substring,
        )

    def test4(self) -> None:
        """
        Test the `--rule` dispatch.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        rule_file = os.path.join(scratch_dir, "test.rules.md")
        hio.to_file(rule_file, "# My Rule\nDo the thing.\n")
        topic = ""
        skill = ""
        rule = rule_file
        # Prepare outputs.
        expected_prompt_substring = "# My Rule\nDo the thing."
        # Run test.
        self.helper(
            topic=topic,
            skill=skill,
            rule=rule,
            expected_prompt_substring=expected_prompt_substring,
        )


# #############################################################################
# Test_process_file_incremental
# #############################################################################


class Test_process_file_incremental(hunitest.TestCase):
    """
    Test `cc_lint._process_file()` in `--mode session`/`--mode stateless`
    across {topic, skill, rule, default}, against a fake SDK client (no
    network).
    """

    def helper(
        self,
        *,
        mode: str,
        topic: str,
        skill: str,
        rule: str,
        expected_num_messages: int,
        resume: bool = False,
        journal_file: str = "",
    ) -> List[str]:
        """
        Run `_process_file()` incrementally and check the dispatched
        message count.

        :param mode: `"session"` or `"stateless"`
        :param topic: `--topic` value, or `""`
        :param skill: `--skill` value, or `""`
        :param rule: `--rule` value, or `""`
        :param expected_num_messages: expected number of prompts queried
        :param resume: `--resume` value
        :param journal_file: `--journal_file` value, or `""` for a fresh
            scratch-space journal
        :return: prompts queried against the fake SDK client, for tests that
            need additional checks
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "example.py")
        hio.to_file(file_path, "x = 1\n")
        if not journal_file:
            journal_file = os.path.join(scratch_dir, "journal.json")
        args = argparse.Namespace(
            mode=mode,
            topic=topic,
            skill=skill,
            rule=rule,
            dry_run=False,
            model="",
            rule_level=2,
            max_chunk_tokens=1500,
            merge_small_rules=False,
            filter_rules_by_relevance=False,
            order_rules_by_dependency=False,
            resume=resume,
            journal_file=journal_file,
            max_turns_per_chunk=15,
        )
        msg = claude_agent_sdk.AssistantMessage(
            content=[claude_agent_sdk.TextBlock(text="LLM> NO-OP")],
            model="claude-test",
        )
        fake_client = dshaccli.FakeClaudeSDKClient(
            responses_by_call=[[msg]] * expected_num_messages
        )
        # Run test.
        with (
            umock.patch("claude_agent_sdk.ClaudeSDKClient") as mock_client_cls,
            umock.patch.object(
                lcclint.hmarsele,
                "find_skill",
                return_value=".claude/skills/coding.fix_inline.md",
            ),
        ):
            mock_client_cls.return_value = fake_client
            rc, topic_info = lcclint._process_file(file_path, args)
        # Check outputs.
        self.assertEqual(rc, 0)
        self.assertEqual(len(fake_client.queried_prompts), expected_num_messages)
        for prompt in fake_client.queried_prompts:
            self.assertIn(file_path, prompt)
        self.assertTrue(topic_info)
        return fake_client.queried_prompts

    def test1(self) -> None:
        """
        Test `--mode session` with the default (filename-inferred) topic.
        """
        # Prepare inputs.
        mode = "session"
        topic = ""
        skill = ""
        rule = ""
        # Prepare outputs.
        coding_topic_info = lcclint._get_rules_for_topic("coding")
        expected_num_messages = len(
            lcclint._build_rule_chunks(coding_topic_info)
        )
        # Run test.
        self.helper(
            mode=mode,
            topic=topic,
            skill=skill,
            rule=rule,
            expected_num_messages=expected_num_messages,
        )

    def test2(self) -> None:
        """
        Test `--mode session` with an explicit `--topic`.
        """
        # Prepare inputs.
        mode = "session"
        topic = "markdown"
        skill = ""
        rule = ""
        # Prepare outputs.
        markdown_topic_info = lcclint._get_rules_for_topic("markdown")
        expected_num_messages = len(
            lcclint._build_rule_chunks(markdown_topic_info)
        )
        # Run test.
        self.helper(
            mode=mode,
            topic=topic,
            skill=skill,
            rule=rule,
            expected_num_messages=expected_num_messages,
        )

    def test3(self) -> None:
        """
        Test `--mode session` with `--skill`.
        """
        # Prepare inputs.
        mode = "session"
        topic = ""
        skill = "coding.fix_inline"
        rule = ""
        # Prepare outputs.
        expected_num_messages = 1
        # Run test.
        prompts = self.helper(
            mode=mode,
            topic=topic,
            skill=skill,
            rule=rule,
            expected_num_messages=expected_num_messages,
        )
        # Check outputs.
        self.assertTrue(
            prompts[0].startswith("/.claude/skills/coding.fix_inline.md ")
        )

    def test4(self) -> None:
        """
        Test `--mode session` with `--rule`.
        """
        # Prepare inputs.
        mode = "session"
        scratch_dir = self.get_scratch_space()
        rule_file = os.path.join(scratch_dir, "test.rules.md")
        rule_content = """
            # Rule One
            Content one

            # Rule Two
            Content two
            """
        rule_content = hprint.dedent(rule_content)
        hio.to_file(rule_file, rule_content)
        topic = ""
        skill = ""
        rule = rule_file
        # Prepare outputs.
        expected_num_messages = 2
        # Run test.
        self.helper(
            mode=mode,
            topic=topic,
            skill=skill,
            rule=rule,
            expected_num_messages=expected_num_messages,
        )

    def test5(self) -> None:
        """
        Test `--mode stateless` with the default (filename-inferred) topic.
        """
        # Prepare inputs.
        mode = "stateless"
        topic = ""
        skill = ""
        rule = ""
        # Prepare outputs.
        coding_topic_info = lcclint._get_rules_for_topic("coding")
        expected_num_messages = len(
            lcclint._build_rule_chunks(coding_topic_info)
        )
        # Run test.
        self.helper(
            mode=mode,
            topic=topic,
            skill=skill,
            rule=rule,
            expected_num_messages=expected_num_messages,
        )

    def test6(self) -> None:
        """
        Test `--mode stateless` with an explicit `--topic`.
        """
        # Prepare inputs.
        mode = "stateless"
        topic = "markdown"
        skill = ""
        rule = ""
        # Prepare outputs.
        markdown_topic_info = lcclint._get_rules_for_topic("markdown")
        expected_num_messages = len(
            lcclint._build_rule_chunks(markdown_topic_info)
        )
        # Run test.
        self.helper(
            mode=mode,
            topic=topic,
            skill=skill,
            rule=rule,
            expected_num_messages=expected_num_messages,
        )

    def test7(self) -> None:
        """
        Test `--mode stateless` with `--skill`.
        """
        # Prepare inputs.
        mode = "stateless"
        topic = ""
        skill = "coding.fix_inline"
        rule = ""
        # Prepare outputs.
        expected_num_messages = 1
        # Run test.
        prompts = self.helper(
            mode=mode,
            topic=topic,
            skill=skill,
            rule=rule,
            expected_num_messages=expected_num_messages,
        )
        # Check outputs.
        self.assertTrue(
            prompts[0].startswith("/.claude/skills/coding.fix_inline.md ")
        )

    def test8(self) -> None:
        """
        Test `--mode stateless` with `--rule`.
        """
        # Prepare inputs.
        mode = "stateless"
        scratch_dir = self.get_scratch_space()
        rule_file = os.path.join(scratch_dir, "test.rules.md")
        rule_content = """
            # Rule One
            Content one

            # Rule Two
            Content two
            """
        rule_content = hprint.dedent(rule_content)
        hio.to_file(rule_file, rule_content)
        topic = ""
        skill = ""
        rule = rule_file
        # Prepare outputs.
        expected_num_messages = 2
        # Run test.
        self.helper(
            mode=mode,
            topic=topic,
            skill=skill,
            rule=rule,
            expected_num_messages=expected_num_messages,
        )

    def test9(self) -> None:
        """
        Test that a `--mode session` run journals each chunk's outcome,
        recording `NO-OP` replies as `"no_op"`.
        """
        # Prepare inputs.
        mode = "session"
        scratch_dir = self.get_scratch_space()
        rule_file = os.path.join(scratch_dir, "test.rules.md")
        rule_content = """
            # Rule One
            Content one

            # Rule Two
            Content two
            """
        rule_content = hprint.dedent(rule_content)
        hio.to_file(rule_file, rule_content)
        journal_file = os.path.join(scratch_dir, "journal.json")
        # Run test.
        self.helper(
            mode=mode,
            topic="",
            skill="",
            rule=rule_file,
            expected_num_messages=2,
            journal_file=journal_file,
        )
        # Check outputs.
        journal = lcclint._load_journal(journal_file)
        statuses = {entry["chunk_title"]: entry["status"] for entry in journal}
        self.assertEqual(statuses, {"Rule One": "no_op", "Rule Two": "no_op"})

    def test10(self) -> None:
        """
        Test that a second `--mode session --resume` run against the same
        journal skips every chunk already `no_op` and queries nothing.
        """
        # Prepare inputs.
        mode = "session"
        scratch_dir = self.get_scratch_space()
        rule_file = os.path.join(scratch_dir, "test.rules.md")
        rule_content = """
            # Rule One
            Content one

            # Rule Two
            Content two
            """
        rule_content = hprint.dedent(rule_content)
        hio.to_file(rule_file, rule_content)
        journal_file = os.path.join(scratch_dir, "journal.json")
        self.helper(
            mode=mode,
            topic="",
            skill="",
            rule=rule_file,
            expected_num_messages=2,
            journal_file=journal_file,
        )
        # Run test.
        prompts = self.helper(
            mode=mode,
            topic="",
            skill="",
            rule=rule_file,
            expected_num_messages=0,
            resume=True,
            journal_file=journal_file,
        )
        # Check outputs.
        self.assertEqual(prompts, [])
        # The resumed run journals a `"skipped"` entry for each chunk it
        # didn't re-send, on top of the first run's two `"no_op"` entries.
        journal = lcclint._load_journal(journal_file)
        skipped_titles = [
            entry["chunk_title"]
            for entry in journal
            if entry["status"] == "skipped"
        ]
        self.assertEqual(sorted(skipped_titles), ["Rule One", "Rule Two"])

    def test11(self) -> None:
        """
        Test that `--max_turns_per_chunk` is forwarded into
        `ClaudeAgentOptions.max_turns`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "example.py")
        hio.to_file(file_path, "x = 1\n")
        journal_file = os.path.join(scratch_dir, "journal.json")
        args = argparse.Namespace(
            mode="session",
            topic="",
            skill="coding.fix_inline",
            rule="",
            dry_run=False,
            model="",
            rule_level=2,
            max_chunk_tokens=1500,
            merge_small_rules=False,
            filter_rules_by_relevance=False,
            order_rules_by_dependency=False,
            resume=False,
            journal_file=journal_file,
            max_turns_per_chunk=3,
        )
        msg = claude_agent_sdk.AssistantMessage(
            content=[claude_agent_sdk.TextBlock(text="LLM> NO-OP")],
            model="claude-test",
        )
        fake_client = dshaccli.FakeClaudeSDKClient(responses_by_call=[[msg]])
        # Run test.
        with (
            umock.patch("claude_agent_sdk.ClaudeSDKClient") as mock_client_cls,
            umock.patch.object(
                lcclint.hmarsele,
                "find_skill",
                return_value=".claude/skills/coding.fix_inline.md",
            ),
        ):
            mock_client_cls.return_value = fake_client
            lcclint._process_file(file_path, args)
        # Check outputs.
        _, kwargs = mock_client_cls.call_args
        self.assertEqual(kwargs["options"].max_turns, 3)


# #############################################################################
# Test_process_file_end_to_end
# #############################################################################


@pytest.mark.skip(
    reason=(
        "Run manually: makes a real Claude Agent SDK/CLI call and costs tokens"
    )
)
class Test_process_file_end_to_end(hunitest.TestCase):
    """
    Exercise `cc_lint._process_file()` for real across {topic, skill, rule,
    default}, using the `--mode` selected by `_MODE`.
    """

    # Edit this to exercise a different `--mode` manually.
    _MODE = "stateless"
    # The cheapest available model, to keep manual runs inexpensive. Only
    # takes effect for `_MODE in ("session", "stateless")`:
    # `_run_claude_code()` does not forward `--model` to the `cc` wrapper.
    _MODEL = "claude-haiku-4-5-20251001"

    def helper(
        self, *, topic: str, skill: str, rule: str, expected_substring: str
    ) -> None:
        """
        Run `_process_file()` for real under `_MODE` and loosely check the
        outcome.

        :param topic: `--topic` value, or `""`
        :param skill: `--skill` value, or `""`
        :param rule: `--rule` value, or `""`
        :param expected_substring: substring expected in the prompt file
            written by the `one_shot` path; unused for `session`/`stateless`,
            which only expose a no-op contract outcome, not the prompt text
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "example.py")
        hio.to_file(file_path, "x = 1\n")
        args = argparse.Namespace(
            mode=self._MODE,
            topic=topic,
            skill=skill,
            rule=rule,
            dry_run=False,
            model=self._MODEL,
            rule_level=2,
            max_chunk_tokens=1500,
            merge_small_rules=False,
            filter_rules_by_relevance=False,
            order_rules_by_dependency=False,
        )
        # Run test.
        rc, topic_info = lcclint._process_file(file_path, args)
        # Check outputs.
        self.assertEqual(rc, 0)
        self.assertTrue(topic_info)
        if self._MODE == "one_shot":
            prompt_content = hio.from_file("tmp.cc_lint.prompt.txt")
            self.assertIn(expected_substring, prompt_content)

    def test1(self) -> None:
        """
        Test the default (filename-inferred topic) dispatch.
        """
        # Prepare inputs.
        topic = ""
        skill = ""
        rule = ""
        # Prepare outputs.
        expected_substring = "coding.rules.md"
        # Run test.
        self.helper(
            topic=topic,
            skill=skill,
            rule=rule,
            expected_substring=expected_substring,
        )

    def test2(self) -> None:
        """
        Test the explicit `--topic` dispatch.
        """
        # Prepare inputs.
        topic = "markdown"
        skill = ""
        rule = ""
        # Prepare outputs.
        expected_substring = "markdown.rules.md"
        # Run test.
        self.helper(
            topic=topic,
            skill=skill,
            rule=rule,
            expected_substring=expected_substring,
        )

    def test3(self) -> None:
        """
        Test the `--skill` dispatch.
        """
        # Prepare inputs.
        topic = ""
        skill = "coding.fix_inline"
        rule = ""
        # Prepare outputs.
        expected_substring = "coding.fix_inline"
        # Run test.
        self.helper(
            topic=topic,
            skill=skill,
            rule=rule,
            expected_substring=expected_substring,
        )

    def test4(self) -> None:
        """
        Test the `--rule` dispatch.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        rule_file = os.path.join(scratch_dir, "test.rules.md")
        hio.to_file(rule_file, 
                    # TODO(ai_gp): Use """
                    "# My Rule\nReply with exactly the word OK.\n")
        topic = ""
        skill = ""
        rule = rule_file
        # Prepare outputs.
        expected_substring = "My Rule"
        # Run test.
        self.helper(
            topic=topic,
            skill=skill,
            rule=rule,
            expected_substring=expected_substring,
        )


# #############################################################################
# Test_parse
# #############################################################################


class Test_parse(hunitest.TestCase):
    """
    Tests for `cc_lint._parse()` function.
    """

    def helper(self, argv: List[str], expected_mode: str) -> None:
        """
        Parse `argv` with the `cc_lint` argument parser and check `--mode`.

        :param argv: command-line arguments to parse
        :param expected_mode: expected value of `args.mode`
        """
        # Prepare inputs.
        parser = lcclint._parse()
        # Run test.
        args = parser.parse_args(argv)
        # Check outputs.
        self.assert_equal(args.mode, expected_mode)

    def helper2(self, argv: List[str], expected: Dict[str, Any]) -> None:
        """
        Parse `argv` and check the rule-chunking args against `expected`.

        :param argv: command-line arguments to parse
        :param expected: expected `{attr_name: value}` for every
            rule-chunking arg (`rule_level`, `max_chunk_tokens`,
            `merge_small_rules`, `filter_rules_by_relevance`,
            `order_rules_by_dependency`)
        """
        # Prepare inputs.
        parser = lcclint._parse()
        # Run test.
        args = parser.parse_args(argv)
        # Check outputs.
        actual = {name: getattr(args, name) for name in expected}
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that `--mode` defaults to `one_shot`.
        """
        # Prepare inputs.
        argv: List[str] = []
        # Prepare outputs.
        expected_mode = "one_shot"
        # Run test.
        self.helper(argv, expected_mode)

    def test2(self) -> None:
        """
        Test that `--mode` accepts `session`.
        """
        # Prepare inputs.
        argv = ["--mode", "session"]
        # Prepare outputs.
        expected_mode = "session"
        # Run test.
        self.helper(argv, expected_mode)

    def test3(self) -> None:
        """
        Test that `--mode` accepts `stateless`.
        """
        # Prepare inputs.
        argv = ["--mode", "stateless"]
        # Prepare outputs.
        expected_mode = "stateless"
        # Run test.
        self.helper(argv, expected_mode)

    def test4(self) -> None:
        """
        Test that `--mode` rejects values outside the choice set.
        """
        # Prepare inputs.
        parser = lcclint._parse()
        argv = ["--mode", "bogus"]
        # Run test and check outputs.
        with self.assertRaises(SystemExit):
            parser.parse_args(argv)

    def test5(self) -> None:
        """
        Test the default values of the rule-chunking args.
        """
        # Prepare inputs.
        argv: List[str] = []
        # Prepare outputs.
        expected = {
            "rule_level": 2,
            "max_chunk_tokens": 1500,
            "merge_small_rules": False,
            "filter_rules_by_relevance": False,
            "order_rules_by_dependency": False,
        }
        # Run test.
        self.helper2(argv, expected)

    def test6(self) -> None:
        """
        Test that `--rule_level` and `--max_chunk_tokens` parse as `int`.
        """
        # Prepare inputs.
        argv = ["--rule_level", "1", "--max_chunk_tokens", "500"]
        # Prepare outputs.
        expected = {"rule_level": 1, "max_chunk_tokens": 500}
        # Run test.
        self.helper2(argv, expected)

    def test7(self) -> None:
        """
        Test that `--merge_small_rules`, `--filter_rules_by_relevance`, and
        `--order_rules_by_dependency` are independent boolean switches.
        """
        # Prepare inputs.
        argv = [
            "--merge_small_rules",
            "--filter_rules_by_relevance",
            "--order_rules_by_dependency",
        ]
        # Prepare outputs.
        expected = {
            "merge_small_rules": True,
            "filter_rules_by_relevance": True,
            "order_rules_by_dependency": True,
        }
        # Run test.
        self.helper2(argv, expected)
