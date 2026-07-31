"""
Test cc_script module.

Import as:

import dev_scripts_helpers.ai.test.test_cc_script as daiattccs
"""

import logging

import helpers.hio as hio
import helpers.hunit_test as hunitest

import dev_scripts_helpers.ai.cc_script as ccscr

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse
# #############################################################################


class Test_parse(hunitest.TestCase):
    """
    Test argument parsing for cc_script.

    Tests cover:
    - Parser creation and default values
    - Required mutually exclusive group (prompts vs prompts_file)
    - Optional arguments parsing
    """

    def test1(self) -> None:
        """
        Test parser creation with valid prompt arguments.
        """
        # Prepare inputs.
        parser = ccscr._parse()
        args = parser.parse_args(["--prompts", "test prompt"])
        # Check outputs.
        self.assertIsNotNone(args)
        self.assertIn("test prompt", args.prompts)
        self.assertEqual(args.permission_mode, "ask")

    def test2(self) -> None:
        """
        Test parser with custom permission_mode and tools.
        """
        # Prepare inputs.
        parser = ccscr._parse()
        args = parser.parse_args([
            "--prompts", "prompt1",
            "--permission_mode", "acceptEdits",
            "--tools", "Read",
            "--tools", "Edit",
        ])
        # Check outputs.
        self.assertEqual(args.permission_mode, "acceptEdits")
        self.assertEqual(args.tools, ["Read", "Edit"])

    def test3(self) -> None:
        """
        Test parser with output_file and cwd options.
        """
        # Prepare inputs.
        parser = ccscr._parse()
        args = parser.parse_args([
            "--prompts", "test",
            "--output_file", "/tmp/session.log",
            "--cwd", "/home/user",
        ])
        # Check outputs.
        self.assertEqual(args.output_file, "/tmp/session.log")
        self.assertEqual(args.cwd, "/home/user")

    def test4(self) -> None:
        """
        Test parser default values.
        """
        # Prepare inputs.
        parser = ccscr._parse()
        args = parser.parse_args(["--prompts", "test"])
        # Check outputs.
        self.assertEqual(args.permission_mode, "ask")
        self.assertEqual(args.tools, [])
        self.assertEqual(args.cwd, "")
        self.assertEqual(args.output_file, "cc_session.log")


# #############################################################################
# Test_load_prompts_from_file
# #############################################################################


class Test_load_prompts_from_file(hunitest.TestCase):
    """
    Test loading prompts from file.

    Tests cover:
    - Loading single prompt from file
    - Loading multiple prompts (one per line)
    - Handling whitespace and empty lines
    """

    def test1(self) -> None:
        """
        Test loading single prompt from file.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        input_file = f"{input_dir}/single_prompt.txt"
        # Create input file.
        content = "What is the capital of France?"
        hio.to_file(input_file, content)
        # Load prompts.
        prompts = ccscr._load_prompts_from_file(input_file)
        # Check outputs.
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0], "What is the capital of France?")

    def test2(self) -> None:
        """
        Test loading multiple prompts from file.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        input_file = f"{input_dir}/multi_prompts.txt"
        # Create input file with multiple prompts.
        content = """First prompt here
Second prompt here
Third prompt here"""
        hio.to_file(input_file, content)
        # Load prompts.
        prompts = ccscr._load_prompts_from_file(input_file)
        # Check outputs.
        self.assertEqual(len(prompts), 3)
        self.assertEqual(prompts[0], "First prompt here")
        self.assertEqual(prompts[1], "Second prompt here")
        self.assertEqual(prompts[2], "Third prompt here")

    def test3(self) -> None:
        """
        Test loading prompts with empty lines and whitespace.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        input_file = f"{input_dir}/whitespace_prompts.txt"
        # Create input file with whitespace.
        content = """Prompt 1

Prompt 2

  Prompt 3  """
        hio.to_file(input_file, content)
        # Load prompts.
        prompts = ccscr._load_prompts_from_file(input_file)
        # Check outputs.
        self.assertEqual(len(prompts), 3)
        self.assertEqual(prompts[0], "Prompt 1")
        self.assertEqual(prompts[1], "Prompt 2")
        self.assertEqual(prompts[2], "Prompt 3")
