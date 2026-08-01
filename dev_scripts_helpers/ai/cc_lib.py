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
from typing import Any, Dict, List, Optional

import claude_agent_sdk

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# #############################################################################
# Message Rendering
# #############################################################################


def print_message(message: Any) -> None:
    """
    Print the content of a Claude message to stdout.

    Render assistant text, thinking, and tool calls in a human-readable
    format. Messages that carry no printable content (e.g., results,
    system metadata) are skipped.

    :param message: Message received from the Claude SDK
    """
    # _LOG.debug("Printing message of type: %s", type(message).__name__)
    if not isinstance(message, claude_agent_sdk.AssistantMessage):
        return
    # Render each content block in the message with appropriate formatting.
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
        print(f"\n{header}\n{body}", flush=True)


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
        permission_mode: str = "ask",
        cwd: str = "",
        print_output: bool = True,
    ) -> None:
        """
        Initialize PromptSequencer with Claude Code options.

        :param allowed_tools: List of allowed tools (e.g., ["Read", "Edit"])
            - None means "all tools allowed"
        :param permission_mode: Permission handling mode
            - "ask" (prompt user for each operation)
            - "acceptEdits" (auto-accept edits without prompting)
            - "bypassPermissions" (bypass all permission checks)
        :param cwd: Working directory for Claude Code execution
            - "" means current directory
        :param print_output: If True, print Claude messages to stdout as
            they are received
        """
        _LOG.debug(
            hprint.to_str("allowed_tools permission_mode cwd")
        )
        self.allowed_tools = allowed_tools or []
        self.permission_mode = permission_mode
        self.cwd = cwd
        self.print_output = print_output
        # Tracks if async session has started.
        self._session_started = False
        # Count of executed prompts.
        self._prompts_executed = 0
        # Last response from Claude.
        self._last_response = ""

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
            "Starting prompt sequence execution with %d prompts", len(prompts)
        )
        # Create options for Claude SDK.
        options = claude_agent_sdk.ClaudeAgentOptions(
            allowed_tools=self.allowed_tools,
            permission_mode=self.permission_mode,  # type: ignore
            cwd=self.cwd or None,
        )
        # Execute prompts in session with context preservation.
        async with claude_agent_sdk.ClaudeSDKClient(options=options) as client:
            self._session_started = True
            for prompt_idx, prompt in enumerate(prompts, 1):
                # TODO(ai_gp): Make it blue
                _LOG.info(
                    "%s",
                    hprint.frame(f"Executing prompt {prompt_idx}/{len(prompts)}")
                )
                _LOG.debug("Prompt content:\n%s ...", prompt[:200])
                # Query Claude with prompt and collect response asynchronously.
                await client.query(prompt)
                # Collect response messages from stream.
                response_parts: List[str] = []
                async for message in client.receive_response():
                    if self.print_output:
                        print_message(message)
                    response_parts.append(str(message))
                response_text = "".join(response_parts)
                self._last_response = response_text
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
    _LOG.debug(
        "save_session_log() called: output_file=%s num_pairs=%d",
        output_file,
        len(prompts),
    )
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
    _LOG.debug("return=None")
