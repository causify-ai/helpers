import io
import os
# TODO(ai_gp): Use import
from contextlib import redirect_stdout

import helpers.hunit_test as hunitest

import dev_scripts_helpers.system_tools.md_utils as devmduti


# #############################################################################
# Test_match_prefix
# #############################################################################


class Test_match_prefix(hunitest.TestCase):
    """
    Test the _match_prefix function for prefix matching against valid options.
    """

    def test1(self) -> None:
        """
        Test prefix 'res' matches 'research' from the valid types list.
        """
        # Prepare inputs.
        value = "res"
        valid_options = ["research", "blog", "story", "skill"]
        # Run test.
        actual = devmduti._match_prefix(value, valid_options)
        # Check outputs.
        expected = "research"
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test prefix 'sk' matches 'skill' from the valid types list.
        """
        # Prepare inputs.
        value = "sk"
        valid_options = ["research", "blog", "story", "skill"]
        # Run test.
        actual = devmduti._match_prefix(value, valid_options)
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
        actual = devmduti._match_prefix(value, valid_options)
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
        actual = devmduti._match_prefix(value, valid_options)
        # Check outputs.
        expected = "blog"
        self.assertEqual(actual, expected)


# #############################################################################
# Test_get_template
# #############################################################################


class Test_get_template(hunitest.TestCase):
    """
    Test the _get_template function for correct template generation by type.
    """

    def test1(self) -> None:
        """
        Test blog template contains YAML frontmatter and TL;DR section.
        """
        # Prepare inputs.
        type_ = "blog"
        name = "My_Post"
        # Run test.
        actual = devmduti._get_template(type_, name)
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
        type_ = "skill"
        name = "test_skill"
        # Run test.
        actual = devmduti._get_template(type_, name)
        # Check outputs.
        self.assertIn("# Summary", actual)

    def test3(self) -> None:
        """
        Test research template contains the passed name in a header.
        """
        # Prepare inputs.
        type_ = "research"
        name = "my_idea"
        # Run test.
        actual = devmduti._get_template(type_, name)
        # Check outputs.
        expected = f"# {name}"
        self.assertIn(expected, actual)

    def test4(self) -> None:
        """
        Test story template returns empty string.
        """
        # Prepare inputs.
        type_ = "story"
        name = "story_name"
        # Run test.
        actual = devmduti._get_template(type_, name)
        # Check outputs.
        self.assertEqual(actual, "")


# #############################################################################
# Test_action_types
# #############################################################################


class Test_action_types(hunitest.TestCase):
    """
    Test the _action_types function for listing unique prefixes from markdown
    files in a directory.
    """

    def _capture_output(self, func, *args, **kwargs):
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

    def test1(self) -> None:
        """
        Test _action_types with skill directory lists prefixes.
        """
        # Prepare inputs.
        type_ = "skill"
        dir_ = devmduti._get_directory(type_)
        # Run test.
        actual = self._capture_output(devmduti._action_types, type_, dir_)
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)
        # Verify they look like prefixes (alphabetic characters).
        for prefix in lines:
            self.assertTrue(prefix.isalpha() or all(c.isalnum() or c == "_" for c in prefix))

    def test2(self) -> None:
        """
        Test _action_types with pattern filter for skill directory.
        """
        # Prepare inputs.
        type_ = "skill"
        dir_ = devmduti._get_directory(type_)
        pattern = "blog"
        # Run test.
        actual = self._capture_output(devmduti._action_types, type_, dir_, pattern=pattern)
        # Check outputs.
        self.assertIn("blog", actual)

    def test3(self) -> None:
        """
        Test _action_list function with skill directory.
        """
        # Prepare inputs.
        type_ = "skill"
        dir_ = devmduti._get_directory(type_)
        # Run test.
        actual = self._capture_output(devmduti._action_list, type_, dir_)
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)

    def test4(self) -> None:
        """
        Test _action_full_list function with skill directory.
        """
        # Prepare inputs.
        type_ = "skill"
        dir_ = devmduti._get_directory(type_)
        # Run test.
        actual = self._capture_output(devmduti._action_full_list, type_, dir_)
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)
        # Check that at least one path contains SKILL.md.
        self.assertTrue(any("SKILL.md" in line for line in lines))

    def test5(self) -> None:
        """
        Test _action_describe function with skill directory.
        """
        # Prepare inputs.
        type_ = "skill"
        dir_ = devmduti._get_directory(type_)
        # Run test.
        actual = self._capture_output(devmduti._action_describe, type_, dir_)
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)

    def test6(self) -> None:
        """
        Test _action_directory function returns correct path.
        """
        # Prepare inputs.
        type_ = "skill"
        dir_ = devmduti._get_directory(type_)
        # Run test.
        actual = self._capture_output(devmduti._action_directory, dir_)
        # Check outputs.
        self.assertEqual(actual, dir_)
        self.assertTrue(os.path.isdir(actual))
