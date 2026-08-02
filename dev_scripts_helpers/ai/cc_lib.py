"""
Claude Code Prompt Sequencer Library.

Provides async execution of sequential prompts against Claude Code,
maintaining context across prompts.

Import as:

import dev_scripts_helpers.ai.cc_lib as dshaccli
"""

# TODO(gp): Maybe -> helpers/hanthropic.py?

import json
import logging
import os
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional

import claude_agent_sdk

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

CanUseToolFn = Callable[
    [str, Dict[str, Any], Any],
    Awaitable[Any],
]


# #############################################################################
# Message Rendering
# #############################################################################


def message_to_str(message: Any) -> str:
    """
    Render the content of a Claude message as a human-readable string.

    Render assistant text, thinking, and tool calls in a human-readable format.
    Messages that carry no printable content (e.g., results, system metadata)
    yield `""`.

    :param message: Message received from the Claude SDK
    :return: human-readable rendering of `message`, or `""` if there is
        nothing to print
    """
    if not isinstance(message, claude_agent_sdk.AssistantMessage):
        return ""
    # Render each content block in the message with appropriate formatting.
    chunks = []
    for block in message.content:
        if isinstance(block, claude_agent_sdk.TextBlock):
            header = hprint.color_highlight("=== ASSISTANT ===", "bright_white")
            body = hprint.color_highlight(block.text, "bright_white")
        elif isinstance(block, claude_agent_sdk.ThinkingBlock):
            header = hprint.color_highlight("=== THINKING ===", "gray")
            body = hprint.color_highlight(block.thinking, "gray")
        elif isinstance(block, claude_agent_sdk.ToolUseBlock):
            header = hprint.color_highlight(
                f"=== TOOL: {block.name} ===", "yellow"
            )
            body = hprint.color_highlight(block.input, "gray")
        else:
            continue
        chunks.append(f"\n{header}\n{body}")
    return "".join(chunks)


# TODO(ai_gp): Consider inlining.
def print_message(message: Any) -> None:
    """
    Print the content of a Claude message to stdout.

    :param message: Message received from the Claude SDK
    """
    text = message_to_str(message)
    if text:
        print(text, flush=True)


def _extract_assistant_text(message: Any) -> str:
    """
    Extract the concatenated `TextBlock` content from an assistant message.

    :param message: message received from the Claude SDK
    :return: joined text blocks, or `""` for non-assistant messages
    """
    if not isinstance(message, claude_agent_sdk.AssistantMessage):
        return ""
    parts = [
        block.text
        for block in message.content
        if isinstance(block, claude_agent_sdk.TextBlock)
    ]
    return "\n".join(parts)


# #############################################################################
# No-Op Contract Parsing
# #############################################################################


# TODO(gp): Generalize or move it to cc_lint.py since it's specific of that
# Match a structured no-op contract reply; `cc_lint.py`'s
# `_build_rule_message()` asks every rule prompt to end with one of these.
_NO_OP_RE = re.compile(r"^LLM>\s*NO-OP\s*$", re.MULTILINE)
_CHANGED_RE = re.compile(r"^LLM>\s*CHANGED:\s*(.+)$", re.MULTILINE)


def _parse_rule_outcome(assistant_text: str) -> str:
    """
    Parse the no-op contract reply for a single rule prompt.

    :param assistant_text: concatenated text blocks from the assistant's
        reply to one rule prompt
    :return: `"NO-OP"`, `"CHANGED: <summary>"`, or `"UNKNOWN"` when
        `assistant_text` does not follow the contract
        Example:
        ```
        "LLM> NO-OP" -> "NO-OP"
        "LLM> CHANGED: renamed foo to _foo" -> "CHANGED: renamed foo to _foo"
        "I did something" -> "UNKNOWN"
        ```
    """
    changed_match = _CHANGED_RE.search(assistant_text)
    if changed_match:
        outcome = "CHANGED: " + changed_match.group(1).strip()
    elif _NO_OP_RE.search(assistant_text):
        outcome = "NO-OP"
    else:
        outcome = "UNKNOWN"
    _LOG.debug("return=%s", outcome)
    return outcome


