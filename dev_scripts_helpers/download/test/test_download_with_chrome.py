#!/usr/bin/env python

import logging
import os
import socket
from typing import Any, List
from unittest import mock

import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.download.download_with_chrome as dshddwich

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__resolve_urls
# #############################################################################


class Test__resolve_urls(hunitest.TestCase):
    """
    Test `download_with_chrome._resolve_urls()`.
    """

    def helper(
        self,
        input_arg: str,
        mode: str,
        referer: str,
        expected_url: str,
        expected_referer: str,
    ) -> None:
        """
        Test helper for `_resolve_urls()`.

        :param input_arg: URL or SSRN DOI to download
        :param mode: "html" or "file"
        :param referer: referer page passed by the user, "" if none
        :param expected_url: expected URL to download
        :param expected_referer: expected referer page
        """
        # Run test.
        actual_url, actual_referer = dshddwich._resolve_urls(
            input_arg, mode, referer
        )
        # Check outputs.
        self.assert_equal(actual_url, expected_url)
        self.assert_equal(actual_referer, expected_referer)

    def test1(self) -> None:
        """
        Test an SSRN DOI in `file` mode is resolved to the PDF and abstract.
        """
        # Prepare inputs.
        input_arg = "10.2139/ssrn.5277078"
        mode = "file"
        referer = ""
        # Prepare outputs.
        expected_url = (
            "https://papers.ssrn.com/sol3/Delivery.cfm/5277078.pdf"
            "?abstractid=5277078&mirid=1"
        )
        expected_referer = (
            "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"
        )
        # Run test.
        self.helper(input_arg, mode, referer, expected_url, expected_referer)

    def test2(self) -> None:
        """
        Test an SSRN DOI in `html` mode is resolved to the abstract page.
        """
        # Prepare inputs.
        input_arg = "10.2139/ssrn.5277078"
        mode = "html"
        referer = ""
        # Prepare outputs.
        expected_url = (
            "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"
        )
        expected_referer = ""
        # Run test.
        self.helper(input_arg, mode, referer, expected_url, expected_referer)

    def test3(self) -> None:
        """
        Test an SSRN delivery URL is kept, with the abstract page as referer.
        """
        # Prepare inputs.
        input_arg = (
            "https://papers.ssrn.com/sol3/Delivery.cfm/5277078.pdf"
            "?abstractid=5277078&mirid=2"
        )
        mode = "file"
        referer = ""
        # Prepare outputs.
        expected_url = input_arg
        expected_referer = (
            "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"
        )
        # Run test.
        self.helper(input_arg, mode, referer, expected_url, expected_referer)

    def test4(self) -> None:
        """
        Test a referer passed by the user is kept.
        """
        # Prepare inputs.
        input_arg = "https://papers.ssrn.com/sol3/Delivery.cfm/5277078.pdf"
        mode = "file"
        referer = "https://papers.ssrn.com/other"
        # Prepare outputs.
        expected_url = input_arg
        expected_referer = referer
        # Run test.
        self.helper(input_arg, mode, referer, expected_url, expected_referer)

    def test5(self) -> None:
        """
        Test the referer of a generic file defaults to the origin of the URL.
        """
        # Prepare inputs.
        input_arg = "https://example.com/files/paper.pdf"
        mode = "file"
        referer = ""
        # Prepare outputs.
        expected_url = input_arg
        expected_referer = "https://example.com/"
        # Run test.
        self.helper(input_arg, mode, referer, expected_url, expected_referer)

    def test6(self) -> None:
        """
        Test a generic URL in `html` mode is unchanged and has no referer.
        """
        # Prepare inputs.
        input_arg = "https://example.com/page"
        mode = "html"
        referer = ""
        # Prepare outputs.
        expected_url = input_arg
        expected_referer = ""
        # Run test.
        self.helper(input_arg, mode, referer, expected_url, expected_referer)


# #############################################################################
# Test__launch_chrome
# #############################################################################


