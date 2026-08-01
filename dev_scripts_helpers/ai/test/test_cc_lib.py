"""
Test cc_lib module.

Import as:

import dev_scripts_helpers.ai.test.test_cc_lib as daiattccl
"""

import os

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

import pytest

pytest.importorskip("claude_agent_sdk")

import dev_scripts_helpers.ai.cc_lib as dshaccli


# #############################################################################
# TestPromptSequencer
# #############################################################################


class TestPromptSequencer(hunitest.TestCase):
    """
    Test PromptSequencer class initialization and configuration.
    """

    def test1(self) -> None:
        """
        Test PromptSequencer initialization with default options.
        """
        # Prepare inputs.
        # (no input needed for default initialization)
        # Run test.
        sequencer = dshaccli.PromptSequencer()
        # Check outputs.
        self.assertIsNotNone(sequencer)
        self.assertEqual(sequencer.allowed_tools, [])
        self.assertEqual(sequencer.permission_mode, "ask")
        self.assertEqual(sequencer.cwd, "")

    def test2(self) -> None:
        """
        Test PromptSequencer initialization with custom options.
        """
        # Prepare inputs.
        allowed_tools = ["Read", "Edit", "Bash"]
        permission_mode = "acceptEdits"
        cwd = self.get_scratch_space()
        # Run test.
        sequencer = dshaccli.PromptSequencer(
            allowed_tools=allowed_tools,
            permission_mode=permission_mode,
            cwd=cwd,
        )
        # Check outputs.
        self.assertEqual(sequencer.allowed_tools, allowed_tools)
        self.assertEqual(sequencer.permission_mode, permission_mode)
        self.assertEqual(sequencer.cwd, cwd)

    def test3(self) -> None:
        """
        Test execution stats initialization.
        """
        # Prepare inputs.
        sequencer = dshaccli.PromptSequencer()
        # Run test.
        stats = sequencer.get_execution_stats()
        # Check outputs.
        self.assertEqual(stats["prompts_executed"], 0)
        self.assertFalse(stats["session_started"])
        self.assertEqual(stats["last_response_length"], 0)

    def test4(self) -> None:
        """
        Test last response getter when no execution occurred.
        """
        # Prepare inputs.
        sequencer = dshaccli.PromptSequencer()
        # Run test.
        response = sequencer.get_last_response()
        # Check outputs.
        self.assertEqual(response, "")


# #############################################################################
# Test_save_session_log
# #############################################################################


class Test_save_session_log(hunitest.TestCase):
    """
    Test save_session_log function.
    """

    def helper(
        self, prompts: list, responses: list, expected_output: str
    ) -> None:
        """
        Helper for testing save_session_log.

        :param prompts: List of prompts to save
        :param responses: List of responses to save
        :param expected_output: Expected file content
        """
        # Prepare inputs.
        output_dir = self.get_output_dir()
        output_file = os.path.join(output_dir, "session.log")
        # Run test.
        dshaccli.save_session_log(output_file, prompts, responses)
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))
        actual = hio.from_file(output_file)
        self.assert_equal(actual, expected_output)

    def test1(self) -> None:
        """
        Test saving single prompt-response pair to file.
        """
        # Prepare inputs.
        prompts = ["What is 2+2?"]
        responses = ["2+2 equals 4"]
        # Prepare outputs.
        expected = """
        {
          "prompts_and_responses": [
            {
              "prompt_index": 1,
              "prompt": "What is 2+2?",
              "response": "2+2 equals 4"
            }
          ],
          "total_prompts": 1
        }"""
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(prompts, responses, expected)

    def test2(self) -> None:
        """
        Test saving multiple prompt-response pairs to file.
        """
        # Prepare inputs.
        prompts = ["First prompt", "Second prompt", "Third prompt"]
        responses = ["Response 1", "Response 2", "Response 3"]
        # Prepare outputs.
        expected = """
        {
          "prompts_and_responses": [
            {
              "prompt_index": 1,
              "prompt": "First prompt",
              "response": "Response 1"
            },
            {
              "prompt_index": 2,
              "prompt": "Second prompt",
              "response": "Response 2"
            },
            {
              "prompt_index": 3,
              "prompt": "Third prompt",
              "response": "Response 3"
            }
          ],
          "total_prompts": 3
        }"""
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(prompts, responses, expected)
