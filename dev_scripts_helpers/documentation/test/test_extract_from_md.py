import logging
import os
from typing import Generator, List
from unittest import mock

import pytest

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.extract_from_md as dshdefrmd

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_extract_from_md_py
# #############################################################################


class Test_extract_from_md_py(hunitest.TestCase):
    """
    Test extract_from_md script functionality.
    """

    def _create_test_input_file(self) -> None:
        """
        Create the test markdown input file dynamically.
        """
        content = """
        # Introduction

        This is the introduction section.

        ## Background

        Some background information.

        ## Motivation

        Why we are doing this.

        # Methods

        ## Data Collection

        How we collected data.

        ### Sampling Strategy

        Details about sampling.

        # Results

        Our findings.
        """
        content = hprint.dedent(content)
        in_file = os.path.join(self.get_input_dir(), "input.md")
        hio.to_file(in_file, content)

    def _run_script(self, input_file: str, args: str = "") -> str:
        """
        Helper to run the script and return output content.

        :param input_file: input file name in input directory
        :param args: additional arguments to pass to script
        :return: output content
        """
        in_file = os.path.join(self.get_input_dir(), input_file)
        script_path = hgit.find_file_in_git_tree("extract_from_md.py")
        #
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        cmd = f"{script_path} -i {in_file} -o {out_file} {args}"
        hsystem.system(cmd)
        #
        actual = hio.from_file(out_file)
        return actual

    def _assert_script_fails(self, args: str) -> None:
        """
        Helper to assert that _run_script fails with given args.

        :param args: additional arguments to pass to script
        """
        # Run test and check output.
        with self.assertRaises(RuntimeError):
            self._run_script("input.md", args)

    def helper(self, args: str, expected_output: str) -> None:
        """
        Test helper for script execution.

        :param args: Command line arguments for the script
        :param expected_output: Expected output content
        """
        # Prepare inputs.
        self._create_test_input_file()
        # Prepare outputs.
        expected = hprint.dedent(expected_output)
        # Run test.
        actual = self._run_script("input.md", args)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test extracting text between two headers.
        """
        # Prepare inputs.
        args = "--select '# Methods:# Results'"
        # Prepare outputs.
        expected_output = """
        # Methods

        ## Data Collection

        How we collected data.

        ### Sampling Strategy

        Details about sampling.
        """
        # Run test.
        self.helper(args, expected_output)

    def test2(self) -> None:
        """
        Test extracting from header to next same-level header (explicit end).
        """
        # Prepare inputs.
        args = "--select '## Background:## Motivation'"
        # Prepare outputs.
        expected_output = """
        ## Background

        Some background information.
        """
        # Run test.
        self.helper(args, expected_output)

    def test3(self) -> None:
        """
        Test extracting from a header to next same-level (no explicit end).
        """
        # Prepare inputs.
        args = "--select '# Results'"
        # Prepare outputs.
        expected_output = """
        # Results

        Our findings.
        """
        # Run test.
        self.helper(args, expected_output)

    def test4(self) -> None:
        """
        Test error when end header not found.
        """
        # Prepare inputs.
        args = "--select '## Data Collection:## Results'"
        # Run test and check output.
        self._assert_script_fails(args)

    def test5(self) -> None:
        """
        Test error when start header not found.
        """
        # Prepare inputs.
        args = "--select '# Nonexistent'"
        # Run test and check output.
        self._assert_script_fails(args)

    def test6(self) -> None:
        """
        Test error when no --select argument provided.
        """
        # Run test and check output.
        self._assert_script_fails("")


# #############################################################################
# Test_extract_from_md_py_main
# #############################################################################


class Test_extract_from_md_py_main(hunitest.TestCase):
    """
    Test `_main()` called directly (in-process) with mocked `sys.argv`.
    """

    def _run_main(self, argv: List[str]) -> str:
        """
        Run `dshdexfm._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        :return: content of the output file
        """
        parser = dshdefrmd._parse()
        with mock.patch("sys.argv", argv):
            dshdefrmd._main(parser)
        output_file = argv[argv.index("-o") + 1]
        actual = hio.from_file(output_file)
        return actual

    def helper(
        self, file_name: str, content: str, select_arg: str, expected: str
    ) -> None:
        """
        Test helper for `_main()`.

        :param file_name: Input file name
        :param content: Input file content
        :param select_arg: Value for --select argument
        :param expected: Expected output content
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, file_name)
        output_file = os.path.join(scratch_dir, "output.txt")
        content = hprint.dedent(content)
        hio.to_file(input_file, content)
        argv = [
            "extract_from_md.py",
            "-i",
            input_file,
            "-o",
            output_file,
            "--select",
            select_arg,
        ]
        # Run test.
        actual = self._run_main(argv)
        # Check outputs.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test extract a section from a markdown file.
        """
        # Prepare inputs.
        file_name = "input.md"
        content = """
            # Chapter 1
            Intro text.
            # Chapter 2
            Body text.
            """
        select_arg = "# Chapter 2"
        # Prepare outputs.
        expected = """
            # Chapter 2
            Body text.
            """
        # Run test.
        self.helper(file_name, content, select_arg, expected)

    def test2(self) -> None:
        """
        Test extract a slide from a `.txt` slide file.
        """
        # Prepare inputs.
        file_name = "input.txt"
        content = """
            * Slide 1
            Slide 1 content.
            * Slide 2
            Slide 2 content.
            """
        select_arg = "* Slide 1:* Slide 2"
        # Prepare outputs.
        expected = """
            ##### Slide 1
            Slide 1 content.
            """
        # Run test.
        self.helper(file_name, content, select_arg, expected)
