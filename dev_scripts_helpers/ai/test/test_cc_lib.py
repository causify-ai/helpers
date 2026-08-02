"""
Test cc_lib module.

Import as:

import dev_scripts_helpers.ai.test.test_cc_lib as daiattccl
"""

import asyncio
import os
# TODO(ai_gp): Use import and not from import
from unittest import mock

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

import pytest

pytest.importorskip("claude_agent_sdk")

import claude_agent_sdk

import dev_scripts_helpers.ai.cc_lib as dshaccli


# #############################################################################
# Test_make_file_scope_guard
# #############################################################################


class Test_make_file_scope_guard(hunitest.TestCase):
    """
    Test `_make_file_scope_guard()` permission callback factory.
    """

    def helper(self, target_file: str, tool_name: str, tool_input: dict):
        """
        Build a guard for `target_file` and invoke it with `tool_name`/`tool_input`.

        :param target_file: file passed to `_make_file_scope_guard()`
        :param tool_name: tool name passed to the guard callback
        :param tool_input: tool input dict passed to the guard callback
        :return: permission result returned by the guard callback
        """
        guard = dshaccli._make_file_scope_guard(target_file)
        # TODO(ai_gp): Assign None to a var and then use that.
        return asyncio.run(guard(tool_name, tool_input, None))  # type: ignore

    def test1(self) -> None:
        """
        Test that editing the target file itself is allowed.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input = {"file_path": "/tmp/target.py"}
        # Run test.
        # TODO(ai_gp): Assign "Edit" to a var and then use that.
        result = self.helper(target_file, "Edit", tool_input)
        # Check outputs.
        # TODO(ai_gp): Move the checking to the helper.
        self.assertIsInstance(
            result, claude_agent_sdk.types.PermissionResultAllow
        )

    def test2(self) -> None:
        """
        Test that editing a different file is denied with target filename in message.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input = {"file_path": "/tmp/other.py"}
        # Run test.
        result = self.helper(target_file, "Edit", tool_input)
        # Check outputs.
        self.assertIsInstance(
            result, claude_agent_sdk.types.PermissionResultDeny
        )
        self.assertIn(target_file, result.message)

    def test3(self) -> None:
        """
        Test that all file-modifying tools are denied on a mismatched path.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input = {"file_path": "/tmp/other.py"}
        # Run test and check outputs.
        for tool_name in dshaccli._FILE_MODIFYING_TOOLS:
            result = self.helper(target_file, tool_name, tool_input)
            self.assertIsInstance(
                result, claude_agent_sdk.types.PermissionResultDeny
            )

    def test4(self) -> None:
        """
        Test that non-modifying tools are always allowed on a different file.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input = {"file_path": "/tmp/other.py"}
        # Run test and check outputs.
        for tool_name in ("Read", "Bash"):
            result = self.helper(target_file, tool_name, tool_input)
            self.assertIsInstance(
                result, claude_agent_sdk.types.PermissionResultAllow
            )

    def test5(self) -> None:
        """
        Test that non-modifying tools are allowed when file_path is absent.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input: dict = {}
        # Run test.
        result = self.helper(target_file, "Bash", tool_input)
        # Check outputs.
        self.assertIsInstance(
            result, claude_agent_sdk.types.PermissionResultAllow
        )

    def test6(self) -> None:
        """
        Test that a missing file_path is allowed for a modifying tool.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input: dict = {}
        # Run test.
        result = self.helper(target_file, "Edit", tool_input)
        # Check outputs.
        self.assertIsInstance(
            result, claude_agent_sdk.types.PermissionResultAllow
        )

    def test7(self) -> None:
        """
        Test that an empty file_path is allowed for a modifying tool.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input = {"file_path": ""}
        # Run test.
        result = self.helper(target_file, "Edit", tool_input)
        # Check outputs.
        self.assertIsInstance(
            result, claude_agent_sdk.types.PermissionResultAllow
        )

    def test8(self) -> None:
        """
        Test that a relative target_file matching an absolute file_path is allowed.
        """
        # Prepare inputs.
        target_file = "target.py"
        tool_input = {"file_path": os.path.abspath("target.py")}
        # Run test.
        result = self.helper(target_file, "Edit", tool_input)
        # Check outputs.
        self.assertIsInstance(
            result, claude_agent_sdk.types.PermissionResultAllow
        )


# #############################################################################
# Test_PromptSequencer_execute
# #############################################################################


# TODO(ai_gp): move this to cc_lib.py
class _FakeClaudeSDKClient:
    """
    Minimal stand-in for `claude_agent_sdk.ClaudeSDKClient`.

    A plain `AsyncMock` cannot cleanly emulate an async-generator method
    like `receive_response()`, so a small hand-written fake is used instead.
    """

    def __init__(self, responses_by_call: list) -> None:
        self._responses_by_call = responses_by_call
        self.queried_prompts: list = []
        self.aenter_called = False
        self.aexit_called = False

    async def __aenter__(self) -> "_FakeClaudeSDKClient":
        self.aenter_called = True
        return self

    async def __aexit__(self, *_exc_info) -> bool:
        self.aexit_called = True
        return False

    async def query(self, prompt: str) -> None:
        self.queried_prompts.append(prompt)

    async def receive_response(self):
        idx = len(self.queried_prompts) - 1
        for message in self._responses_by_call[idx]:
            yield message


class Test_PromptSequencer_execute(hunitest.TestCase):
    """
    Test `PromptSequencer.execute()` against a fake SDK client (no network).
    """

    def test1(self) -> None:
        """
        Test that execute() drives the SDK client with the expected options.
        """
        # Prepare inputs.
        msg1 = claude_agent_sdk.AssistantMessage(
            content=[claude_agent_sdk.TextBlock(text="response A")],
            model="claude-test",
        )
        msg2 = claude_agent_sdk.AssistantMessage(
            content=[claude_agent_sdk.TextBlock(text="response B")],
            model="claude-test",
        )
        fake_client = _FakeClaudeSDKClient(responses_by_call=[[msg1], [msg2]])
        sequencer = dshaccli.PromptSequencer(
            allowed_tools=["Read", "Edit"],
            disallowed_tools=["Bash"],
            permission_mode="acceptEdits",
            cwd=self.get_scratch_space(),
            model="claude-test-model",
            setting_sources=["project"],
            target_file="/tmp/target.py",
            print_output=False,
        )
        # Run test.
        with mock.patch(
            "claude_agent_sdk.ClaudeSDKClient"
        ) as mock_client_cls:
            mock_client_cls.return_value = fake_client
            asyncio.run(sequencer.execute(["prompt A", "prompt B"]))
        # Check outputs.
        # TODO(ai_gp): Create a function that generates a str representation
        # from the mock_client_cls and then compare the string to an
        # expected one with self.assert_equal
        mock_client_cls.assert_called_once()
        _, kwargs = mock_client_cls.call_args
        options = kwargs["options"]
        self.assertEqual(options.allowed_tools, ["Read", "Edit"])
        self.assertEqual(options.disallowed_tools, ["Bash"])
        self.assertEqual(options.permission_mode, "acceptEdits")
        self.assertEqual(options.model, "claude-test-model")
        self.assertEqual(options.setting_sources, ["project"])
        self.assertIs(options.can_use_tool, sequencer.can_use_tool)
        self.assertTrue(fake_client.aenter_called)
        self.assertTrue(fake_client.aexit_called)
        self.assertEqual(fake_client.queried_prompts, ["prompt A", "prompt B"])
        self.assertEqual(sequencer._prompts_executed, 2)
        self.assertNotEqual(sequencer.get_last_response(), "")


# #############################################################################
# Test_PromptSequencer_execute_end_to_end
# #############################################################################


class Test_PromptSequencer_execute_end_to_end(hunitest.TestCase):
    """
    Exercise `PromptSequencer.execute()` against the real Claude Agent SDK.

    Unlike `Test_PromptSequencer_execute`, nothing here is mocked: each test
    makes a real `claude_agent_sdk.ClaudeSDKClient` call, requires the local
    `claude` CLI to be authenticated, and spends real API tokens. Tests are
    skipped by default; remove the `@pytest.mark.skip` decorator to run one
    manually. The cheapest available model is used to keep manual runs
    inexpensive.
    """

    _MODEL = "claude-haiku-4-5-20251001"
    # Block every tool so plain Q&A prompts cannot trigger tool use.
    _NO_TOOLS = [
        "Bash",
        "Read",
        "Write",
        "Edit",
        "MultiEdit",
        "NotebookEdit",
        "Grep",
        "Glob",
        "WebFetch",
        "WebSearch",
        "Task",
    ]

    @pytest.mark.skip(
        reason="Run manually: makes a real Claude Agent SDK call and costs tokens"
    )
    def test1(self) -> None:
        """
        Test that a real single-prompt session returns the expected reply.
        """
        # Prepare inputs.
        sequencer = dshaccli.PromptSequencer(
            disallowed_tools=self._NO_TOOLS,
            permission_mode="bypassPermissions",
            cwd=self.get_scratch_space(),
            model=self._MODEL,
            print_output=False,
        )
        prompt = (
            "Reply with exactly the single word PONG and nothing else, "
            "no punctuation."
        )
        # Run test.
        asyncio.run(sequencer.execute([prompt]))
        # Check outputs.
        self.assertEqual(sequencer.get_execution_stats()["prompts_executed"], 1)
        self.assertIn("PONG", sequencer.get_last_response())

    @pytest.mark.skip(
        reason="Run manually: makes real Claude Agent SDK calls and costs tokens"
    )
    def test2(self) -> None:
        """
        Test that conversation context is preserved across sequential prompts.
        """
        # Prepare inputs.
        sequencer = dshaccli.PromptSequencer(
            disallowed_tools=self._NO_TOOLS,
            permission_mode="bypassPermissions",
            cwd=self.get_scratch_space(),
            model=self._MODEL,
            print_output=False,
        )
        prompts = [
            "Remember the secret number 84210. Reply with OK and nothing else.",
            "What secret number did I ask you to remember? Reply with only "
            "the number and nothing else.",
        ]
        # Run test.
        asyncio.run(sequencer.execute(prompts))
        # Check outputs.
        self.assertEqual(sequencer.get_execution_stats()["prompts_executed"], 2)
        self.assertIn("84210", sequencer.get_last_response())

    @pytest.mark.skip(
        reason="Run manually: makes a real Claude Agent SDK call and costs tokens"
    )
    def test3(self) -> None:
        """
        Test that the real SDK enforces the file-scope guard end-to-end.

        Mirrors the `_process_file_incrementally()` production configuration
        (`allowed_tools=["Edit"]`, `permission_mode="acceptEdits"`,
        `target_file=...`) and verifies that a file outside `target_file` is
        left untouched even though the model is asked to overwrite it.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        target_file = os.path.join(scratch_dir, "target.txt")
        other_file = os.path.join(scratch_dir, "other.txt")
        hio.to_file(target_file, "target\n")
        hio.to_file(other_file, "other\n")
        sequencer = dshaccli.PromptSequencer(
            allowed_tools=["Edit", "Write"],
            disallowed_tools=["Bash", "Task", "WebFetch"],
            permission_mode="acceptEdits",
            cwd=scratch_dir,
            model=self._MODEL,
            target_file=target_file,
            print_output=False,
        )
        prompt = (
            f"Use the Write tool to overwrite the file {other_file} so its "
            "content is exactly 'hacked'."
        )
        # Run test.
        asyncio.run(sequencer.execute([prompt]))
        # Check outputs.
        self.assertEqual(hio.from_file(other_file), "other\n")


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
