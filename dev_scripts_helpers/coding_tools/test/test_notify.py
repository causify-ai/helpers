import logging
import os

import dev_scripts_helpers.coding_tools.notify as dsctonot
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse_last_command1
# #############################################################################


class Test_parse_last_command1(hunitest.TestCase):
    """
    Test `_parse_last_command()`.
    """

    def helper(self, history_text: str, file_name: str, expected: str) -> None:
        """
        Write `history_text` to `file_name` in the input dir, parse it, and
        check that the last command matches `expected`.

        :param history_text: raw content of the shell history file
        :param file_name: name of the input file to create
        :param expected: expected last command
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        input_file = os.path.join(input_dir, file_name)
        hio.to_file(input_file, history_text)
        # Run test.
        actual_text = hio.from_file(input_file)
        actual = dsctonot._parse_last_command(actual_text)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test extraction of the last command from a `bash`-style history file.
        """
        history_text = """
        git status
        ls -la
        """
        history_text = hprint.dedent(history_text)
        expected = "ls -la"
        self.helper(history_text, "bash_history.txt", expected)

    def test2(self) -> None:
        """
        Test extraction of the last command from a `zsh`-style history file
        with `: <timestamp>:<duration>;<command>` entries.
        """
        history_text = """
        : 1700000000:0;git status
        : 1700000001:0;ls -la
        """
        history_text = hprint.dedent(history_text)
        expected = "ls -la"
        self.helper(history_text, "zsh_history.txt", expected)

    def test3(self) -> None:
        """
        Test extraction of the last command when trailing empty lines are
        present.
        """
        history_text = """
        git status
        ls -la


        """
        history_text = hprint.dedent(history_text)
        expected = "ls -la"
        self.helper(history_text, "trailing_newlines.txt", expected)

    def test4(self) -> None:
        """
        Test that parsing an empty history asserts.
        """
        # Prepare inputs.
        history_text = ""
        # Run test.
        with self.assertRaises(AssertionError):
            _ = dsctonot._parse_last_command(history_text)
