import json
import os
from unittest import mock

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.extract_toc_from_txt as dshdextt


def _get_sample_header_list() -> list:
    """
    Build a sample list of `HeaderInfo` objects for testing.

    :return: list of headers spanning levels 1, 2, and 5
    """
    header_list = [
        hmarkdo.HeaderInfo(1, "Chapter 1", 1),
        hmarkdo.HeaderInfo(2, "Section 1.1", 2),
        hmarkdo.HeaderInfo(5, "Slide 1", 3),
        hmarkdo.HeaderInfo(5, "Slide 2", 4),
        hmarkdo.HeaderInfo(2, "Section 1.2", 5),
        hmarkdo.HeaderInfo(5, "Slide 3", 6),
        hmarkdo.HeaderInfo(1, "Chapter 2", 7),
    ]
    return header_list


# #############################################################################
# Test_extract_toc_from_txt_script1
# #############################################################################


class Test_extract_toc_from_txt_script1(hunitest.TestCase):
    def helper(self, file: str, extra_args: str = "") -> None:
        """
        Test helper for script execution.

        :param file: Input file name
        :param extra_args: Extra command-line arguments
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        in_file = os.path.join(input_dir, file)
        # Build command to call the script.
        script_path = hgit.find_file_in_git_tree("extract_toc_from_txt.py")
        scratch_space = self.get_scratch_space()
        out_file = os.path.join(scratch_space, "output.txt")
        cmd = f"{script_path} --input {in_file} --output {out_file} --mode list --max_level 3 {extra_args}"
        # Run the script.
        hsystem.system(cmd)
        # Read the actual output.
        actual = hio.from_file(out_file)
        # Prepare expected output.
        output_dir = self.get_output_dir()
        expected_file = os.path.join(output_dir, "test.txt")
        expected = hio.from_file(expected_file)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test extraction of headers from a Markdown file.
        """
        self.helper("input.md")

    def test2(self) -> None:
        """
        Test extraction of headers from a LaTeX file.
        """
        self.helper("input.tex")

    def test3(self) -> None:
        """
        Test extraction of headers from a txt slide file.
        """
        self.helper("input.txt")

    def test4(self) -> None:
        """
        Test extraction of headers from a Jupyter notebook file.
        """
        self.helper("input.ipynb")

    def test5(self) -> None:
        """
        Test extraction of headers with slide counts from a Markdown file.
        """
        self.helper("input.md", extra_args="--count_slides")


# #############################################################################
# Test_count_headers_by_level
# #############################################################################


class Test_count_headers_by_level(hunitest.TestCase):
    """
    Test the `_count_headers_by_level()` function.
    """

    def helper(self, target_level: int, expected: dict) -> None:
        """
        Test helper for `_count_headers_by_level()`.

        :param target_level: Target header level to count
        :param expected: Expected result dictionary
        """
        # Prepare inputs.
        header_list = _get_sample_header_list()
        # Run test.
        actual = dshdextt._count_headers_by_level(header_list, target_level=target_level)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test count level-5 headers per (h1, h2) and h1 totals.
        """
        # Prepare outputs.
        expected = {
            ("Chapter 1", "Section 1.1"): 2,
            ("Chapter 1", None): 3,
            ("Chapter 1", "Section 1.2"): 1,
        }
        # Run test.
        self.helper(target_level=5, expected=expected)

    def test2(self) -> None:
        """
        Test no headers of the target level returns an empty dict.
        """
        # Prepare outputs.
        expected: dict = {}
        # Run test.
        self.helper(target_level=3, expected=expected)


# #############################################################################
# Test_format_headers_with_counts
# #############################################################################


class Test_format_headers_with_counts(hunitest.TestCase):
    """
    Test the `_format_headers_with_counts()` function.
    """

    def helper(self, mode: str, max_level: int, expected: str) -> None:
        """
        Test helper for `_format_headers_with_counts()`.

        :param mode: Output mode ("headers" or "list")
        :param max_level: Maximum header level to include
        :param expected: Expected formatted output
        """
        # Prepare inputs.
        header_list = _get_sample_header_list()
        counts = dshdextt._count_headers_by_level(header_list, target_level=5)
        # Run test.
        actual = dshdextt._format_headers_with_counts(
            header_list, mode, counts, max_level=max_level
        )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test `headers` mode annotates h1/h2 with slide counts.
        """
        # Prepare outputs.
        expected = """
        # Chapter 1 (3)
        ## Section 1.1 (2)
        ## Section 1.2 (1)
        # Chapter 2
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(mode="headers", max_level=2, expected=expected)

    def test2(self) -> None:
        """
        Test `list` mode with headers beyond level 2 use the
        original indentation-based formatting.
        """
        # Prepare outputs.
        expected = """
        - Chapter 1 (3)
          - Section 1.1 (2)
                - Slide 1
                - Slide 2
          - Section 1.2 (1)
                - Slide 3
        - Chapter 2
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(mode="list", max_level=5, expected=expected)


