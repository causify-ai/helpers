#!/usr/bin/env -S uv run

# /// script
# dependencies = ["requests", "beautifulsoup4", "tqdm", "playwright"]
# ///

r"""
Download a URL with a real Chrome browser attached through the Chrome DevTools
Protocol (CDP).

Some sites (e.g., SSRN) return a bot-protection page to scripted clients,
including the headless browser that `download_html_to_md.py` falls back to. This
script drives instead a normal Chrome, started by the user or by
`--launch_chrome`, so the site sees an ordinary browser session with its own
profile and cookies.

- If the site shows a check that needs a person (e.g., a CAPTCHA), the script
  waits (up to `--timeout_sec`) while the check is completed in the Chrome window
- A Chrome started by `--launch_chrome` is closed when the download succeeds,
  unless `--keep_chrome` is passed: a Chrome that was already running is never
  closed
- `--mode html` saves the rendered HTML of the page
- `--mode file` saves a file (e.g., a PDF): the `--referer` page is opened first,
  then the file is fetched from inside that page, so it is requested with the
  cookies and the origin of a person browsing the site
- For an SSRN abstract URL, an SSRN delivery URL, or an SSRN DOI
  (`10.2139/ssrn.<id>`) the referer and the PDF URL are derived automatically

# Usage Example

- Download the PDF of an SSRN paper, starting Chrome if it is not running:
> download_with_chrome.py \
    --launch_chrome \
    --mode file \
    --input "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078" \
    --output ssrn_5277078.pdf

- Download the PDF of an SSRN paper from its DOI, with a Chrome already
  running with `--remote-debugging-port=9222`:
> download_with_chrome.py --mode file --input "10.2139/ssrn.5277078" --output ssrn_5277078.pdf

- Download an explicit file URL, opening a referer page first:
> download_with_chrome.py \
    --mode file \
    --input "https://example.com/files/paper.pdf" \
    --referer "https://example.com/paper" \
    --output paper.pdf

- Save the rendered HTML of a page:
> download_with_chrome.py --launch_chrome --input "https://example.com/page" --output page.html

- Keep the Chrome that the script started open after the download:
> download_with_chrome.py --launch_chrome --keep_chrome --input "https://example.com/page" --output page.html

- Show what would be done without starting Chrome or downloading:
> download_with_chrome.py --mode file --input "10.2139/ssrn.5277078" --output ssrn_5277078.pdf --dry_run

- Overwrite an existing output file instead of skipping:
> download_with_chrome.py --input "https://example.com/page" --output page.html --no_incremental

Import as:

import dev_scripts_helpers.download.download_with_chrome as dshddwich
"""

import argparse
import base64
import logging
import os
import socket
import sys
import time
import urllib.parse
from typing import Any, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import dev_scripts_helpers.download.download_utils as dshddut

_LOG = logging.getLogger(__name__)


# #############################################################################
# SSRN URLs
# #############################################################################


def _resolve_urls(input_arg: str, mode: str, referer: str) -> Tuple[str, str]:
    """
    Resolve the URL to download and the referer page to open first.

    For an SSRN paper, the abstract page is the page to save in `html` mode,
    while in `file` mode the PDF URL is downloaded with the abstract page as
    referer. For any other URL in `file` mode, the referer defaults to the
    origin of the URL, so that the file is fetched from the same origin.

    :param input_arg: URL (or SSRN DOI) to download
    :param mode: "html" or "file"
    :param referer: page to open before fetching the file, "" to use the
        default
    :return: tuple of (URL to download, referer page, "" in `html` mode)
    """
    _LOG.debug(hprint.to_str("input_arg mode referer"))
    url = input_arg
    ssrn_id = dshddut.get_ssrn_id(input_arg)
    if ssrn_id:
        abstract_url = (
            f"https://papers.ssrn.com/sol3/papers.cfm?abstract_id={ssrn_id}"
        )
        if mode == "html":
            url = abstract_url
        else:
            # Keep a delivery URL given by the user, build it otherwise.
            if "Delivery.cfm" not in input_arg:
                url = (
                    f"https://papers.ssrn.com/sol3/Delivery.cfm/{ssrn_id}.pdf"
                    f"?abstractid={ssrn_id}&mirid=1"
                )
            if not referer:
                referer = abstract_url
    if mode == "file" and not referer:
        # Fetching from the origin of the file avoids cross-origin blocking.
        parsed = urllib.parse.urlparse(url)
        referer = f"{parsed.scheme}://{parsed.netloc}/"
    if mode == "html":
        referer = ""
    _LOG.debug(hprint.to_str("url referer"))
    return url, referer


