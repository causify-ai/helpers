import argparse
import os
import pprint
from typing import Any, Dict

import linters2.lint_cc as llincc
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


# #############################################################################
# Test_infer_topic_from_filename
# #############################################################################


class Test_infer_topic_from_filename(hunitest.TestCase):
    """
    Tests for `lint_cc._infer_topic_from_filename()` function.
    """

    def helper(self, filename: str, expected: str) -> None:
        """
        Test helper for `_infer_topic_from_filename()`.

        :param filename: Input filename to test
        :param expected: Expected topic result
        """
        # Run test.
        topic = llincc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

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
            llincc._infer_topic_from_filename(filename)

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
    Tests for `lint_cc._get_rules_for_topic()` function.
    """

    def helper(self, topic: str, expected: str) -> Dict[str, Any]:
        """
        Test helper for `_get_rules_for_topic()`.

        :param topic: topic name to retrieve rules for
        :param expected: expected string representation of `topic_info`
        :return: `topic_info` dict, for tests that need additional checks
        """
        # Run test.
        topic_info = llincc._get_rules_for_topic(topic)
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
            llincc._get_rules_for_topic(topic)

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
        topic_info = self.helper(topic, expected)
        # Check outputs.
        self.assertTrue(topic_info["role"].startswith(".claude/skills/"))
        for rule in topic_info["rules"]:
            self.assertTrue(rule.startswith(".claude/skills/"))
        for template in topic_info["templates"]:
            self.assertTrue(template.startswith(".claude/templates/"))

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
            topic_info = llincc._get_rules_for_topic(topic)
            self.assertIsNotNone(topic_info)


# #############################################################################
# Test_extract_h1_sections
# #############################################################################


class Test_extract_h1_sections(hunitest.TestCase):
    """
    Tests for `lint_cc._extract_h1_sections()` function.
    """

    def test1(self) -> None:
        """
        Test extraction of H1 sections from a simple markdown file.
        """
        # Prepare inputs.
        content = """
            # Section 1
            Content for section 1

            ## Subsection 1.1
            More content

            # Section 2
            Content for section 2

            ## Subsection 2.1
            More content
            """
        content = hprint.dedent(content)
        # Prepare outputs.
        expected = r"""
        [('Section 1',
          '# Section 1\nContent for section 1\n\n## Subsection 1.1\nMore content'),
         ('Section 2',
          '# Section 2\nContent for section 2\n\n## Subsection 2.1\nMore content')]
        """
        # Run test.
        self._helper(content, expected)

    def test2(self) -> None:
        """
        Test extraction of H1 sections from testing.rules.md.
        """
        # Prepare inputs.
        rule_file = "./.claude/skills/testing.rules.md"
        # Run test.
        sections = llincc._extract_h1_sections(rule_file)
        # Check outputs.
        self.assertGreater(len(sections), 0)
        # Verify we have expected H1 sections.
        # `rule_file` is the live `testing.rules.md` doc, whose H1 section
        # content changes often; hardwiring its full text as `expected` for
        # `assert_equal` would be large and brittle, so property-based checks
        # are kept instead.
        titles = [title for title, _ in sections]
        self.assertIn("Testing Philosophy", titles)
        self.assertIn("Test Coverage", titles)

    def test3(self) -> None:
        """
        Test that H1 sections include their content.
        """
        # Prepare inputs.
        content = """# Header 1
Line 1
Line 2

### Subsection
Line 3

# Header 2
Line 4
"""
        # Prepare outputs.
        expected = r"""
        [('Header 1', '# Header 1\nLine 1\nLine 2\n\n### Subsection\nLine 3'),
         ('Header 2', '# Header 2\nLine 4')]
        """
        # Run test.
        self._helper(content, expected)

    def _helper(self, content: str, expected: str) -> None:
        """
        Write `content` to a scratch markdown file and check the extracted
        H1 sections against `expected`.

        :param content: markdown content to write to the scratch file
        :param expected: expected `pprint.pformat()` output of the
            extracted sections
        """
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "test.md")
        hio.to_file(file_path, content)
        # Run test.
        sections = llincc._extract_h1_sections(file_path)
        # Check outputs.
        actual = pprint.pformat(sections)
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_process_file_apply_incrementally
# #############################################################################


class Test_process_file_apply_incrementally(hunitest.TestCase):
    """
    Tests for `lint_cc._process_file()` on the `--apply_incrementally` branch.
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
            apply_incrementally=True,
            skill="",
            rule="",
            topic="",
            dry_run=True,
            model="",
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
        rc, topic_info = llincc._process_file(file_path, args)
        # Check outputs.
        self.assertEqual(rc, expected_rc)
        actual_topic_info = pprint.pformat(topic_info)
        self.assert_equal(actual_topic_info, expected_topic_info, dedent=True)