# #############################################################################
# Test_extract_headers_from_markdown
# #############################################################################


class Test_extract_headers_from_markdown(hunitest.TestCase):
    """
    Test the `_extract_headers_from_markdown()` function.
    """

    def test1(self) -> None:
        """
        Test writes markdown headers to the output file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        output_file = os.path.join(scratch_dir, "output.txt")
        content = """
        # Chapter 1
        Text.
        ## Section 1.1
        More text.
        """
        content = hprint.dedent(content)
        lines = content.split("\n")
        # Prepare outputs.
        expected = content
        mode = "headers"
        max_level = 3
        # Run test.
        dshdextt._extract_headers_from_markdown(
            input_file, lines, mode, max_level, output_file
        )
        # Check outputs.
        actual = hio.from_file(output_file)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_extract_headers_from_latex
# #############################################################################


class Test_extract_headers_from_latex(hunitest.TestCase):
    """
    Test the `_extract_headers_from_latex()` function.
    """

    def test1(self) -> None:
        """
        Test writes LaTeX section headers to the output file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.tex")
        output_file = os.path.join(scratch_dir, "output.txt")
        content = r"""
        \section{Chapter 1}
        Text.
        \subsection{Section 1.1}
        More text.
        """
        content = hprint.dedent(content)
        lines = content.split("\n")
        # Prepare outputs.
        expected = """
        # Chapter 1
        ## Section 1.1
        """
        expected = hprint.dedent(expected)
        # Prepare outputs.
        mode = "headers"
        max_level = 3
        show_num_slides = False
        # Run test.
        dshdextt._extract_headers_from_latex(
            input_file, lines, mode, max_level, output_file, show_num_slides
        )
        # Check outputs.
        actual = hio.from_file(output_file)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_extract_headers_from_txtslides
# #############################################################################


class Test_extract_headers_from_txtslides(hunitest.TestCase):
    """
    Test the `_extract_headers_from_txtslides()` function.
    """

    def test1(self) -> None:
        """
        Test writes txt-slide headers to the output file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.txt")
        output_file = os.path.join(scratch_dir, "output.txt")
        content = """
        # Chapter 1
        Text.
        ## Section 1.1
        More text.
        """
        content = hprint.dedent(content)
        lines = content.split("\n")
        # Prepare outputs.
        expected = """
        # Chapter 1
        ## Section 1.1
        """
        expected = hprint.dedent(expected)
        # Prepare outputs.
        mode = "headers"
        max_level = 3
        show_num_slides = False
        # Run test.
        dshdextt._extract_headers_from_txtslides(
            input_file, lines, mode, max_level, output_file, show_num_slides
        )
        # Check outputs.
        actual = hio.from_file(output_file)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_extract_headers_from_notebook
# #############################################################################


class Test_extract_headers_from_notebook(hunitest.TestCase):
    """
    Test the `_extract_headers_from_notebook()` function.
    """

    def test1(self) -> None:
        """
        Test writes headers extracted from markdown cells.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.ipynb")
        output_file = os.path.join(scratch_dir, "output.txt")
        notebook = {
            "cells": [
                {"cell_type": "markdown", "source": ["# Chapter 1\n"]},
                {"cell_type": "code", "source": ["print('hi')\n"]},
                {"cell_type": "markdown", "source": "## Section 1.1\n"},
            ]
        }
        lines = json.dumps(notebook).split("\n")
        # Prepare outputs.
        expected = """
        # Chapter 1
        ## Section 1.1
        """
        expected = hprint.dedent(expected)
        # Prepare outputs.
        mode = "headers"
        max_level = 3
        show_num_slides = False
        # Run test.
        dshdextt._extract_headers_from_notebook(
            input_file, lines, mode, max_level, output_file, show_num_slides
        )
        # Check outputs.
        actual = hio.from_file(output_file)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_extract_toc_from_txt_py_main
