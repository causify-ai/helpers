import logging
import os
from typing import List

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.extract_text_from_txt as dshdetftx

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_extract_text_from_markdown
# #############################################################################


class Test_extract_text_from_markdown(hunitest.TestCase):
    """
    Test _extract_text_from_markdown function.
    """

    @staticmethod
    def _to_lines(text: str) -> List[str]:
        return hprint.dedent(text).strip().split("\n")

    def test1(self) -> None:
        """
        Test extracting text between two headers.
        """
        # Prepare inputs.
        text = """
            # Introduction

            This is the introduction.

            # Methods

            This is the methods section.

            # Results

            Our findings.
            """
        lines = self._to_lines(text)
        # Run test.
        actual = dshdetftx._extract_text_from_markdown(
            lines, "# Methods", "# Results"
        )
        # Check outputs.
        expected_text = """
            # Methods

            This is the methods section.
            """
        expected = self._to_lines(expected_text)
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test extracting from header to next same-level header (implicit end).
        """
        # Prepare inputs.
        text = """
            # Introduction

            Intro text.

            # Methods

            Methods text.

            # Results

            Results text.
            """
        lines = self._to_lines(text)
        # Run test.
        actual = dshdetftx._extract_text_from_markdown(lines, "# Methods", None)
        # Check outputs.
        expected_text = """
            # Methods

            Methods text.
            """
        expected = self._to_lines(expected_text)
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test extracting with nested headers (## under #).
        """
        # Prepare inputs.
        text = """
            # Chapter 1

            ## Section 1.1

            Content 1.1

            ## Section 1.2

            Content 1.2

            # Chapter 2
            """
        lines = self._to_lines(text)
        # Run test: extract from ## Section 1.1 to ## Section 1.2 (next same level)
        actual = dshdetftx._extract_text_from_markdown(
            lines, "## Section 1.1", None
        )
        # Check outputs.
        expected_text = """
            ## Section 1.1

            Content 1.1
            """
        expected = self._to_lines(expected_text)
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test extracting until end of file when no next same-level header.
        """
        # Prepare inputs.
        text = """
            # Chapter 1

            ## Section 1.1

            Content 1.1

            # Chapter 2

            Content of chapter 2
            """
        lines = self._to_lines(text)
        # Run test: extract from ## Section 1.1 with no explicit end
        actual = dshdetftx._extract_text_from_markdown(
            lines, "## Section 1.1", None
        )
        # Check outputs: should stop at next level 1 header
        expected_text = """
            ## Section 1.1

            Content 1.1
            """
        expected = self._to_lines(expected_text)
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Test error when start header not found.
        """
        # Prepare inputs.
        text = """
            # Introduction

            Text
            """
        lines = self._to_lines(text)
        # Run test and check output.
        with self.assertRaises(Exception):
            dshdetftx._extract_text_from_markdown(lines, "# Nonexistent", None)

    def test6(self) -> None:
        """
        Test error when end header not found.
        """
        # Prepare inputs.
        text = """
            # Introduction

            Text
            """
        lines = self._to_lines(text)
        # Run test and check output.
        with self.assertRaises(Exception):
            dshdetftx._extract_text_from_markdown(
                lines, "# Introduction", "# Nonexistent"
            )


# #############################################################################
# Test_extract_text_from_txt_script1
# #############################################################################


class Test_extract_text_from_txt_script1(hunitest.TestCase):
    """
    Test extract_text_from_txt script functionality.
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
        script_path = hgit.find_file_in_git_tree("extract_text_from_txt.py")
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        cmd = f"{script_path} -i {in_file} -o {out_file} {args}"
        hsystem.system(cmd)
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

    def test1(self) -> None:
        """
        Test extracting text between two headers.
        """
        # Prepare inputs.
        args = "--start '# Methods' --end '# Results'"
        # Run test.
        actual = self._run_script("input.md", args)
        # Check outputs.
        expected = """
        # Methods

        ## Data Collection

        How we collected data.

        ### Sampling Strategy

        Details about sampling.
        """
        expected = hprint.dedent(expected)
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test extracting from header to next same-level header (implicit end).
        """
        # Prepare inputs.
        args = "--start '## Background' --end '## Motivation'"
        # Run test.
        actual = self._run_script("input.md", args)
        # Check outputs.
        expected = """
        ## Background

        Some background information.
        """
        expected = hprint.dedent(expected)
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test extracting from a header to next same-level (no explicit end).
        """
        # Prepare inputs.
        args = "--start '# Results'"
        # Run test.
        actual = self._run_script("input.md", args)
        # Check outputs.
        expected = """
        # Results

        Our findings.
        """
        expected = hprint.dedent(expected)
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test error when end header not found.
        """
        # Prepare inputs.
        args = "--start '## Data Collection' --end '## Results'"
        # Run test and check output.
        self._assert_script_fails(
            args, "Expected script to fail when end header not found"
        )

    def test5(self) -> None:
        """
        Test error when start header not found.
        """
        # Prepare inputs.
        args = "--start '# Nonexistent'"
        # Run test and check output.
        self._assert_script_fails(
            args, "Expected script to fail when start header not found"
        )

    def test6(self) -> None:
        """
        Test error when no --start argument provided.
        """
        # Run test and check output.
        self._assert_script_fails(
            "", "Expected script to fail when --start is missing"
        )
