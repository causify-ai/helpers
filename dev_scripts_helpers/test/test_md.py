import io
import logging
import os
import tempfile
from contextlib import redirect_stdout

import helpers.hunit_test as hunitest

import dev_scripts_helpers.md as devmd

_LOG = logging.getLogger(__name__)


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
        actual = devmd._match_prefix(value, valid_options)
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
        actual = devmd._match_prefix(value, valid_options)
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
        actual = devmd._match_prefix(value, valid_options)
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
        actual = devmd._match_prefix(value, valid_options)
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
        actual = devmd._get_template(type_, name)
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
        actual = devmd._get_template(type_, name)
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
        actual = devmd._get_template(type_, name)
        # Check outputs.
        expected = f"# {name}"
        self.assertIn(expected, actual)

    def test4(self) -> None:
        """
        Test story template contains YAML frontmatter with title and author.
        """
        # Prepare inputs.
        type_ = "story"
        name = "story_name"
        # Run test.
        actual = devmd._get_template(type_, name)
        # Check outputs.
        self.assertIn("---", actual)
        self.assertIn("title:", actual)
        self.assertIn("author:", actual)