# #############################################################################
# Permission Guards
# #############################################################################


def _make_file_scope_guard(target_file: str) -> CanUseToolFn:
    """
    Build a `can_use_tool` callback that restricts edits to `target_file`.

    Any file-modifying tool (`Edit`, `Write`, `NotebookEdit`, `MultiEdit`)
    whose `file_path` input resolves to a different file is denied.

    :param target_file: the only file that file-modifying tools may target
    :return: async callback usable as `ClaudeAgentOptions.can_use_tool`
    """
    # Tools that can modify file content, and therefore must be scoped to
    # `target_file` below.
    file_modifying_tools = ("Edit", "Write", "NotebookEdit", "MultiEdit")
    target_abspath = os.path.abspath(target_file)

    async def can_use_tool(
        tool_name: str,
        tool_input: Dict[str, Any],
        _context: Any,
    ) -> Any:
        if tool_name in file_modifying_tools:
            file_path = tool_input.get("file_path", "")
            if file_path and os.path.abspath(file_path) != target_abspath:
                _LOG.warning(
                    "Denying '%s' on '%s': only '%s' may be modified",
                    tool_name,
                    file_path,
                    target_file,
                )
                return claude_agent_sdk.types.PermissionResultDeny(
                    message=(
                        f"Only '{target_file}' may be modified in this "
                        "session"
                    ),
                )
        return claude_agent_sdk.types.PermissionResultAllow()

    return can_use_tool


# #############################################################################
# PromptSequencer
# #############################################################################


