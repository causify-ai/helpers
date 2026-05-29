import logging
import os

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

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

    def setUp(self) -> None:
        """
        Create test input file.
        """
        super().setUp()
        self._create_test_input_file()

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

    def _assert_script_fails(self, args: str, msg: str) -> None:
        """
        Helper to assert that _run_script fails with given args.

        :param args: additional arguments to pass to script
        :param msg: failure message if script doesn't raise
        """
        try:
            self._run_script("input.md", args)
            self.fail(msg)
        except Exception as e:
            _LOG.info(f"Got expected error: {e}")

    def helper(self, args: str, expected_output: str) -> None:
        """
        Test helper for script execution.

        :param args: Command line arguments for the script
        :param expected_output: Expected output content
        """
        # Run test.
        actual = self._run_script("input.md", args)
        # Prepare outputs.
        expected = hprint.dedent(expected_output)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test extracting text between two headers.
        """
        # Prepare inputs.
        args = "--select '# Methods:# Results'"
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
        self._assert_script_fails(
            args, "Expected script to fail when end header not found"
        )

    def test5(self) -> None:
        """
        Test error when start header not found.
        """
        # Prepare inputs.
        args = "--select '# Nonexistent'"
        # Run test and check output.
        self._assert_script_fails(
            args, "Expected script to fail when start header not found"
        )

    def test6(self) -> None:
        """
        Test error when no --select argument provided.
        """
        # Run test and check output.
        self._assert_script_fails(
            "", "Expected script to fail when --select is missing"
        )
