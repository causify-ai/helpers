#!/usr/bin/env python3
"""
Execute a command executed in iTerm, save screenshot, and closes iTerm window
after capture is complete.

By default:
- captures only iTerm window
- sources ~/.bashrc
- opens the captured screenshot

Usage:
> capture_iterm_command.py \
    --command "glow TODO.convert_slides_into_book.md" \
    --output_file screenshot.png

> capture_iterm_command.py \
    --command "echo Hello" \
    --output_file hello.png \
    --delay_seconds 3 \
    --no_bashrc

> capture_iterm_command.py \
        --command "ls" \
        --output_file ls.png \
        --include_background \
        --no_open
"""

import argparse
import logging
import subprocess
import time

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# Default delay for command execution.
DEFAULT_DELAY_SECONDS = 5


def _run_in_iterm(
    command: str,
    output_file: str,
    delay_seconds: int,
    *,
    use_bashrc: bool = True,
    window_only: bool = True,
    open_file: bool = True,
) -> None:
    """
    Execute a command in iTerm and capture screenshot.

    Opens an iTerm terminal (~120 characters wide)
    - runs the specified command,
    - waits for execution
    - saves a screenshot to the output file

    By default:
    - Sources `~/.bashrc` before executing the command to ensure environment is
      properly configured
    - Captures only the iTerm window (excluding other applications and desktop)
    - Automatically opens the screenshot file after capture.

    :param command: Command to execute in iTerm
    :param output_file: Path where screenshot should be saved
    :param delay_seconds: Seconds to wait before taking screenshot
        - Default: `DEFAULT_DELAY_SECONDS`
    :param use_bashrc: Whether to source `~/.bashrc` before running command
        - Default: `True`
    :param window_only: Capture only iTerm window, exclude other windows/desktop
        - Default: `True`
    :param open_file: Automatically open captured screenshot with `open` command
        - Default: `True`
    """
    hdbg.dassert_ne(command, "", "Command cannot be empty")
    hdbg.dassert_ne(output_file, "", "Output file path cannot be empty")
    # TODO(ai_gp): Use dassert_lte
    hdbg.dassert(
        delay_seconds >= 0,
        "Delay must be non-negative: %d",
        delay_seconds,
    )
    _LOG.info("Opening iTerm and running command='%s'", command)
    # Build command with optional bashrc sourcing.
    final_command = command
    if use_bashrc:
        final_command = f"source ~/.bashrc && {command}"
        _LOG.debug("Command will be executed with ~/.bashrc sourced")
    # Open iTerm with ~120 character width and execute command.
    apple_script = f"""
    tell application "iTerm"
        activate
        set w to create window with default profile
        tell current session of w
            set columns to 120
            write text "{final_command}"
        end tell
    end tell
    """
    subprocess.run(["osascript", "-e", apple_script])
    _LOG.debug("Waiting '%d' seconds for command execution", delay_seconds)
    time.sleep(delay_seconds)
    _LOG.info("Capturing screenshot and saving to '%s'", output_file)
    # Take screenshot: use window bounds if window_only is True.
    screenshot_cmd = ["screencapture"]
    if window_only:
        _LOG.debug("Screenshot will capture only iTerm window")
        # Get iTerm window bounds using AppleScript.
        bounds_script = """
        tell application "iTerm"
            set w to current window
            set {x1, y1, x2, y2} to bounds of w
            return (x1 as text) & "," & (y1 as text) & "," & ((x2 - x1) as text) & "," & ((y2 - y1) as text)
        end tell
        """
        result = subprocess.run(
            ["osascript", "-e", bounds_script],
            capture_output=True,
            text=True,
        )
        bounds_str = result.stdout.strip()
        _LOG.debug("Window bounds: '%s'", bounds_str)
        # Parse bounds: "x,y,width,height"
        bounds_parts = [int(x.strip()) for x in bounds_str.split(",")]
        if len(bounds_parts) == 4:
            x, y, width, height = bounds_parts
            # screencapture uses -R x,y,width,height format.
            screenshot_cmd.extend(["-R", f"{x},{y},{width},{height}"])
        else:
            _LOG.warning(
                "Invalid bounds format, capturing full screen: %s",
                bounds_str,
            )
    subprocess.run(screenshot_cmd + [output_file])
    _LOG.info("Screenshot saved to '%s'", output_file)
    # Close iTerm window.
    close_script = """
    tell application "iTerm"
        set w to current window
        close w
    end tell
    """
    subprocess.run(["osascript", "-e", close_script])
    _LOG.debug("iTerm window closed")
    # Open captured file if requested.
    if open_file:
        _LOG.info("Opening captured screenshot with 'open' command")
        subprocess.run(["open", output_file])
        _LOG.debug("Screenshot opened: '%s'", output_file)


def _parse() -> argparse.ArgumentParser:
    """
    Create command line argument parser.

    :return: Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "--command",
        type=str,
        default="",
        help="Command to execute in iTerm",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="",
        help="Path to save screenshot",
    )
    parser.add_argument(
        "--delay_seconds",
        type=int,
        default=DEFAULT_DELAY_SECONDS,
        help="Seconds to wait before capturing screenshot",
    )
    parser.add_argument(
        "--no_bashrc",
        action="store_true",
        help="Do not source ~/.bashrc before running command",
    )
    parser.add_argument(
        "--include_background",
        action="store_true",
        help="Include background and other windows in screenshot",
    )
    parser.add_argument(
        "--no_open",
        action="store_true",
        help="Do not open captured screenshot",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for the script.

    Parses arguments and executes the iTerm command capture.

    :param parser: ArgumentParser instance to parse command line arguments
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate required arguments.
    hdbg.dassert_ne(
        args.command,
        "",
        "Must specify --command parameter",
    )
    hdbg.dassert_ne(
        args.output_file,
        "",
        "Must specify --output_file parameter",
    )
    # Execute command capture.
    _run_in_iterm(
        args.command,
        args.output_file,
        args.delay_seconds,
        use_bashrc=not args.no_bashrc,
        window_only=not args.include_background,
        open_file=not args.no_open,
    )


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
