import logging
import os

import pytest

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.amp_check_md_toc_headers as lacmdtoch

_LOG = logging.getLogger(__name__)

# #############################################################################
# Test_process_markdown_file
# #############################################################################


class Test_process_markdown_file(hunitest.TestCase):
    """
    Unit tests for `process_markdown_file` function.
    """

    def test1(self) -> None:
        """
        Test that a warning is issued when content appears before TOC.
        """
        txt_without_toc = """
        # Introduction

        Some introductory content before TOC.

        Table of Contents

        - [Introduction](#introduction)
        """
        file_name = "test_no_toc.md"
        file_path = self._write_input_file(txt_without_toc, file_name)
        # Run the process_markdown_file function.
        _, updated_lines, out_warnings = lacmdtoch.process_markdown_file(file_path)
        # Check the output warnings.
        output = "\n".join(
            ["# linter warnings", ""]
            + out_warnings
            + ["", "# linted file", ""]
            + updated_lines
        )
        self.check_string(output)

    def test2(self) -> None:
        """
        Test that header levels are adjusted correctly.
        """
        txt_with_skipped_headers = """
        # Header 1

        ### Header 3
        """
        file_name = "test_header_levels.md"
        file_path = self._write_input_file(txt_with_skipped_headers, file_name)
        # Run the process_markdown_file function.
        _, updated_lines, out_warnings = lacmdtoch.process_markdown_file(file_path)
        # Check the output warnings and fixed lines.
        output = "\n".join(
            ["# linter warnings", ""]
            + out_warnings
            + ["", "# linted file", ""]
            + updated_lines
        )
        self.check_string(output)

    def test3(self) -> None:
        """
        Test that no warnings are issued when TOC and headers are correct.
        """
        txt_correct = """
        Table of Contents

        - [Header 1](#header-1)
        - [Header 2](#header-2)

        # Header 1

        ## Header 2
        """
        file_name = "test_correct_toc_and_headers.md"
        file_path = self._write_input_file(txt_correct, file_name)
        # Run the process_markdown_file function.
        _, updated_lines, out_warnings = lacmdtoch.process_markdown_file(file_path)
        # Check that there are no warnings.
        self.assertEqual(out_warnings, [])
        # Check that the updated lines match the input.
        self.assertEqual(updated_lines, txt_correct.splitlines())

    def _write_input_file(self, txt: str, file_name: str) -> str:
        """
        Write test content to a file.

        :param txt: the content of the file
        :param file_name: the name of the file
        :return: the path to the file
        """
        # Get the path to the scratch space.
        dir_name = self.get_scratch_space()
        # Compile the file path.
        file_path = os.path.join(dir_name, file_name)
        file_path = os.path.abspath(file_path)
        # Write the file.
        hio.to_file(file_path, txt)
        return file_path
