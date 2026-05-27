import io
import os
from contextlib import redirect_stdout

import helpers.hprint as hprint
import helpers.hunit_test as hunitest

import dev_scripts_helpers.system_tools.mdm_utils as dshstmdut


def _capture_output(func, *args, **kwargs):
    """
    Capture stdout from calling a function.

    :param func: function to call
    :param args: positional arguments
    :param kwargs: keyword arguments
    :return: captured output as string (stripped)
    """
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        func(*args, **kwargs)
    return captured_output.getvalue().strip()


# #############################################################################
# Test_match_prefix
# #############################################################################


class Test_match_prefix(hunitest.TestCase):
    """
    Test the _match_prefix function for prefix matching against valid options.
    """

    def test1(self) -> None:
        """
        Test prefix 'res' matches 'research' from the valid topics list.
        """
        # Prepare inputs.
        value = "res"
        valid_options = ["research", "blog", "story", "skill"]
        # Run test.
        actual = dshstmdut._match_prefix(value, valid_options)
        # Check outputs.
        expected = "research"
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test prefix 'sk' matches 'skill' from the valid topics list.
        """
        # Prepare inputs.
        value = "sk"
        valid_options = ["research", "blog", "story", "skill"]
        # Run test.
        actual = dshstmdut._match_prefix(value, valid_options)
        # Check outputs.
        expected = "skill"
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test prefix 'l' matches 'list' from the valid actions list.
        """
        # Prepare inputs.
        value = "l"
        valid_options = ["list", "edit", "directory"]
        # Run test.
        actual = dshstmdut._match_prefix(value, valid_options)
        # Check outputs.
        expected = "list"
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test full name 'blog' matches 'blog' exactly.
        """
        # Prepare inputs.
        value = "blog"
        valid_options = ["research", "blog", "story", "skill"]
        # Run test.
        actual = dshstmdut._match_prefix(value, valid_options)
        # Check outputs.
        expected = "blog"
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Test prefix 'ru' matches 'rules' from the valid topics list.
        """
        # Prepare inputs.
        value = "ru"
        valid_options = ["research", "blog", "story", "skill", "rules"]
        # Run test.
        actual = dshstmdut._match_prefix(value, valid_options)
        # Check outputs.
        expected = "rules"
        self.assertEqual(actual, expected)


# #############################################################################
# Test_get_template
# #############################################################################


class Test_get_template(hunitest.TestCase):
    """
    Test the _get_template function for correct template generation by topic.
    """

    def test1(self) -> None:
        """
        Test blog template contains YAML frontmatter and TL;DR section.
        """
        # Prepare inputs.
        topic_ = "blog"
        name = "My_Post"
        # Run test.
        actual = dshstmdut._get_template(topic_, name)
        # Check outputs.
        self.assertIn("---", actual)
        self.assertIn("title:", actual)
        self.assertIn("TL;DR:", actual)
        self.assertIn("<!-- more -->", actual)

    def test2(self) -> None:
        """
        Test skill template contains Summary section.
        """
        # Prepare inputs.
        topic_ = "skill"
        name = "test_skill"
        # Run test.
        actual = dshstmdut._get_template(topic_, name)
        # Check outputs.
        self.assertIn("# Summary", actual)

    def test3(self) -> None:
        """
        Test research template contains the passed name in a header.
        """
        # Prepare inputs.
        topic_ = "research"
        name = "my_idea"
        # Run test.
        actual = dshstmdut._get_template(topic_, name)
        # Check outputs.
        expected = f"# {name}"
        self.assertIn(expected, actual)

    def test4(self) -> None:
        """
        Test story template returns empty string.
        """
        # Prepare inputs.
        topic_ = "story"
        name = "story_name"
        # Run test.
        actual = dshstmdut._get_template(topic_, name)
        # Check outputs.
        self.assertEqual(actual, "")

    def test5(self) -> None:
        """
        Test rules template returns empty string.
        """
        # Prepare inputs.
        topic_ = "rules"
        name = "rules_name"
        # Run test.
        actual = dshstmdut._get_template(topic_, name)
        # Check outputs.
        self.assertEqual(actual, "")