# #############################################################################


class Test_extract_toc_from_txt_py_main(hunitest.TestCase):
    """
    Test `_main()` called directly (in-process) with mocked `sys.argv`.
    """

    def _run_main(self, argv: list) -> str:
        """
        Run `dshdextt._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        :return: content of the output file
        """
        parser = dshdextt._parse()
        with mock.patch("sys.argv", argv):
            dshdextt._main(parser)
        output_file = argv[argv.index("--output") + 1]
        actual = hio.from_file(output_file)
        return actual

    def _helper_extract_headers(
        self, extension: str, content: str, expected: str
    ) -> None:
        """
        Test helper for extracting headers from different file formats.

        :param extension: File extension (.md, .tex, .txt, .ipynb)
        :param content: File content to write
        :param expected: Expected output
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, f"input{extension}")
        output_file = os.path.join(scratch_dir, "output.txt")
        hio.to_file(input_file, content)
        argv = [
            "extract_toc_from_txt.py",
            "--input",
            input_file,
            "--output",
            output_file,
            "--mode",
            "headers",
        ]
        # Run test.
        actual = self._run_main(argv)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test extracts markdown headers via the `.md` dispatch
        branch.
        """
        # Prepare inputs.
        content = """
        # Chapter 1
        Text.
        """
        content = hprint.dedent(content)
        expected = "# Chapter 1"
        # Run test.
        self._helper_extract_headers(".md", content, expected)

    def test2(self) -> None:
        """
        Test unsupported file extension raises a `ValueError`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.foo")
        output_file = os.path.join(scratch_dir, "output.txt")
        hio.to_file(input_file, "some text")
        argv = [
            "extract_toc_from_txt.py",
            "--input",
            input_file,
            "--output",
            output_file,
        ]
        parser = dshdextt._parse()
        # Run test and check output.
        with mock.patch("sys.argv", argv):
            with self.assertRaises(ValueError):
                dshdextt._main(parser)

    def test3(self) -> None:
        """
        Test extracts LaTeX headers via the `.tex` dispatch
        branch.
        """
        # Prepare inputs.
        content = r"\section{Chapter 1}" + "\n"
        expected = "# Chapter 1"
        # Run test.
        self._helper_extract_headers(".tex", content, expected)

    def test4(self) -> None:
        """
        Test extracts txt-slide headers via the `.txt` dispatch
        branch.
        """
        # Prepare inputs.
        content = "# Chapter 1\n"
        expected = "# Chapter 1"
        # Run test.
        self._helper_extract_headers(".txt", content, expected)

    def test5(self) -> None:
        """
        Test extracts notebook headers via the `.ipynb` dispatch
        branch.
        """
        # Prepare inputs.
        notebook = {
            "cells": [
                {"cell_type": "markdown", "source": ["# Chapter 1\n"]},
            ]
        }
        content = json.dumps(notebook)
        expected = "# Chapter 1"
        # Run test.
        self._helper_extract_headers(".ipynb", content, expected)

    def test6(self) -> None:
        """
        Test `cfile` mode writes Vim quickfix formatted output.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        output_file = os.path.join(scratch_dir, "output.txt")
        content = "# Chapter 1\n"
        hio.to_file(input_file, content)
        argv = [
            "extract_toc_from_txt.py",
            "--input",
            input_file,
            "--output",
            output_file,
            "--mode",
            "cfile",
        ]
        # Run test.
        actual = self._run_main(argv)
        # Check outputs: cfile format includes filename and header text.
        self.assertIn(input_file, actual)
        self.assertIn("Chapter 1", actual)

    def test7(self) -> None:
        """
        Test `--count_slides` annotates headers with slide
        counts.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        output_file = os.path.join(scratch_dir, "output.txt")
        content = """
        # Chapter 1
        ## Section 1.1
        ### Sub 1
        #### Sub 2
        ##### Slide 1
        ##### Slide 2
        """
        content = hprint.dedent(content)
        hio.to_file(input_file, content)
        argv = [
            "extract_toc_from_txt.py",
            "--input",
            input_file,
            "--output",
            output_file,
            "--mode",
            "headers",
            "--count_slides",
        ]
        # Prepare outputs.
        expected = """
        # Chapter 1 (2)
        ## Section 1.1 (2)
        ### Sub 1
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self._run_main(argv)
        # Check outputs.
        self.assert_equal(actual, expected)
