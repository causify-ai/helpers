"""
Utility to wrap subprocess and hsystem.system calls for coverage tracking. This
module provides a way to automatically wrap subprocess calls to ensure that any
Python invocations are run under coverage, if enabled via environment variables
or command-line options.

Examples:
coverage run --parallel-mode -m pytest --coverage_subprocess <directory>
coverage run --parallel-mode -m pytest --coverage_subprocess --arg1 --arg2
coverage combine
coverage report

or
export COVERAGE_SUBPROCESS_WRAP=1
coverage run --parallel-mode -m pytest <directory>
coverage combine
coverage report

Import as:

import coverage_subprocess_util as csubutil
"""

import os
import shlex
import subprocess
from typing import Any, List, Union

import helpers.hsystem as hsystem


# #############################################################################
# CoverageSubprocessWrapper
# #############################################################################


class CoverageSubprocessWrapper:
    """
    Wraps subprocess calls to include coverage tracking.
    """

    def __init__(self) -> None:
        # Preserve original commands.
        self._orig_popen = subprocess.Popen
        self._orig_run = subprocess.run
        self._orig_call = subprocess.call
        self._orig_check_call = subprocess.check_call
        self._orig_system = os.system
        self._orig_hsystem_system = hsystem.system
        self._is_patched = False

    def patch(self) -> None:
        """
        Patch commands.
        """
        if self._is_patched:
            return
        # Patch subprocess and system.
        subprocess.Popen = self._patched_popen
        subprocess.run = self._patched_run
        subprocess.call = self._patched_call
        subprocess.check_call = self._patched_check_call
        os.system = lambda cmd: self._orig_system(self._wrap_cmd_str(cmd))
        hsystem.system = lambda cmd, *a, **k: self._orig_hsystem_system(
            self._wrap_cmd_str(cmd), *a, **k
        )
        self._is_patched = True

    def unpatch(self) -> None:
        """
        Restore original commands.
        """
        if not self._is_patched:
            return
        # Restore subprocess and system.
        subprocess.Popen = self._orig_popen
        subprocess.run = self._orig_run
        subprocess.call = self._orig_call
        subprocess.check_call = self._orig_check_call
        os.system = self._orig_system
        hsystem.system = self._orig_hsystem_system
        self._is_patched = False

    def _wrap_cmd_str(self, cmd: str) -> str:
        """
        Wrap a command to include coverage if it's a Python invocation.

        :param cmd: the command to wrap
        :return: the wrapped command
        """
        if isinstance(cmd, str):
            cmd = os.fsdecode(cmd)
        # Handle the case where _system wraps the command in parentheses.
        original_cmd = cmd
        wrapped_in_parens = False
        suffix = ""
        if cmd.startswith("(") and ") 2>&1" in cmd:
            # Command is wrapped in parentheses like "(...) 2>&1"
            # Extract the inner command.
            paren_end = cmd.rfind(") 2>&1")
            if paren_end > 0:
                inner_cmd = cmd[1:paren_end]
                suffix = cmd[paren_end:]
                wrapped_in_parens = True
                cmd = inner_cmd
        try:
            tokens = shlex.split(cmd)
        except ValueError:
            # Command could not be split, return original.
            return original_cmd
        if not tokens:
            return original_cmd
        # Check if --parallel-mode is already in the command.
        if "--parallel-mode" in tokens:
            return original_cmd
        first = tokens[0]
        second = tokens[1] if len(tokens) > 1 else ""
        # Wrap anything named python*, any .py script, or -m invocations.
        wants_wrap = (
            first.startswith("python")
            or first.endswith(".py")
            or second.endswith(".py")
            or (second == "-m" and len(tokens) > 2)
            or first == "coverage"
        )
        if wants_wrap:
            # If it's already a coverage command, just add --parallel-mode.
            if first == "coverage":
                # Find where to insert --parallel-mode.
                if "run" in tokens:
                    run_index = tokens.index("run")
                    new_tokens = (
                        tokens[: run_index + 1]
                        + ["--parallel-mode"]
                        + tokens[run_index + 1 :]
                    )
                else:
                    # Coverage without run subcommand, add run --parallel-mode.
                    new_tokens = ["coverage", "run", "--parallel-mode"] + tokens[
                        1:
                    ]
            else:
                # Not a coverage command, wrap it completely.
                prefix = ["coverage", "run", "--parallel-mode"]
                new_tokens = prefix + tokens
            # Add data file if specified.
            data_file = os.getenv("COVERAGE_FILE")
            if data_file and "--data-file" not in new_tokens:
                try:
                    run_index = new_tokens.index("run")
                    new_tokens = (
                        new_tokens[: run_index + 1]
                        + ["--data-file", data_file]
                        + new_tokens[run_index + 1 :]
                    )
                except ValueError:
                    # 'run' not found, append at the end.
                    new_tokens.extend(["--data-file", data_file])
            wrapped_cmd = " ".join(new_tokens)
            if wrapped_in_parens:
                # Original was wrapped in parentheses, restore that structure.
                return f"({wrapped_cmd}){suffix}"
            return wrapped_cmd
        return original_cmd

    def _wrap_cmd_list(self, tokens: List[str]) -> List[str]:
        """
        Wrap a command collection to include coverage if it's a Python
        invocation.

        :param tokens: the command to wrap
        :return: the wrapped command
        """
        if not tokens or "--parallel-mode" in tokens:
            return tokens
        first = tokens[0]
        second = tokens[1] if len(tokens) > 1 else ""
        wants_wrap = (
            first.endswith(("python", "python3"))
            or first.endswith(".py")
            or second.endswith(".py")
            or first == "coverage"
        )
        if wants_wrap:
            # If it's already a coverage command, just add --parallel-mode.
            if first == "coverage":
                # Find where to insert --parallel-mode.
                if "run" in tokens:
                    run_index = tokens.index("run")
                    new_tokens = (
                        tokens[: run_index + 1]
                        + ["--parallel-mode"]
                        + tokens[run_index + 1 :]
                    )
                else:
                    # Coverage without run subcommand, add run --parallel-mode.
                    new_tokens = ["coverage", "run", "--parallel-mode"] + tokens[
                        1:
                    ]
            else:
                # Not a coverage command, wrap it completely.
                prefix = ["coverage", "run", "--parallel-mode"]
                new_tokens = prefix + tokens
            # Add data file if specified.
            data_file = os.getenv("COVERAGE_FILE")
            if data_file and "--data-file" not in new_tokens:
                run_index = new_tokens.index("run")
                new_tokens = (
                    new_tokens[: run_index + 1]
                    + ["--data-file", data_file]
                    + new_tokens[run_index + 1 :]
                )
            return new_tokens
        return tokens

    def _patched_popen(self, *args: Any, **kwargs: Any) -> subprocess.Popen:
        """
        Wrap `subprocess.Popen`.

        :param args: the command to wrap
        :param kwargs: additional arguments
        :return: the wrapped command
        """
        cmd = args[0]
        if isinstance(cmd, str) and kwargs.get("shell"):
            cmd = self._wrap_cmd_str(cmd)
            return self._orig_popen(cmd, **kwargs)
        if isinstance(cmd, (list, tuple)):
            cmd_list = self._wrap_cmd_list(list(cmd))
            return self._orig_popen(cmd_list, **kwargs)
        return self._orig_popen(*args, **kwargs)

    def _patched_run(
        self, cmd: Union[str, List[str]], *args: Any, **kwargs: Any
    ) -> subprocess.CompletedProcess:
        """
        Wrap `subprocess.run`.

        :param cmd: the command to wrap
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: the wrapped command
        """
        user_check = kwargs.pop("check", False)
        if isinstance(cmd, str):
            cmd = self._wrap_cmd_str(cmd)
        elif isinstance(cmd, (list, tuple)):
            cmd = self._wrap_cmd_list(list(cmd))
        return self._orig_run(cmd, *args, check=user_check, **kwargs)

    def _patched_call(self, *args: Any, **kwargs: Any) -> int:
        """
        Wrap `subprocess.call`.

        :param args: the command to wrap
        :param kwargs: additional arguments
        :return: the wrapped command
        """
        cmd = args[0]
        if isinstance(cmd, str):
            cmd = self._wrap_cmd_str(cmd)
        return self._orig_call(cmd, **kwargs)

    def _patched_check_call(self, *args: Any, **kwargs: Any) -> int:
        """
        Wrap `subprocess.check_call`.

        :param args: the command to wrap
        :param kwargs: additional arguments
        :return: the wrapped command
        """
        cmd = args[0]
        if isinstance(cmd, str):
            cmd = self._wrap_cmd_str(cmd)
        return self._orig_check_call(cmd, **kwargs)


# Create a global instance and convenience functions.
_wrapper = CoverageSubprocessWrapper()


def patch_subprocess_for_coverage() -> None:
    """
    General function to patch.
    """
    _wrapper.patch()


def unpatch_subprocess_for_coverage() -> None:
    """
    General function to unpatch.
    """
    _wrapper.unpatch()
