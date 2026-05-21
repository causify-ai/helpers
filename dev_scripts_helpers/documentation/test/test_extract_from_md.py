import logging
import os
from typing import List, Optional

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown_select as hmarsele
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

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

    def helper(
        self,
        document_text: str,
        start_header: str,
        end_header: Optional[str],
        expected_text: str,
    ) -> None:
        """
        Test helper for extract_text_from_markdown_lines.

        :param document_text: Full document text to extract from
        :param start_header: Starting header (full or partial)
        :param end_header: Ending header (full or partial) or None
        :param expected_text: Expected extracted text
        """
        # Prepare inputs.
        lines = self._to_lines(document_text)
        # Prepare outputs.
        expected = self._to_lines(expected_text)
        # Run test.
        actual = hmarsele.extract_text_from_markdown_lines(
            lines, start_header, end_header, is_slide_format=False
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test extracting text between two headers.
        """
        # Prepare inputs.
        document_text = """
            # Introduction

            This is the introduction.

            # Methods

            This is the methods section.

            # Results

            Our findings.
            """
        start_header = "# Methods"
        end_header = "# Results"
        expected_text = """
            # Methods

            This is the methods section.
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def test2(self) -> None:
        """
        Test extracting from header to next same-level header (implicit end).
        """
        # Prepare inputs.
        document_text = """
            # Introduction

            Intro text.

            # Methods

            Methods text.

            # Results

            Results text.
            """
        start_header = "# Methods"
        end_header = None
        expected_text = """
            # Methods

            Methods text.
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def test3(self) -> None:
        """
        Test extracting with nested headers (## under #).
        """
        # Prepare inputs.
        document_text = """
            # Chapter 1

            ## Section 1.1

            Content 1.1

            ## Section 1.2

            Content 1.2

            # Chapter 2
            """
        start_header = "## Section 1.1"
        end_header = None
        expected_text = """
            ## Section 1.1

            Content 1.1
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def test4(self) -> None:
        """
        Test extracting until end of file when no next same-level header.
        """
        # Prepare inputs.
        document_text = """
            # Chapter 1

            ## Section 1.1

            Content 1.1

            # Chapter 2

            Content of chapter 2
            """
        start_header = "## Section 1.1"
        end_header = None
        expected_text = """
            ## Section 1.1

            Content 1.1
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def helper_error(
        self, document_text: str, start_header: str, end_header: Optional[str]
    ) -> None:
        """
        Test helper for extract_text_from_markdown_lines error cases.

        :param document_text: Full document text to extract from
        :param start_header: Starting header (full or partial)
        :param end_header: Ending header (full or partial) or None
        """
        # Prepare inputs.
        lines = self._to_lines(document_text)
        # Run test and check output.
        with self.assertRaises(Exception):
            hmarsele.extract_text_from_markdown_lines(
                lines, start_header, end_header, is_slide_format=False
            )

    def test5(self) -> None:
        """
        Test error when start header not found.
        """
        # Prepare inputs.
        document_text = """
            # Introduction

            Text
            """
        start_header = "# Nonexistent"
        end_header = None
        # Run test.
        self.helper_error(document_text, start_header, end_header)

    def test6(self) -> None:
        """
        Test error when end header not found.
        """
        # Prepare inputs.
        document_text = """
            # Introduction

            Text
            """
        start_header = "# Introduction"
        end_header = "# Nonexistent"
        # Run test.
        self.helper_error(document_text, start_header, end_header)


# #############################################################################
# Test_extract_from_md_script1
# #############################################################################


class Test_extract_from_md_script1(hunitest.TestCase):
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
        args = "--md_start '# Methods' --md_end '# Results'"
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
        Test extracting from header to next same-level header (implicit end).
        """
        # Prepare inputs.
        args = "--md_start '## Background' --md_end '## Motivation'"
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
        args = "--md_start '# Results'"
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
        args = "--md_start '## Data Collection' --md_end '## Results'"
        # Run test and check output.
        self._assert_script_fails(
            args, "Expected script to fail when end header not found"
        )

    def test5(self) -> None:
        """
        Test error when start header not found.
        """
        # Prepare inputs.
        args = "--md_start '# Nonexistent'"
        # Run test and check output.
        self._assert_script_fails(
            args, "Expected script to fail when start header not found"
        )

    def test6(self) -> None:
        """
        Test error when no --md_start argument provided.
        """
        # Run test and check output.
        self._assert_script_fails(
            "", "Expected script to fail when --md_start is missing"
        )


# #############################################################################
# Test__extract_from_md_slides
# #############################################################################


class Test__extract_from_md_slides(hunitest.TestCase):
    """
    Test _extract_from_md_slides function with slide notation.
    """

    @staticmethod
    def _to_lines(text: str) -> List[str]:
        return hprint.dedent(text).strip().split("\n")

    def helper(
        self,
        document_text: str,
        start_header: str,
        end_header: Optional[str],
        expected_text: str,
    ) -> None:
        """
        Test helper for extract_text_from_markdown_lines with slide format.

        :param document_text: Full document text with slide notation
        :param start_header: Starting header/slide (e.g., "* Title" or "##### Title")
        :param end_header: Ending header/slide (optional)
        :param expected_text: Expected extracted text
        """
        # Prepare inputs.
        lines = self._to_lines(document_text)
        # Prepare outputs.
        expected = self._to_lines(expected_text)
        # Run test.
        actual = hmarsele.extract_text_from_markdown_lines(
            lines, start_header, end_header, is_slide_format=True
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test extracting from slide using * notation, no explicit end.
        """
        # Prepare inputs.
        document_text = """
            * Introduction

            This is the introduction slide.

            * Methods

            This is the methods slide.

            * Results

            Our findings.
            """
        start_header = "* Methods"
        end_header = None
        expected_text = """
            ##### Methods

            This is the methods slide.
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def test2(self) -> None:
        """
        Test extracting between two slides using * notation.
        """
        # Prepare inputs.
        document_text = """
            * Introduction

            Intro text.

            * Methods

            Methods text.

            * Results

            Results text.
            """
        start_header = "* Methods"
        end_header = "* Results"
        expected_text = """
            ##### Methods

            Methods text.
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)

    def test3(self) -> None:
        """
        Test extracting from slide using * notation to header using # notation.
        """
        # Prepare inputs.
        document_text = """
            * Slide 1

            Content of slide 1.

            ##### Subsection 1.1

            Content 1.1

            * Slide 2

            Content of slide 2.
            """
        start_header = "* Slide 1"
        end_header = "##### Subsection 1.1"
        expected_text = """
            ##### Slide 1

            Content of slide 1.
            """
        # Run test.
        self.helper(document_text, start_header, end_header, expected_text)


# #############################################################################
# Test_extract_rule_from_file
# #############################################################################


class Test_extract_rule_from_file(hunitest.TestCase):
    """
    Test extracting rules from markdown rule files.
    """

    def helper_create_rule_file(self) -> str:
        """
        Create a test rule file with multiple sections at different levels.

        :return: path to the created rule file
        """
        out_dir = self.get_scratch_space()
        file_path = os.path.join(out_dir, "rules.md")
        content = """
            - Document intro

            # Level 1 Section

            - Level 1 content line 1
            - Level 1 content line 2

            ## Level 1.1 Subsection

            - Level 1.1 content line 1
            - Level 1.1 content line 2

            ## Level 1.2 Subsection

            - Level 1.2 content

            # Another Level 1 Section

            - Another level 1 content
            """
        content = hprint.dedent(content)
        hio.to_file(file_path, content)
        return file_path

    def test1(self) -> None:
        """
        Test extracting entire file when no line number is provided.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = file_path
        actual = hmarsele.extract_rule_from_file(rule_spec)
        # The content should be the full file.
        expected = hio.from_file(file_path)
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test extracting level-1 header section (line 3).
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:3"
        actual = hmarsele.extract_rule_from_file(rule_spec)
        # Should extract from line 3 until the next level-1 header (line 13).
        expected = """
            # Level 1 Section

            - Level 1 content line 1
            - Level 1 content line 2

            ## Level 1.1 Subsection

            - Level 1.1 content line 1
            - Level 1.1 content line 2

            ## Level 1.2 Subsection

            - Level 1.2 content"""
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """
        Test extracting level-2 header section stops at next level-2 or level-1.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:8"
        actual = hmarsele.extract_rule_from_file(rule_spec)
        # Should extract from line 8 (level-2 header) to next level-2 header
        # (line 13).
        expected = """
            ## Level 1.1 Subsection

            - Level 1.1 content line 1
            - Level 1.1 content line 2"""
        self.assert_equal(actual, expected, dedent=True)

    def test4(self) -> None:
        """
        Test extracting with section name validation (matching).
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:3:# Level 1 Section"
        actual = hmarsele.extract_rule_from_file(rule_spec)
        # Same as test2 since the name matches.
        expected = """
            # Level 1 Section

            - Level 1 content line 1
            - Level 1 content line 2

            ## Level 1.1 Subsection

            - Level 1.1 content line 1
            - Level 1.1 content line 2

            ## Level 1.2 Subsection

            - Level 1.2 content"""
        self.assert_equal(actual, expected, dedent=True)

    def test5(self) -> None:
        """
        Test that section name mismatch raises ValueError.
        """
        file_path = self.helper_create_rule_file()
        rule_spec = f"{file_path}:3:# Different Name"
        with self.assertRaises(ValueError):
            hmarsele.extract_rule_from_file(rule_spec)

    def test6(self) -> None:
        """
        Test that non-header line raises ValueError.
        """
        file_path = self.helper_create_rule_file()
        # This is "- Level 1 content line 1", not a header.
        rule_spec = f"{file_path}:4"
        with self.assertRaises(ValueError):
            hmarsele.extract_rule_from_file(rule_spec)

    def test7(self) -> None:
        """
        Test that invalid line number raises error.
        """
        file_path = self.helper_create_rule_file()
        # Out of range.
        rule_spec = f"{file_path}:999"
        with self.assertRaises(AssertionError):
            hmarsele.extract_rule_from_file(rule_spec)

    def test8(self) -> None:
        """
        Test that non-existent file raises error.
        """
        rule_spec = "/nonexistent/path/to/file.md"
        with self.assertRaises(AssertionError):
            hmarsele.extract_rule_from_file(rule_spec)
