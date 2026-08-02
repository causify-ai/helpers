import argparse
import os
import pprint
import unittest.mock as umock
from typing import Any, Dict, List, Tuple

import helpers.hio as hio
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
            with self.subTest(topic=topic):
                topic_info = lcclint._get_rules_for_topic(topic)
                self.assertIsNotNone(topic_info)


# #############################################################################
# Test_extract_h1_sections
# #############################################################################


class Test_extract_h1_sections(hunitest.TestCase):
    """
    Tests for `cc_lint._extract_h1_sections()` function.
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
        sections = lcclint._extract_h1_sections(rule_file)
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
        sections = lcclint._extract_h1_sections(file_path)
        # Check outputs.
        actual = pprint.pformat(sections)
        self.assert_equal(actual, expected, dedent=True)


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

    def helper(
        self, file_path: str, rule_content: str, expected: str
    ) -> None:
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
        # TODO(ai_gp): Use """ and dedent
        expected = (
            f"Re-read `{file_path}` from disk\n"
            f"Apply ONLY the rule below to `{file_path}`\n"
            "Do not revisit rules applied earlier\n"
            f"{rule_content}\n\n"
            "Reply with exactly one line:\n"
            "- `LLM> NO-OP` if the file already complies with the rule\n"
            "- `LLM> CHANGED: <one-line summary>` if you made an edit"
        )
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
        # TODO(ai_gp): Use """ and dedent
        expected = (
            f"Re-read `{file_path}` from disk\n"
            f"Apply ONLY the rule below to `{file_path}`\n"
            "Do not revisit rules applied earlier\n"
            f"{rule_content}\n\n"
            "Reply with exactly one line:\n"
            "- `LLM> NO-OP` if the file already complies with the rule\n"
            "- `LLM> CHANGED: <one-line summary>` if you made an edit"
        )
        # Run test.
        self.helper(file_path, rule_content, expected)


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
        def _expected_message(section_content: str) -> str:
            # TODO(ai_gp): Use """ and dedent
            return (
                f"Re-read `{file_path}` from disk\n"
                f"Apply ONLY the rule below to `{file_path}`\n"
                "Do not revisit rules applied earlier\n"
                f"{section_content}\n\n"
                "Reply with exactly one line:\n"
                "- `LLM> NO-OP` if the file already complies with the rule\n"
                "- `LLM> CHANGED: <one-line summary>` if you made an edit"
            )

        # Prepare outputs.
        expected = [
            _expected_message("# Rule One\nContent one"),
            _expected_message("# Rule Two\nContent two"),
        ]
        # Run test.
        messages = lcclint._build_incremental_messages(file_path, topic_info)
        # Check outputs.
        self.assert_equal(str(messages), str(expected))
        role_content = hio.from_file(topic_info["role"])
        for msg in messages:
            self.assertNotIn(role_content, msg)


# #############################################################################
# Test_build_incremental_messages_for_rule
# #############################################################################


class Test_build_incremental_messages_for_rule(hunitest.TestCase):
    """
    Tests for `cc_lint._build_incremental_messages_for_rule()` function.
    """

    def helper(
        self, file_path: str, rule_content: str, expected: List[str]
    ) -> None:
        """
        Build messages for `rule_content` and check them against `expected`.

        :param file_path: path of the file the rule applies to
        :param rule_content: rule text as returned by
            `hmarsele.extract_rule_from_file()`
        :param expected: expected list of messages
        """
        # Run test.
        actual = lcclint._build_incremental_messages_for_rule(
            file_path, rule_content
        )
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that a whole-file rule spec with two H1 sections is split into
        one message per section.
        """
        # Prepare inputs.
        file_path = "example.py"
        rule_content = """
            # Rule One
            Content one

            # Rule Two
            Content two
            """
        rule_content = hprint.dedent(rule_content)
        # Prepare outputs.
        expected = [
            lcclint._build_rule_message(
                file_path, "# Rule One\nContent one"
            ),
            lcclint._build_rule_message(
                file_path, "# Rule Two\nContent two"
            ),
        ]
        # Run test.
        self.helper(file_path, rule_content, expected)

    def test2(self) -> None:
        """
        Test that a rule spec with zero H1 sections (a line-anchored extract
        starting below H1 level) is kept as a single message.
        """
        # Prepare inputs.
        file_path = "example.py"
        rule_content = "## Mark Private Functions\nSome content here."
        # Prepare outputs.
        expected = [lcclint._build_rule_message(file_path, rule_content)]
        # Run test.
        self.helper(file_path, rule_content, expected)

    def test3(self) -> None:
        """
        Test that a whole-file rule spec with a single H1 section is kept as
        a single message.
        """
        # Prepare inputs.
        file_path = "example.py"
        rule_content = "# Only Rule\nSome content."
        # Prepare outputs.
        expected = [lcclint._build_rule_message(file_path, rule_content)]
        # Run test.
        self.helper(file_path, rule_content, expected)


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
    ) -> List[str]:
        """
        Run `_process_file()` incrementally and check the dispatched
        message count.

        :param mode: `"session"` or `"stateless"`
        :param topic: `--topic` value, or `""`
        :param skill: `--skill` value, or `""`
        :param rule: `--rule` value, or `""`
        :param expected_num_messages: expected number of prompts queried
        :return: prompts queried against the fake SDK client, for tests that
            need additional checks
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "example.py")
        hio.to_file(file_path, "x = 1\n")
        args = argparse.Namespace(
            mode=mode,
            topic=topic,
            skill=skill,
            rule=rule,
            dry_run=False,
            model="",
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
            umock.patch(
                "claude_agent_sdk.ClaudeSDKClient"
            ) as mock_client_cls,
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
        self.assertEqual(
            len(fake_client.queried_prompts), expected_num_messages
        )
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
        expected_num_messages = len(
            lcclint._extract_h1_sections(".claude/skills/coding.rules.md")
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
        expected_num_messages = len(
            lcclint._extract_h1_sections(".claude/skills/markdown.rules.md")
        ) + len(lcclint._extract_h1_sections(".claude/skills/text.rules.md"))
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
        expected_num_messages = len(
            lcclint._extract_h1_sections(".claude/skills/coding.rules.md")
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
        expected_num_messages = len(
            lcclint._extract_h1_sections(".claude/skills/markdown.rules.md")
        ) + len(lcclint._extract_h1_sections(".claude/skills/text.rules.md"))
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


# #############################################################################
# Test_process_file_end_to_end
# #############################################################################


@pytest.mark.skip(
    reason=(
        "Run manually: makes a real Claude Agent SDK/CLI call and costs "
        "tokens"
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
        hio.to_file(
            rule_file, "# My Rule\nReply with exactly the word OK.\n"
        )
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
        self.assertEqual(args.mode, expected_mode)

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