class Test__launch_chrome(hunitest.TestCase):
    """
    Test `download_with_chrome._launch_chrome()`.
    """

    def test1(self) -> None:
        """
        Test a Chrome that is already listening is reused, not started, and
        reported as not launched so that it is not closed afterwards.
        """
        # Prepare inputs.
        chrome_path = "/path/to/chrome"
        profile_dir = os.path.join(self.get_scratch_space(), "profile")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]
            cdp_url = f"http://127.0.0.1:{port}"
            # Run test.
            with hunteuti.capture_sys_calls() as sys_calls:
                actual = dshddwich._launch_chrome(
                    cdp_url, chrome_path, profile_dir
                )
        # Check outputs.
        self.assertEqual(actual, False)
        self.assertEqual(len(sys_calls), 0)

    def test2(self) -> None:
        """
        Test Chrome is started, and reported as launched, when none is
        listening.
        """
        # Prepare inputs.
        chrome_path = "/path/to/chrome"
        profile_dir = os.path.join(self.get_scratch_space(), "profile")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            port = server.getsockname()[1]
        cdp_url = f"http://127.0.0.1:{port}"
        # Chrome is not really started: the call is captured, and the port is
        # opened as the started Chrome would do.
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        def _start_chrome(*args: Any, **kwargs: Any) -> None:
            listener.bind(("127.0.0.1", port))
            listener.listen(1)

        # Run test.
        with mock.patch.object(
            dshddwich.hsystem, "system", side_effect=_start_chrome
        ) as system:
            actual = dshddwich._launch_chrome(cdp_url, chrome_path, profile_dir)
        listener.close()
        # Check outputs.
        self.assertEqual(actual, True)
        self.assertEqual(system.call_count, 1)


# #############################################################################
# Test__is_cdp_ready
# #############################################################################


class Test__is_cdp_ready(hunitest.TestCase):
    """
    Test `download_with_chrome._is_cdp_ready()` with a real local socket.
    """

    def test1(self) -> None:
        """
        Test a port with a listening socket is ready.
        """
        # Prepare inputs.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            # Port 0 lets the OS pick a free port.
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]
            cdp_url = f"http://127.0.0.1:{port}"
            # Run test.
            actual = dshddwich._is_cdp_ready(cdp_url)
        # Check outputs.
        self.assertEqual(actual, True)

    def test2(self) -> None:
        """
        Test a port that was just released is not ready.
        """
        # Prepare inputs.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            port = server.getsockname()[1]
        cdp_url = f"http://127.0.0.1:{port}"
        # Run test.
        actual = dshddwich._is_cdp_ready(cdp_url)
        # Check outputs.
        self.assertEqual(actual, False)


# #############################################################################
# Test_download_with_chrome_py
# #############################################################################


class Test_download_with_chrome_py(hunitest.TestCase):
    """
    Test the `download_with_chrome.py` executable without a browser.
    """

    def run_main(self, argv: List[str]) -> None:
        """
        Run `_main()` with a mocked `sys.argv`.

        :param argv: command-line arguments, starting with the script name
        """
        parser = dshddwich._parse()
        with mock.patch("sys.argv", argv):
            dshddwich._main(parser)

    def test1(self) -> None:
        """
        Test `--dry_run` does not start Chrome nor create the output.
        """
        # Prepare inputs.
        output_file = os.path.join(self.get_scratch_space(), "paper.pdf")
        argv = [
            "download_with_chrome.py",
            "--mode",
            "file",
            "--input",
            "10.2139/ssrn.5277078",
            "--output",
            output_file,
            "--launch_chrome",
            "--dry_run",
        ]
        # Run test.
        with mock.patch.object(dshddwich, "_launch_chrome") as launch_chrome:
            self.run_main(argv)
        # Check outputs.
        self.assertFalse(launch_chrome.called)
        self.assertFalse(os.path.exists(output_file))

    def test2(self) -> None:
        """
        Test an existing output is skipped before Chrome is needed.
        """
        # Prepare inputs.
        output_file = os.path.join(self.get_scratch_space(), "paper.pdf")
        with open(output_file, "w") as f:
            f.write("old content")
        argv = [
            "download_with_chrome.py",
            "--mode",
            "file",
            "--input",
            "10.2139/ssrn.5277078",
            "--output",
            output_file,
            "--launch_chrome",
        ]
        # Run test.
        with mock.patch.object(dshddwich, "_launch_chrome") as launch_chrome:
            self.run_main(argv)
        # Check outputs.
        self.assertFalse(launch_chrome.called)
        with open(output_file) as f:
            self.assert_equal(f.read(), "old content")