# #############################################################################
# Chrome
# #############################################################################


def _get_default_chrome_path() -> str:
    """
    Get the path of the Chrome executable for the current platform.

    :return: path on macOS, command name on Linux
    """
    if sys.platform == "darwin":
        chrome_path = (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
    else:
        chrome_path = "google-chrome"
    return chrome_path


def _is_cdp_ready(cdp_url: str) -> bool:
    """
    Check if a Chrome is listening for CDP connections.

    :param cdp_url: CDP endpoint, e.g., `http://127.0.0.1:9222`
    :return: True if something accepts connections on its host and port
    """
    _LOG.debug(hprint.to_str("cdp_url"))
    parsed = urllib.parse.urlparse(cdp_url)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        # `connect_ex()` returns an error code instead of raising when nothing
        # is listening.
        is_ready = sock.connect_ex((parsed.hostname, parsed.port)) == 0
    _LOG.debug("return=%s", is_ready)
    return is_ready


def _launch_chrome(
    cdp_url: str, chrome_path: str, profile_dir: str, *, timeout_sec: int = 30
) -> bool:
    """
    Start Chrome with remote debugging, unless one is already listening.

    Chrome only enables remote debugging on a non-default profile, so a
    dedicated `profile_dir` is used: it persists the cookies of the sites
    between runs, e.g., the passed bot checks.

    :param cdp_url: CDP endpoint, e.g., `http://127.0.0.1:9222`
    :param chrome_path: path of the Chrome executable
    :param profile_dir: Chrome user data dir
    :param timeout_sec: seconds to wait for Chrome to accept connections
    :return: True if this call started Chrome, False if one was already
        listening, which is not ours to close
    """
    _LOG.debug(hprint.to_str("cdp_url chrome_path profile_dir timeout_sec"))
    is_launched = not _is_cdp_ready(cdp_url)
    if is_launched:
        port = urllib.parse.urlparse(cdp_url).port
        hio.create_dir(profile_dir, incremental=True)
        # Run Chrome in the background, detached from this script, so that it
        # does not block the script.
        cmd = [
            "nohup",
            f'"{chrome_path}"',
            f"--remote-debugging-port={port}",
            f'--user-data-dir="{profile_dir}"',
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
            "> /dev/null 2>&1 &",
        ]
        cmd = " ".join(cmd)
        _LOG.info("Starting Chrome with profile '%s'", profile_dir)
        hsystem.system(cmd, print_command=True)
        # Wait until Chrome accepts connections.
        start_time = time.time()
        while not _is_cdp_ready(cdp_url):
            hdbg.dassert_lt(
                time.time() - start_time,
                timeout_sec,
                "Chrome did not start listening on '%s'",
                cdp_url,
            )
            time.sleep(0.5)
    else:
        _LOG.info("Chrome is already listening on '%s'", cdp_url)
    _LOG.debug("return=%s", is_launched)
    return is_launched


# #############################################################################
# Download
# #############################################################################


def _wait_until_not_blocked(page: Any, timeout_sec: int) -> None:
    """
    Wait while the page is a bot-protection page that a person can pass.

    A check like a CAPTCHA is completed in the Chrome window, which makes the
    page navigate to the real content.

    :param page: Playwright page
    :param timeout_sec: seconds to wait for the check to be completed
    """
    _LOG.debug(hprint.to_str("timeout_sec"))
    marker = dshddut.detect_blocked_page(page.content())
    if marker:
        _LOG.warning(
            "The page is a bot-protection page ('%s'): complete the check in "
            "the Chrome window, waiting up to %s seconds",
            marker,
            timeout_sec,
        )
        # Poll in the page, which survives the navigations done by a check.
        js_not_blocked = """
            ({markers, maxChars}) => {
                const text = (document.body ? document.body.innerText : "")
                    .replace(/\\s+/g, " ").toLowerCase();
                return text.length >= maxChars
                    || !markers.some((m) => text.includes(m));
            }
        """
        arg = {
            "markers": dshddut.BLOCKED_PAGE_MARKERS,
            "maxChars": dshddut.BLOCKED_PAGE_MAX_TEXT_CHARS,
        }
        page.wait_for_function(
            js_not_blocked, arg=arg, timeout=timeout_sec * 1000
        )
    # Check the final page, since a block page can also be shown at the end.
    marker = dshddut.detect_blocked_page(page.content())
    hdbg.dassert_eq(
        marker, "", "The page is still a bot-protection page:", page.url
    )


def _fetch_file(page: Any, url: str) -> bytes:
    """
    Fetch a file from inside the page, using the cookies of the browser.

    :param page: Playwright page on the same origin as `url`
    :param url: URL of the file
    :return: content of the file
    """
    _LOG.debug(hprint.to_str("url"))
    # `fetch()` returns the file as bytes, which are passed to Python as a
    # base64 string since `evaluate()` only transfers JSON-like values.
    js_fetch = """
        async (url) => {
            const response = await fetch(url, {credentials: "include"});
            if (!response.ok) {
                throw new Error("HTTP " + response.status + " for " + url);
            }
            const bytes = new Uint8Array(await response.arrayBuffer());
            let binary = "";
            const chunk = 0x8000;
            for (let i = 0; i < bytes.length; i += chunk) {
                binary += String.fromCharCode.apply(
                    null, bytes.subarray(i, i + chunk));
            }
            return btoa(binary);
        }
    """
    content_base64 = page.evaluate(js_fetch, url)
    content = base64.b64decode(content_base64)
    _LOG.debug("return len=%s", len(content))
    return content


def _download(
    url: str,
    referer: str,
    output_file: str,
    mode: str,
    cdp_url: str,
    *,
    close_chrome: bool = False,
    timeout_sec: int = 120,
) -> None:
    """
    Download `url` with the Chrome listening on `cdp_url`.

    :param url: URL to download
    :param referer: page to open before fetching the file, only used in
        `file` mode
    :param output_file: path to save the page or file to
    :param mode: "html" to save the rendered page, "file" to save the file
    :param cdp_url: CDP endpoint of the running Chrome
    :param close_chrome: if True, close the whole Chrome (not only our tab)
        once the download succeeded
    :param timeout_sec: seconds to wait for the page to load and for a bot
        check to be completed
    """
    _LOG.debug(
        hprint.to_str("url referer output_file mode cdp_url close_chrome")
    )
    # Lazy import to run unit tests and to avoid the dependency unless needed.
    from playwright.sync_api import sync_playwright

    timeout_ms = timeout_sec * 1000
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp_url)
        hdbg.dassert_lt(0, len(browser.contexts), "Chrome has no window")
        page = browser.contexts[0].new_page()
        if mode == "html":
            # Save the rendered HTML of the page.
            _LOG.info("Opening '%s'", url)
            page.goto(url, wait_until="load", timeout=timeout_ms)
            _wait_until_not_blocked(page, timeout_sec)
            content = page.content()
            hio.to_file(output_file, content)
        else:
            # Open the referer page first, so that the file is fetched with the
            # cookies set by the site, e.g., after a bot check.
            _LOG.info("Opening referer '%s'", referer)
            page.goto(referer, wait_until="load", timeout=timeout_ms)
            _wait_until_not_blocked(page, timeout_sec)
            _LOG.info("Fetching '%s'", url)
            content = _fetch_file(page, url)
            if output_file.lower().endswith(".pdf"):
                hdbg.dassert_eq(
                    content[:5],
                    b"%PDF-",
                    "'%s' is not a PDF (first bytes shown)",
                    url,
                )
            with open(output_file, "wb") as f:
                f.write(content)
        page.close()
        # Only now that the file is saved, close the whole Chrome if it is
        # ours: on a failure the window is left open, to see what the page
        # shows. `Browser.close` is the CDP command to quit the browser, while
        # `browser.close()` would only disconnect from it.
        if close_chrome:
            _LOG.info("Closing Chrome")
            browser.new_browser_cdp_session().send("Browser.close")
    _LOG.info("Saved '%s'", output_file)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    _LOG.debug(hprint.func_signature_to_str())
    parser = argparse.ArgumentParser(
        formatter_class=hparser.CustomHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="URL to download, or SSRN DOI (`10.2139/ssrn.<id>`)",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="File to save the page or file to",
    )
    parser.add_argument(
        "--mode",
        choices=["html", "file"],
        default="html",
        help=(
            "`html` to save the rendered page, `file` to save a file (e.g., a "
            "PDF) fetched from inside the browser"
        ),
    )
    parser.add_argument(
        "--referer",
        default="",
        help=(
            "Page to open before fetching the file in `file` mode, on the "
            "same site as the file. If not specified, it is the SSRN abstract "
            "page for an SSRN paper and the origin of the URL otherwise"
        ),
    )
    parser.add_argument(
        "--cdp_url",
        default="http://127.0.0.1:9222",
        help="CDP endpoint of the running Chrome",
    )
    parser.add_argument(
        "--launch_chrome",
        action="store_true",
        help=(
            "Start Chrome with remote debugging on the port of `--cdp_url` if "
            "none is listening there"
        ),
    )
    parser.add_argument(
        "--keep_chrome",
        action="store_true",
        help=(
            "Do not close the Chrome started by `--launch_chrome` after the "
            "download. A Chrome that was already running is never closed"
        ),
    )
    parser.add_argument(
        "--chrome_path",
        default="",
        help=(
            "Chrome executable for `--launch_chrome`. If not specified, the "
            "standard one for the platform is used"
        ),
    )
    parser.add_argument(
        "--chrome_profile_dir",
        default="~/.cache/chrome_cdp_profile",
        help=(
            "Chrome user data dir for `--launch_chrome`, separate from your "
            "usual Chrome profile"
        ),
    )
    parser.add_argument(
        "--timeout_sec",
        type=int,
        default=120,
        help=(
            "Seconds to wait for a page to load and for a bot check to be "
            "completed in the Chrome window"
        ),
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help="Overwrite the output file instead of skipping",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Download a URL with a real Chrome browser.
    """
    _LOG.debug(hprint.func_signature_to_str())
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Resolve what to download and where to save it.
    url, referer = _resolve_urls(args.input, args.mode, args.referer)
    output_file = os.path.abspath(os.path.expanduser(args.output))
    if os.path.exists(output_file) and not args.no_incremental:
        _LOG.warning("Output already exists, skipping: '%s'", output_file)
        return
    if args.mode == "file":
        hdbg.dassert_eq(
            urllib.parse.urlparse(referer).netloc,
            urllib.parse.urlparse(url).netloc,
            "The referer must be on the same site as the file, to fetch it "
            "from inside the page",
        )
    if args.dry_run:
        if args.launch_chrome:
            _LOG.warning(
                "[DRY_RUN] Would start Chrome listening on '%s'", args.cdp_url
            )
        _LOG.warning(
            "[DRY_RUN] Would download '%s' (mode '%s', referer '%s') to '%s'",
            url,
            args.mode,
            referer,
            output_file,
        )
        return
    # Start Chrome if requested, then download with it. Only a Chrome that
    # this script started is closed afterwards, unless `--keep_chrome`.
    is_launched = False
    if args.launch_chrome:
        chrome_path = args.chrome_path or _get_default_chrome_path()
        profile_dir = os.path.expanduser(args.chrome_profile_dir)
        is_launched = _launch_chrome(args.cdp_url, chrome_path, profile_dir)
    hdbg.dassert(
        _is_cdp_ready(args.cdp_url),
        "No Chrome is listening on '%s': start one with "
        "--remote-debugging-port or pass --launch_chrome",
        args.cdp_url,
    )
    hio.create_dir(os.path.dirname(output_file), incremental=True)
    _download(
        url,
        referer,
        output_file,
        args.mode,
        args.cdp_url,
        close_chrome=is_launched and not args.keep_chrome,
        timeout_sec=args.timeout_sec,
    )


if __name__ == "__main__":
    _main(_parse())
