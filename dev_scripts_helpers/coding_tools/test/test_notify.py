import logging
import os

import dev_scripts_helpers.coding_tools.notify as dsctonot
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse_last_command1
# #############################################################################


# TODO(ai_gp): Create an helper and factor out common code from the test methods.
class Test_parse_last_command1(hunitest.TestCase):
    """
    Test `_parse_last_command()`.
    """

    def test1(self) -> None:
        """
        Test extraction of the last command from a `bash`-style history file.
        """
        # Prepare inputs.
        # TODO(ai_gp): Use """ and dedent
        history_text = "git status\nls -la\n"
        input_dir = self.get_input_dir()
        input_file = os.path.join(input_dir, "bash_history.txt")
        hio.to_file(input_file, history_text)
        # Prepare outputs.
        expected = "ls -la"
        # Run test.
        actual_text = hio.from_file(input_file)
        actual = dsctonot._parse_last_command(actual_text)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test extraction of the last command from a `zsh`-style history file
        with `: <timestamp>:<duration>;<command>` entries.
        """
        # Prepare inputs.
        # TODO(ai_gp): Use """ and dedent
        history_text = ": 1700000000:0;git status\n: 1700000001:0;ls -la\n"
        input_dir = self.get_input_dir()
        input_file = os.path.join(input_dir, "zsh_history.txt")
        hio.to_file(input_file, history_text)
        # Prepare outputs.
        expected = "ls -la"
        # Run test.
        actual_text = hio.from_file(input_file)
        actual = dsctonot._parse_last_command(actual_text)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test extraction of the last command when trailing empty lines are
        present.
        """
        # Prepare inputs.
        # TODO(ai_gp): Use """ and dedent
        history_text = "git status\nls -la\n\n\n"
        input_dir = self.get_input_dir()
        input_file = os.path.join(input_dir, "trailing_newlines.txt")
        hio.to_file(input_file, history_text)
        # Prepare outputs.
        expected = "ls -la"
        # Run test.
        actual_text = hio.from_file(input_file)
        actual = dsctonot._parse_last_command(actual_text)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test that parsing an empty history asserts.
        """
        # Prepare inputs.
        history_text = ""
        # Run test.
        with self.assertRaises(AssertionError):
            _ = dsctonot._parse_last_command(history_text)
