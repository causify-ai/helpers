"""
Test cc_script module.

Import as:

import dev_scripts_helpers.ai.test.test_cc_script as daiattccs
"""

import logging

import helpers.hio as hio
import helpers.hunit_test as hunitest

import dev_scripts_helpers.ai.cc_script as dshaccsc

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
        expected = "test prompt"
        # Run test.
        args = parser.parse_args(["--prompts", "test prompt"])
        # Check outputs.
        self.assert_equal(args.prompts, expected)

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
        expected_output_file = "cc_session.log"
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

    def test1(self) -> None:
        """
        Test loading single prompt from file.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        input_file = f"{input_dir}/single_prompt.txt"
        content = "What is the capital of France?"
        hio.to_file(input_file, content)
        # Prepare outputs.
        expected = ["What is the capital of France?"]
        # Run test.
        prompts = dshaccsc._load_prompts_from_file(input_file)
        # Check outputs.
        self.assert_equal(str(prompts), str(expected))

    def test2(self) -> None:
        """
        Test loading multiple prompts from file.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        input_file = f"{input_dir}/multi_prompts.txt"
        # TODO(ai_gp): Align with text and dedent.
        content = """First prompt here
Second prompt here
Third prompt here"""
        hio.to_file(input_file, content)
        # Prepare outputs.
        expected = [
            "First prompt here",
            "Second prompt here",
            "Third prompt here",
        ]
        # Run test.
        prompts = dshaccsc._load_prompts_from_file(input_file)
        # Check outputs.
        self.assert_equal(str(prompts), str(expected))

    def test3(self) -> None:
        """
        Test loading prompts with empty lines and whitespace.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        input_file = f"{input_dir}/whitespace_prompts.txt"
        # TODO(ai_gp): Align with text and dedent.
        content = """Prompt 1

Prompt 2

  Prompt 3  """
        hio.to_file(input_file, content)
        # Prepare outputs.
        expected = ["Prompt 1", "Prompt 2", "Prompt 3"]
        # Run test.
        prompts = dshaccsc._load_prompts_from_file(input_file)
        # Check outputs.
        self.assert_equal(str(prompts), str(expected))
