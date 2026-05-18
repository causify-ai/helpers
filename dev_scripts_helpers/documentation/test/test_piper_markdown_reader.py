import logging
import os

import pytest

import dev_scripts_helpers.documentation.piper_markdown_reader as dshdpmare
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__extract_markdown_section
# #############################################################################


class Test__extract_markdown_section(hunitest.TestCase):
    """
    Test _extract_markdown_section function.
    """

    def _create_input_file(self) -> str:
        """
        Create a test markdown input file and return its path.

        :return: path to created input file
        """
        content = """
        # Introduction

        This is the introduction section.

        ## Background

        Some background information.

        # Methods

        ## Data Collection

        How we collected data.

        ### Sampling Strategy

        Details about sampling.

        # Results

        Our findings.
        """
        content = hprint.dedent(content)
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, content)
        return in_file

    def test1(self) -> None:
        """
        Test extracting section between two headers.
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Prepare outputs.
        expected = """
        # Methods

        ## Data Collection
        How we collected data

        ### Sampling Strategy
        Details about sampling
        """
        expected = hprint.dedent(expected)
        # Run test.
        result = dshdpmare._extract_markdown_section(
            in_file, "# Methods", "# Results"
        )
        # Check outputs.
        self.assert_equal(result, expected)

    def test2(self) -> None:
        """
        Test extracting from header to next same-level (implicit end).
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Prepare outputs.
        expected = """
        # Methods

        ## Data Collection
        How we collected data

        ### Sampling Strategy
        Details about sampling
        """
        expected = hprint.dedent(expected)
        # Run test.
        result = dshdpmare._extract_markdown_section(
            in_file, "# Methods", None
        )
        # Check outputs.
        self.assert_equal(result, expected)

    def test3(self) -> None:
        """
        Test error when start header not found.
        """
        in_file = self._create_input_file()
        with self.assertRaises(Exception):
            dshdpmare._extract_markdown_section(
                in_file, "# Nonexistent", None
            )

    def test4(self) -> None:
        """
        Test extracting with partial header match.
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Prepare outputs.
        expected = """
        # Results
        Our findings
        """
        expected = hprint.dedent(expected)
        # Run test.
        result = dshdpmare._extract_markdown_section(in_file, "Results", None)
        # Check outputs.
        self.assert_equal(result, expected)

    def test5(self) -> None:
        """
        Test extracting from header to end of file using "END" special value.
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Prepare outputs.
        expected = """
        # Methods

        ## Data Collection
        How we collected data

        ### Sampling Strategy
        Details about sampling

        # Results
        Our findings
        """
        expected = hprint.dedent(expected)
        # Run test.
        result = dshdpmare._extract_markdown_section(
            in_file, "# Methods", "END"
        )
        # Check outputs.
        self.assert_equal(result, expected)

    def test6(self) -> None:
        """
        Test extracting with "END" from nested header to file end.
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Prepare outputs - should include everything from "Data Collection" to end.
        expected = """
        ## Data Collection
        How we collected data

        ### Sampling Strategy
        Details about sampling

        # Results
        Our findings
        """
        expected = hprint.dedent(expected)
        # Run test.
        result = dshdpmare._extract_markdown_section(
            in_file, "Data Collection", "END"
        )
        # Check outputs.
        self.assert_equal(result, expected)

    @pytest.mark.slow
    def test7(self) -> None:
        """
        Test that intermediate file is created.
        """
        # Prepare inputs.
        in_file = self._create_input_file()
        # Run test.
        dshdpmare._extract_markdown_section(in_file, "# Methods", "# Results")
        # Check outputs.
        tmp_file = dshdpmare._TMP_EXTRACT_FILE
        self.assertTrue(
            os.path.exists(tmp_file),
            f"Intermediate file {tmp_file} was not created",
        )


# #############################################################################
# Test_piper_markdown_reader_script
# #############################################################################


@pytest.mark.skip(reason="Requires piper-tts installation and voice models")
class Test_piper_markdown_reader_script(hunitest.TestCase):
    """
    Test piper_markdown_reader script CLI functionality.
    """

    def _create_input_file(self) -> None:
        """
        Create the test markdown input file.
        """
        content = """
        # Introduction

        This is the introduction section.

        # Methods

        ## Data Collection

        How we collected data.

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
        self._create_input_file()

    def _run_script(self, args: str = "") -> None:
        """
        Helper to run the script with given arguments.

        :param args: additional command line arguments
        """
        in_file = os.path.join(self.get_input_dir(), "input.md")
        script_path = hgit.find_file_in_git_tree("piper_markdown_reader.py")
        cmd = f"{script_path} --input {in_file} --no_play {args}"
        hsystem.system(cmd)

    def test1(self) -> None:
        """
        Test script runs with --md_start and --md_end arguments.
        """
        # Run test.
        self._run_script("--md_start '# Methods' --md_end '# Results'")

    def test2(self) -> None:
        """
        Test script runs with --md_start only (auto-detect end).
        """
        # Run test.
        self._run_script("--md_start '# Results'")

    def test3(self) -> None:
        """
        Test script runs with --md_start and --md_end 'END' (extract to file end).
        """
        # Run test.
        self._run_script("--md_start '# Methods' --md_end 'END'")

    def test4(self) -> None:
        """
        Test script runs without --md_start (full file).
        """
        # Run test.
        self._run_script("")

    @pytest.mark.slow
    def test5(self) -> None:
        """
        Test script creates intermediate file when --md_start provided.
        """
        # Run test.
        self._run_script("--md_start '# Methods' --md_end '# Results'")
        # Check outputs.
        tmp_file = dshdpmare._TMP_EXTRACT_FILE
        self.assertTrue(
            os.path.exists(tmp_file),
            f"Intermediate file {tmp_file} was not created",
        )
