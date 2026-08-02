"""
Test cc_lib module.

Import as:

import dev_scripts_helpers.ai.test.test_cc_lib as daiattccl
"""

import asyncio
import os
import unittest.mock as umock

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

    def helper(
        self, target_file: str, tool_name: str, tool_input: dict, expected_type: type
    ):
        """
        Build a guard for `target_file`, invoke it, and check the result type.

        :param target_file: file passed to `_make_file_scope_guard()`
        :param tool_name: tool name passed to the guard callback
        :param tool_input: tool input dict passed to the guard callback
        :param expected_type: expected type of the permission result
        :return: permission result returned by the guard callback
        """
        guard = dshaccli._make_file_scope_guard(target_file)
        context = None
        result = asyncio.run(guard(tool_name, tool_input, context))  # type: ignore
        self.assertIsInstance(result, expected_type)
        return result

    def test1(self) -> None:
        """
        Test that editing the target file itself is allowed.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_name = "Edit"
        tool_input = {"file_path": "/tmp/target.py"}
        # Run test and check outputs.
        self.helper(
            target_file,
            tool_name,
            tool_input,
            claude_agent_sdk.types.PermissionResultAllow,
        )

    def test2(self) -> None:
        """
        Test that editing a different file is denied with target filename in message.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input = {"file_path": "/tmp/other.py"}
        # Run test.
        result = self.helper(
            target_file,
            "Edit",
            tool_input,
            claude_agent_sdk.types.PermissionResultDeny,
        )
        # Check outputs.
        self.assertIn(target_file, result.message)

    def test3(self) -> None:
        """
        Test that all file-modifying tools are denied on a mismatched path.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input = {"file_path": "/tmp/other.py"}
        file_modifying_tools = ("Edit", "Write", "NotebookEdit", "MultiEdit")
        # Run test and check outputs.
        for tool_name in file_modifying_tools:
            self.helper(
                target_file,
                tool_name,
                tool_input,
                claude_agent_sdk.types.PermissionResultDeny,
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
            self.helper(
                target_file,
                tool_name,
                tool_input,
                claude_agent_sdk.types.PermissionResultAllow,
            )

    def test5(self) -> None:
        """
        Test that non-modifying tools are allowed when file_path is absent.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input: dict = {}
        # Run test and check outputs.
        self.helper(
            target_file,
            "Bash",
            tool_input,
            claude_agent_sdk.types.PermissionResultAllow,
        )

    def test6(self) -> None:
        """
        Test that a missing file_path is allowed for a modifying tool.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input: dict = {}
        # Run test and check outputs.
        self.helper(
            target_file,
            "Edit",
            tool_input,
            claude_agent_sdk.types.PermissionResultAllow,
        )

    def test7(self) -> None:
        """
        Test that an empty file_path is allowed for a modifying tool.
        """
        # Prepare inputs.
        target_file = "/tmp/target.py"
        tool_input = {"file_path": ""}
        # Run test and check outputs.
        self.helper(
            target_file,
            "Edit",
            tool_input,
            claude_agent_sdk.types.PermissionResultAllow,
        )

    def test8(self) -> None:
        """
        Test that a relative target_file matching an absolute file_path is allowed.
        """
        # Prepare inputs.
        target_file = "target.py"
        tool_input = {"file_path": os.path.abspath("target.py")}
        # Run test and check outputs.
        self.helper(
            target_file,
            "Edit",
            tool_input,
            claude_agent_sdk.types.PermissionResultAllow,
        )


# #############################################################################
# Test_PromptSequencer_execute
# #############################################################################


class Test_PromptSequencer_execute(hunitest.TestCase):
    """
    Test `PromptSequencer.execute()` against a fake SDK client (no network).
    """

    # TODO(ai_gp): Factor out common code in helper.
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
        fake_client = dshaccli.FakeClaudeSDKClient(
            responses_by_call=[[msg1], [msg2]]
        )
        with umock.patch(
            "claude_agent_sdk.ClaudeSDKClient"
        ) as mock_client_cls:
            mock_client_cls.return_value = fake_client
            asyncio.run(sequencer.execute(["prompt A", "prompt B"]))
        # Check outputs.
        mock_client_cls.assert_called_once()
        _, kwargs = mock_client_cls.call_args
        fake_client.options = kwargs["options"]
        actual = str(fake_client)
        expected = (
            "options=(['Read', 'Edit'], ['Bash'], 'acceptEdits', "
            "'claude-test-model', ['project']), queried_prompts=['prompt "
            "A', 'prompt B'], aenter_called=True, aexit_called=True"
        )
        self.assert_equal(actual, expected)
        self.assertIs(fake_client.options.can_use_tool, sequencer.can_use_tool)
        self.assertEqual(sequencer._prompts_executed, 2)
        self.assertNotEqual(sequencer.get_last_response(), "")

    def test2(self) -> None:
        """
        Test that `system_prompt` is forwarded to `ClaudeAgentOptions`.
        """
        # Prepare inputs.
        msg1 = claude_agent_sdk.AssistantMessage(
            content=[claude_agent_sdk.TextBlock(text="LLM> NO-OP")],
            model="claude-test",
        )
        sequencer = dshaccli.PromptSequencer(
            cwd=self.get_scratch_space(),
            system_prompt="Follow the rules.",
            target_file="/tmp/target.py",
            print_output=False,
        )
        fake_client = dshaccli.FakeClaudeSDKClient(responses_by_call=[[msg1]])
        # Run test.
        with umock.patch(
            "claude_agent_sdk.ClaudeSDKClient"
        ) as mock_client_cls:
            mock_client_cls.return_value = fake_client
            asyncio.run(sequencer.execute(["prompt A"]))
        # Check outputs.
        _, kwargs = mock_client_cls.call_args
        options = kwargs["options"]
        self.assertEqual(options.system_prompt, "Follow the rules.")

    def test3(self) -> None:
        """
        Test that `get_outcomes()` records the no-op contract per prompt.
        """
        # Prepare inputs.
        msg1 = claude_agent_sdk.AssistantMessage(
            content=[claude_agent_sdk.TextBlock(text="LLM> NO-OP")],
            model="claude-test",
        )
        msg2 = claude_agent_sdk.AssistantMessage(
            content=[
                claude_agent_sdk.TextBlock(text="LLM> CHANGED: fixed x")
            ],
            model="claude-test",
        )
        sequencer = dshaccli.PromptSequencer(
            cwd=self.get_scratch_space(),
            target_file="/tmp/target.py",
            print_output=False,
        )
        fake_client = dshaccli.FakeClaudeSDKClient(
            responses_by_call=[[msg1], [msg2]]
        )
        # Run test.
        with umock.patch(
            "claude_agent_sdk.ClaudeSDKClient"
        ) as mock_client_cls:
            mock_client_cls.return_value = fake_client
            asyncio.run(sequencer.execute(["prompt A", "prompt B"]))
        # Check outputs.
        expected = "['NO-OP', 'CHANGED: fixed x']"
        self.assertEqual(str(sequencer.get_outcomes()), expected)
        self.assertEqual(len(sequencer.get_responses()), 2)


# #############################################################################
# Test_PromptSequencer_context_strategy
# #############################################################################


class Test_PromptSequencer_context_strategy(hunitest.TestCase):
    """
    Test `PromptSequencer.execute()` client construction per context strategy.
    """

    def helper(
        self, context_strategy: str, expected_call_count: int
    ) -> None:
        """
        Run two prompts under `context_strategy` and check how many times
        `ClaudeSDKClient` was constructed.

        :param context_strategy: `"session"` or `"stateless"`
        :param expected_call_count: expected `ClaudeSDKClient` construction
            count
        """
        # Prepare inputs.
        msg1 = claude_agent_sdk.AssistantMessage(
            content=[claude_agent_sdk.TextBlock(text="LLM> NO-OP")],
            model="claude-test",
        )
        msg2 = claude_agent_sdk.AssistantMessage(
            content=[claude_agent_sdk.TextBlock(text="LLM> NO-OP")],
            model="claude-test",
        )
        sequencer = dshaccli.PromptSequencer(
            cwd=self.get_scratch_space(),
            context_strategy=context_strategy,
            target_file="/tmp/target.py",
            print_output=False,
        )
        fake_client = dshaccli.FakeClaudeSDKClient(
            responses_by_call=[[msg1], [msg2]]
        )
        # Run test.
        with umock.patch(
            "claude_agent_sdk.ClaudeSDKClient"
        ) as mock_client_cls:
            mock_client_cls.return_value = fake_client
            asyncio.run(sequencer.execute(["prompt A", "prompt B"]))
        # Check outputs.
        self.assertEqual(mock_client_cls.call_count, expected_call_count)
        self.assertEqual(sequencer._prompts_executed, 2)

    def test1(self) -> None:
        """
        Test that `session` mode reuses a single client for all prompts.
        """
        # Prepare inputs.
        context_strategy = "session"
        # Prepare outputs.
        expected_call_count = 1
        # Run test.
        self.helper(context_strategy, expected_call_count)

    def test2(self) -> None:
        """
        Test that `stateless` mode opens one fresh client per prompt.
        """
        # Prepare inputs.
        context_strategy = "stateless"
        # Prepare outputs.
        expected_call_count = 2
        # Run test.
        self.helper(context_strategy, expected_call_count)

    def test3(self) -> None:
        """
        Test that an invalid context strategy is rejected at construction.
        """
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            dshaccli.PromptSequencer(context_strategy="bogus")


# #############################################################################
# Test_parse_rule_outcome
# #############################################################################


class Test_parse_rule_outcome(hunitest.TestCase):
    """
    Test `_parse_rule_outcome()` no-op contract parser.
    """

    def helper(self, assistant_text: str, expected: str) -> None:
        """
        Parse `assistant_text` and check the result against `expected`.

        :param assistant_text: assistant reply text to parse
        :param expected: expected parsed outcome
        """
        # Run test.
        actual = dshaccli._parse_rule_outcome(assistant_text)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test that a bare NO-OP reply is parsed as NO-OP.
        """
        # Prepare inputs.
        assistant_text = "LLM> NO-OP"
        # Prepare outputs.
        expected = "NO-OP"
        # Run test.
        self.helper(assistant_text, expected)

    def test2(self) -> None:
        """
        Test that a CHANGED reply is parsed together with its summary.
        """
        # Prepare inputs.
        assistant_text = "LLM> CHANGED: renamed foo to _foo"
        # Prepare outputs.
        expected = "CHANGED: renamed foo to _foo"
        # Run test.
        self.helper(assistant_text, expected)

    def test3(self) -> None:
        """
        Test that surrounding prose does not prevent the contract from
        being found.
        """
        # Prepare inputs.
        assistant_text = """
        I re-read the file and applied the rule.

        LLM> CHANGED: added docstring
        """
        assistant_text = hprint.dedent(assistant_text)
        # Prepare outputs.
        expected = "CHANGED: added docstring"
        # Run test.
        self.helper(assistant_text, expected)

    def test4(self) -> None:
        """
        Test that a reply without the contract markers is UNKNOWN.
        """
        # Prepare inputs.
        assistant_text = "I made some changes but forgot the format."
        # Prepare outputs.
        expected = "UNKNOWN"
        # Run test.
        self.helper(assistant_text, expected)

    def test5(self) -> None:
        """
        Test that an empty reply is UNKNOWN.
        """
        # Prepare inputs.
        assistant_text = ""
        # Prepare outputs.
        expected = "UNKNOWN"
        # Run test.
        self.helper(assistant_text, expected)


