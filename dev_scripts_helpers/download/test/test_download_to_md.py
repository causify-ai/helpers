#!/usr/bin/env python

import logging

import pytest

pytest.importorskip("feedparser")
pytest.importorskip("fitz")

import helpers.hgit as hgit
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.download.download_to_md as dshddtomd

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_detect_input_type
# #############################################################################


class Test_detect_input_type(hunitest.TestCase):
    """
    Test `download_to_md.detect_input_type()`.
    """

    def helper(self, input_arg: str, expected: str) -> None:
        """
        Test helper for `detect_input_type()`.

        :param input_arg: URL to classify
        :param expected: expected input type
        """
        # Run test.
        actual = dshddtomd.detect_input_type(input_arg)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a Hacker News submission URL is detected as `hn`.
        """
        # Prepare inputs.
        input_arg = "https://news.ycombinator.com/item?id=12345"
        # Prepare outputs.
        expected = "hn"
        # Run test.
        self.helper(input_arg, expected)

    def test2(self) -> None:
        """
        Test an arXiv abstract URL is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "https://arxiv.org/abs/1706.03762"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        self.helper(input_arg, expected)

    def test3(self) -> None:
        """
        Test a DOI URL is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "https://doi.org/10.1038/nature12373"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        self.helper(input_arg, expected)

    def test4(self) -> None:
        """
        Test a bare DOI is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "10.1038/nature12373"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        self.helper(input_arg, expected)

    def test5(self) -> None:
        """
        Test a generic PDF URL is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "https://example.com/paper.pdf"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        self.helper(input_arg, expected)

    def test6(self) -> None:
        """
        Test a PDF URL with a query string is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "https://example.com/paper.pdf?download=1"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        self.helper(input_arg, expected)

    def test7(self) -> None:
        """
        Test a generic web page URL is detected as `html`.
        """
        # Prepare inputs.
        input_arg = "https://example.com/some/article"
        # Prepare outputs.
        expected = "html"
        # Run test.
        self.helper(input_arg, expected)

    def test8(self) -> None:
        """
        Test an empty input is detected as `html`.
        """
        # Prepare inputs.
        input_arg = ""
        # Prepare outputs.
        expected = "html"
        # Run test.
        self.helper(input_arg, expected)

    def test9(self) -> None:
        """
        Test a single character input is detected as `html`.
        """
        # Prepare inputs.
        input_arg = "a"
        # Prepare outputs.
        expected = "html"
        # Run test.
        self.helper(input_arg, expected)

    def test10(self) -> None:
        """
        Test a large URL with a long query string is detected as `html`.
        """
        # Prepare inputs.
        input_arg = "https://example.com/article?" + "a" * 10000
        # Prepare outputs.
        expected = "html"
        # Run test.
        self.helper(input_arg, expected)


# #############################################################################
# Test_detect_input_type_local_file
# #############################################################################


class Test_detect_input_type_local_file(hunitest.TestCase):
    """
    Test `download_to_md.detect_input_type()` with a local PDF file path.
    """

    def test1(self) -> None:
        """
        Test a path to a local PDF file is detected as `academic_paper`.
        """
        # Prepare inputs.
        input_arg = "~/Downloads/ssrn_5277078.pdf"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        actual = dshddtomd.detect_input_type(input_arg)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_detect_input_type_ssrn
# #############################################################################


class Test_detect_input_type_ssrn(hunitest.TestCase):
    """
    Test `download_to_md.detect_input_type()` with an SSRN abstract page.
    """

    def test1(self) -> None:
        """
        Test an SSRN abstract page is detected as `academic_paper`, not `html`.
        """
        # Prepare inputs.
        input_arg = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"
        # Prepare outputs.
        expected = "academic_paper"
        # Run test.
        actual = dshddtomd.detect_input_type(input_arg)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test__dispatch
# #############################################################################


class Test__dispatch(hunitest.TestCase):
    """
    Test `download_to_md._dispatch()` command construction.
    """

    def helper(
        self,
        input_arg: str,
        input_type: str,
        email: str,
        model: str,
        script_name: str,
        expected_args: str,
    ) -> None:
        """
        Test helper for `_dispatch()`: capture the command it would run.

        :param input_arg: URL or local file to download
        :param input_type: "hn", "academic_paper", or "html"
        :param email: contact email to forward
        :param model: LLM model to forward
        :param script_name: name of the script expected to be dispatched to
        :param expected_args: expected arguments of the dispatched script
        """
        # Prepare inputs.
        # Resolve the script path (the result is cached) before capturing the
        # system calls, since `find_file_in_git_tree()` runs `find` through
        # `hsystem`, which would be mocked out.
        script_path = hgit.find_file_in_git_tree(script_name)
        # Prepare outputs.
        expected_cmd = f"{script_path} {expected_args}"
        expected_str = hprint.dedent(
            f"""
            [
                {{
                'function': hsystem.system,
                'args': ('{expected_cmd}',),
                'kwargs': {{'print_command': True}},
                }},
            ]
            """
        )
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshddtomd._dispatch(
                input_arg, "", input_type, email=email, model=model
            )
        # Check outputs.
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test1(self) -> None:
        """
        Test the email is forwarded to the academic paper script.
        """
        # Prepare inputs.
        input_arg = "10.2139/ssrn.5277078"
        input_type = "academic_paper"
        email = "me@example.org"
        model = ""
        script_name = "download_academic_paper_to_md.py"
        # Prepare outputs.
        expected_args = '--input "10.2139/ssrn.5277078" --email "me@example.org"'
        # Run test.
        self.helper(
            input_arg, input_type, email, model, script_name, expected_args
        )

    def test2(self) -> None:
        """
        Test the email is not forwarded to a script without `--email`.
        """
        # Prepare inputs.
        input_arg = "https://example.com/article"
        input_type = "html"
        email = "me@example.org"
        model = ""
        script_name = "download_html_to_md.py"
        # Prepare outputs.
        expected_args = '--input "https://example.com/article"'
        # Run test.
        self.helper(
            input_arg, input_type, email, model, script_name, expected_args
        )

    def test3(self) -> None:
        """
        Test the model is forwarded to the HTML script.
        """
        # Prepare inputs.
        input_arg = "https://example.com/article"
        input_type = "html"
        email = ""
        model = "openrouter/anthropic/claude-haiku-4.5"
        script_name = "download_html_to_md.py"
        # Prepare outputs.
        expected_args = (
            '--input "https://example.com/article" '
            '--model "openrouter/anthropic/claude-haiku-4.5"'
        )
        # Run test.
        self.helper(
            input_arg, input_type, email, model, script_name, expected_args
        )

    def test4(self) -> None:
        """
        Test the model is forwarded to the academic paper script.
        """
        # Prepare inputs.
        input_arg = "https://arxiv.org/abs/1706.03762"
        input_type = "academic_paper"
        email = ""
        model = "openrouter/anthropic/claude-haiku-4.5"
        script_name = "download_academic_paper_to_md.py"
        # Prepare outputs.
        expected_args = (
            '--input "https://arxiv.org/abs/1706.03762" '
            '--model "openrouter/anthropic/claude-haiku-4.5"'
        )
        # Run test.
        self.helper(
            input_arg, input_type, email, model, script_name, expected_args
        )
