"""
Claude Code Prompt Sequencer Library.

Provides async execution of sequential prompts against Claude Code,
maintaining context across prompts.

Import as:

import dev_scripts_helpers.ai.cc_lib as dshaccli
"""

import json
import logging
from typing import Any, Dict, List, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio

_LOG = logging.getLogger(__name__)


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
    ) -> None:
        """
        Initialize PromptSequencer with Claude Code options.

        :param allowed_tools: List of allowed tools (e.g., ["Read", "Edit"])
            - Default: None (all tools allowed)
        :param permission_mode: Permission handling mode
            - Options: "ask", "acceptEdits", "bypassPermissions"
            - Default: "ask"
        :param cwd: Working directory for Claude Code execution
            - Default: "" (current directory)
        """
        self.allowed_tools = allowed_tools or []
        self.permission_mode = permission_mode
        self.cwd = cwd
        self._session_started = False
        self._prompts_executed = 0
        self._last_response = ""
        _LOG.debug(
            "PromptSequencer initialized: allowed_tools=%s, "
            "permission_mode=%s, cwd=%s",
            allowed_tools,
            permission_mode,
            cwd,
        )

    async def execute(self, prompts: List[str]) -> None:
        """
        Execute a sequence of prompts sequentially.

        Maintains context across prompts, stopping on first error.

        :param prompts: List of prompts to execute in order
            - Each prompt executed in sequence
            - Context preserved between prompts
        :raises RuntimeError: If any prompt execution fails
        """
        hdbg.dassert(
            len(prompts) > 0,
            "Must provide at least one prompt",
        )
        _LOG.info(
            "Starting prompt sequence execution with %d prompts", len(prompts)
        )

        # Import Claude SDK here to avoid hard dependency at module level.
        try:
            from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        except ImportError as e:
            raise RuntimeError(
                "Claude Agent SDK not installed. "
                "Install with: pip install claude-agent-sdk"
            ) from e

        # Create options for Claude SDK.
        options = ClaudeAgentOptions(
            allowed_tools=self.allowed_tools,
            permission_mode=self.permission_mode,  # type: ignore
            cwd=self.cwd or None,
        )

        # Execute prompts in session.
        async with ClaudeSDKClient(options=options) as client:
            self._session_started = True

            for prompt_idx, prompt in enumerate(prompts, 1):
                _LOG.info("Executing prompt %d/%d", prompt_idx, len(prompts))
                _LOG.debug("Prompt content: %s", prompt[:100])

                try:
                    # Query Claude with prompt.
                    await client.query(prompt)

                    # Collect response messages.
                    response_parts: List[str] = []
                    async for message in client.receive_response():
                        response_parts.append(str(message))

                    response_text = "".join(response_parts)
                    self._last_response = response_text
                    self._prompts_executed += 1

                    _LOG.info("Prompt %d completed successfully", prompt_idx)
                    _LOG.debug("Response length: %d chars", len(response_text))

                except Exception as e:
                    error_msg = "Prompt %d execution failed: %s" % (
                        prompt_idx,
                        str(e),
                    )
                    _LOG.error(error_msg)
                    raise RuntimeError(error_msg) from e

    def get_last_response(self) -> str:
        """
        Get the response from the last executed prompt.

        :return: Raw response text from Claude
        """
        return self._last_response

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.

        :return: Dictionary with execution metadata
            - `prompts_executed`: Number of prompts executed
            - `session_started`: Whether async session started
        """
        return {
            "prompts_executed": self._prompts_executed,
            "session_started": self._session_started,
            "last_response_length": len(self._last_response),
        }


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
    hdbg.dassert_eq(
        len(prompts), len(responses), "Mismatched prompt/response counts"
    )

    # Create session record.
    session_log = {
        "prompts_and_responses": [
            {
                "prompt_index": idx,
                "prompt": prompt,
                "response": response,
            }
            for idx, (prompt, response) in enumerate(zip(prompts, responses), 1)
        ],
        "total_prompts": len(prompts),
    }

    # Save to file.
    content = json.dumps(session_log, indent=2)
    hio.to_file(output_file, content)
    _LOG.info("Session log saved to '%s'", output_file)
