"""
Test cc_script module.

Import as:

import dev_scripts_helpers.ai.test.test_cc_script as daiattccs
"""

import logging
import textwrap
from typing import List

import pytest

import helpers.hio as hio  # noqa: E402
import helpers.hprint as hprint
import helpers.hunit_test as hunitest  # noqa: E402

pytest.importorskip("claude_agent_sdk")
import dev_scripts_helpers.ai.cc_script as dshaccsc  # noqa: E402

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse
# #############################################################################


class Test_parse(hunitest.TestCase):
    """
    Test argument parsing for cc_script.
    """

    def test1(self) -> None:
        """
        Test parser creation with valid prompt arguments.
        """
        # Prepare inputs.
        parser = dshaccsc._parse()
        # Prepare outputs.
        expected = "['test prompt']"
        # Run test.
        args = parser.parse_args(["--prompts", "test prompt"])
        # Check outputs.
        self.assert_equal(str(args.prompts), expected)

    def test2(self) -> None:
        """
        Test parser with custom permission_mode and tools.
        """
        # Prepare inputs.
        parser = dshaccsc._parse()
        argv = [
            "--prompts",
            "prompt1",
            "--permission_mode",
            "acceptEdits",
            "--tools",
            "Read",
            "--tools",
            "Edit",
        ]
        # Prepare outputs.
        expected_permission = "acceptEdits"
        expected_tools = ["Read", "Edit"]
        # Run test.
        args = parser.parse_args(argv)
        # Check outputs.
        self.assert_equal(args.permission_mode, expected_permission)
        self.assert_equal(str(args.tools), str(expected_tools))

    def test3(self) -> None:
        """
        Test parser with output_file and cwd options.
        """
        # Prepare inputs.
        parser = dshaccsc._parse()
        argv = [
            "--prompts",
            "test",
            "--output_file",
            "/tmp/session.log",
            "--cwd",
            "/home/user",
        ]
        # Prepare outputs.
        expected_output_file = "/tmp/session.log"
        expected_cwd = "/home/user"
        # Run test.
        args = parser.parse_args(argv)
        # Check outputs.
        self.assert_equal(args.output_file, expected_output_file)
        self.assert_equal(args.cwd, expected_cwd)

    def test4(self) -> None:
        """
        Test parser default values.
        """
        # Prepare inputs.
        parser = dshaccsc._parse()
        # Prepare outputs.
        expected_permission = "ask"
        expected_tools = []
        expected_cwd = ""
        expected_output_file = "tmp.cc_script.log"
        # Run test.
        args = parser.parse_args(["--prompts", "test"])
        # Check outputs.
        self.assert_equal(args.permission_mode, expected_permission)
        self.assert_equal(str(args.tools), str(expected_tools))
        self.assert_equal(args.cwd, expected_cwd)
        self.assert_equal(args.output_file, expected_output_file)


# #############################################################################
# Test_load_prompts_from_file
# #############################################################################


class Test_load_prompts_from_file(hunitest.TestCase):
    """
    Test loading prompts from file.
    """

    def _load_and_parse_prompts(
        self, filename: str, content: str, expected: List[str]
    ) -> None:
        """
        Helper to create a file with content, load prompts from it, and assert.
        """
        input_dir = self.get_input_dir()
        input_file = f"{input_dir}/{filename}"
        hio.to_file(input_file, content)
        prompts = dshaccsc._load_prompts_from_file(input_file)
        self.assert_equal(str(prompts), str(expected))

    def test1(self) -> None:
        """
        Test loading single prompt from file.
        """
        content = "What is the capital of France?"
        expected = ["What is the capital of France?"]
        self._load_and_parse_prompts("single_prompt.txt", content, expected)

    def test2(self) -> None:
        """
        Test loading multiple prompts from file.
        """
        content = hprint.dedent(
        """
        First prompt here
        Second prompt here
        Third prompt here
        """
        )
        expected = [
            "First prompt here",
            "Second prompt here",
            "Third prompt here",
        ]
        self._load_and_parse_prompts("multi_prompts.txt", content, expected)

    def test3(self) -> None:
        """
        Test loading prompts with empty lines and whitespace.
        """
        content = hprint.dedent(
        """
        Prompt 1

        Prompt 2

          Prompt 3  """
        )
        expected = ["Prompt 1", "Prompt 2", "Prompt 3"]
        self._load_and_parse_prompts("whitespace_prompts.txt", content, expected)
