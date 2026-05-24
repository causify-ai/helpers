import logging

import linters2.lint_cc as l2lccc
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


class Test_infer_topic_from_filename(hunitest.TestCase):
    """
    Tests for `lint_cc._infer_topic_from_filename()` function.
    """

    def test1(self) -> None:
        """
        Test detection of Jupyter notebook files.
        """
        # Prepare inputs.
        filename = "example.ipynb"
        # Prepare outputs.
        expected = "notebook"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test2(self) -> None:
        """
        Test detection of README markdown files.
        """
        # Prepare inputs.
        filename = "README.md"
        # Prepare outputs.
        expected = "readme"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test3(self) -> None:
        """
        Test detection of tool-in-30-mins markdown files.
        """
        # Prepare inputs.
        filename = "tutorials/tool_X_in_30_mins.md"
        # Prepare outputs.
        expected = "tool_X_in_30_mins"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test4(self) -> None:
        """
        Test detection of tool-in-60-mins markdown files.
        """
        # Prepare inputs.
        filename = "tutorials/tool_X_in_60_mins.md"
        # Prepare outputs.
        expected = "tool_X_in_60_mins"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test5(self) -> None:
        """
        Test detection of skill markdown files.
        """
        # Prepare inputs.
        filename = ".claude/skills/coding.rules.md"
        # Prepare outputs.
        expected = "skill"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test6(self) -> None:
        """
        Test detection of regular markdown files.
        """
        # Prepare inputs.
        filename = "docs/guide.md"
        # Prepare outputs.
        expected = "markdown"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test7(self) -> None:
        """
        Test detection of Python test files.
        """
        # Prepare inputs.
        filename = "test_example.py"
        # Prepare outputs.
        expected = "testing"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test8(self) -> None:
        """
        Test detection of regular Python files.
        """
        # Prepare inputs.
        filename = "example.py"
        # Prepare outputs.
        expected = "coding"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test9(self) -> None:
        """
        Test detection of bash script files.
        """
        # Prepare inputs.
        filename = "script.sh"
        # Prepare outputs.
        expected = "bash"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test10(self) -> None:
        """
        Test detection of LaTeX files.
        """
        # Prepare inputs.
        filename = "document.tex"
        # Prepare outputs.
        expected = "latex"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test11(self) -> None:
        """
        Test detection of slides (txt) files.
        """
        # Prepare inputs.
        filename = "slides.txt"
        # Prepare outputs.
        expected = "slides"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test12(self) -> None:
        """
        Test that invalid file extensions raise ValueError.
        """
        # Prepare inputs.
        filename = "unsupported.xyz"
        # Run test and check outputs.
        with self.assertRaises(ValueError):
            l2lccc._infer_topic_from_filename(filename)

    def test13(self) -> None:
        """
        Test that function correctly extracts basename from full paths.
        """
        # Prepare inputs.
        filename = "/path/to/directory/test_module.py"
        # Prepare outputs.
        expected = "testing"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)

    def test14(self) -> None:
        """
        Test README detection works from any directory.
        """
        # Prepare inputs.
        filename = "subdir/README.md"
        # Prepare outputs.
        expected = "readme"
        # Run test.
        topic = l2lccc._infer_topic_from_filename(filename)
        # Check outputs.
        self.assertEqual(topic, expected)


class Test_get_rules_for_topic(hunitest.TestCase):
    """
    Tests for `lint_cc._get_rules_for_topic()` function.
    """

    def test1(self) -> None:
        """
        Test retrieval of coding topic rules.
        """
        # Prepare inputs.
        topic = "coding"
        # Run test.
        topic_info = l2lccc._get_rules_for_topic(topic)
        # Check outputs.
        self.assertIn("role", topic_info)
        self.assertIn("rules", topic_info)
        self.assertIn("templates", topic_info)
        self.assertTrue(topic_info["role"].endswith("role.coding.md"))
        self.assertGreater(len(topic_info["rules"]), 0)

    def test2(self) -> None:
        """
        Test retrieval of testing topic rules.
        """
        # Prepare inputs.
        topic = "testing"
        # Run test.
        topic_info = l2lccc._get_rules_for_topic(topic)
        # Check outputs.
        self.assertIn("rules", topic_info)
        self.assertTrue(
            any("testing" in r for r in topic_info["rules"])
        )

    def test3(self) -> None:
        """
        Test retrieval of markdown topic rules.
        """
        # Prepare inputs.
        topic = "markdown"
        # Run test.
        topic_info = l2lccc._get_rules_for_topic(topic)
        # Check outputs.
        self.assertGreater(len(topic_info["rules"]), 0)

    def test4(self) -> None:
        """
        Test retrieval of notebook topic rules.
        """
        # Prepare inputs.
        topic = "notebook"
        # Run test.
        topic_info = l2lccc._get_rules_for_topic(topic)
        # Check outputs.
        self.assertTrue(topic_info["run_jupytext"])

    def test5(self) -> None:
        """
        Test that readme topic has run_lint flag set.
        """
        # Prepare inputs.
        topic = "readme"
        # Run test.
        topic_info = l2lccc._get_rules_for_topic(topic)
        # Check outputs.
        self.assertTrue(topic_info["run_lint"])

    def test6(self) -> None:
        """
        Test that markdown topic has run_lint flag set.
        """
        # Prepare inputs.
        topic = "markdown"
        # Run test.
        topic_info = l2lccc._get_rules_for_topic(topic)
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
            l2lccc._get_rules_for_topic(topic)

    def test8(self) -> None:
        """
        Test that topic paths are prefixed with .claude paths.
        """
        # Prepare inputs.
        topic = "coding"
        # Run test.
        topic_info = l2lccc._get_rules_for_topic(topic)
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
            "bash", "blog", "book", "coding", "interactive_notebook",
            "latex", "markdown", "notebook", "readme", "skill", "slides",
            "testing", "tool_X_in_30_mins", "tool_X_in_60_mins",
        ]
        # Run test and check outputs.
        for topic in topics:
            topic_info = l2lccc._get_rules_for_topic(topic)
            self.assertIsNotNone(topic_info)