# #############################################################################
# Test_PromptSequencer_execute_end_to_end
# #############################################################################


@pytest.mark.skip(
    reason="Run manually: makes a real Claude Agent SDK call and costs tokens"
)
class Test_PromptSequencer_execute_end_to_end(hunitest.TestCase):
    """
    Exercise `PromptSequencer.execute()` against the real Claude Agent SDK.

    Unlike `Test_PromptSequencer_execute`, nothing here is mocked: each test
    makes a real `claude_agent_sdk.ClaudeSDKClient` call, requires the local
    `claude` CLI to be authenticated, and spends real API tokens.

    Real LLM replies are not byte-exact even under strict formatting
    instructions, so `self.assert_equal` is not used on `get_last_response()`,
    and we use `assertIn`.
    """

    # The cheapest available model is used to keep manual runs inexpensive.
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

    def helper(self) -> "dshaccli.PromptSequencer":
        """
        Build a `PromptSequencer` for a real, manual, no-tool-access run.

        :return: sequencer configured with `_NO_TOOLS` and `_MODEL`, ready
            for `execute()`
        """
        return dshaccli.PromptSequencer(
            disallowed_tools=self._NO_TOOLS,
            permission_mode="bypassPermissions",
            cwd=self.get_scratch_space(),
            model=self._MODEL,
            print_output=False,
        )

    def test1(self) -> None:
        """
        Test that a real single-prompt session returns the expected reply.
        """
        # Prepare inputs.
        sequencer = self.helper()
        prompt = (
            "Reply with exactly the single word PONG and nothing else, "
            "no punctuation."
        )
        # Run test.
        asyncio.run(sequencer.execute([prompt]))
        # Check outputs.
        self.assertEqual(sequencer.get_execution_stats()["prompts_executed"], 1)
        self.assertIn("PONG", sequencer.get_last_response())

    def test2(self) -> None:
        """
        Test that conversation context is preserved across sequential prompts.
        """
        # Prepare inputs.
        sequencer = self.helper()
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
        hio.to_file(target_file, "target\n")
        other_file = os.path.join(scratch_dir, "other.txt")
        hio.to_file(other_file, "other\n")
        #
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
        expected_output = hprint.dedent(expected_output)
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
        # Run test.
        self.helper(prompts, responses, expected)
