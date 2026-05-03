import logging
import os

import helpers.hgit as hgit
import helpers.hio as hio
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

    def test1(self) -> None:
        """
        Test extracting text between two headers.
        """
        # Prepare inputs.
        from dev_scripts_helpers.documentation import extract_text_from_txt

        lines = [
            "# Introduction",
            "",
            "This is the introduction.",
            "",
            "# Methods",
            "",
            "This is the methods section.",
            "",
            "# Results",
            "",
            "Our findings.",
        ]
        # Run test.
        actual = extract_text_from_txt._extract_text_from_markdown(
            lines, "# Methods", "# Results"
        )
        # Check outputs.
        expected = [
            "# Methods",
            "",
            "This is the methods section.",
            "",
        ]
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test extracting from header to next same-level header (implicit end).
        """
        # Prepare inputs.
        from dev_scripts_helpers.documentation import extract_text_from_txt

        lines = [
            "# Introduction",
            "",
            "Intro text.",
            "",
            "# Methods",
            "",
            "Methods text.",
            "",
            "# Results",
            "",
            "Results text.",
        ]
        # Run test.
        actual = extract_text_from_txt._extract_text_from_markdown(
            lines, "# Methods", None
        )
        # Check outputs.
        expected = [
            "# Methods",
            "",
            "Methods text.",
            "",
        ]
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test extracting with nested headers (## under #).
        """
        # Prepare inputs.
        from dev_scripts_helpers.documentation import extract_text_from_txt

        lines = [
            "# Chapter 1",
            "",
            "## Section 1.1",
            "",
            "Content 1.1",
            "",
            "## Section 1.2",
            "",
            "Content 1.2",
            "",
            "# Chapter 2",
        ]
        # Run test: extract from ## Section 1.1 to ## Section 1.2 (next same level)
        actual = extract_text_from_txt._extract_text_from_markdown(
            lines, "## Section 1.1", None
        )
        # Check outputs.
        expected = [
            "## Section 1.1",
            "",
            "Content 1.1",
            "",
        ]
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test extracting until end of file when no next same-level header.
        """
        # Prepare inputs.
        from dev_scripts_helpers.documentation import extract_text_from_txt

        lines = [
            "# Chapter 1",
            "",
            "## Section 1.1",
            "",
            "Content 1.1",
            "",
            "# Chapter 2",
            "",
            "Content of chapter 2",
        ]
        # Run test: extract from ## Section 1.1 with no explicit end
        actual = extract_text_from_txt._extract_text_from_markdown(
            lines, "## Section 1.1", None
        )
        # Check outputs: should stop at next level 1 header
        expected = [
            "## Section 1.1",
            "",
            "Content 1.1",
            "",
        ]
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Test error when start header not found.
        """
        # Prepare inputs.
        from dev_scripts_helpers.documentation import extract_text_from_txt

        lines = [
            "# Introduction",
            "",
            "Text",
        ]
        # Run test and check output.
        with self.assertRaises(Exception):
            extract_text_from_txt._extract_text_from_markdown(
                lines, "# Nonexistent", None
            )

    def test6(self) -> None:
        """
        Test error when end header not found.
        """
        # Prepare inputs.
        from dev_scripts_helpers.documentation import extract_text_from_txt

        lines = [
            "# Introduction",
            "",
            "Text",
        ]
        # Run test and check output.
        with self.assertRaises(Exception):
            extract_text_from_txt._extract_text_from_markdown(
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
        try:
            self._run_script("input.md", args)
            self.fail("Expected script to fail when end header not found")
        except Exception as e:
            _LOG.info(f"Got expected error: {e}")

    def test5(self) -> None:
        """
        Test error when start header not found.
        """
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "input.md")
        script_path = hgit.find_file_in_git_tree("extract_text_from_txt.py")
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        cmd = f"{script_path} -i {in_file} -o {out_file} --start '# Nonexistent'"
        # Run test and check output.
        try:
            hsystem.system(cmd)
            self.fail("Expected script to fail when start header not found")
        except Exception as e:
            _LOG.info(f"Got expected error: {e}")

    def test6(self) -> None:
        """
        Test error when no --start argument provided.
        """
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "input.md")
        script_path = hgit.find_file_in_git_tree("extract_text_from_txt.py")
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        cmd = f"{script_path} -i {in_file} -o {out_file}"
        # Run test and check output.
        try:
            hsystem.system(cmd)
            self.fail("Expected script to fail when --start is missing")
        except Exception as e:
            _LOG.info(f"Got expected error: {e}")
