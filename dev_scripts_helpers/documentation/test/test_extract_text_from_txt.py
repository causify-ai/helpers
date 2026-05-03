import logging
import os

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown_headers as hmarhead
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_find_header_line
# #############################################################################


class Test_find_header_line(hunitest.TestCase):
    """
    Test _find_header_line function.
    """

    def test1(self) -> None:
        """
        Test finding a single header in a header list.
        """
        # Prepare inputs.
        from dev_scripts_helpers.documentation import extract_text_from_txt

        header_list = [
            hmarhead.HeaderInfo(1, "Introduction", 1),
            hmarhead.HeaderInfo(2, "Background", 5),
            hmarhead.HeaderInfo(1, "Methods", 13),
        ]
        # Run test.
        line_num = extract_text_from_txt._find_header_line(
            "# Introduction", header_list
        )
        # Check outputs.
        self.assertEqual(line_num, 1)

    def test2(self) -> None:
        """
        Test finding a level 2 header.
        """
        # Prepare inputs.
        from dev_scripts_helpers.documentation import extract_text_from_txt

        header_list = [
            hmarhead.HeaderInfo(1, "Introduction", 1),
            hmarhead.HeaderInfo(2, "Background", 5),
            hmarhead.HeaderInfo(1, "Methods", 13),
        ]
        # Run test.
        line_num = extract_text_from_txt._find_header_line(
            "## Background", header_list
        )
        # Check outputs.
        self.assertEqual(line_num, 5)

    def test3(self) -> None:
        """
        Test error when header is not found.
        """
        # Prepare inputs.
        from dev_scripts_helpers.documentation import extract_text_from_txt

        header_list = [
            hmarhead.HeaderInfo(1, "Introduction", 1),
        ]
        # Run test and check output.
        with self.assertRaises(ValueError):
            extract_text_from_txt._find_header_line(
                "# Nonexistent", header_list
            )

    def test4(self) -> None:
        """
        Test error when header format is invalid.
        """
        # Prepare inputs.
        from dev_scripts_helpers.documentation import extract_text_from_txt

        header_list = [
            hmarhead.HeaderInfo(1, "Introduction", 1),
        ]
        # Run test and check output.
        with self.assertRaises(ValueError):
            extract_text_from_txt._find_header_line(
                "Invalid header", header_list
            )


# #############################################################################
# Test_extract_text_from_txt_script1
# #############################################################################


class Test_extract_text_from_txt_script1(hunitest.TestCase):
    """
    Test extract_text_from_txt script functionality.
    """

    def _run_script(
        self, input_file: str, args: str = ""
    ) -> tuple:
        """
        Helper to run the script and return output file path and output.

        :param input_file: input file name in scratch space
        :param args: additional arguments to pass to script
        :return: tuple of (out_file, output_content)
        """
        in_file = os.path.join(self.get_input_dir(), input_file)
        script_path = hgit.find_file_in_git_tree(
            "extract_text_from_txt.py"
        )
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        cmd = f"{script_path} -i {in_file} -o {out_file} {args}"
        result = hsystem.system(cmd)
        actual = hio.from_file(out_file)
        return out_file, actual, result

    def test1(self) -> None:
        """
        Test extracting text between two headers.
        """
        # Prepare inputs.
        args = "--start '# Methods' --end '# Results'"
        # Run test.
        _, actual, _ = self._run_script("input.md", args)
        # Check outputs.
        self.check_string(actual)

    def test2(self) -> None:
        """
        Test extracting from file start to a header.
        """
        # Prepare inputs.
        args = "--end '# Methods'"
        # Run test.
        _, actual, _ = self._run_script("input.md", args)
        # Check outputs.
        self.check_string(actual)

    def test3(self) -> None:
        """
        Test extracting from a header to file end.
        """
        # Prepare inputs.
        args = "--start '# Results'"
        # Run test.
        _, actual, _ = self._run_script("input.md", args)
        # Check outputs.
        self.check_string(actual)

    def test4(self) -> None:
        """
        Test extracting between level 2 headers.
        """
        # Prepare inputs.
        args = "--start '## Background' --end '## Motivation'"
        # Run test.
        _, actual, _ = self._run_script("input.md", args)
        # Check outputs.
        self.check_string(actual)

    def test5(self) -> None:
        """
        Test dry run mode outputs line numbers only.
        """
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "input.md")
        script_path = hgit.find_file_in_git_tree(
            "extract_text_from_txt.py"
        )
        cmd = f"{script_path} -i {in_file} --start '# Methods' --end '# Results' --dry_run"
        # Run test.
        _, output = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertIn("start_line_num=", output)
        self.assertIn("end_line_num=", output)

    def test6(self) -> None:
        """
        Test error message when header is not found.
        """
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "input.md")
        script_path = hgit.find_file_in_git_tree(
            "extract_text_from_txt.py"
        )
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        cmd = f"{script_path} -i {in_file} -o {out_file} --start '# Nonexistent'"
        # Run test and check output.
        try:
            hsystem.system(cmd)
            self.fail("Expected script to fail when header not found")
        except Exception as e:
            _LOG.info(f"Got expected error: {e}")
