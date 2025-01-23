import logging
import os

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.amp_check_md_toc_headers as lacmtohe

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_fix_md_headers
# #############################################################################


class Test_fix_md_headers(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test that no modifications are made when headers are correct.
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
        # Run.
        lines = hio.from_file(file_path).splitlines()
        updated_lines = lacmtohe.fix_md_headers(lines, file_path)
        # Check.
        self.assertEqual(updated_lines, txt_correct.splitlines())

    def test2(self) -> None:
        """
        Test that header levels are adjusted correctly.
        """
        txt_with_skipped_headers = """
        # Given Header level 1; no change

        ### Given Header level 3; change to 2

        ## Given Header level 2; no change

        #### Given Header level 4; change to 3
        """
        file_name = "test_header_levels.md"
        file_path = self._write_input_file(txt_with_skipped_headers, file_name)
        # Run.
        lines = hio.from_file(file_path).splitlines()
        updated_lines = lacmtohe.fix_md_headers(lines, file_path)
        # Check.
        output = "\n".join(
            ["# linter warnings", ""]
            + []
            + ["", "# linted file", ""]
            + updated_lines
        )
        self.check_string(output)

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


# #############################################################################
# Test_verify_toc_postion
# #############################################################################


class Test_verify_toc_postion(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test that a warning is issued when content appears before TOC.
        """
        txt = """
        # Introduction

        Some introductory content before TOC.

        <!-- toc -->

        - [Header](#header)

        <!-- tocstop -->

        # Header
        """
        file_name = "test.md"
        file_path = self._write_input_file(txt, file_name)
        # Run.
        lines = hio.from_file(file_path).splitlines()
        out_warnings = lacmtohe.verify_toc_position(lines, file_path)
        # Check.
        output = "\n".join(
            ["# linter warnings", ""]
            + out_warnings
            + ["", "# linted file", ""]
            + []
        )
        self.check_string(output)

    def test2(self) -> None:
        """
        Test that no warnings are issued when TOC is correct.

        - TOC is at the start of the file.
        - No empty lines and spaces before the TOC
        """
        txt_correct = """
        <!-- toc -->

        - [Header 1](#header-1)
        - [Header 2](#header-2)

        <!-- tocstop -->

        # Header 1

        ## Header 2
        """
        file_name = "test_correct_toc_and_headers.md"
        file_path = self._write_input_file(txt_correct, file_name)
        # Run.
        lines = hio.from_file(file_path).splitlines()
        out_warnings = lacmtohe.verify_toc_position(lines, file_path)
        # Check.
        self.assertEqual(out_warnings, [])

    def test3(self) -> None:
        """
        Test that no warnings are issued when TOC is correct.

        - TOC is not at the start of the file.
        - Headers and empty lines before the TOC.
        """
        txt_correct = """
            # Header 1

            # Header 2


            <!-- toc -->

            - [header 3](#header-3)
            - [header 4](#header-4)

            <!-- tocstop -->

            ## Header 3

            ## Header 4
        """
        file_name = "test_correct_toc_and_headers.md"
        file_path = self._write_input_file(txt_correct, file_name)
        # Run.
        lines = hio.from_file(file_path).splitlines()
        out_warnings = lacmtohe.verify_toc_position(lines, file_path)
        # Check.
        self.assertEqual(out_warnings, [])

    def test4(self) -> None:
        """
        Test that no warnings are issued if TOC is not present.
        """
        txt = """
        # Header 1

        This file has no TOC.

        ## Header 2

        No warning should be generated.
        """
        file_name = "test.md"
        file_path = self._write_input_file(txt, file_name)
        # Run.
        lines = hio.from_file(file_path).splitlines()
        out_warnings = lacmtohe.verify_toc_position(lines, file_path)
        # Check.
        self.assertEqual(out_warnings, [])

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
