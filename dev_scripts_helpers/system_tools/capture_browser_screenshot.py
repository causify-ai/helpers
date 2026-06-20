#!/usr/bin/env python3
"""
Open a website in a browser, capture screenshot, and optionally close the browser.

By default:
- Opens website in Safari
- Sets browser window to 1024x768
- Captures only browser window
- Waits for page load
- Opens the captured screenshot

Usage:
> capture_browser_screenshot.py \
    --url "https://example.com" \
    --output_file screenshot.png

> capture_browser_screenshot.py \
    --url "https://example.com" \
    --output_file screenshot.png \
    --delay_seconds 3 \
    --browser chrome

> capture_browser_screenshot.py \
    --url "https://example.com" \
    --output_file screenshot.png \
    --window_width 1920 \
    --window_height 1080

> capture_browser_screenshot.py \
    --url "https://example.com" \
    --output_file screenshot.png \
    --browser safari \
    --include_background \
    --no_open \
    --no_close
"""

import argparse
import logging
import subprocess
import time

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# Default delay for page load.
DEFAULT_DELAY_SECONDS = 3

# Default browser window size (width, height).
DEFAULT_WINDOW_WIDTH = 1024
DEFAULT_WINDOW_HEIGHT = 768

# Supported browsers.
SUPPORTED_BROWSERS = ["safari", "chrome"]


def _run_in_browser(
    url: str,
    output_file: str,
    delay_seconds: int,
    *,
    browser: str = "safari",
    window_width: int = DEFAULT_WINDOW_WIDTH,
    window_height: int = DEFAULT_WINDOW_HEIGHT,
    window_only: bool = True,
    open_file: bool = True,
    close_browser: bool = True,
) -> None:
    """
    Open a website in browser and capture screenshot.

    Opens a browser window, navigates to the URL, waits for page load,
    and saves a screenshot to the output file.

    By default:
    - Uses Safari browser
    - Sets browser window to 1024x768
    - Captures only the browser window (excluding other applications/desktop)
    - Waits for page load completion
    - Automatically opens the screenshot file after capture
    - Closes browser window after screenshot

    :param url: Website URL to capture
    :param output_file: Path where screenshot should be saved
    :param delay_seconds: Seconds to wait for page load before taking screenshot
        - Default: `DEFAULT_DELAY_SECONDS`
    :param browser: Browser to use ('safari' or 'chrome')
        - Default: `'safari'`
    :param window_width: Browser window width in pixels
        - Default: `DEFAULT_WINDOW_WIDTH` (1024)
    :param window_height: Browser window height in pixels
        - Default: `DEFAULT_WINDOW_HEIGHT` (768)
    :param window_only: Capture only browser window, exclude other windows/desktop
        - Default: `True`
    :param open_file: Automatically open captured screenshot with `open` command
        - Default: `True`
    :param close_browser: Close browser window after screenshot
        - Default: `True`
    """
    hdbg.dassert_ne(url, "", "URL cannot be empty")
    hdbg.dassert_ne(output_file, "", "Output file path cannot be empty")
    # TODO(ai_gp): dassert_lte
    hdbg.dassert(
        delay_seconds >= 0,
        "Delay must be non-negative: %d",
        delay_seconds,
    )
    hdbg.dassert(
        window_width > 0,
        "Window width must be positive: %d",
        window_width,
    )
    hdbg.dassert(
        window_height > 0,
        "Window height must be positive: %d",
        window_height,
    )
    hdbg.dassert_in(
        browser.lower(),
        SUPPORTED_BROWSERS,
        f"Browser must be one of {SUPPORTED_BROWSERS}, got: %s",
        browser,
    )

    browser = browser.lower()
    _LOG.info("Opening %s and navigating to '%s'", browser.capitalize(), url)

    # Open browser and navigate to URL based on browser type.
    apple_script: str
    if browser == "safari":
        apple_script = f"""
        tell application "Safari"
            activate
            set w to make new document
            set URL of w to "{url}"
        end tell
        """
    else:  # browser == "chrome"
        apple_script = f"""
        tell application "Google Chrome"
            activate
            make new window
            set URL of active tab of front window to "{url}"
        end tell
        """
    subprocess.run(["osascript", "-e", apple_script])

    # Resize browser window to specified dimensions.
    _LOG.debug("Resizing window to %dx%d", window_width, window_height)
    resize_script: str
    if browser == "safari":
        resize_script = f"""
        tell application "Safari"
            set w to front window
            set bounds of w to {{0, 0, {window_width}, {window_height}}}
        end tell
        """
    else:  # browser == "chrome"
        resize_script = f"""
        tell application "Google Chrome"
            set w to front window
            set bounds of w to {{0, 0, {window_width}, {window_height}}}
        end tell
        """
    subprocess.run(["osascript", "-e", resize_script])

    _LOG.debug("Waiting '%d' seconds for page load", delay_seconds)
    time.sleep(delay_seconds)
    _LOG.info("Capturing screenshot and saving to '%s'", output_file)
    # Take screenshot: use window bounds if window_only is True.
    screenshot_cmd = ["screencapture"]
    if window_only:
        _LOG.debug("Screenshot will capture only browser window")
        # Get browser window bounds using AppleScript.
        bounds_script: str
        if browser == "safari":
            bounds_script = """
            tell application "Safari"
                set w to front window
                set {x1, y1, x2, y2} to bounds of w
                return (x1 as text) & "," & (y1 as text) & "," & ((x2 - x1) as text) & "," & ((y2 - y1) as text)
            end tell
            """
        else:  # browser == "chrome"
            bounds_script = """
            tell application "Google Chrome"
                set w to front window
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

    # Close browser window if requested.
    if close_browser:
        _LOG.debug("Closing %s window", browser.capitalize())
        close_script: str
        if browser == "safari":
            close_script = """
            tell application "Safari"
                set w to front window
                close w
            end tell
            """
        else:  # browser == "chrome"
            close_script = """
            tell application "Google Chrome"
                set w to front window
                close w
            end tell
            """
        subprocess.run(["osascript", "-e", close_script])
        _LOG.debug("%s window closed", browser.capitalize())
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
        "--url",
        type=str,
        default="",
        help="Website URL to capture",
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
        help="Seconds to wait for page load before capturing screenshot",
    )
    parser.add_argument(
        "--browser",
        type=str,
        default="safari",
        choices=SUPPORTED_BROWSERS,
        help="Browser to use for capturing",
    )
    parser.add_argument(
        "--window_width",
        type=int,
        default=DEFAULT_WINDOW_WIDTH,
        help=f"Browser window width in pixels",
    )
    parser.add_argument(
        "--window_height",
        type=int,
        default=DEFAULT_WINDOW_HEIGHT,
        help=f"Browser window height in pixels",
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
    parser.add_argument(
        "--no_close",
        action="store_true",
        help="Do not close browser window after screenshot",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for the script.

    Parses arguments and executes the browser screenshot capture.

    :param parser: ArgumentParser instance to parse command line arguments
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate required arguments.
    hdbg.dassert_ne(
        args.url,
        "",
        "Must specify --url parameter",
    )
    hdbg.dassert_ne(
        args.output_file,
        "",
        "Must specify --output_file parameter",
    )
    # Execute screenshot capture.
    _run_in_browser(
        args.url,
        args.output_file,
        args.delay_seconds,
        browser=args.browser,
        window_width=args.window_width,
        window_height=args.window_height,
        window_only=not args.include_background,
        open_file=not args.no_open,
        close_browser=not args.no_close,
    )


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