# #############################################################################
# Test_action_topics
# #############################################################################


class Test_action_topics(hunitest.TestCase):
    """
    Test the _action_topics function for listing unique prefixes from markdown
    files in a directory.
    """

    def _assert_non_empty_lines(self, output: str) -> list:
        """
        Assert output is not empty and return split lines.

        :param output: captured output
        :return: list of lines
        """
        self.assertNotEqual(output, "")
        lines = output.split("\n")
        self.assertGreater(len(lines), 0)
        return lines

    def test1(self) -> None:
        """
        Test _action_topics with skill directory lists prefixes.
        """
        # Prepare inputs.
        topic_ = "skill"
        dir_ = dshstmdut._get_directory(topic_)
        # Run test.
        actual = _capture_output(dshstmdut._action_topics, topic_, dir_)
        # Check outputs.
        lines = self._assert_non_empty_lines(actual)
        # Verify they look like prefixes (alphabetic characters).
        for prefix in lines:
            self.assertTrue(
                prefix.isalpha() or all(c.isalnum() or c == "_" for c in prefix)
            )

    def test2(self) -> None:
        """
        Test _action_topics with pattern filter for skill directory.
        """
        # Prepare inputs.
        topic_ = "skill"
        dir_ = dshstmdut._get_directory(topic_)
        pattern = "blog"
        # Run test.
        actual = _capture_output(
            dshstmdut._action_topics, topic_, dir_, pattern=pattern
        )
        # Check outputs.
        self.assertIn("blog", actual)

    def test3(self) -> None:
        """
        Test _action_list function with skill directory.
        """
        # Prepare inputs.
        topic_ = "skill"
        dir_ = dshstmdut._get_directory(topic_)
        # Run test.
        actual = _capture_output(dshstmdut._action_list, topic_, dir_)
        # Check outputs.
        self._assert_non_empty_lines(actual)

    def test4(self) -> None:
        """
        Test _action_full_list function with skill directory.
        """
        # Prepare inputs.
        topic_ = "skill"
        dir_ = dshstmdut._get_directory(topic_)
        # Run test.
        actual = _capture_output(dshstmdut._action_full_list, topic_, dir_)
        # Check outputs.
        lines = self._assert_non_empty_lines(actual)
        # Check that at least one path contains SKILL.md.
        self.assertTrue(any("SKILL.md" in line for line in lines))

    def test5(self) -> None:
        """
        Test _action_describe function with skill directory.
        """
        # Prepare inputs.
        topic_ = "skill"
        dir_ = dshstmdut._get_directory(topic_)
        # Run test.
        actual = _capture_output(dshstmdut._action_describe, topic_, dir_)
        # Check outputs.
        self._assert_non_empty_lines(actual)

    def test6(self) -> None:
        """
        Test _action_directory function returns correct path.
        """
        # Prepare inputs.
        topic_ = "skill"
        dir_ = dshstmdut._get_directory(topic_)
        # Run test.
        actual = _capture_output(dshstmdut._action_directory, dir_)
        # Check outputs.
        self.assertEqual(actual, dir_)
        self.assertTrue(os.path.isdir(actual))


# #############################################################################
# Test_rules_topic
# #############################################################################


class Test_rules_topic(hunitest.TestCase):
    """
    Test rules topic functionality for mdm.
    """

    def _assert_non_empty_lines(self, output: str) -> list:
        """
        Assert output is not empty and return split lines.

        :param output: captured output
        :return: list of lines
        """
        self.assertNotEqual(output, "")
        lines = output.split("\n")
        self.assertGreater(len(lines), 0)
        return lines

    def test_get_directory(self) -> None:
        """
        Test _get_directory returns skills directory for rules topic.
        """
        # Prepare inputs.
        topic_ = "rules"
        # Run test.
        actual = dshstmdut._get_directory(topic_)
        # Check outputs.
        self.assertTrue(os.path.isdir(actual))
        self.assertIn(".claude/skills", actual)

    def test_list(self) -> None:
        """
        Test _action_list with rules directory lists rule names.
        """
        # Prepare inputs.
        topic_ = "rules"
        dir_ = dshstmdut._get_directory(topic_)
        # Run test.
        actual = _capture_output(dshstmdut._action_list, topic_, dir_)
        # Check outputs.
        lines = self._assert_non_empty_lines(actual)
        # Verify at least one line is a rule name (no .rules.md extension).
        self.assertTrue(all(".rules.md" not in line for line in lines))

    def test_full_list(self) -> None:
        """
        Test _action_full_list with rules directory shows full paths.
        """
        # Prepare inputs.
        topic_ = "rules"
        dir_ = dshstmdut._get_directory(topic_)
        # Run test.
        actual = _capture_output(dshstmdut._action_full_list, topic_, dir_)
        # Check outputs.
        lines = self._assert_non_empty_lines(actual)
        # Check that paths contain .rules.md extension.
        self.assertTrue(any(".rules.md" in line for line in lines))


