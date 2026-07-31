"""
Test cc_lib module.

Import as:

import dev_scripts_helpers.ai.test.test_cc_lib as daiattccl
"""

import logging

import helpers.hio as hio
import helpers.hunit_test as hunitest

import dev_scripts_helpers.ai.cc_lib as dshaccli

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_PromptSequencer
# #############################################################################


class Test_PromptSequencer(hunitest.TestCase):
    """
    Test PromptSequencer class initialization and configuration.

    Tests cover:
    - Initialization with default options
    - Initialization with custom options
    - Execution statistics
    """

    def test1(self) -> None:
        """
        Test PromptSequencer initialization with default options.
        """
        # Prepare inputs.
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
        cwd = "/tmp/test"
        # Create sequencer.
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
        # Get stats.
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
        # Get response.
        response = sequencer.get_last_response()
        # Check outputs.
        self.assertEqual(response, "")


# #############################################################################
# Test_save_session_log
# #############################################################################


class Test_save_session_log(hunitest.TestCase):
    """
    Test save_session_log function.

    Tests cover:
    - Saving single prompt-response pair
    - Saving multiple prompt-response pairs
    - File format verification
    """

    def test1(self) -> None:
        """
        Test saving single prompt-response pair to file.
        """
        # Prepare inputs.
        output_dir = self.get_output_dir()
        output_file = f"{output_dir}/session.log"
        prompts = ["What is 2+2?"]
        responses = ["2+2 equals 4"]
        # Save session log.
        dshaccli.save_session_log(output_file, prompts, responses)
        # Check outputs.
        import os

        self.assertTrue(os.path.exists(output_file))
        # Verify content.
        actual = hio.from_file(output_file)
        self.check_string(actual)

    def test2(self) -> None:
        """
        Test saving multiple prompt-response pairs to file.
        """
        # Prepare inputs.
        output_dir = self.get_output_dir()
        output_file = f"{output_dir}/session_multi.log"
        prompts = ["First prompt", "Second prompt", "Third prompt"]
        responses = ["Response 1", "Response 2", "Response 3"]
        # Save session log.
        dshaccli.save_session_log(output_file, prompts, responses)
        # Check outputs.
        import os

        self.assertTrue(os.path.exists(output_file))
        # Verify content.
        actual = hio.from_file(output_file)
        self.check_string(actual)