class PromptSequencer:
    """
    Execute a sequence of prompts against Claude Code with context preservation.

    Maintains a single async session across multiple prompts, preserving
    conversation state and message history.
    """

    def __init__(
        self,
        *,
        allowed_tools: Optional[List[str]] = None,
        disallowed_tools: Optional[List[str]] = None,
        permission_mode: str = "ask",
        cwd: str = "",
        print_output: bool = True,
        model: str = "",
        system_prompt: str = "",
        context_strategy: str = "session",
        setting_sources: Optional[List[str]] = None,
        target_file: str = "",
        can_use_tool: Optional[CanUseToolFn] = None,
    ) -> None:
        """
        Initialize PromptSequencer with Claude Code options.

        :param allowed_tools: List of allowed tools (e.g., ["Read", "Edit"])
            - None means "all tools allowed"
        :param disallowed_tools: List of tools to explicitly deny (e.g.,
            ["Bash", "Task", "WebFetch"])
        :param permission_mode: Permission handling mode
            - "ask" (prompt user for each operation)
            - "acceptEdits" (auto-accept edits without prompting)
            - "bypassPermissions" (bypass all permission checks)
        :param cwd: Working directory for Claude Code execution
            - "" means current directory
        :param print_output: If True, print Claude messages to stdout as
            they are received
        :param model: Model name to use for the session
            - "" means the SDK default
        :param system_prompt: System prompt sent once per session
            - "" means no system prompt
        :param context_strategy: How sessions are managed across prompts
            - "session": one `ClaudeSDKClient` shared by all prompts,
              preserving context across them
            - "stateless": a fresh `ClaudeSDKClient` per prompt, giving
              each prompt uniform cost and full attention
        :param setting_sources: Which settings sources to load
            (`"user"`, `"project"`, `"local"`)
            - None defaults to `[]` so the session does not pick up user
              global instructions or project hooks, keeping runs
              reproducible
        :param target_file: if non-empty and `can_use_tool` is not passed,
            a default guard is installed that denies edits to any file
            other than this one
        :param can_use_tool: explicit permission callback, overrides the
            `target_file` guard when provided
        """
        _LOG.debug(
            hprint.to_str(
                "allowed_tools disallowed_tools permission_mode cwd model "
                "context_strategy setting_sources target_file"
            )
        )
        hdbg.dassert_in(
            context_strategy,
            ("session", "stateless"),
            "Unknown context strategy",
        )
        self.allowed_tools = allowed_tools or []
        self.disallowed_tools = disallowed_tools or []
        self.permission_mode = permission_mode
        self.cwd = cwd
        self.print_output = print_output
        self.model = model
        self.system_prompt = system_prompt
        self.context_strategy = context_strategy
        self.setting_sources = (
            [] if setting_sources is None else setting_sources
        )
        self.target_file = target_file
        if can_use_tool is not None:
            self.can_use_tool = can_use_tool
        elif target_file:
            self.can_use_tool = _make_file_scope_guard(target_file)
        else:
            self.can_use_tool = None
        # Tracks if async session has started.
        self._session_started = False
        # Count of executed prompts.
        self._prompts_executed = 0
        # Last response from Claude.
        self._last_response = ""
        # Raw response text per executed prompt, in order.
        self._responses: List[str] = []
        # Parsed no-op contract outcome per executed prompt, in order.
        self._outcomes: List[str] = []

    async def execute(self, prompts: List[str]) -> None:
        """
        Execute a sequence of prompts sequentially.

        Maintains context across prompts, stopping on first error.

        :param prompts: List of prompts to execute in order
            - Each prompt executed in sequence
            - Context preserved between prompts
        :raises RuntimeError: If any prompt execution fails
        """
        _LOG.debug("execute() called with %d prompts", len(prompts))
        hdbg.dassert_lt(0, len(prompts), "Must provide at least one prompt")
        _LOG.info(
            "Starting prompt sequence execution with %d prompts using '%s' "
            "context strategy",
            len(prompts),
            self.context_strategy,
        )
        # Create options for Claude SDK.
        options = claude_agent_sdk.ClaudeAgentOptions(
            allowed_tools=self.allowed_tools,
            disallowed_tools=self.disallowed_tools,
            permission_mode=self.permission_mode,  # type: ignore
            cwd=self.cwd or None,
            model=self.model or None,
            system_prompt=self.system_prompt or None,
            setting_sources=self.setting_sources,  # type: ignore
            can_use_tool=self.can_use_tool,
        )
        if self.context_strategy == "session":
            # Single session: preserve context across all prompts.
            async with claude_agent_sdk.ClaudeSDKClient(
                options=options
            ) as client:
                self._session_started = True
                for prompt_idx, prompt in enumerate(prompts, 1):
                    await self._execute_one_prompt(
                        client, prompt, prompt_idx, len(prompts)
                    )
        else:
            # Stateless: fresh session per prompt, no cross-prompt context.
            for prompt_idx, prompt in enumerate(prompts, 1):
                async with claude_agent_sdk.ClaudeSDKClient(
                    options=options
                ) as client:
                    self._session_started = True
                    await self._execute_one_prompt(
                        client, prompt, prompt_idx, len(prompts)
                    )

    async def _execute_one_prompt(
        self,
        client: Any,
        prompt: str,
        prompt_idx: int,
        total_prompts: int,
    ) -> None:
        """
        Query `client` with a single `prompt` and record its outcome.

        :param client: active `ClaudeSDKClient` session
        :param prompt: prompt text to send
        :param prompt_idx: 1-based index of `prompt` in the overall sequence
        :param total_prompts: total number of prompts in the sequence
        """
        _LOG.info(
            "%s",
            hprint.color_highlight(
                hprint.frame(f"Executing prompt {prompt_idx}/{total_prompts}"),
                "blue",
            ),
        )
        _LOG.debug("Prompt content:\n%s ...", prompt[:200])
        # Query Claude with prompt and collect response asynchronously.
        await client.query(prompt)
        # Collect response messages from stream.
        response_parts: List[str] = []
        text_parts: List[str] = []
        async for message in client.receive_response():
            if self.print_output:
                print_message(message)
            response_parts.append(str(message))
            text = _extract_assistant_text(message)
            if text:
                text_parts.append(text)
        response_text = "".join(response_parts)
        self._last_response = response_text
        self._responses.append(response_text)
        self._outcomes.append(_parse_rule_outcome("\n".join(text_parts)))
        self._prompts_executed += 1
        # Log prompt completion with response metrics.
        _LOG.info("Prompt %d completed successfully", prompt_idx)
        _LOG.debug("Response length: %d chars", len(response_text))

    def get_last_response(self) -> str:
        """
        Get the response from the last executed prompt.

        :return: Raw response text from Claude
        """
        _LOG.debug(
            "get_last_response() returning %d chars", len(self._last_response)
        )
        return self._last_response

    def get_responses(self) -> List[str]:
        """
        Get the raw response text for every executed prompt, in order.

        :return: one entry per executed prompt
        """
        _LOG.debug(
            "get_responses() returning %d responses", len(self._responses)
        )
        return self._responses

    def get_outcomes(self) -> List[str]:
        """
        Get the parsed no-op contract outcome for every executed prompt.

        :return: one entry per executed prompt, each `"NO-OP"`, `"CHANGED:
            <summary>"`, or `"UNKNOWN"` when the reply did not follow the
            contract (see `_parse_rule_outcome()`)
        """
        _LOG.debug("get_outcomes() returning %d outcomes", len(self._outcomes))
        return self._outcomes

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.

        :return: Dictionary with execution metadata
            - `prompts_executed`: Number of prompts executed
            - `session_started`: Whether async session started
        """
        stats = {
            "prompts_executed": self._prompts_executed,
            "session_started": self._session_started,
            "last_response_length": len(self._last_response),
        }
        _LOG.debug("return=%s", hprint.to_str("stats"))
        return stats


# #############################################################################
# Testing Utilities
# #############################################################################


class FakeClaudeSDKClient:
    """
    Minimal stand-in for `claude_agent_sdk.ClaudeSDKClient`.

    A plain `AsyncMock` cannot cleanly emulate an async-generator method
    like `receive_response()`, so a small hand-written fake is used instead.
    """

    def __init__(self, responses_by_call: list) -> None:
        self._responses_by_call = responses_by_call
        self.queried_prompts: List = []
        self.aenter_called = False
        self.aexit_called = False
        # Populated by the caller from the `options` a mocked
        # `claude_agent_sdk.ClaudeSDKClient(...)` construction received,
        # since this fake is not actually built with those kwargs.
        self.options: Any = None

    async def __aenter__(self) -> "FakeClaudeSDKClient":
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

    # TODO(gp): Maybe better to just print all the values.
    def __str__(self) -> str:
        """
        Render all the fake client's state, for test assertions.

        Extracts only the subset of `options` fields that, rather than the full
        `ClaudeAgentOptions` repr, which carries many defaulted fields.

        :return: string with `options`, `queried_prompts`, `aenter_called`, and
            `aexit_called`
        """
        options = None
        if self.options is not None:
            options = (
                self.options.allowed_tools,
                self.options.disallowed_tools,
                self.options.permission_mode,
                self.options.model,
                self.options.setting_sources,
            )
        return (
            f"options={options!r}, "
            f"queried_prompts={self.queried_prompts!r}, "
            f"aenter_called={self.aenter_called!r}, "
            f"aexit_called={self.aexit_called!r}"
        )


# #############################################################################
# Session Logging
# #############################################################################


def save_session_log(
    output_file: str,
    prompts: List[str],
    responses: List[str],
) -> None:
    """
    Save prompt-response pairs to a session log file.

    Stores structured session data as JSON for later analysis.

    :param output_file: Path to output log file
    :param prompts: List of executed prompts
    :param responses: List of corresponding responses
    """
    _LOG.debug("output_file=%s num_pairs=%d", output_file, len(prompts))
    hdbg.dassert_eq(
        len(prompts), len(responses), "Mismatched prompt/response counts"
    )
    _LOG.debug("Saving session log with %d prompt-response pairs", len(prompts))
    # Create session record with prompt-response pairs indexed for traceability.
    prompts_and_responses = [
        {
            "prompt_index": idx,
            "prompt": prompt,
            "response": response,
        }
        for idx, (prompt, response) in enumerate(zip(prompts, responses), 1)
    ]
    session_log = {
        "prompts_and_responses": prompts_and_responses,
        "total_prompts": len(prompts),
    }
    # Serialize session log to JSON and persist to file.
    content = json.dumps(session_log, indent=2)
    hio.to_file(output_file, content)
    _LOG.info("Session log saved to '%s'", output_file)