# #############################################################################
# Test_end_to_end_read_only
# #############################################################################


class Test_end_to_end_read_only(hunitest.TestCase):
    """
    End-to-end tests for all read-only mdm commands across all content topics.
    """

    def _print_with_ellipsis(
        self, label: str, items: list, *, max_display: int = 3
    ) -> None:
        """
        Print label, count, and first N items with ellipsis.

        :param label: section label
        :param items: list of items to print
        :param max_display: number of items to display before ellipsis
        """
        print(f"\n{label}:")
        print(f"  Found {len(items)} items")
        if items and len(items) <= max_display:
            for item in items:
                print(f"    {item}")
        elif items:
            for item in items[:max_display]:
                print(f"    {item}")
            print(f"    ... and {len(items) - max_display} more")

    def _test_read_only_commands(self, topic_: str) -> None:
        """
        Helper to test all read-only commands for a given topic.

        Tests: directory, describe, topics, list, full_list

        :param topic_: the content topic (research, blog, story, skill, rules)
        """
        print(
            hprint.frame(
                f"Testing read-only commands for topic: {topic_}",
                char1="=",
                num_chars=60,
                char2="=",
            )
        )
        # Get directory.
        dir_ = dshstmdut._get_directory(topic_)
        print(f"\n[directory] {topic_}:")
        output = _capture_output(dshstmdut._action_directory, dir_)
        print(f"  {output}")
        # Test describe.
        print(f"\n[describe] {topic_}:")
        output = _capture_output(dshstmdut._action_describe, topic_, dir_)
        lines = output.split("\n") if output else []
        self._print_with_ellipsis(f"[describe] {topic_}", lines, max_display=5)
        # Test topics.
        print(f"\n[topics] {topic_}:")
        output = _capture_output(dshstmdut._action_topics, topic_, dir_)
        topics_list = output.split("\n") if output else []
        print(f"  Found {len(topics_list)} unique prefixes")
        if topics_list:
            for prefix in topics_list:
                print(f"    {prefix}")
        # Test list.
        print(f"\n[list] {topic_}:")
        output = _capture_output(dshstmdut._action_list, topic_, dir_)
        items = output.split("\n") if output else []
        self._print_with_ellipsis(f"[list] {topic_}", items, max_display=5)
        # Test full_list.
        print(f"\n[full_list] {topic_}:")
        output = _capture_output(dshstmdut._action_full_list, topic_, dir_)
        items = output.split("\n") if output else []
        self._print_with_ellipsis(f"[full_list] {topic_}", items, max_display=3)

    def test_skill_read_only_commands(self) -> None:
        """
        Test commands for "skill" topic.
        """
        self._test_read_only_commands("skill")

    def test_blog_read_only_commands(self) -> None:
        """
        Test commands for "blog" topic.
        """
        self._test_read_only_commands("blog")

    def test_research_read_only_commands(self) -> None:
        """
        Test commands for "research" topic.
        """
        self._test_read_only_commands("research")

    def test_story_read_only_commands(self) -> None:
        """
        Test commands for "story" topic.
        """
        self._test_read_only_commands("story")

    def test_rules_read_only_commands(self) -> None:
        """
        Test commands for "rules" topic.
        """
        self._test_read_only_commands("rules")
